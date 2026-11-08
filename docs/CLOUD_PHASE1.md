# Executable Phase 1 cloud fallback

This is a source-only Linux/Codespaces fallback for private XEX intake and **Ghidra import without full auto-analysis**. It is not a decompilation, a recompiled game, or proof that the uploaded DOTM executable has been read. The original ChatGPT execution workspace returned ClientError; the GitHub connector cannot transfer those mounted binary bytes or control a Codespace terminal.

## Start from the implementation branch

Use GitHub's Code / Codespaces control on `engineering/phase1-codespaces-fallback`, not `main` while PR #2 remains unmerged. Create a Codespace from this branch. Codespaces usage and retention are subject to the owner's account; this change does not start a billed Codespace automatically. The devcontainer installs Python 3.14 and JDK 21, runs unit tests, downloads SHA-256-pinned Ghidra and XEXLoaderWV, and runs a synthetic smoke test.

After successful setup, upload the existing local `default.xex` to `.local/source/default.xex` using the Codespace Explorer. Do not upload it through the repository Add file control, a PR, issue, release, Actions artifact, or public port. No web server or port forwarding is configured. Then run:

```bash
python tools/run_phase1.py
```

There is also a VS Code task named `DOTM: Phase 1 private XEX intake and Ghidra import`. To inspect only the outer XEX headers without Java:

```bash
python tools/run_phase1.py --intake-only
```

The private runner refuses to execute under GitHub Actions. Public CI uses independently created synthetic fixtures only.

## Evidence and failure handling

Each invocation creates a unique ignored `.local/runs/<UTC timestamp>-<random id>/` directory. Outputs include `intake.json`, environment and exact-command records, Ghidra logs, a private Ghidra project and `ghidra-import.json`. `SUCCESS.json` is written only after the relevant gates pass and the input SHA-256 remains unchanged. A Ghidra exit code of zero is insufficient: the JSON report must exist, the XEX loader and expected PowerPC language must be present, a memory block must exist, and Ghidra's input hash must match the intake hash. Failures preserve diagnostics with `FAILED.json` where the run directory was established. Missing/malformed inputs may stop before a run directory is created. Existing evidence is not overwritten.

Metadata includes declared XEX fields, image base, imported memory blocks, entry points, library names, language/endianness and imported function count. Imported function count is not complete function discovery. No decompiled C, instruction listing, game bytes, signature authentication, retail validity, or PC gameplay result is claimed. The `-noanalysis` switch deliberately separates a loader/import gate from a later full analysis task.

For review in ChatGPT, download and attach only `intake.json`, `ghidra-import.json` and `SUCCESS.json`, or the small relevant failure logs after checking for private paths. Never attach the entire run directory to public GitHub: a Ghidra project contains the imported executable. Reports remain private unless the owner explicitly approves sharing.

## Pinned upstream packages

- Ghidra tag `Ghidra_12.1.3_build`, asset `ghidra_12.1.3_PUBLIC_20260817.zip`, SHA-256 `93a5d11a9ad510622acaaf908c556a7b9b764d338e78a7567f3689bf5081fd54`.
- XEXLoaderWV tag `12.1.3`, asset `ghidra_12.1.3_PUBLIC_20260920_XEXLoaderWV.zip`, SHA-256 `afdaf425bb8e16706f28a453a836ac84fcd0d5000f93a2275a02105807d030a3`.
- Ghidra's pinned `application.properties` specifies minimum Java 21. Its corresponding loader source selects `PowerPC:BE:64:A2ALT-32addr` with compiler specification `default`.
- This is a matched pair, not a claim that 12.1.3 is the newest version. Downloads are private user installations, not redistributed tool packages. Ghidra ships its licences; the extension's licensing must be reviewed before any redistribution. No ReXGlue integration is added here.
- Python's Docker image tag and Debian dependency packages are mutable. The environment is not a fully bit-reproducible image; CI logs and per-run Python/platform records expose the actual environment. Tool archive hashes are checked before extraction. The local installation manifest detects accidental changes, not an attacker able to replace both files and the manifest.

Primary references:

- https://github.com/NationalSecurityAgency/ghidra/releases/tag/Ghidra_12.1.3_build
- https://github.com/zeroKilo/XEXLoaderWV/releases/tag/12.1.3
- https://github.com/NationalSecurityAgency/ghidra/blob/Ghidra_12.1.3_build/Ghidra/application.properties
- https://github.com/zeroKilo/XEXLoaderWV/blob/12.1.3/XEXLoaderWV/src/main/java/xexloaderwv/XEXLoaderWVLoader.java

## Validation boundary and recovery

The public smoke test builds the actual devcontainer Dockerfile, verifies archive hashes, starts headless Ghidra, discovers the XEX extension, imports four synthetic PPC bytes and validates a JSON report. It does **not** test encrypted/compressed XEX loading or DOTM compatibility. Read the actual GitHub run outcome before claiming it passed.

Original sources are read-only inputs. Keep a local backup: a Codespace is not archival storage. To repair a partial installation, preserve or rename `.local/toolchains/ghidra-12.1.3` and rerun `bash tools/bootstrap_ghidra.sh`; do not delete `.local/source` or `.local/runs`. To roll back the implementation, check out the preceding branch commit; private inputs and reports remain untouched. No game installation, account secret, public network service, or original binary is modified.
