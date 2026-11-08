# Phase 1 fallback: local machine or GitHub Codespaces

Status: documented procedure, not proof that the user's real executable has been analyzed. The read-only `tools/source_intake.py` parser and synthetic Windows/Linux Actions tests are already present. Do not duplicate them.

## Security and evidence boundaries

- **Never commit or attach** `default.xex`, ISO/archive parts, extracted UE3 assets, decrypted PE images, or generated proprietary code to this public repository, a PR, an issue, a release, or GitHub Actions artifacts.
- Use a local installation or a private Codespace working directory for source bytes. `.local/` is ignored by the existing repository rules. **GitHub Actions jobs do not inherit ChatGPT Project uploads or Codespace files.**
- The observed ChatGPT file-service transfer returned 26,591,232 bytes for `default.xex`. No SHA-256, XEX magic, title ID, entry point, import list, or function count has yet been established from those bytes. Do not convert an upload-size observation into a verified parse.
- Keep original media and the original executable unchanged. Analyse only read-only copies. A report created by a probe is untrusted until the command has exited successfully and its input hash is verified.

## Route A — local Windows checkout (preferred if the source is already on the PC)

From a checked-out copy of this repository in PowerShell, with Python 3.14 installed:

```powershell
py -3.14 -m unittest discover -s tests -v
py -3.14 tools/source_intake.py xex 'D:\Transformers - Dark of the Moon (USA, Europe) (En,Fr,De,Es,It)\default.xex' --out '.local\reports\xex-intake-001.json'
```

If the input is in a different location, use its actual full path. The script must exit 0 and create a **new** report (it never overwrites old reports). The report stays in ignored `.local/`. Do not regard synthetic test results as findings about the user's binary.

## Route B — GitHub Codespaces (isolated cloud computer, when available)

1. In GitHub, open this repository and choose **Code → Codespaces → Create codespace on main**, subject to the user's GitHub account capabilities and quotas.
2. In the Codespace editor, create `.local/` and upload a copy of `default.xex` there using the editor's upload capability. **Do not stage or commit it.** The copy is private to the Codespace workspace, not automatically available to GitHub Actions or to this ChatGPT session. Avoid sharing the Codespace session.
3. In the Codespace terminal, verify Python 3.11+ and run:

```bash
python3 --version
git check-ignore .local/default.xex
python3 -m unittest discover -s tests -v
python3 tools/source_intake.py xex .local/default.xex --out .local/reports/xex-intake-001.json
python3 -m json.tool .local/reports/xex-intake-001.json
```

4. Confirm the `check-ignore` output is `.local/default.xex`. If Python is older than 3.11, install a supported version in that Codespace **before** running the parser. A successfully generated JSON report may be shared separately for interpretation, after private-info review; do not add it to public git.
5. Save the exact command, Python version, SHA-256 from the report, and exit status in the private investigation log. Treat a parse failure as evidence of that command failing, not proof that the source was corrupt.

Codespaces stores files on a cloud machine. It is not a guarantee of offline-only handling or indefinite retention. Make sure the owner accepts its storage/security implications before uploading a proprietary source file.

## Ghidra escalation — separate evidence gate

Ghidra and an Xbox 360 XEX loader are **not** currently exposed among this ChatGPT session's installed plugin skills. Relevant public projects:

- [Ghidra](https://github.com/NationalSecurityAgency/ghidra)
- [XEXLoaderWV](https://github.com/zeroKilo/XEXLoaderWV)
- [Xenia's XEX2 structures](https://github.com/xenia-project/xenia/blob/master/src/xenia/kernel/util/xex2_info.h)

Select and record the **specific Ghidra and XEXLoaderWV versions**, required Java version, hashes and licences. Verify loader compatibility before using it, and process an **unmodified local/private XEX copy**. Do not invent a loader command line or assume that XEX decryption, decompression, PPC code recovery or import resolution succeeded. Capture real import/entry-point/architecture and function discoveries only from an actual completed analysis, with tool versions and logs. Only then investigate ReXGlue integration, separately and with its revision pinned.

## Recovery

These procedures do not update or install the game. Keep the input untouched. Delete a disposable Codespace or discard an incomplete report if the run fails. Review `git status --short` before every commit; no game binary, report, reverse-engineering database or translated game code may enter public git. Return to `main` or revert a source-only commit to roll back process documentation.
