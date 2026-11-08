# DOTM Phase 2 synthetic evidence record — 2026-11-08

## Scope

This record describes code and CI validation only. It does not claim analysis of the actual copyrighted Xbox 360 `default.xex`, decryption of a private XEX, full decompilation or Windows gameplay.

The Phase 2 code branch is `engineering/phase2-pe-identity-probe`; dependent on draft Phase 1 PR #2 and tracked by draft PR #3.

## Tested implementation

- Commit: `062bfb26fccf1fa771d77024e7d394b790038f4b`.
- Python: 3.14 in GitHub Actions; Ghidra toolchain matched the already validated 12.1.3 and XEXLoaderWV 12.1.3 releases.
- Unit coverage includes mismatch rejection for source hash, entry point, encryption, PE signatures, recovered-image size, private PE hash, missing decoded PPC entry, and synthetic output masquerading as a real-source success.
- A Windows regression test explicitly allows creation-time metadata drift while still rejecting modification-time drift.

## Actual observed CI

| Workflow | Run | Result | Evidence |
|---|---|---|---|
| Source tooling, Windows | 42531423644 | PASS | 62/62 unit tests |
| Source tooling, Ubuntu | 42531423644 | PASS | 62/62 unit tests |
| Cloud Docker, Ghidra | 42531423655 | PASS | 62/62 unit tests, SHA-256 pinned toolchain, synthetic PPC import and instruction decoding |

The cloud test's source was exactly four synthetic bytes, `4E 80 00 20` (PowerPC `blr`). Its Ghidra importer used the Raw Binary loader, not the XEX loader. The Java Phase 2 script compiled, ran, decoded that instruction and wrote a synthetic-only metadata JSON.

## Prior failure and fix

An initial run 42531168688 had a Windows unit-test failure `Input changed before opening`; another older Windows run showed the same condition on synthetic temporary files. This was a false-positive comparison involving `st_ctime_ns`, not proof of source corruption. Commit 062bfb2 omitted the unstable timestamp from the identity stamp; stat identity, size, mtime, full-file hash and exact expected SHA-256 remain. Replacement run 42531423644 passed. Preserve failed logs for regression tracking.

## Next evidence gate

A controlled private Codespace with the real unmodified source at `.local/source/default.xex` must run `python tools/run_phase2.py`. Accept it only if `SUCCESS.json`, `intake.json`, `ghidra-import.json` and `phase2-pe.json` meet their validators; on failure inspect redacted logs privately. Do not publish the reconstructed PE, Ghidra database or imported game code.
