from __future__ import annotations
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import run_phase1 as phase
import source_intake


def synthetic_header() -> bytes:
    data = bytearray(0x404)
    struct.pack_into('>4s5I', data, 0, b'XEX2', 1, 0x400, 0, 0x80, 0)
    struct.pack_into('>II', data, 0x80, 0x184, 0x1000)
    return bytes(data)


def synthetic_report() -> dict:
    return {'schema_version': 1, 'xex_loader_discovered': True,
            'language_id': phase.LANGUAGE, 'big_endian': True,
            'executable_sha256': 'a' * 64, 'memory_blocks': [{'size_bytes': 4}],
            'executable_format': 'XEX Loader by Warranty Voider',
            'full_auto_analysis_requested': False}


class ValidationTests(unittest.TestCase):
    def test_accepts_matching_import_metadata(self):
        phase.validate_import(synthetic_report(), 'a' * 64, xex=True)

    def test_rejects_wrong_hash(self):
        with self.assertRaises(source_intake.IntakeError):
            phase.validate_import(synthetic_report(), 'b' * 64, xex=True)

    def test_rejects_missing_extension(self):
        report = synthetic_report()
        report['xex_loader_discovered'] = False
        with self.assertRaises(source_intake.IntakeError):
            phase.validate_import(report, 'a' * 64, xex=True)

    def test_rejects_wrong_language(self):
        report = synthetic_report()
        report['language_id'] = 'x86:LE:64:default'
        with self.assertRaises(source_intake.IntakeError):
            phase.validate_import(report, 'a' * 64, xex=True)

    def test_rejects_wrong_loader(self):
        report = synthetic_report()
        report['executable_format'] = 'Raw Binary'
        with self.assertRaises(source_intake.IntakeError):
            phase.validate_import(report, 'a' * 64, xex=True)

    def test_rejects_empty_memory(self):
        report = synthetic_report()
        report['memory_blocks'] = []
        with self.assertRaises(source_intake.IntakeError):
            phase.validate_import(report, 'a' * 64, xex=True)

    def test_json_output_is_exclusive(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'report.json'
            phase.write_json(out, {'initial': True})
            with self.assertRaises(FileExistsError):
                phase.write_json(out, {'initial': False})
            self.assertEqual(json.loads(out.read_text()), {'initial': True})


class PrivateRunTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        (self.root / '.gitignore').write_text('.local/\n', encoding='utf-8')
        subprocess.run(['git', 'add', '.gitignore'], cwd=self.root, check=True)
        subprocess.run(['git', '-c', 'user.name=Synthetic Test', '-c', 'user.email=test@example.invalid',
                        'commit', '-qm', 'Synthetic fixture only'], cwd=self.root, check=True)
        self.source = self.root / 'input.xex'
        self.source.write_bytes(synthetic_header())
        self.environment = mock.patch.dict(os.environ, {'GITHUB_ACTIONS': 'false'})
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def test_intake_keeps_original_unchanged(self):
        before = self.source.read_bytes()
        out = phase.run(self.root, self.source, intake_only=True)
        self.assertEqual(self.source.read_bytes(), before)
        result = json.loads((out / 'SUCCESS.json').read_text())
        self.assertTrue(result['header_intake_passed'])
        self.assertFalse(result['ghidra_import_validated'])
        self.assertFalse(result['native_pc_build_tested'])

    def test_repeated_runs_preserve_previous_evidence(self):
        a = phase.run(self.root, self.source, intake_only=True)
        b = phase.run(self.root, self.source, intake_only=True)
        self.assertNotEqual(a, b)
        self.assertTrue((a / 'SUCCESS.json').is_file())
        self.assertTrue((b / 'SUCCESS.json').is_file())

    def test_unignored_workspace_is_rejected(self):
        (self.root / '.gitignore').write_text('', encoding='utf-8')
        with self.assertRaises(source_intake.IntakeError):
            phase.run(self.root, self.source, intake_only=True)

    def test_real_source_entry_disabled_in_actions(self):
        with mock.patch.dict(os.environ, {'GITHUB_ACTIONS': 'true'}):
            with self.assertRaises(source_intake.IntakeError):
                phase.run(self.root, self.source, intake_only=True)

    def test_invalid_xex_has_no_success_report(self):
        self.source.write_bytes(b'not an XEX')
        with self.assertRaises(source_intake.IntakeError):
            phase.run(self.root, self.source, intake_only=True)
        self.assertFalse(list(self.root.rglob('SUCCESS.json')))

    def test_missing_source_has_no_success_report(self):
        with self.assertRaises(FileNotFoundError):
            phase.run(self.root, self.root / 'missing.xex', intake_only=True)
        self.assertFalse(list(self.root.rglob('SUCCESS.json')))

    def test_missing_toolchain_leaves_failure_evidence(self):
        with self.assertRaises(source_intake.IntakeError):
            phase.run(self.root, self.source)
        self.assertEqual(len(list(self.root.rglob('FAILED.json'))), 1)
        self.assertFalse(list(self.root.rglob('SUCCESS.json')))


if __name__ == '__main__':
    unittest.main()
