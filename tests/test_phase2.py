"""Synthetic-only regression checks for the private Phase 2 evidence gate."""
from __future__ import annotations

import os
from pathlib import Path
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import run_phase2
import source_intake


def good_observation():
    return {
        "sha256": run_phase2.EXPECTED_SHA256,
        "size_bytes": run_phase2.EXPECTED_SIZE,
        "xex": {
            "execution_info": {"title_id": run_phase2.EXPECTED_TITLE_ID},
            "entry_point_header_value": run_phase2.EXPECTED_ENTRY,
            "image_base_header_value": run_phase2.EXPECTED_BASE,
            "file_format": {"encryption_type": 1, "compression_type": 1},
            "declared_image": {"image_size_bytes": run_phase2.EXPECTED_IMAGE_BYTES}
        }
    }


def good_report():
    return {
        "schema_version": 2, "kind": "xex",
        "source_sha256": run_phase2.EXPECTED_SHA256,
        "source_size_bytes": run_phase2.EXPECTED_SIZE,
        "language_id": "PowerPC:BE:64:A2ALT-32addr",
        "ghidra_executable_format": "XEX Loader by Warranty Voider",
        "mz_verified": True, "pe_signature_verified": True,
        "pe_machine_hex": "0x01F2", "pe_optional_magic": "0x010B",
        "pe_image_length_bytes": run_phase2.EXPECTED_IMAGE_BYTES,
        "xex_entry_point": run_phase2.EXPECTED_ENTRY,
        "xex_image_base": run_phase2.EXPECTED_BASE,
        "pe_image_base": run_phase2.EXPECTED_BASE,
        "pe_sections": [{"name": ".text", "executable": True}],
        "executable_section_count": 1,
        "recovered_pe_sha256_private": "b" * 64,
        "entry_in_executable_memory": True,
        "entry_instruction_decoded": True,
        "full_auto_analysis_performed": False,
        "native_pc_execution_tested": False,
    }


class FingerprintTests(unittest.TestCase):
    def test_known_observation_passes(self):
        run_phase2.verify_source(good_observation())

    def test_hash_mismatch_rejected(self):
        value = good_observation()
        value["sha256"] = "0" * 64
        with self.assertRaises(source_intake.IntakeError):
            run_phase2.verify_source(value)

    def test_wrong_encryption_rejected(self):
        value = good_observation()
        value["xex"]["file_format"]["encryption_type"] = 0
        with self.assertRaises(source_intake.IntakeError):
            run_phase2.verify_source(value)

    def test_wrong_entry_rejected(self):
        value = good_observation()
        value["xex"]["entry_point_header_value"] = "0xDEADBEEF"
        with self.assertRaises(source_intake.IntakeError):
            run_phase2.verify_source(value)


class EvidenceTests(unittest.TestCase):
    def test_validated_metadata_passes(self):
        run_phase2.validate_probe(good_report(), good_observation())

    def test_synthetic_report_rejected_for_real_source(self):
        value = good_report()
        value["kind"] = "synthetic"
        with self.assertRaises(source_intake.IntakeError):
            run_phase2.validate_probe(value, good_observation())

    def test_missing_pe_signature_rejected(self):
        value = good_report()
        value["pe_signature_verified"] = False
        with self.assertRaises(source_intake.IntakeError):
            run_phase2.validate_probe(value, good_observation())

    def test_missing_disassembly_rejected(self):
        value = good_report()
        value["entry_instruction_decoded"] = False
        with self.assertRaises(source_intake.IntakeError):
            run_phase2.validate_probe(value, good_observation())

    def test_bad_recovered_image_size_rejected(self):
        value = good_report()
        value["pe_image_length_bytes"] += 4
        with self.assertRaises(source_intake.IntakeError):
            run_phase2.validate_probe(value, good_observation())

    def test_bad_image_hash_rejected(self):
        value = good_report()
        value["recovered_pe_sha256_private"] = None
        with self.assertRaises(source_intake.IntakeError):
            run_phase2.validate_probe(value, good_observation())

    def test_no_false_full_analysis_claim(self):
        value = good_report()
        value["full_auto_analysis_performed"] = True
        with self.assertRaises(source_intake.IntakeError):
            run_phase2.validate_probe(value, good_observation())

    def test_real_source_entry_disabled_in_actions(self):
        with mock.patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
            with self.assertRaises(source_intake.IntakeError):
                run_phase2.run(Path("synthetic.xex"))


if __name__ == "__main__":
    unittest.main()
