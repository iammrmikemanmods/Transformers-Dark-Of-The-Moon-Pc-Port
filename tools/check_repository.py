"""Fail closed on common proprietary/binary inputs in the tracked tree."""
from pathlib import Path
import subprocess
import sys

FORBIDDEN_SUFFIXES = {".iso", ".xex", ".xexp", ".7z", ".zip", ".rar", ".upk",
                      ".xxx", ".u", ".bik", ".bnk", ".xma", ".pak", ".pcc",
                      ".usm", ".exe", ".dll", ".pdb", ".obj", ".lib"}
FORBIDDEN_ROOTS = {".local", "private", "originals", "extracted", "generated", "build"}


def forbidden_path(name):
    path = Path(name.lower())
    return (path.parts[0] in FORBIDDEN_ROOTS or path.suffix in FORBIDDEN_SUFFIXES
            or ".7z." in path.name or name.lower().startswith("reports/local/"))


def main():
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(["git", "ls-files", "-z"], cwd=root,
                            check=True, capture_output=True)
    rejected = []
    for encoded in result.stdout.split(b"\0"):
        if not encoded:
            continue
        name = encoded.decode("utf-8", errors="strict")
        path = root / name
        if forbidden_path(name) or path.is_symlink() or not path.is_file():
            rejected.append(name)
            continue
        if path.stat().st_size > 1024 * 1024:
            rejected.append(name)
            continue
        data = path.read_bytes()
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            rejected.append(name)
        else:
            if b"\0" in data:
                rejected.append(name)
    if rejected:
        print("Publication guard rejected tracked paths:", *rejected, sep="\n", file=sys.stderr)
        return 1
    print("Tracked-file publication guard passed; manual content review is still required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
