# Project export and recovery policy

Applies to this standalone DOTM project. Do not import another project's directory structure.

Each future downloadable build must include this file, a unique version and build identifier, a change manifest, checksums, exact target directory, prerequisite/previous-version checks, diagnostic instructions, and a rollback procedure. Verify archive CRCs and extracted structure before release. Reject traversal paths, duplicate destinations, placeholders, fabricated binaries, and unrelated project files.

Public packages must not include original game executables/assets, source ISO images, decrypted images, or generated translations of proprietary game code. Keep locally generated reports private until reviewed. Never overwrite original inputs.

The initial source-tooling branch is not an installer, a memory export ZIP, or a game build. No deployment to a game installation is required. An ordinary Git checkout is the destination for source tooling. Git commits are the source rollback boundary; revert the relevant commit rather than deleting or rewriting history. Generated reports are new files only and existing files are never overwritten by the intake tool.
