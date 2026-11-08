# Source intake v0.1.0

## Scope

A standard-library-only Python tool for read-only source observations. It is not a XEX loader, decryptor, disassembler, recompiler, signature authenticator, or Xbox ISO extractor. Source SHA-256 values are observations, not matches to a known-good reference database.

Python 3.11+ is required; automated tests target Python 3.14 on Windows and Linux. No game files are required for unit tests. Public CI must use only the synthetic fixtures constructed in tests/test_source_intake.py.

## Run locally

Run from this repository's checkout. The quoted source path below uses the game folder supplied for this project; change it only if your local extraction is elsewhere.

```powershell
py -3.14 tools/source_intake.py xex 'D:\Transformers - Dark of the Moon (USA, Europe) (En,Fr,De,Es,It)\default.xex' --out '.local\reports\xex-intake-001.json'
```

To inventory an already extracted game directory, including empty directories and SHA-256 for each regular file:

```powershell
py -3.14 tools/source_intake.py inventory 'D:\Transformers - Dark of the Moon (USA, Europe) (En,Fr,De,Es,It)' --out '.local\reports\inventory-001.json'
```

The actual input path must exist. These commands do not extract an ISO. If py is unavailable, invoke the installed Python interpreter directly. The report directory may be created, but reports must be outside the inventoried source tree. Existing report files are rejected: choose a fresh report name for a new observation. Omit --out to print JSON to standard output. Exit code 0 means the requested limited observation succeeded; 2 means an error. Neither means the game is compatible or playable.

The tool never executes the input or writes to it. It streams SHA-256, checks for ordinary file changes during inspection, and rejects inspected links/reparse points. Run against a quiescent local copy, not a concurrently edited or adversarially modified filesystem; the inventory is not an atomic filesystem snapshot and cannot guarantee immunity from all filesystem races. A changed source or interrupted run is not a trusted observation.

## XEX report

Validates the XEX2 magic, basic header/table bounds, optional-header storage bounds, and security page-descriptor bounds. Reports available execution-info fields, packed versions, entry-point/image-base header values, file-format encryption/compression indicators, and declared image metadata. The 16 MiB header-read cap is a tool resource limit, not an Xbox specification constraint. A limit error does not establish file corruption.

Packed version integers are preserved without an unverified bitfield interpretation. Missing optional metadata remains null. Import libraries and other unknown optional records are listed as metadata only; imports are not resolved. RSA signature authentication, decryption/decompression, PE architecture, loaded sections, and control-flow analysis are explicitly unverified.

## Publication and recovery

Keep source files and reports in ignored .local/ or outside the checkout. Inspect reports before sharing; they include filenames and hashes but no extracted game bytes. Git ignore rules and the tracked-file guard reduce accidental publication risk, but do not replace review. Never force-add protected inputs. No public Actions run should receive the XEX, ISO, game assets, or generated game-code translations.

Rollback: revert source commits through Git. No source-installation rollback is needed because the tool does not modify game files. An interrupted output may be incomplete; use a new report filename and retain the failed report for diagnosis rather than treating it as valid.

## Format provenance

Xenia src/xenia/kernel/util/xex2_info.h was inspected at blob cad98dd833f207605d915e70cd2a22fc26ceb85d on 2026-11-08:
https://github.com/xenia-project/xenia/blob/master/src/xenia/kernel/util/xex2_info.h

This is an original limited parser based on observed format declarations. Xenia runtime code has not been vendored. Third-party runtime integration and licence decisions remain separate work.
