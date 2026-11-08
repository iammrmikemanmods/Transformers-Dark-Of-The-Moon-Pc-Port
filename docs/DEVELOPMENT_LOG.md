# Development log

## 2026-11-08 — Phase 2 executable-identity probe, synthetic validation only

Started a separate dependent draft branch `engineering/phase2-pe-identity-probe` (PR #3), based on the Phase 1 Ghidra fallback branch rather than main.

Implemented a private read-only Phase 2 runner (`tools/run_phase2.py`) and a headless Ghidra PE verifier (`tools/ghidra/DotmPhase2Probe.java`). This uses the pinned XEXLoaderWV to privately reconstruct the PE in memory, then verifies MZ/PE signatures, PE32 section-directory boundaries, source/XEX identity, image-base consistency, executable memory mapping and one 4-byte PPC entry instruction before producing private JSON. No PE bytes, executable instructions or decompiled output are exported. Full auto-analysis remains deferred until that evidence gate passes.

Observed CI for implementation commit `062bfb26fccf1fa771d77024e7d394b790038f4b`:
- [Source tools run 42531423644](https://github.com/iammrmikemanmods/Transformers-Dark-Of-The-Moon-Pc-Port/actions/runs/42531423644): **62 tests on Windows and 62 on Ubuntu passed**. Read actual job logs.
- [Cloud Ghidra run 42531423655](https://github.com/iammrmikemanmods/Transformers-Dark-Of-The-Moon-Pc-Port/actions/runs/42531423655): Docker container, 62 synthetic tests, pinned archive hash verification and a bounded **synthetic** PowerPC instruction decoding test all passed. Actual job logs inspected.
- A prior Windows run failed due to platform-unstable `st_ctime_ns` comparison; corrected in the Phase 2 branch while keeping file identity, size, mtime and exact SHA-256 source validation. Added two regression tests and confirmed replacement CI passes.

The human-readable Phase 1 analysis was supplied by the owner from a separate working ChatGPT conversation. Its reported DOTM SHA-256, Title ID, base, entry and encryption/compression fields are embedded only as an exact **input gate**; these have NOT been independently reread in this blocked project workspace.

**Still blocked:** real `default.xex` import and reconstruction, real PE machine determination, actual PowerPC instruction discovery and native compilation. This container continues to return `ClientError`. The GitHub connector can edit source and inspect CI, but cannot transfer the user's Project-mounted XEX bytes to private Codespaces or operate the Codespace terminal. The owner must place the original XEX privately in `.local/source/default.xex` and run `python tools/run_phase2.py`. Actual source success is not claimed.

Evidence and user operation: [PHASE2_PE_GATE.md](PHASE2_PE_GATE.md).

## 2026-11-08 — executable cloud fallback and observed validation

Implemented private Codespaces configuration, SHA-256-pinned Ghidra 12.1.3 with matching XEXLoaderWV, an import-only metadata reporter, a source-preserving Phase 1 runner, and synthetic cloud validation on `engineering/phase1-codespaces-fallback` (PR #2). No original game data is in the changes. The branch remains separate from main.

Implementation commit `bb947950798355f54b027ce850f00ea81d21739c` was directly validated by reading GitHub job outcomes and logs:

- Source-tools run `42511031610`: 48 tests passed on Windows and 48 on Ubuntu; publication checks passed.
- Cloud Ghidra smoke run `42511031603`: built the actual devcontainer Dockerfile; 48 tests passed inside it; verified both pinned upstream archive hashes; started headless Ghidra; discovered XEXLoaderWV; imported a four-byte synthetic PowerPC fixture and produced validated JSON.
- Observed cloud-container versions: Python 3.14.10, OpenJDK 21.0.13, Ghidra 12.1.3.

The first smoke run `42510811993` failed because Ghidra rejects hidden project-path components. Fixed by moving private project databases out of `.local` into ignored `private/ghidra-projects/`, while preserving `.local` for inputs, reports and toolchains. Added regression tests. Do not regress to storing the Ghidra database under `.local`.

Full evidence and scope: [validation/CLOUD_PHASE1_2026-11-08.md](validation/CLOUD_PHASE1_2026-11-08.md). Owner setup: [CLOUD_PHASE1.md](CLOUD_PHASE1.md).

Actual `default.xex` analysis is still NOT PERFORMED. The ChatGPT workspace failed and the connector has no binary-transfer or Codespace-terminal capability. No Codespace has been launched. A private source upload and invocation of `python tools/run_phase1.py` remain necessary. The smoke test validates extension discovery and raw PowerPC import, not encrypted/compressed XEX loading. Full auto-analysis, decompilation, recompilation and native gameplay remain unattempted.

## 2026-11-08 — repository bootstrap and source-tooling v0.1.0

### Completed and directly observed

- GitHub connector resolved iammrmikemanmods/Transformers-Dark-Of-The-Moon-Pc-Port as a public, writable repository with default branch main.
- The contents endpoint explicitly reported an empty repository before initialisation.
- Added the initial scope/evidence README in commit 92af695e841d9ffbe3f3fe7e36310a86536ae1b7.
- Created engineering/source-intake-v0.1.0 from that commit.
- Inspected Xenia's XEX2 structure declarations, blob cad98dd833f207605d915e70cd2a22fc26ceb85d, for bounded header inspection. The original Python parser uses format constants and offsets, not copied runtime implementation.

### Implemented here, pending execution evidence

- Read-only SHA-256/file-size collection, limited XEX2 metadata parsing, and recursive extracted-directory inventory.
- Malformed/truncated-input handling; rejection of symbolic links and Windows reparse points at inspected entries; refusal to overwrite reports or write them inside inventoried source directories.
- Synthetic unit tests and a tracked-file publication guard.
- Windows/Linux CI definition, using pinned official checkout and setup-python actions.

The code in this commit has not yet been exercised against the uploaded game. CI outcomes must be read from the actual workflow run; a workflow definition is not a passing test result.

### Blocked

- The local container command interface and Python interface both returned ClientError on basic filesystem probes in this turn. Neither produced file contents.
- ISO reconstruction, 7-Zip integrity checks, complete filesystem inventory, and SHA-256 validation of the actual game inputs remain blocked by source/execution access.

### Prior-session metadata, not revalidated byte evidence

Eleven archive volumes were previously listed in Project storage. Earlier transfer calls reported ten parts of 524,288,000 bytes and a final part of 86,405,634 bytes; larger parts hit a 104,857,600-byte transfer-tool limit. Earlier upload records reported default.xex as 26,591,232 bytes. These records do not prove complete archive integrity, a valid XEX, or a reconstructed ISO. Do not assume missing files or require a reupload based only on a failing execution environment.

### Not attempted / unknown

- Actual executable title ID, version, entry point, imports, PE machine type, function boundaries, and UE3 startup pathways.
- ReXGlue environment installation, function discovery, code generation, compilation, linking, and runtime testing.
- Installer transformations and public release licensing/distribution design.

### Next evidence gates

1. Obtain working read access to existing inputs; run the intake tool against default.xex without publishing the file.
2. Record real SHA-256 and header findings; review any metadata report before publication.
3. Test the complete multipart archive, reconstruct the ISO in isolation, verify its Xbox filesystem, and inventory extracted files. The intake tool does not perform archive or ISO extraction.
4. Pin a ReXGlue revision and reproduce its documented setup; attempt analysis/code generation against the actual executable. Record exact command output and blockers.

No playable executable, proprietary generated C++, or game asset is included in this branch.
