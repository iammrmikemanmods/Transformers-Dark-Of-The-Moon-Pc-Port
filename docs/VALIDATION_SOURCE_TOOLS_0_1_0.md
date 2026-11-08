# Verified source-tooling validation — v0.1.0

Observed 2026-11-08 by retrieving completed GitHub Actions job records and their full logs. This is a follow-up to the pending-execution snapshot in DEVELOPMENT_LOG.md.

## Exact evidence

- Tested source commit: `af3715001738706c790970b00dd86056aa063b78`
- Build identity: `dotm-source-intake-0.1.0`
- Workflow run: https://github.com/iammrmikemanmods/Transformers-Dark-Of-The-Moon-Pc-Port/actions/runs/42507354794
- Windows job: `128812752304`
- Linux job: `128812752150`

| Observation | Windows runner | Linux runner |
| --- | --- | --- |
| Reported OS | Windows Server 2025, 10.0.26100 | Ubuntu 24.04.5 LTS |
| Reported Python | CPython 3.14.10 x64 | CPython 3.14.10 x64 |
| Unit tests | 28 run; OK | 28 run; OK |
| Skipped tests | 0 | 0 |
| Tracked-file publication guard | Passed | Passed |
| CLI version smoke test | dotm-source-intake-0.1.0 | dotm-source-intake-0.1.0 |
| Job conclusion | success | success |

## What this establishes

The tested commit executes on both listed runner environments. Tests cover synthetic header parsing and invalid/truncated bounds; source hashing and preservation; missing/invalid sources; fresh JSON report creation; refusal to overwrite sources or reports; refusal to write inventory reports inside the source tree; empty-directory inventory; inspected symbolic-link rejection; and common protected publication paths.

No proprietary game file was a CI input. Fixtures are created in temporary directories by the test code and are explicitly synthetic.

## What remains unverified

The actual uploaded default.xex and multipart archives have not been byte-read by this work. No authentic title ID, source hash, entry point, import map, function boundary, or ISO integrity result has been established. These tests do not establish Xbox signature authenticity, ReXGlue compatibility, UE3 compatibility, or a playable port. Windows 10/11 owner-machine testing has not occurred; the Windows CI environment was Server 2025.

No ReXGlue setup, code generation, native compilation, linker test, or game runtime test was performed. The local analysis container still failed its filesystem probes. GitHub runner access does not automatically provide access to ChatGPT Project uploads.

This file records results for the exact source commit above; it does not silently extend those results to later code changes.
