from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check import unchanged_examples
from check_output import positions
from install import install
from build import manifest_text


class OutputStyleTests(unittest.TestCase):
    def test_detects_separators_in_prose_quotes_and_code_blocks(self):
        text = "가" + chr(0x00B7) + "나\n“다" + chr(0x2027) + "라”\n"
        text += "~~~\n마" + chr(0x30FB) + "바\n~~~\n사" + chr(0x318D) + "아"
        self.assertEqual(
            positions(text),
            [(1, 2, "U+00B7"), (2, 3, "U+2027"),
             (4, 2, "U+30FB"), (6, 2, "U+318D")],
        )

    def test_keeps_ordinary_punctuation_and_line_endings(self):
        self.assertEqual(positions("너, 나와 우리 / 사랑: 말과 기억.\r\n- 다음\n"), [])

    def test_actual_installed_checker_fails_until_text_is_cleaned(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            target = base / "installed"
            install(ROOT, target)
            path = base / "final.txt"
            path.write_text("사랑" + chr(0x00B7) + "그리움", encoding="utf-8-sig")
            command = [sys.executable, str(target / "scripts/check_output.py"), str(path)]
            bad = subprocess.run(command, text=True, encoding="utf-8", capture_output=True)
            self.assertEqual(bad.returncode, 1, bad.stderr)
            self.assertNotIn("사랑", bad.stdout)
            self.assertIn("U+00B7", bad.stdout)
            path.write_text("사랑과 그리움", encoding="utf-8")
            clean = subprocess.run(command, text=True, encoding="utf-8", capture_output=True)
            self.assertEqual(clean.returncode, 0, clean.stderr)

    def test_invalid_utf8_is_not_reported_as_clean(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.txt"
            path.write_bytes(b"\xff")
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/check_output.py"), str(path)],
                capture_output=True,
            )
            self.assertEqual(result.returncode, 2)

    def test_unchanged_improvement_example_is_caught(self):
        same = "원문:\n\n> 썼다. 지웠다.\n\n윤문:\n\n> 썼다. 지웠다.\n"
        self.assertEqual(len(unchanged_examples(same)), 1)
        different = same.replace("윤문:\n\n> 썼다. 지웠다.", "윤문:\n\n> 썼다가 지웠다.")
        self.assertEqual(unchanged_examples(different), [])

    def test_installed_version_fingerprint_detects_changed_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "installed"
            install(ROOT, target)
            recorded = (target / "VERSION.json").read_text(encoding="utf-8")
            self.assertEqual(recorded, manifest_text(target))
            reference = target / "references/word-choice.md"
            reference.write_text(reference.read_text(encoding="utf-8") + "\nChanged reference.\n",
                                 encoding="utf-8")
            self.assertNotEqual(recorded, manifest_text(target))


if __name__ == "__main__":
    unittest.main()
