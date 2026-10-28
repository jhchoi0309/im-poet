"""Portable file handling; native junction coverage runs on the Windows CI job."""

from pathlib import Path, PureWindowsPath
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from install import NAME, LOCATIONS, destination_for, existing_files, has_skill_name, install, is_link


class PortabilityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="im-portability-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)

    def test_crlf_and_bom_package_installs_and_updates_without_losing_previous_bytes(self):
        source = self.base / "source"
        shutil.copytree(ROOT, source, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        skill = source / "SKILL.md"
        data = b"\xef\xbb\xbf" + skill.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        skill.write_bytes(data)
        target = self.base / "installed" / NAME
        install(source, target)
        self.assertEqual((target / "SKILL.md").read_bytes(), data)
        old = existing_files(target)
        install(ROOT, target, update=True)
        backup = next(target.parent.glob(f".{NAME}-backup-*"))
        self.assertEqual(existing_files(backup), old)
        self.assertTrue(has_skill_name((target / "SKILL.md").read_bytes(), NAME))

    def test_unicode_and_spaces_in_cli_destination(self):
        target = self.base / "사용자 폴더 📝" / NAME
        result = subprocess.run([sys.executable, str(ROOT / "scripts/install.py"),
                                 "--destination", str(target)], capture_output=True,
                                text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(str(target), result.stdout)
        self.assertTrue((target / "SKILL.md").is_file())

    def test_native_and_windows_home_paths_are_composed_without_posix_assumptions(self):
        windows_home = PureWindowsPath("C:/Users/한글 사용자")
        for tool, location in LOCATIONS.items():
            self.assertEqual(destination_for(tool, home=self.base), self.base / location / NAME)
            self.assertEqual(destination_for(tool, home=windows_home),
                             windows_home / str(location) / NAME)

    def test_explicit_project_root_overrides_home(self):
        project = self.base / "project with spaces"
        expected = project.resolve() / ".agents" / "skills" / NAME
        self.assertEqual(destination_for("codex", project=project, home=self.base / "home"), expected)

    def test_line_endings_do_not_relax_skill_identity(self):
        self.assertTrue(has_skill_name(f"---\r\nname: {NAME}\r\n---\r\n".encode(), NAME))
        self.assertFalse(has_skill_name(b"---\r\nname: unrelated\r\n---\r\n", NAME))
        self.assertFalse(has_skill_name(b"not frontmatter", NAME))

    def test_antigravity_app_and_cli_have_distinct_user_paths_and_shared_project_scope(self):
        self.assertEqual(destination_for("antigravity", home=self.base),
                         self.base / ".gemini/config/skills" / NAME)
        self.assertEqual(destination_for("antigravity-cli", home=self.base),
                         self.base / ".gemini/antigravity-cli/skills" / NAME)
        for tool in ("antigravity", "antigravity-cli"):
            project = self.base / tool
            result = subprocess.run([sys.executable, str(ROOT / "scripts/install.py"),
                                     "--target", tool, "--project", str(project)],
                                    capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((project / ".agents/skills" / NAME / "SKILL.md").is_file())

    @unittest.skipUnless(os.name == "nt", "Native Windows junction test")
    def test_windows_junction_target_is_preserved(self):
        actual = self.base / "actual folder"
        actual.mkdir()
        (actual / "marker.txt").write_text("keep", encoding="utf-8")
        target = self.base / NAME
        result = subprocess.run(["cmd", "/c", "mklink", "/J", str(target), str(actual)], capture_output=True)
        if result.returncode:
            self.skipTest("Junction creation unavailable on this filesystem")
        self.addCleanup(lambda: target.rmdir() if target.exists() else None)
        self.assertTrue(is_link(target))
        with self.assertRaises(FileExistsError):
            install(ROOT, target, update=True)
        self.assertEqual((actual / "marker.txt").read_text(encoding="utf-8"), "keep")


if __name__ == "__main__":
    unittest.main()
