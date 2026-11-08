"""Cloud smoke test using only one synthetic PowerPC blr instruction."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from run_phase1 import ROOT, headless_command, validate_import


def main() -> int:
    base = ROOT / '.local/smoke'
    base.mkdir(parents=True, exist_ok=True)
    # Deliberately retain this synthetic-only evidence for inspection.
    output = Path(tempfile.mkdtemp(prefix='ppc-', dir=base)).resolve()
    source = output / 'synthetic-ppc.bin'
    payload = bytes.fromhex('4e800020')  # blr: return using the link register.
    source.write_bytes(payload)
    (output / 'project').mkdir()
    command = headless_command(ROOT, source, output, smoke=True)
    subprocess.run(command, cwd=ROOT, check=True, timeout=300)
    report = json.loads((output / 'ghidra-import.json').read_text(encoding='utf-8'))
    validate_import(report, hashlib.sha256(payload).hexdigest(), xex=False)
    print('PASS: pinned Ghidra starts; XEX extension is discovered; PPC import and JSON export work.')
    print('Fixture: four synthetic bytes. NOT an XEX payload/decompression test or a DOTM result.')
    print(f'Synthetic evidence retained at: {output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
