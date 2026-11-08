# Engineering instructions

This repository belongs only to Transformers: Dark of the Moon native Windows x64 static recompilation. Do not merge it with Transformers PC Merge, UPS, or unrelated projects.

## Mandatory evidence discipline

Read README.md and docs/DEVELOPMENT_LOG.md before work. Inspect actual files before claiming availability. Metadata records, successful byte reads, integrity tests, code generation, compilation, and gameplay are distinct milestones. Report each separately. Never invent hashes, addresses, function counts, tool output, runtime behaviour, or parallel workers.

Original game copies are read-only inputs. Keep originals, extracted content, decrypted images, generated game-code translations, and runtime data outside version control. Do not upload these to GitHub, Actions artifacts, releases, or issues. Use synthetic test data for public CI. Never use generated C++ as a public CI input.

ReXGlue is the first framework to evaluate, not a verified dependency yet. Pin and record the exact upstream commit and licence before integration. Do not guess the current CLI. Never copy another title's function map, memory layout, patches, or compatibility configuration.

Place persistent fixes in handwritten modules or generator configuration, not generated code. Every release needs a unique version/build identity, checksums, change manifest, destination, previous-version checks, logs, and rollback instructions. See README_MEMORY_ZIP_POLICY.md.

## Current tooling checks

Requires Python 3.11 or newer; CI targets Python 3.14. No third-party Python modules are needed.

```text
python -m unittest discover -s tests -v
python tools/check_repository.py
```

Passing these checks establishes only tooling behaviour on test fixtures. It does not prove anything about the uploaded game, ReXGlue compatibility, or a playable port. Keep changes on reviewable branches and do not force-push or delete evidence.
