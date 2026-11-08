#!/usr/bin/env bash
set -euo pipefail
umask 077
cd "$(dirname "${BASH_SOURCE[0]}")/.."
python --version
java -version
git check-ignore --quiet .local/source/default.xex
python tools/check_repository.py
python -m unittest discover -s tests -v
bash tools/bootstrap_ghidra.sh
python tools/smoke_ghidra.py
mkdir -p .local/source
printf '\n%s\n' \
 'Cloud toolchain smoke test completed; no original game was analyzed.' \
 'Upload your own default.xex into .local/source/ using the Codespace Explorer.' \
 'Then run: python tools/run_phase1.py' \
 'Do not commit .local or upload it as a GitHub artifact.'
