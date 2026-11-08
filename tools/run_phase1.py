"""Private XEX header intake and Ghidra import, never a playable game build."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import stat
import subprocess
import sys
import uuid

import source_intake

ROOT = Path(__file__).resolve().parents[1]
GHIDRA_RELATIVE = Path('.local/toolchains/ghidra-12.1.3/ghidra_12.1.3_PUBLIC')
LANGUAGE = 'PowerPC:BE:64:A2ALT-32addr'


def write_json(path: Path, value: dict) -> None:
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def reject_links(path: Path) -> None:
    for part in (path.absolute(), *path.absolute().parents):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise source_intake.IntakeError('Linked/reparse input or output path is not allowed')


def require_ignored(root: Path, name: str) -> None:
    reject_links(root / name)
    ignored = subprocess.run(['git', 'check-ignore', '--quiet', f'{name}/probe'], cwd=root)
    tracked = subprocess.run(['git', 'ls-files', '-z', '--', name], cwd=root,
                             check=True, capture_output=True)
    if ignored.returncode != 0 or tracked.stdout:
        raise source_intake.IntakeError(f'{name} must be ignored and entirely untracked')


def private_workspace(root: Path) -> Path:
    require_ignored(root, '.local')
    require_ignored(root, 'private')
    runs = root / '.local/runs'
    reject_links(runs)
    runs.mkdir(parents=True, exist_ok=True)
    return runs


def private_project(root: Path, run_name: str) -> Path:
    # Ghidra 12.1.3 rejects a project path if ANY component starts with '.'.
    # Keep reports/tools in .local, but databases in the already ignored private/.
    if not run_name or Path(run_name).name != run_name or run_name.startswith('.'):
        raise source_intake.IntakeError('Invalid private project identifier')
    require_ignored(root, 'private')
    project = root.absolute() / 'private/ghidra-projects' / run_name
    reject_links(project)
    if any(part.startswith('.') for part in project.parts):
        raise source_intake.IntakeError('Ghidra project paths cannot contain hidden components; use a non-hidden repository path')
    project.parent.mkdir(parents=True, exist_ok=True)
    project.mkdir()
    return project


def validate_import(report: dict, digest: str, *, xex: bool) -> None:
    if not isinstance(report, dict) or report.get('schema_version') != 1:
        raise source_intake.IntakeError('Unexpected Ghidra report schema')
    if report.get('xex_loader_discovered') is not True:
        raise source_intake.IntakeError('XEX loader not discovered')
    if report.get('language_id') != LANGUAGE or report.get('big_endian') is not True:
        raise source_intake.IntakeError('Unexpected Ghidra processor configuration')
    observed_digest = report.get('executable_sha256')
    if not isinstance(observed_digest, str) or observed_digest.lower() != digest.lower():
        raise source_intake.IntakeError('Ghidra input hash does not match the inspected input')
    if not report.get('memory_blocks'):
        raise source_intake.IntakeError('No memory blocks were imported')
    if xex and report.get('executable_format') != 'XEX Loader by Warranty Voider':
        raise source_intake.IntakeError('Ghidra did not use the expected XEX loader')
    if report.get('full_auto_analysis_requested') is not False:
        raise source_intake.IntakeError('Unexpected analysis mode')


def headless_command(root: Path, source: Path, output: Path, *, smoke: bool = False) -> list[str]:
    if os.name != 'posix':
        raise source_intake.IntakeError('This Ghidra fallback targets Linux/Codespaces; use --intake-only on Windows')
    launcher = root / GHIDRA_RELATIVE / 'support/analyzeHeadless'
    if not launcher.is_file():
        raise source_intake.IntakeError('Pinned Ghidra installation missing; run bash tools/bootstrap_ghidra.sh')
    project = private_project(root, output.name)
    command = [str(launcher), str(project), 'DOTM_Phase1',
               '-import', str(source.resolve()), '-noanalysis', '-max-cpu', '2',
               '-loader', 'BinaryLoader' if smoke else 'XEXLoaderWVLoader']
    if smoke:
        command += ['-processor', LANGUAGE, '-cspec', 'default']
    command += ['-scriptPath', str(root / 'tools/ghidra'),
                '-postScript', 'DotmImportReport.java', str(output / 'ghidra-import.json'),
                '-log', str(output / 'ghidra.log'), '-scriptlog', str(output / 'script.log')]
    return command


def run(root: Path, source: Path, *, intake_only: bool = False) -> Path:
    # Real sources must never be fed to public CI. The dedicated smoke program
    # uses only a four-byte synthetic PPC fixture and does not call this entry.
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        raise source_intake.IntakeError('Real-source entry is disabled in GitHub Actions; use a private Codespace')
    reject_links(source)
    runs = private_workspace(root)
    observation = source_intake.inspect_xex(source)
    name = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:12]
    output = runs / name
    output.mkdir()
    write_json(output / 'intake.json', {'schema_version': 1, 'tool_version': source_intake.VERSION,
               'observed_at_utc': datetime.now(timezone.utc).isoformat(), 'result': observation})
    try:
        environment = {'python': sys.version, 'platform': platform.platform(), 'intake_only': intake_only}
        commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=root, check=True,
                                capture_output=True, text=True).stdout.strip()
        environment['repository_commit'] = commit
        write_json(output / 'environment.json', environment)
        if not intake_only:
            command = headless_command(root, source, output)
            write_json(output / 'command.json', {'argv': command, 'timeout_seconds': 900})
            with (output / 'console.log').open('x', encoding='utf-8') as log:
                result = subprocess.run(command, cwd=root, stdout=log, stderr=subprocess.STDOUT,
                                        timeout=900, check=False)
            if result.returncode != 0:
                raise source_intake.IntakeError(f'Ghidra exited {result.returncode}; retained private logs at {output}')
            report = json.loads((output / 'ghidra-import.json').read_text(encoding='utf-8'))
            validate_import(report, observation['sha256'], xex=True)
        fingerprint = source_intake.hash_source(source)
        if fingerprint != {key: observation[key] for key in ('size_bytes', 'sha256')}:
            raise source_intake.IntakeError('Input changed during this run; results are not accepted')
        write_json(output / 'SUCCESS.json', {'header_intake_passed': True,
                   'ghidra_import_validated': not intake_only, 'source_hash_unchanged': True,
                   'full_auto_analysis_performed': False, 'native_pc_build_tested': False})
        return output
    except Exception as error:
        write_json(output / 'FAILED.json', {'accepted': False, 'error_type': type(error).__name__,
                   'error': str(error), 'header_intake_passed': True})
        raise


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / '.local/source/default.xex')
    parser.add_argument('--intake-only', action='store_true')
    args = parser.parse_args(argv)
    try:
        output = run(ROOT, args.source, intake_only=args.intake_only)
        print(f'Private Phase 1 evidence: {output}')
        print('No decompilation, full analysis or native PC runtime is claimed.')
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f'Phase 1 stopped: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
