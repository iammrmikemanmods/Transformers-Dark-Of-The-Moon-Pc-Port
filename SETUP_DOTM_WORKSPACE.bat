@echo off
setlocal EnableExtensions DisableDelayedExpansion
title Transformers Dark of the Moon - Safe Windows Workspace Setup

rem DOTM native Windows x64 static recompilation workspace bootstrap.
rem Default path follows the owner's verified screenshot. No game data is moved.
rem Optional arguments: [workspace root] [/CLONE]
rem Example: SETUP_DOTM_WORKSPACE.bat "F:\Transformers DOTM PC Recomp" /CLONE
set "ROOT=F:\Transformers DOTM PC Recomp"
if not "%~1"=="" set "ROOT=%~1"
set "REPO_URL=https://github.com/iammrmikemanmods/Transformers-Dark-Of-The-Moon-Pc-Port.git"
set "REPO_BRANCH=engineering/windows-workspace-bootstrap-2026-11-10"
set "REPO_DEST=%ROOT%\12_GITHUB_SOURCE\Transformers-Dark-Of-The-Moon-Pc-Port"

echo.
echo [DOTM] Initializing isolated project workspace
echo [DOTM] Root: "%ROOT%"
echo [DOTM] Original ISO and extracted ISO are never moved or modified.
echo.

if not exist "%ROOT%\" mkdir "%ROOT%" >nul 2>&1
if not exist "%ROOT%\" (
  echo [ERROR] Cannot create or access root: "%ROOT%"
  echo [ERROR] Verify that drive F: is connected and writable.
  exit /b 2
)
if not exist "%ROOT%\00_PROJECT_CONTROL\RUN_LOGS\" mkdir "%ROOT%\00_PROJECT_CONTROL\RUN_LOGS" >nul 2>&1
if not exist "%ROOT%\00_PROJECT_CONTROL\RUN_LOGS\" (
  echo [ERROR] Cannot create the project-control logs directory.
  exit /b 3
)
set "LOG=%ROOT%\00_PROJECT_CONTROL\RUN_LOGS\SETUP_%RANDOM%_%RANDOM%.log"
if exist "%LOG%" set "LOG=%ROOT%\00_PROJECT_CONTROL\RUN_LOGS\SETUP_%RANDOM%_%RANDOM%_%RANDOM%.log"
> "%LOG%" echo DOTM workspace setup - %DATE% %TIME%
>> "%LOG%" echo Root: %ROOT%
>> "%LOG%" echo Source assets are preserved in their existing locations.

for %%D in (
  "00_PROJECT_CONTROL\POLICY"
  "00_PROJECT_CONTROL\DECISIONS"
  "00_PROJECT_CONTROL\CHECKPOINTS"
  "00_PROJECT_CONTROL\MANIFESTS"
  "01_SOURCE_INTAKE\ISO_CHECKSUMS"
  "01_SOURCE_INTAKE\XEX_METADATA"
  "01_SOURCE_INTAKE\FILESYSTEM_INVENTORY"
  "01_SOURCE_INTAKE\READONLY_REFERENCES"
  "02_PPC_ANALYSIS\GHIDRA_PROJECTS_PRIVATE"
  "02_PPC_ANALYSIS\FUNCTION_MAPS_PRIVATE"
  "02_PPC_ANALYSIS\IMPORT_RESOLUTION"
  "02_PPC_ANALYSIS\POWERPC_ENTRY"
  "02_PPC_ANALYSIS\BRANCH_TABLES"
  "03_STATIC_RECOMPILATION\REXGLUE"
  "03_STATIC_RECOMPILATION\GENERATED_CPP_PRIVATE"
  "03_STATIC_RECOMPILATION\HANDWRITTEN_FIXES"
  "03_STATIC_RECOMPILATION\TRAMPOLINES"
  "03_STATIC_RECOMPILATION\FUNCTION_REGISTRY"
  "04_XBOX_RUNTIME\KERNEL"
  "04_XBOX_RUNTIME\XAM"
  "04_XBOX_RUNTIME\MEMORY"
  "04_XBOX_RUNTIME\THREADING"
  "04_XBOX_RUNTIME\INPUT"
  "04_XBOX_RUNTIME\AUDIO"
  "04_XBOX_RUNTIME\D3D9_GRAPHICS"
  "04_XBOX_RUNTIME\FILESYSTEM"
  "05_UE3_COMPATIBILITY\COOKED_ASSETS_PRIVATE"
  "05_UE3_COMPATIBILITY\PACKAGE_INVENTORY"
  "05_UE3_COMPATIBILITY\SHADERS"
  "05_UE3_COMPATIBILITY\MATERIALS"
  "05_UE3_COMPATIBILITY\ANIMATIONS"
  "05_UE3_COMPATIBILITY\PHYSICS"
  "05_UE3_COMPATIBILITY\CINEMATICS"
  "05_UE3_COMPATIBILITY\SCRIPTING"
  "06_WINDOWS_X64\HOST_EXECUTABLE"
  "06_WINDOWS_X64\LAUNCHER"
  "06_WINDOWS_X64\BUILD_SYSTEM"
  "06_WINDOWS_X64\CONFIGURATION"
  "06_WINDOWS_X64\PLATFORM_BRIDGE"
  "07_ISO_INSTALLER\ISO_VALIDATION"
  "07_ISO_INSTALLER\ASSET_STAGING_PRIVATE"
  "07_ISO_INSTALLER\INSTALLER_SOURCE"
  "07_ISO_INSTALLER\INSTALL_TESTS"
  "08_QA_PARITY\UNIT"
  "08_QA_PARITY\REGRESSION"
  "08_QA_PARITY\SMOKE"
  "08_QA_PARITY\PLAYBACK"
  "08_QA_PARITY\PERFORMANCE"
  "08_QA_PARITY\ISSUES"
  "09_PRIVATE_TEST_BUILDS\INCREMENTAL"
  "09_PRIVATE_TEST_BUILDS\DRAG_AND_DROP"
  "09_PRIVATE_TEST_BUILDS\LOGS"
  "09_PRIVATE_TEST_BUILDS\PDB_SYMBOLS"
  "10_PUBLIC_DISTRIBUTION\CODE_ONLY"
  "10_PUBLIC_DISTRIBUTION\INSTALLER_ONLY"
  "10_PUBLIC_DISTRIBUTION\RELEASE_MANIFESTS"
  "11_PINNED_TOOLS\GHIDRA"
  "11_PINNED_TOOLS\REXGLUE"
  "11_PINNED_TOOLS\COMPILERS"
  "11_PINNED_TOOLS\REFERENCE_NOTES"
  "12_GITHUB_SOURCE"
  "13_REPORTS\FORENSIC"
  "13_REPORTS\BUILD_REPORTS"
  "13_REPORTS\SECURITY"
  "13_REPORTS\EVIDENCE"
  "14_BACKUPS\WORKSPACE_SNAPSHOTS"
  "14_BACKUPS\KNOWN_GOOD_BUILDS"
  "14_BACKUPS\ROLLBACK"
) do (
  call :ENSURE_DIR "%%~D"
  if errorlevel 1 goto :FAILED
)

set "POLICY=%ROOT%\00_PROJECT_CONTROL\WORKSPACE_POLICY.txt"
if not exist "%POLICY%" (
  > "%POLICY%" echo Transformers Dark of the Moon - native PC recompilation workspace
  >> "%POLICY%" echo Project root: %ROOT%
  >> "%POLICY%" echo Existing ISO and extracted ISO remain in place, unchanged.
  >> "%POLICY%" echo Do not ingest, hash or extract an ISO while it is still copying.
  >> "%POLICY%" echo Keep Xbox executables, original assets, decrypted PE images, Ghidra databases,
  >> "%POLICY%" echo and generated proprietary game code outside the public Git repository.
  >> "%POLICY%" echo Public releases must not contain game files or recovered proprietary code.
  >> "%POLICY%" echo Public goal: native Windows x64 launcher and code-only installer
  >> "%POLICY%" echo that requires a user-provided original game ISO or extracted installation.
  >> "%POLICY%" echo Preserve original behaviour: UE3, Stealth Force, campaigns, animation, physics,
  >> "%POLICY%" echo cinematics, graphics, sound, original input and gameplay parity.
  >> "%POLICY%" echo Use reviewable Git branches; no changes to originals or forced deletions.
  >> "%POLICY%" echo Evidence states: unverified, source-verified, tooling-verified, build-verified, gameplay-verified.
  >> "%POLICY%" echo Every ZIP test build requires README_MEMORY_ZIP_POLICY.md, SHA-256, manifest and rollback.
  >> "%POLICY%" echo Current repository: %REPO_URL%
  >> "%POLICY%" echo Current engineering branch: %REPO_BRANCH%
)
>> "%LOG%" echo Policy file present: %POLICY%

echo.
if exist "%ROOT%\extracted ISO\" (
  echo [SOURCE] Existing "extracted ISO" directory detected - left unchanged.
  >> "%LOG%" echo Existing extracted ISO directory found. NO source changes performed.
) else (
  echo [SOURCE] "extracted ISO" not found yet - no extraction attempted.
  >> "%LOG%" echo Extracted ISO folder not yet present. No extraction attempted.
)

if /I "%~2"=="/CLONE" (
  call :CLONE_REPOSITORY
  if errorlevel 1 goto :FAILED
) else (
  echo [GIT] Optional clone skipped. Pass /CLONE as the second argument to clone.
)

echo.
echo [PASS] Workspace directories ready. Originals not moved, overwritten or deleted.
echo [LOG] "%LOG%"
echo [NEXT] Use the mission brief from this repository with a fresh ChatGPT Work session.
echo [NOTE] Existing ISO copy must finish before hashing or parsing the ISO.
exit /b 0

:ENSURE_DIR
set "DEST=%ROOT%\%~1"
if exist "%DEST%\" exit /b 0
if exist "%DEST%" (
  echo [ERROR] A file blocks directory creation: "%DEST%"
  >> "%LOG%" echo BLOCKED: %DEST%
  exit /b 1
)
mkdir "%DEST%" >nul 2>&1
if not exist "%DEST%\" (
  echo [ERROR] Could not create: "%DEST%"
  >> "%LOG%" echo FAILED: %DEST%
  exit /b 1
)
echo [CREATE] %~1
>> "%LOG%" echo CREATED: %~1
exit /b 0

:CLONE_REPOSITORY
if exist "%REPO_DEST%\.git\" (
  echo [GIT] Repository already exists. No fetch, pull, reset or checkout performed.
  >> "%LOG%" echo EXISTING REPO PRESERVED: %REPO_DEST%
  exit /b 0
)
if exist "%REPO_DEST%" (
  echo [ERROR] Clone destination exists and is not a Git checkout:
  echo         "%REPO_DEST%"
  echo         Please inspect manually. Nothing was overwritten.
  >> "%LOG%" echo CLONE BLOCKED BY EXISTING DIRECTORY: %REPO_DEST%
  exit /b 1
)
where git.exe >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Git for Windows is not on PATH. Folder setup succeeded; clone skipped.
  >> "%LOG%" echo GIT NOT INSTALLED. Clone not attempted.
  exit /b 1
)
echo [GIT] Cloning source-only branch into separate repository folder...
git clone --branch "%REPO_BRANCH%" --single-branch "%REPO_URL%" "%REPO_DEST%"
if errorlevel 1 (
  echo [ERROR] Git clone failed. Review error and preserve existing folders.
  >> "%LOG%" echo GIT CLONE FAILED.
  exit /b 1
)
echo [GIT] Repository cloned; original source inputs remain outside Git.
>> "%LOG%" echo GIT CLONE SUCCESS: %REPO_DEST%
exit /b 0

:FAILED
echo.
echo [STOP] Workspace initialization encountered an error.
echo [LOG] "%LOG%"
echo [SAFE] No existing source ISO or extracted game file was modified by this script.
exit /b 1
