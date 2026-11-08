"""Phase 2: validate a private DOTM XEX reconstruction and one PPC entry instruction.

The pinned XEXLoaderWV extension reconstructs the PE in Ghidra memory. This
runner never exports recovered PE bytes or disassembly and never runs in Actions.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import uuid

import run_phase1 as phase1
import source_intake

ROOT = phase1.ROOT
EXPECTED_SHA256 = "6fd9ae9fb94ea8e9cc91a6a0cc62b04441411bdafe2479f0d380d4a3a9957ca6"
EXPECTED_SIZE = 26_591_232
EXPECTED_TITLE_ID = "0x415608A4"
EXPECTED_ENTRY = "0x8277F670"
EXPECTED_BASE = "0x82000000"
EXPECTED_IMAGE_BYTES = 28_377_088
DIGEST = re.compile(r"^[a-f0-9]{64}$")


def verify_source(observation: dict) -> None:
    if observation.get("size_bytes") != EXPECTED_SIZE:
        raise source_intake.IntakeError("Source file size does not match the verified DOTM fingerprint")
    if observation.get("sha256", "").lower() != EXPECTED_SHA256:
        raise source_intake.IntakeError("Source SHA-256 mismatch; stop before decrypting")
    xex = observation.get("xex") or {}
    execution = xex.get("execution_info") or {}
    fmt = xex.get("file_format") or {}
    image = xex.get("declared_image") or {}
    if execution.get("title_id") != EXPECTED_TITLE_ID:
        raise source_intake.IntakeError("Title ID does not match the DOTM source gate")
    if xex.get("entry_point_header_value") != EXPECTED_ENTRY:
        raise source_intake.IntakeError("XEX entry point differs from the recorded source")
    if xex.get("image_base_header_value") != EXPECTED_BASE:
        raise source_intake.IntakeError("XEX image base differs from the recorded source")
    if fmt.get("encryption_type") != 1 or fmt.get("compression_type") != 1:
        raise source_intake.IntakeError("Unexpected XEX encryption or compression declaration")
    if image.get("image_size_bytes") != EXPECTED_IMAGE_BYTES:
        raise source_intake.IntakeError("Declared reconstructed image size mismatch")


def validate_probe(report: dict, observation: dict) -> None:
    if not isinstance(report, dict) or report.get("schema_version") != 2:
        raise source_intake.IntakeError("Invalid Phase 2 report schema")
    if report.get("kind") != "xex":
        raise source_intake.IntakeError("Synthetic output cannot satisfy the real-source gate")
    if report.get("source_sha256") != observation["sha256"]:
        raise source_intake.IntakeError("PE verifier source hash mismatch")
    if report.get("source_size_bytes") != observation["size_bytes"]:
        raise source_intake.IntakeError("PE verifier source size mismatch")
    if report.get("language_id") != phase1.LANGUAGE:
        raise source_intake.IntakeError("PE verifier used an unexpected processor")
    if report.get("ghidra_executable_format") != "XEX Loader by Warranty Voider":
        raise source_intake.IntakeError("PE verifier did not use the XEX loader")
    if report.get("mz_verified") is not True or report.get("pe_signature_verified") is not True:
        raise source_intake.IntakeError("Decrypted PE signatures were not validated")
    if report.get("pe_optional_magic") != "0x010B":
        raise source_intake.IntakeError("Unexpected PE optional header")
    if report.get("pe_image_length_bytes") != EXPECTED_IMAGE_BYTES:
        raise source_intake.IntakeError("Reconstructed PE size mismatch")
    if report.get("xex_entry_point") != EXPECTED_ENTRY or report.get("xex_image_base") != EXPECTED_BASE:
        raise source_intake.IntakeError("Ghidra XEX entry/base differs from the source")
    if report.get("pe_image_base") != EXPECTED_BASE:
        raise source_intake.IntakeError("Reconstructed PE image base differs from the source")
    if report.get("entry_in_executable_memory") is not True:
        raise source_intake.IntakeError("Entrypoint is not in an initialized executable block")
    if report.get("entry_instruction_decoded") is not True:
        raise source_intake.IntakeError("PPC instruction was not decoded")
    if not isinstance(report.get("pe_sections"), list) or not report["pe_sections"]:
        raise source_intake.IntakeError("No validated recovered PE sections")
    if not isinstance(report.get("executable_section_count"), int) or report["executable_section_count"] < 1:
        raise source_intake.IntakeError("Recovered image does not contain executable sections")
    if not isinstance(report.get("pe_machine_hex"), str) or not re.fullmatch(r"0x[0-9A-F]{4}", report["pe_machine_hex"]):
        raise source_intake.IntakeError("Missing exact PE machine identifier")
    if not isinstance(report.get("recovered_pe_sha256_private"), str) or not DIGEST.fullmatch(report["recovered_pe_sha256_private"]):
        raise source_intake.IntakeError("Missing reconstructed image fingerprint")
    if report.get("full_auto_analysis_performed") is not False or report.get("native_pc_execution_tested") is not False:
        raise source_intake.IntakeError("Report claims work beyond this bounded gate")


def run(source: Path) -> Path:
    if os.environ.get("GITHUB_ACTIONS") == "true":
        raise source_intake.IntakeError("Real-source Phase 2 runs are disabled in public Actions")
    phase1.reject_links(source)
    runs = phase1.private_workspace(ROOT)
    observation = source_intake.inspect_xex(source)
    verify_source(observation)
    name = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:12]
    output = runs / name
    output.mkdir()
    phase1.write_json(output / "intake.json", {
        "schema_version": 1, "source": "local-independent-reinspection",
        "observed_at_utc": datetime.now(timezone.utc).isoformat(), "result": observation
    })
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                                text=True, check=True).stdout.strip()
        phase1.write_json(output / "environment.json", {
            "python": sys.version, "platform": platform.platform(),
            "repository_commit": commit, "phase": 2,
            "full_auto_analysis_performed": False
        })
        command = phase1.headless_command(ROOT, source, output)
        additional = ["-postScript", "DotmPhase2Probe.java",
                      str(output / "phase2-pe.json"), str(source.resolve()), "xex"]
        index = command.index("-log")
        command[index:index] = additional
        phase1.write_json(output / "command.json", {"argv": command, "timeout_seconds": 1200})
        with (output / "console.log").open("x", encoding="utf-8") as stream:
            result = subprocess.run(command, cwd=ROOT, stdout=stream,
                                    stderr=subprocess.STDOUT, timeout=1200, check=False)
        if result.returncode != 0:
            raise source_intake.IntakeError(
                f"Headless Ghidra exited {result.returncode}; review private logs in {output}")
        import_report = json.loads((output / "ghidra-import.json").read_text(encoding="utf-8"))
        phase1.validate_import(import_report, observation["sha256"], xex=True)
        pe_report = json.loads((output / "phase2-pe.json").read_text(encoding="utf-8"))
        validate_probe(pe_report, observation)
        final = source_intake.hash_source(source)
        if final != {key: observation[key] for key in ("size_bytes", "sha256")}:
            raise source_intake.IntakeError("Original XEX changed while being inspected")
        phase1.write_json(output / "SUCCESS.json", {
            "phase": 2, "source_hash_unchanged": True, "xex_header_verified": True,
            "ghidra_import_validated": True, "private_pe_signature_validated": True,
            "bounded_ppc_entry_instruction_verified": True,
            "full_auto_analysis_performed": False, "native_pc_build_tested": False
        })
        return output
    except Exception as error:
        phase1.write_json(output / "FAILED.json", {
            "phase": 2, "accepted": False, "error_type": type(error).__name__,
            "error": str(error), "source_hash_before": observation["sha256"]
        })
        raise


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / ".local/source/default.xex")
    args = parser.parse_args(argv)
    try:
        output = run(args.source)
        print(f"Private Phase 2 evidence directory: {output}")
        print("PE signatures and one PPC entry instruction validated; full analysis not claimed.")
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"Phase 2 STOPPED: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
