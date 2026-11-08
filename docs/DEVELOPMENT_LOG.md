# Development log

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
