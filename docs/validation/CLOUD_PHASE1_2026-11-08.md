# Cloud fallback validation — 2026-11-08

## Evidence scope

Tested implementation commit: `bb947950798355f54b027ce850f00ea81d21739c`.
Branch: `engineering/phase1-codespaces-fallback`.
Review: https://github.com/iammrmikemanmods/Transformers-Dark-Of-The-Moon-Pc-Port/pull/2

This record was written after reading the actual GitHub job results and logs. It concerns synthetic tests and the Ghidra cloud toolchain, not the user's DOTM executable. The subsequent documentation commit changes no executable code or workflow.

## Observed results

| Environment | Job | Observed result |
| --- | --- | --- |
| Windows Server 2025, CPython 3.14.10 | 128823922431 | Publication guard passed; 48 tests passed; intake version command passed. |
| Ubuntu 24.04.5, CPython 3.14.10 | 128823922502 | Publication guard passed; 48 tests passed; intake version command passed. |
| Built devcontainer Dockerfile on Linux, Python 3.14.10 / OpenJDK 21.0.13 | 128823922239 | Image built; publication guard passed; 48 tests passed; both downloaded archives matched pinned SHA-256; headless Ghidra imported a synthetic PowerPC fixture and exported validated JSON. |

Source-tool workflow: https://github.com/iammrmikemanmods/Transformers-Dark-Of-The-Moon-Pc-Port/actions/runs/42511031610

Ghidra cloud smoke workflow: https://github.com/iammrmikemanmods/Transformers-Dark-Of-The-Moon-Pc-Port/actions/runs/42511031603

All three jobs completed with conclusion `success`. Tests were executed in each environment; this does not mean there are 144 distinct test cases. There are 48 cases exercised three times.

The Ghidra smoke log recorded the expected `PowerPC:BE:64:A2ALT-32addr:default` language/compiler pair, successful execution of `DotmImportReport.java`, successful program save, successful import, and successful Python report validation. The validator checks loader discovery, input SHA-256, language/endianness and non-empty imported memory. The extension was discovered but the smoke fixture itself uses Ghidra's Raw Binary loader.

## Important limitation

The smoke input consists of four synthetic bytes encoding one PowerPC return instruction. It does NOT exercise XEX payload decryption, LZX decompression, the complete XEX loader path, DOTM's imports, real function discovery, full auto-analysis, decompilation, static recompilation or native game execution. The Codespaces-specific provisioning UI/lifecycle has not been exercised; CI builds and runs the same Dockerfile and relevant setup components.

No original XEX, ISO volume, game asset, decrypted program image or generated proprietary code was supplied to GitHub Actions. No workflow artifact upload was configured. No Codespace was created through the connector.

## Failure and regression record

Initial implementation `beb9567b5509d078c4d5650f9fd443d843524805`, cloud run `42510811993`, passed its then-current 42 tests, built the image, verified tool archives and started Ghidra. It failed because the project database directory contained the hidden component `.local`.

Correction: reports and tool downloads remain in ignored `.local/`; project databases now use ignored `private/ghidra-projects/<unique run id>/`. Added regression tests for project location, hidden identifiers, reused projects and unignored private roots, plus malformed/null report validation. The final suite has 48 cases. The original failure is not counted as a pass.

## Remaining real-source gate

The ChatGPT execution workspace failed before binary inspection. The available GitHub connector can edit source and inspect Actions but cannot read ChatGPT's mounted binary upload or control a Codespace terminal. Consequently the actual `default.xex` SHA-256, title ID, entry point, payload format and imports remain unverified.

Owner action: create a private Codespace from the implementation branch, upload the existing `default.xex` into `.local/source/default.xex` via the Codespace Explorer (NOT repository Add file), then run `python tools/run_phase1.py`. Detailed setup and recovery are in [CLOUD_PHASE1.md](../CLOUD_PHASE1.md).

Only share the resulting metadata reports privately for review. A Ghidra project contains program bytes and must not be committed or attached to public GitHub. A loader/import failure should be returned as evidence, not relabelled success.

## Trust disposition

- Source tooling under the tested synthetic cases: PASS.
- Pinned cloud Ghidra startup, extension discovery, raw PPC import and JSON export: PASS.
- Actual DOTM XEX inspection/import: NOT PERFORMED.
- Actual DOTM decrypted/decoded image correctness: UNKNOWN.
- Full function analysis/decompilation/recompilation: NOT PERFORMED.
- Native Windows gameplay/build: NOT PERFORMED.

These dispositions are independent; a tooling pass does not upgrade the game analysis or build status.
