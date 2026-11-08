#!/usr/bin/env bash
# Linux-only, user-scoped install. Never reads any game input.
set -euo pipefail
umask 077
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"
for command in python java curl unzip sha256sum git; do
    command -v "$command" >/dev/null || { echo "Missing dependency: $command" >&2; exit 2; }
done
python - <<'PY'
from pathlib import Path
import sys
if sys.version_info < (3, 11):
    raise SystemExit('Python 3.11+ is required')
for p in (Path('.local'), Path('.local/toolchains')):
    if p.is_symlink():
        raise SystemExit('Refusing linked toolchain directory')
PY
git check-ignore --quiet .local/toolchains/probe || { echo '.local is not ignored; refusing installation' >&2; exit 2; }
base="$root/.local/toolchains"
target="$base/ghidra-12.1.3"
mkdir -p "$base"
if [[ -e "$target" || -L "$target" ]]; then
    [[ ! -L "$target" && -f "$target/SHA256SUMS" ]] || { echo 'Incomplete or linked installation; preserve it and choose recovery in docs/CLOUD_PHASE1.md' >&2; exit 2; }
    (cd "$target" && sha256sum --quiet -c SHA256SUMS)
    echo 'Existing pinned toolchain files match the local installation manifest.'
    exit 0
fi
stage="$(mktemp -d "$base/.ghidra-stage.XXXXXXXX")"
trap 'rm -rf -- "$stage"' EXIT
curl --fail --location --proto '=https' --proto-redir '=https' --tlsv1.2 --retry 2 --connect-timeout 30 \
    'https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_12.1.3_build/ghidra_12.1.3_PUBLIC_20260817.zip' \
    --output "$stage/ghidra.zip"
curl --fail --location --proto '=https' --proto-redir '=https' --tlsv1.2 --retry 2 --connect-timeout 30 \
    'https://github.com/zeroKilo/XEXLoaderWV/releases/download/12.1.3/ghidra_12.1.3_PUBLIC_20260920_XEXLoaderWV.zip' \
    --output "$stage/xexloader.zip"
(cd "$stage" && printf '%s\n' \
 '93a5d11a9ad510622acaaf908c556a7b9b764d338e78a7567f3689bf5081fd54  ghidra.zip' \
 'afdaf425bb8e16706f28a453a836ac84fcd0d5000f93a2275a02105807d030a3  xexloader.zip' | sha256sum -c -)
mkdir "$stage/install"
unzip -q "$stage/ghidra.zip" -d "$stage/install"
home="$stage/install/ghidra_12.1.3_PUBLIC"
test -f "$home/Ghidra/application.properties"
grep -qx 'application.version=12.1.3' "$home/Ghidra/application.properties"
unzip -q "$stage/xexloader.zip" -d "$home/Ghidra/Extensions"
test -f "$home/Ghidra/Extensions/XEXLoaderWV/extension.properties"
chmod u+x "$home/support/analyzeHeadless"
printf '%s\n' 'Ghidra archive SHA-256: 93a5d11a9ad510622acaaf908c556a7b9b764d338e78a7567f3689bf5081fd54' \
 'XEXLoaderWV archive SHA-256: afdaf425bb8e16706f28a453a836ac84fcd0d5000f93a2275a02105807d030a3' \
 'Pinned releases: Ghidra_12.1.3_build; XEXLoaderWV 12.1.3' > "$stage/install/PROVENANCE.txt"
(cd "$stage/install" && find ghidra_12.1.3_PUBLIC PROVENANCE.txt -type f -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS)
mv -- "$stage/install" "$target"
echo "Installed pinned toolchain: $target"
echo 'Installation is not proof of an XEX import. Run the synthetic smoke test next.'
