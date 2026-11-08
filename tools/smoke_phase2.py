"""Verify the Phase 2 Ghidra script on four synthetic PPC bytes, not DOTM."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

import run_phase1
import run_phase2


def main() -> int:
    base = run_phase1.ROOT / ".local/smoke"
    base.mkdir(parents=True, exist_ok=True)
    output = Path(tempfile.mkdtemp(prefix="phase2-ppc-", dir=base)).resolve()
    source = output / "synthetic-ppc.bin"
    payload = bytes.fromhex("4e800020")
    source.write_bytes(payload)
    command = run_phase1.headless_command(run_phase1.ROOT, source, output, smoke=True)
    index = command.index("-log")
    command[index:index] = [
        "-postScript", "DotmPhase2Probe.java",
        str(output / "phase2-pe.json"), str(source), "synthetic"
    ]
    subprocess.run(command, cwd=run_phase1.ROOT, check=True, timeout=300)
    report = json.loads((output / "phase2-pe.json").read_text(encoding="utf-8"))
    assert report["schema_version"] == 2
    assert report["kind"] == "synthetic"
    assert report["source_sha256"] == hashlib.sha256(payload).hexdigest()
    assert report["entry_instruction_decoded"] is True
    assert report["mz_verified"] is False
    assert report["pe_signature_verified"] is False
    assert report["full_auto_analysis_performed"] is False
    print("PASS: Phase 2 script compiled and decoded a synthetic PPC blr.")
    print("NO XEX decryption, private PE validation, or real game analysis was performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
