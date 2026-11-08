# Transformers: Dark of the Moon — Native PC Port

Evidence-driven research and engineering toward a faithful Windows 10/11 x64 port of the original Xbox 360 game through static PowerPC recompilation.

**Current status: source intake and tooling. There is no compiled or playable PC port in this repository.**

This project is separate from Transformers PC Merge, Universal Player System (UPS), and all other projects.

## Scope

Preserve original gameplay, physics, animations, transformations, Stealth Force, missions, cinematics, and presentation. ReXGlue is the primary framework to evaluate. A conventional emulator or a replacement game is not the deliverable.

Original discs, ISO images, executables, assets, decrypted images, and generated translations of proprietary game code must remain local and must not be committed or attached to public issues, releases, or CI artifacts. Users must supply their own game copy. Public distribution design and dependency licences require review before release.

## Evidence rules

- Preserve original source files. Work in isolated, recoverable directories.
- Record exact tool revisions, commands, hashes, and results.
- Separate confirmed findings, hypotheses, failures, and untested work.
- Do not claim successful extraction, code generation, compilation, or gameplay without evidence.
- Keep generated code separate from handwritten fixes. Do not invent function maps or reuse another title's addresses.
- Test tooling independently from game compatibility. A tooling test is not a successful game build.

## Initial source-access status

The project owner supplied eleven multipart 7-Zip volumes and `default.xex`. Earlier upload metadata reported the executable as 26,591,232 bytes. Its bytes, SHA-256, title ID, imports, and entry point have not yet been verified by this project.

On 2026-11-08, both available local execution interfaces returned `ClientError` during filesystem probes. This does not establish corruption or absence of the uploaded sources. GitHub access works independently.

## Reference implementations

- [ReXGlue SDK](https://github.com/rexglue/rexglue-sdk)
- [Gears of War 3 recompilation](https://github.com/Flippage/gears-of-war-3-recomp)
- [Saw II recompilation](https://github.com/Matt-code-d/Saw2Recomp)
- [Sonic Unleashed Recompiled](https://github.com/hedge-dev/UnleashedRecomp)
- [XenonRecomp](https://github.com/hedge-dev/XenonRecomp)
- [Xenia](https://github.com/xenia-project/xenia)
- [Ghidra](https://github.com/NationalSecurityAgency/ghidra)

Listing a reference is not a claim that its implementation has been audited or integrated. No third-party runtime or proprietary game code is included in this initial repository.
