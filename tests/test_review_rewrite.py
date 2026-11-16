from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from install import install
from review_rewrite import profile, review, sentences


class ReviewRewriteTests(unittest.TestCase):
    def test_decimal_and_fenced_code_do_not_inflate_sentence_count(self):
        text = "전압은 3.3 V였다. 원인은 모른다.\n```python\na = 1\n# a line\n```\n"
        self.assertEqual(len(sentences(text)), 2)
        self.assertEqual(profile(text)["sentences_approximate"], 2)

    def test_empty_profile_has_no_invented_coverage(self):
        p = profile("")
        self.assertEqual(p["sentences_approximate"], 0)
        self.assertIsNone(p["surface_ending_coverage"])
        self.assertIsNone(p["sentence_length_characters"]["median"])

    def test_explicit_literal_checks_do_not_certify_meaning(self):
        report, code = review("효과가 확인됐다. 전압은 3.3 V였다.",
                              "효과가 확인되지 않았다. 전압은 3.3 V였다.", literals=["3.3 V"])
        self.assertEqual(code, 0)
        self.assertEqual(report["semantic_equivalence"], "not_measured")
        self.assertEqual(report["literary_quality"], "not_measured")
        self.assertTrue(report["manual_review_required"])

    def test_missing_literal_and_forbidden_output_are_failures(self):
        report, code = review("전압은 3.3 V였다.", "전압은 낮았다.", literals=["3.3 V"])
        self.assertEqual(code, 1)
        self.assertFalse(report["literal_checks"]["items"][0]["present_in_rewrite"])
        report, code = review("두 말", "두" + chr(0x00B7) + "말")
        self.assertEqual(code, 1)
        self.assertEqual(report["output_separator_check"]["hits"][0]["codepoint"], "U+00B7")

    def test_source_only_is_not_an_output_check(self):
        report, code = review("두" + chr(0x00B7) + "말", samples=["짧은 글입니다."])
        self.assertEqual(code, 0)
        self.assertFalse(report["output_separator_check"]["performed"])
        self.assertIsNone(report["profiles"]["rewrite"])
        self.assertEqual(len(report["profiles"]["samples"]), 1)

    def test_invalid_protection_rules_are_rejected(self):
        for literals in ("문자열", [""], ["없던 구절"], ["원문", "원문"]):
            with self.assertRaises(ValueError):
                review("원문", "수정문", literals=literals)
        with self.assertRaises(ValueError):
            review("원문", literals=["원문"])

    def test_installed_cli_is_read_only_and_works_outside_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            installed = base / "skill"
            install(ROOT, installed)
            source, revised, sample, protected = [base / name for name in ("원문.txt", "수정.txt", "샘플.txt", "보호.json")]
            source.write_bytes("\ufeff비공개본문 3.3 V였습니다.\r\n".encode("utf-8"))
            revised.write_text("비공개본문은 3.3 V였습니다.", encoding="utf-8")
            sample.write_text("조용히 바라보았습니다.", encoding="utf-8")
            protected.write_text('["3.3 V"]', encoding="utf-8")
            before = [p.read_bytes() for p in (source, revised, sample, protected)]
            result = subprocess.run([sys.executable, str(installed / "scripts/review_rewrite.py"),
                                     str(source), "--rewrite", str(revised), "--sample", str(sample),
                                     "--protected", str(protected)], cwd=base, capture_output=True,
                                    text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("비공개본문", result.stdout)
            report = json.loads(result.stdout)
            self.assertTrue(report["output_separator_check"]["performed"])
            self.assertEqual([p.read_bytes() for p in (source, revised, sample, protected)], before)

    def test_bad_cli_input_is_not_reported_as_success(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source, config = base / "source.txt", base / "literals.json"
            source.write_bytes(b"\xff")
            script = ROOT / "scripts/review_rewrite.py"
            result = subprocess.run([sys.executable, str(script), str(source)], capture_output=True)
            self.assertEqual(result.returncode, 2)
            source.write_text("원문", encoding="utf-8")
            config.write_text("null", encoding="utf-8")
            result = subprocess.run([sys.executable, str(script), str(source), "--rewrite", str(source),
                                     "--protected", str(config)], capture_output=True)
            self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
