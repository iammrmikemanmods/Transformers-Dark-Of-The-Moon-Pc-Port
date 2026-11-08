"""Synthetic fixtures only. No bytes from any proprietary game."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import source_intake as intake
from check_repository import forbidden_path


def synthetic_xex():
    data = bytearray(0x440)
    struct.pack_into(">4s5I", data, 0, b"XEX2", 1, 0x400, 0, 0x100, 4)
    records = [(0x00010100, 0x82001000), (0x00010201, 0x82000000),
               (0x00040006, 0x80), (0x000003FF, 0xA0)]
    for index, pair in enumerate(records):
        struct.pack_into(">II", data, 24 + index * 8, *pair)
    # Deliberately invented title/media IDs. Not DOTM metadata.
    struct.pack_into(">4I4BI", data, 0x80, 0x11223344, 0x01020304,
                     0x01020300, 0x12345678, 2, 0, 1, 1, 0)
    struct.pack_into(">IHH", data, 0xA0, 8, 1, 2)
    struct.pack_into(">II", data, 0x100, 0x184, 0x200000)
    struct.pack_into(">I", data, 0x210, 0x82000000)
    return bytes(data)


class HeaderTests(unittest.TestCase):
    def parse(self, data):
        return intake.parse_xex_header(bytes(data), len(data))

    def test_valid_synthetic_metadata(self):
        report = self.parse(synthetic_xex())
        self.assertEqual(report["execution_info"]["title_id"], "0x12345678")
        self.assertEqual(report["execution_info"]["version_packed"], "0x01020304")
        self.assertEqual(report["entry_point_header_value"], "0x82001000")
        self.assertEqual(report["image_base_header_value"], "0x82000000")
        self.assertEqual(report["declared_image"]["load_address"], "0x82000000")
        self.assertEqual(report["file_format"], {"encryption_type": 1, "compression_type": 2})
        self.assertFalse(report["rsa_signature_verified"])
        self.assertFalse(report["pe_machine_type_verified"])

    def test_bad_magic(self):
        with self.assertRaises(intake.IntakeError):
            self.parse(b"NOPE" + synthetic_xex()[4:])

    def test_truncated_fixed_header(self):
        for size in range(24):
            with self.subTest(size=size), self.assertRaises(intake.IntakeError):
                self.parse(synthetic_xex()[:size])

    def test_header_beyond_file(self):
        data = bytearray(synthetic_xex())
        struct.pack_into(">I", data, 8, len(data) + 4)
        with self.assertRaises(intake.IntakeError):
            self.parse(data)

    def test_header_without_payload(self):
        with self.assertRaises(intake.IntakeError):
            self.parse(synthetic_xex()[:0x400])

    def test_incomplete_header_buffer(self):
        with self.assertRaises(intake.IntakeError):
            intake.parse_xex_header(synthetic_xex()[:100], 0x440)

    def test_table_overflow(self):
        data = bytearray(synthetic_xex())
        struct.pack_into(">I", data, 20, 0xFFFFFFFF)
        with self.assertRaises(intake.IntakeError):
            self.parse(data)

    def test_duplicate_key(self):
        data = bytearray(synthetic_xex())
        struct.pack_into(">I", data, 32, 0x00010100)
        with self.assertRaises(intake.IntakeError):
            self.parse(data)

    def test_execution_pointer_outside_header(self):
        data = bytearray(synthetic_xex())
        struct.pack_into(">I", data, 44, 0x3FF)
        with self.assertRaises(intake.IntakeError):
            self.parse(data)

    def test_execution_pointer_inside_table(self):
        data = bytearray(synthetic_xex())
        struct.pack_into(">I", data, 44, 24)
        with self.assertRaises(intake.IntakeError):
            self.parse(data)

    def test_variable_header_missing_size(self):
        data = bytearray(synthetic_xex())
        struct.pack_into(">I", data, 0xA0, 0)
        with self.assertRaises(intake.IntakeError):
            self.parse(data)

    def test_file_format_too_short(self):
        data = bytearray(synthetic_xex())
        struct.pack_into(">I", data, 0xA0, 4)
        with self.assertRaises(intake.IntakeError):
            self.parse(data)

    def test_security_table_overflow(self):
        data = bytearray(synthetic_xex())
        struct.pack_into(">I", data, 0x280, 0xFFFFFFFF)
        with self.assertRaises(intake.IntakeError):
            self.parse(data)

    def test_security_pointer_outside_header(self):
        data = bytearray(synthetic_xex())
        struct.pack_into(">I", data, 16, 0x3FF)
        with self.assertRaises(intake.IntakeError):
            self.parse(data)

    def test_absent_optional_info_is_unknown(self):
        data = bytearray(synthetic_xex())
        struct.pack_into(">I", data, 20, 0)
        result = self.parse(data)
        self.assertIsNone(result["execution_info"])
        self.assertIsNone(result["entry_point_header_value"])
        self.assertIsNone(result["file_format"])


class FilesystemTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.xex = self.source / "synthetic.xex"
        self.xex.write_bytes(synthetic_xex())

    def run_cli(self, *args):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return intake.main(list(map(str, args)))

    def test_hash_and_source_preservation(self):
        before = self.xex.stat()
        result = intake.inspect_xex(self.xex)
        self.assertEqual(result["sha256"], hashlib.sha256(synthetic_xex()).hexdigest())
        self.assertEqual(result["size_bytes"], len(synthetic_xex()))
        self.assertIsNone(result["known_good_match"])
        self.assertEqual(self.xex.read_bytes(), synthetic_xex())
        self.assertEqual(self.xex.stat().st_mtime_ns, before.st_mtime_ns)

    def test_new_report(self):
        report = self.root / "reports" / "report.json"
        self.assertEqual(self.run_cli("xex", self.xex, "--out", report), 0)
        data = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(data["build_id"], intake.BUILD_ID)
        self.assertEqual(data["result"]["xex"]["execution_info"]["title_id"], "0x12345678")

    def test_existing_report_never_overwritten(self):
        output = self.root / "existing.json"
        output.write_text("KEEP", encoding="utf-8")
        self.assertEqual(self.run_cli("xex", self.xex, "--out", output), 2)
        self.assertEqual(output.read_text(), "KEEP")

    def test_source_never_overwritten(self):
        self.assertEqual(self.run_cli("xex", self.xex, "--out", self.xex), 2)
        self.assertEqual(self.xex.read_bytes(), synthetic_xex())

    def test_report_inside_inventory_rejected(self):
        output = self.source / "report.json"
        self.assertEqual(self.run_cli("inventory", self.source, "--out", output), 2)
        self.assertFalse(output.exists())

    def test_inventory_includes_empty_directory(self):
        (self.source / "empty").mkdir()
        (self.source / "hello.txt").write_bytes(b"abc")
        result = intake.inventory(self.source)
        self.assertEqual(result["file_count"], 2)
        self.assertEqual(result["directory_count_including_root"], 2)
        entry = next(e for e in result["entries"] if e["path"] == "hello.txt")
        self.assertEqual(entry["sha256"], hashlib.sha256(b"abc").hexdigest())
        self.assertIn({"path": "empty", "kind": "directory"}, result["entries"])
        self.assertFalse(result["atomic_snapshot"])

    def test_missing_input_fails_without_report(self):
        output = self.root / "missing-report.json"
        self.assertEqual(self.run_cli("xex", self.root / "missing", "--out", output), 2)
        self.assertFalse(output.exists())

    def test_invalid_xex_fails_without_report(self):
        self.xex.write_bytes(b"invalid")
        output = self.root / "invalid-report.json"
        self.assertEqual(self.run_cli("xex", self.xex, "--out", output), 2)
        self.assertFalse(output.exists())

    def test_header_resource_limit(self):
        data = bytearray(synthetic_xex())
        struct.pack_into(">I", data, 8, intake.MAX_HEADER + 1)
        self.xex.write_bytes(data)
        with self.assertRaisesRegex(intake.IntakeError, "resource limit"):
            intake.inspect_xex(self.xex)

    def test_symlink_input_rejected(self):
        link = self.source / "link"
        try:
            link.symlink_to(self.xex)
        except (OSError, NotImplementedError):
            self.skipTest("Host does not permit creating symbolic links")
        with self.assertRaises(intake.IntakeError):
            intake.inspect_xex(link)
        with self.assertRaises(intake.IntakeError):
            intake.inventory(self.source)

    def test_directory_not_a_file(self):
        with self.assertRaises(intake.IntakeError):
            intake.inspect_xex(self.source)


class PublicationGuardTests(unittest.TestCase):
    def test_protected_paths(self):
        for name in ("default.XEX", "disc.ISO", "disc.7z.001", "data/test.upk",
                     "generated/game.cpp", ".local/report.json", "build/out.txt"):
            with self.subTest(name=name):
                self.assertTrue(forbidden_path(name))

    def test_source_paths_allowed(self):
        for name in ("tools/source_intake.py", "README.md", "tests/test_source_intake.py"):
            with self.subTest(name=name):
                self.assertFalse(forbidden_path(name))


if __name__ == "__main__":
    unittest.main()
