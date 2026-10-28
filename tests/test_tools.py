"""Exercise installs, byte counting, and standalone prompt generation."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build import render
from install import existing_files, install, package_files


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.target = self.base / "skills" / "im-poet"

    def test_install_is_complete_and_does_not_copy_development_files(self):
        install(ROOT, self.target)
        self.assertEqual(package_files(ROOT), package_files(self.target))
        self.assertTrue((self.target / "scripts/count_text.py").is_file())
        self.assertTrue((self.target / "references/genres.md").is_file())
        self.assertFalse((self.target / "scripts/install.py").exists())
        self.assertFalse((self.target / "README.md").exists())

    def test_second_install_is_idempotent(self):
        install(ROOT, self.target)
        self.assertIn("Already current", install(ROOT, self.target))

    def test_different_existing_skill_is_untouched(self):
        self.target.mkdir(parents=True)
        file = self.target / "SKILL.md"
        file.write_text("my existing skill", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            install(ROOT, self.target)
        self.assertEqual(file.read_text(), "my existing skill")

    def test_extra_user_file_prevents_overwrite(self):
        install(ROOT, self.target)
        (self.target / "notes.txt").write_text("keep me")
        with self.assertRaises(FileExistsError):
            install(ROOT, self.target)
        self.assertEqual((self.target / "notes.txt").read_text(), "keep me")

    def test_update_preserves_previous_version_and_extra_files_in_backup(self):
        install(ROOT, self.target)
        (self.target / "notes.txt").write_text("keep me", encoding="utf-8")
        (self.target / "SKILL.md").write_text("---\nname: im-poet\n---\nold\n", encoding="utf-8")
        previous = existing_files(self.target)
        message = install(ROOT, self.target, update=True)
        backups = list(self.target.parent.glob(".im-poet-backup-*"))
        self.assertIn("Updated:", message)
        self.assertEqual(len(backups), 1)
        self.assertEqual(existing_files(backups[0]), previous)
        self.assertEqual(existing_files(self.target), package_files(ROOT))
        self.assertIn("Already current", install(ROOT, self.target, update=True))

    def test_update_rejects_an_unrelated_skill_even_when_requested(self):
        self.target.mkdir(parents=True)
        (self.target / "SKILL.md").write_text("---\nname: another\n---\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            install(ROOT, self.target, update=True)
        self.assertEqual((self.target / "SKILL.md").read_text(), "---\nname: another\n---\n")

    def test_update_dry_run_leaves_existing_version_and_no_backup(self):
        install(ROOT, self.target)
        (self.target / "notes.txt").write_text("keep me", encoding="utf-8")
        before = existing_files(self.target)
        message = install(ROOT, self.target, dry_run=True, update=True)
        self.assertIn("Would update with backup", message)
        self.assertEqual(existing_files(self.target), before)
        self.assertFalse(list(self.target.parent.glob(".im-poet-backup-*")))

    def test_update_restores_existing_folder_if_new_folder_cannot_be_placed(self):
        install(ROOT, self.target)
        (self.target / "notes.txt").write_text("keep me", encoding="utf-8")
        before = existing_files(self.target)
        original_rename = Path.rename

        def fail_stage_rename(path, destination):
            if path.name.startswith(".im-poet-stage-"):
                raise OSError("simulated failure")
            return original_rename(path, destination)

        with patch.object(Path, "rename", autospec=True, side_effect=fail_stage_rename):
            with self.assertRaises(OSError):
                install(ROOT, self.target, update=True)
        self.assertEqual(existing_files(self.target), before)
        self.assertFalse(list(self.target.parent.glob(".im-poet-stage-*")))

    def test_dry_run_creates_nothing(self):
        install(ROOT, self.target, dry_run=True)
        self.assertEqual(list(self.base.iterdir()), [])

    def test_target_symlink_is_not_followed(self):
        other = self.base / "other"
        other.mkdir()
        self.target.parent.mkdir()
        try:
            self.target.symlink_to(other, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"Symbolic links unavailable: {exc}")
        with self.assertRaises(FileExistsError):
            install(ROOT, self.target)
        self.assertEqual(list(other.iterdir()), [])

    def test_cli_project_locations(self):
        for target, directory in (
            ("claude", ".claude"), ("gemini", ".gemini"), ("codex", ".agents")
        ):
            completed = subprocess.run(
                [sys.executable, str(ROOT / "scripts/install.py"), "--target", target,
                 "--project", str(self.base)], text=True, encoding="utf-8", capture_output=True
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue((self.base / directory / "skills/im-poet/SKILL.md").is_file())

    def test_conflicting_cli_options_fail(self):
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts/install.py"), "--destination",
             str(self.target), "--project", str(self.base)], capture_output=True
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertFalse(self.target.exists())


class PromptTests(unittest.TestCase):
    def test_removes_only_frontmatter_and_native_reference_block(self):
        text = "---\nname: example\n---\n\nKeep me.\n<!-- portable:omit:start -->\nNative only\n<!-- portable:omit:end -->\nKeep this too.\n"
        self.assertEqual(render(text), "Keep me.\nKeep this too.\n")

    def test_gemini_app_prompt_is_self_contained_and_matches_the_source(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        prompt = (ROOT / "prompts/gemini-app.txt").read_text(encoding="utf-8")
        self.assertEqual(prompt, render(skill))
        self.assertNotIn("references/", prompt)
        self.assertNotIn("portable:omit", prompt)

    def test_malformed_omission_is_rejected(self):
        for tail in ("<!-- portable:omit:start -->", "<!-- portable:omit:end -->"):
            with self.assertRaises(ValueError):
                render("---\nname: example\n---\n" + tail)

    def test_native_and_standalone_share_protected_examples(self):
        prompt = render((ROOT / "SKILL.md").read_text(encoding="utf-8"))
        for phrase in ("원인을 찾으려 했다", "풍경을 발견할 수 있다", "건강을 증진할 수 있다", "24 °C"):
            self.assertIn(phrase, prompt)
        self.assertNotIn("references/", prompt)
        self.assertLessEqual(len(prompt), 8000)


class ByteCountTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "submission.txt"

    def run_count(self, content, *args):
        self.path.write_bytes(content.encode("utf-8"))
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts/count_text.py"), str(self.path), *args],
            text=True, encoding="utf-8", capture_output=True,
        )

    def test_utf8_counts_actual_bytes_spaces_and_mixed_newlines(self):
        result = self.run_count("가 A\r\n나\n", "--encoding", "utf-8", "--newlines", "preserve", "--max-bytes", "11")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("CRLF=1, LF=1, CR=0", result.stdout)
        self.assertIn("bytes: 11", result.stdout)
        self.assertIn("status: within limit", result.stdout)
        self.assertNotIn("가 A", result.stdout)

    def test_crlf_and_lf_normalization_are_explicit(self):
        lf = self.run_count("가\r\n나\r", "--encoding", "utf-8", "--newlines", "lf")
        crlf = self.run_count("가\r\n나\r", "--encoding", "utf-8", "--newlines", "crlf")
        self.assertIn("bytes: 8", lf.stdout)
        self.assertIn("bytes: 10", crlf.stdout)
        self.assertIn("CRLF=1, LF=0, CR=1", crlf.stdout)

    def test_encoding_and_limit_change_real_count(self):
        utf8 = self.run_count("한글", "--encoding", "utf-8", "--max-bytes", "5")
        cp949 = self.run_count("한글", "--encoding", "cp949", "--max-bytes", "5")
        self.assertEqual(utf8.returncode, 2)
        self.assertIn("bytes: 6", utf8.stdout)
        self.assertEqual(cp949.returncode, 0)
        self.assertIn("bytes: 4", cp949.stdout)

    def test_unencodable_text_does_not_claim_a_count(self):
        result = self.run_count("사진 📷", "--encoding", "cp949")
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("bytes:", result.stdout)

    def test_encoding_is_required_and_bom_is_counted(self):
        missing = self.run_count("한글")
        self.assertNotEqual(missing.returncode, 0)
        result = self.run_count("\ufeff가\n", "--encoding", "utf-8")
        self.assertIn("bytes: 7", result.stdout)
        self.assertIn("input_BOM: included if present", result.stdout)


if __name__ == "__main__":
    unittest.main()
