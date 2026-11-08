# Phase 2 — private reconstructed PE identity and bounded PPC entrypoint

**Status: source-only synthetic CI validated; NOT YET RUN ON THE OWNER'S XEX.**

This stage depends on the Phase 1 Codespaces branch and keeps proprietary game data outside this public repository. It is not full decompilation, static recompilation, an emulator, or a native PC build.

## Input evidence and boundaries

A separately executed user-provided report states that the owner's DOTM XEX has:

- Size: 26,591,232 bytes; SHA-256: 6fd9ae9fb94ea8e9cc91a6a0cc62b04441411bdafe2479f0d380d4a3a9957ca6.
- XEX2 title ID 0x415608A4, image base 0x82000000, entry 0x8277F670.
- Encryption=1 (AES) and BASIC compression=1; reconstructed image size 28,377,088 bytes.
- Two import-library names xam.xex and xboxkrnl.exe.

**These observations were reported from the separate working chat, not independently rerun in this broken project workspace.** The source-identity gate insists on a full new SHA-256 measurement before performing any private loader work. The previous report's structural checks alone are not proof of decrypted PE validity.

## How to run (on a private Codespace)

Use branch engineering/phase2-pe-identity-probe after its code-only CI checks pass. This is based on the existing Phase 1 fallback and includes the pinned Python 3.14/JDK 21/Ghidra 12.1.3/XEXLoaderWV setup.

From the Codespace's Explorer, upload the original unmodified default.xex to the ignored .local/source/default.xex. **Never use GitHub's public repository upload, Add file, public Actions artifacts, releases, PR attachments, or issues for original or decrypted game bytes.** A Codespace is remote cloud storage; keep a local backup.

Run:

    python tools/run_phase2.py

The runner rejects GitHub Actions, links/reparse paths, incorrect XEX size, SHA, Title ID, image base, entry point, encryption, compression or declared image size before invoking Ghidra.

On success, new unique ignored .local/runs/<id>/ evidence includes intake.json, environment.json, command.json, ghidra-import.json, phase2-pe.json and SUCCESS.json. Ghidra's private database lives under ignored private/ghidra-projects/<id>/. A failure yields FAILED.json when a run directory exists; it is not counted as a success. Previous evidence is not overwritten.

Only share the small JSON evidence reports privately after reviewing paths and secrets. Do not share console.log without inspecting it: the upstream loader's diagnostics may log cryptographic session-key material. Never publish the reconstructed PE or Ghidra database.

## What the evidence gates mean

1. **Source identity:** independently hash the real XEX and re-read the outer header.
2. **Ghidra import:** verify XEXLoaderWV, PowerPC big-endian language, source hash and imported memory blocks.
3. **Recovered PE metadata:** use the pinned XEX loader's private in-memory BASIC/AES reconstruction to verify MZ and PE signatures, PE32 optional header, section directory bounds, reconstructed image length, PE image base, and exact machine value.
4. **Entrypoint:** ensure the XEX entry is mapped to initialized executable memory and one four-byte PPC instruction is decoded at that address.
5. **Preservation:** rehash the original, write SUCCESS.json only if all gates pass.

The actual PE machine value is **observed**, not pre-assumed, and will need cross-reference with Xbox 360 PE format definitions. A recovered-image SHA-256 is retained privately for repeated-run comparisons.

The XEXLoaderWV source parses PE headers and maps sections but does not itself enforce all DOS/NT magic validation; this gate adds independent MZ/PE checks and section-bound checks, though it reuses the same underlying loader implementation for decryption. **This is not an independent cryptographic authenticity check** or proof that all instructions are recovered.

The public cloud smoke still uses four bytes of synthetic PowerPC instruction data. Its success proves that the script compiles and its synthetic import path runs, not XEX decryption, the owner's executable, code discovery, or full auto-analysis.

After a successful real-source run, review the PE machine identifier, image-base/entry consistency, section layout, loader errors and import evidence before attempting full Ghidra auto-analysis or any ReXGlue integration.

## Rollback

No game files are changed. Preserve each source and evidence directory. Discard an incomplete private Ghidra database if desired without touching .local/source. Git branch rollback does not delete ignored private evidence. Never force-push verified history.

## Windows intake reliability correction

The first Phase 2 Windows CI run exposed an intermittent, pre-existing `Input changed before opening` false positive on newly created synthetic fixtures. The source-intake identity stamp now compares device, inode, size and last-modification timestamp but omits the platform-dependent creation/change timestamp. Existing full-file SHA-256 verification and the exact DOTM fingerprint gate remain in effect. Regression tests cover creation-time-only drift and actual modification-time changes. Recheck Windows CI results before treating this fix as validated.

## Confirmed synthetic validation (2026-11-08)

Source implementation commit: `062bfb26fccf1fa771d77024e7d394b790038f4b`.

- Source tools: GitHub Actions run [42531423644](https://github.com/iammrmikemanmods/Transformers-Dark-Of-The-Moon-Pc-Port/actions/runs/42531423644). Windows 62/62 tests passed; Ubuntu 62/62 passed. Logs inspected.
- Cloud toolchain: GitHub Actions run [42531423655](https://github.com/iammrmikemanmods/Transformers-Dark-Of-The-Moon-Pc-Port/actions/runs/42531423655). Container built, 62/62 synthetic tests passed, Ghidra and XEXLoaderWV archive hashes verified, headless Ghidra imported the synthetic fixture, and the new Phase 2 Java script decoded the synthetic four-byte PowerPC blr. Logs inspected.
- Earlier source-tools run 42531168688 failed on a Windows timestamp false positive. This was investigated, fixed in commit 062bfb2, and verified by the successful replacement run. That failed run is retained as evidence, not reclassified as a pass.

No real XEX was uploaded to or processed by these public workflows. The actual Xbox PE machine type, recovered PE hash, source-specific memory blocks, imports and PowerPC instructions remain unobserved by this project.
