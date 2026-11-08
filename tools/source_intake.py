"""Read-only source observations; not a loader, decryptor or recompiler."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import struct
import sys

VERSION = "0.1.0"
BUILD_ID = "dotm-source-intake-0.1.0"
MAX_HEADER = 16 * 1024 * 1024
CHUNK = 1024 * 1024


class IntakeError(ValueError):
    """An input cannot be inspected safely by this limited tool."""


def _stamp(info):
    # Windows creation/change timestamps can differ between lstat and fstat on
    # the same newly created file. Identity + size + mtime are stable here;
    # the complete SHA-256 is independently pinned for real game inputs.
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)


def _check_entry(path: Path, directory: bool = False):
    info = path.lstat()
    # Includes Windows junctions and other reparse points, not just symlinks.
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
        raise IntakeError(f"Refusing link/reparse point: {path}")
    expected = stat.S_ISDIR if directory else stat.S_ISREG
    if not expected(info.st_mode):
        raise IntakeError(f"Not a {'directory' if directory else 'regular file'}: {path}")
    return info


def _hash_open(stream):
    before = os.fstat(stream.fileno())
    digest = hashlib.sha256()
    size = 0
    while block := stream.read(CHUNK):
        digest.update(block)
        size += len(block)
    after = os.fstat(stream.fileno())
    if _stamp(before) != _stamp(after) or size != after.st_size:
        raise IntakeError("Input changed while hashing; discard this observation")
    return {"size_bytes": size, "sha256": digest.hexdigest()}, _stamp(after)


def hash_source(path: Path):
    before = _check_entry(path)
    with path.open("rb") as stream:
        if _stamp(before) != _stamp(os.fstat(stream.fileno())):
            raise IntakeError("Input changed before opening")
        result, _ = _hash_open(stream)
    return result


def parse_xex_header(data: bytes, file_size: int):
    """Inspect bounds and metadata only. All multibyte XEX values are BE."""
    if len(data) < 24 or data[:4] != b"XEX2":
        raise IntakeError("Not a complete XEX2 fixed header")
    flags, header_size, reserved, security, count = struct.unpack_from(
        ">5I", data, 4)
    if not 24 <= header_size < file_size:
        raise IntakeError("Header size is outside the file or leaves no payload")
    if len(data) < header_size:
        raise IntakeError("Truncated header data")
    table_end = 24 + count * 8
    if table_end > header_size:
        raise IntakeError("Optional-header table exceeds the header")

    def span(offset, size):
        if offset < table_end or size < 0 or offset + size > header_size:
            raise IntakeError("Referenced metadata is outside the header data area")

    def u32(offset):
        return struct.unpack_from(">I", data, offset)[0]

    def hx(value):
        return f"0x{value:08X}"

    records = {}
    optional = []
    for index in range(count):
        key, value = struct.unpack_from(">II", data, 24 + index * 8)
        if key in records:
            raise IntakeError("Duplicate optional-header key")
        kind = key & 0xFF
        record = {"key": hx(key)}
        if kind <= 1:
            record.update(storage="inline", value=hx(value))
            size = 4
        else:
            if kind == 0xFF:
                span(value, 4)
                size = u32(value)
                if size < 4:
                    raise IntakeError("Variable metadata block is shorter than its size field")
            else:
                size = kind * 4
            span(value, size)
            record.update(storage="offset", offset=value, size_bytes=size)
        records[key] = (value, size)
        optional.append(record)

    execution = None
    if 0x00040006 in records:
        offset, _ = records[0x00040006]
        fields = struct.unpack_from(">4I4BI", data, offset)
        execution = {
            "media_id": hx(fields[0]), "version_packed": hx(fields[1]),
            "base_version_packed": hx(fields[2]), "title_id": hx(fields[3]),
            "platform": fields[4], "executable_table": fields[5],
            "disc_number": fields[6], "disc_count": fields[7],
            "savegame_id": hx(fields[8]),
        }
    file_format = None
    if 0x000003FF in records:
        offset, size = records[0x000003FF]
        if size < 8:
            raise IntakeError("File-format metadata is too short")
        encryption, compression = struct.unpack_from(">HH", data, offset + 4)
        file_format = {"encryption_type": encryption,
                       "compression_type": compression}

    span(security, 0x184)
    page_count = u32(security + 0x180)
    span(security, 0x184 + page_count * 24)
    declared_image = {
        "security_offset": security,
        "security_header_size_field": u32(security),
        "image_size_bytes": u32(security + 4),
        "image_flags": hx(u32(security + 0x10C)),
        "load_address": hx(u32(security + 0x110)),
        "region_flags": hx(u32(security + 0x178)),
        "allowed_media_flags": hx(u32(security + 0x17C)),
        "page_descriptor_count": page_count,
    }
    inline = lambda key: hx(records[key][0]) if key in records else None
    return {
        "magic": "XEX2", "module_flags": hx(flags),
        "header_size_bytes": header_size, "reserved": hx(reserved),
        "optional_header_count": count, "optional_headers": optional,
        "entry_point_header_value": inline(0x00010100),
        "image_base_header_value": inline(0x00010201),
        "execution_info": execution, "file_format": file_format,
        "declared_image": declared_image,
        "rsa_signature_verified": False, "pe_machine_type_verified": False,
        "limitations": ["No signature authentication or known-good hash comparison",
                        "No payload decryption, decompression or PE validation",
                        "No import resolution, disassembly or function discovery"],
    }


def inspect_xex(path: Path):
    before = _check_entry(path)
    with path.open("rb") as stream:
        if _stamp(before) != _stamp(os.fstat(stream.fileno())):
            raise IntakeError("Input changed before opening")
        fingerprint, stamp = _hash_open(stream)
        stream.seek(0)
        fixed = stream.read(24)
        if len(fixed) != 24 or fixed[:4] != b"XEX2":
            raise IntakeError("Not a complete XEX2 fixed header")
        size = struct.unpack_from(">I", fixed, 8)[0]
        if size > MAX_HEADER:
            raise IntakeError("Header exceeds this tool's 16 MiB resource limit")
        if size < 24 or size >= fingerprint["size_bytes"]:
            raise IntakeError("Header size is outside the file or leaves no payload")
        stream.seek(0)
        header = parse_xex_header(stream.read(size), fingerprint["size_bytes"])
        if stamp != _stamp(os.fstat(stream.fileno())):
            raise IntakeError("Input changed during header inspection")
    return {"source_name": path.name, **fingerprint, "known_good_match": None,
            "xex": header}


def inventory(root: Path):
    _check_entry(root, directory=True)
    entries = [{"path": ".", "kind": "directory"}]
    def fail(error):
        raise error
    for current, directories, files in os.walk(root, followlinks=False, onerror=fail):
        directories.sort()
        files.sort()
        base = Path(current)
        _check_entry(base, directory=True)
        for name in directories:
            path = base / name
            _check_entry(path, directory=True)
            entries.append({"path": path.relative_to(root).as_posix(),
                            "kind": "directory"})
        for name in files:
            path = base / name
            entries.append({"path": path.relative_to(root).as_posix(),
                            "kind": "file", **hash_source(path)})
    entries.sort(key=lambda entry: (entry["path"], entry["kind"]))
    return {"source_name": root.name, "entries": entries,
            "file_count": sum(e["kind"] == "file" for e in entries),
            "directory_count_including_root": sum(e["kind"] == "directory" for e in entries),
            "atomic_snapshot": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=BUILD_ID)
    subcommands = parser.add_subparsers(dest="command", required=True)
    for name in ("xex", "inventory"):
        sub = subcommands.add_parser(name)
        sub.add_argument("source", type=Path)
        sub.add_argument("--out", type=Path, help="New JSON report, never overwritten")
    args = parser.parse_args(argv)
    try:
        if args.out:
            target = args.out.resolve()
            source = args.source.resolve()
            if target == source or (args.command == "inventory" and target.is_relative_to(source)):
                raise IntakeError("Report must be outside the input file or source tree")
            if args.out.exists() or args.out.is_symlink():
                raise IntakeError("Report already exists; select a fresh filename")
        result = inspect_xex(args.source) if args.command == "xex" else inventory(args.source)
        report = {"schema_version": 1, "tool_version": VERSION, "build_id": BUILD_ID,
                  "observed_at_utc": datetime.now(timezone.utc).isoformat(),
                  "operation": args.command, "result": result}
        text = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            with args.out.open("x", encoding="utf-8", newline="\n") as output:
                output.write(text)
            print(f"Wrote new report: {args.out}")
        else:
            print(text, end="")
        return 0
    except (OSError, IntakeError, struct.error) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
