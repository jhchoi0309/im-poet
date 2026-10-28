"""Check the reversible legacy uninstaller and optional native PowerShell launchers."""

from pathlib import Path
import contextlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DistributionTests(unittest.TestCase):
    def test_legacy_uninstall_and_restore_preserve_the_two_new_skills(self):
        spec = importlib.util.spec_from_file_location("uninstall_legacy", ROOT / "scripts/uninstall_legacy.py")
        legacy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(legacy)
        with tempfile.TemporaryDirectory(prefix="im-legacy-") as temporary:
            home = Path(temporary) / "한글 home folder"
            for folder in (".claude", ".gemini", ".agents"):
                for name in ("im-poetry", "im-novelist", "im-poet"):
                    target = home / folder / "skills" / name
                    target.mkdir(parents=True)
                    (target / "SKILL.md").write_bytes(f"---\r\nname: {name}\r\n---\r\n".encode("utf-8"))
                    (target / "extra.txt").write_text("keep", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(legacy.main(["--home", str(home), "--dry-run"]), 0)
            self.assertFalse((home / ".local").exists())
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(legacy.main(["--home", str(home)]), 0)
            backup = next((home / ".local/share/im-poetry-uninstall-backups").iterdir())
            for folder in (".claude", ".gemini", ".agents"):
                self.assertFalse((home / folder / "skills/im-poetry").exists())
                for name in ("im-novelist", "im-poet"):
                    self.assertEqual((home / folder / "skills" / name / "extra.txt").read_text(encoding="utf-8"), "keep")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(legacy.main(["--restore", str(backup)]), 0)
            for folder in (".claude", ".gemini", ".agents"):
                self.assertEqual((home / folder / "skills/im-poetry/extra.txt").read_text(encoding="utf-8"), "keep")

    @unittest.skipUnless(shutil.which("pwsh") or shutil.which("powershell"), "Native PowerShell is not available")
    def test_powershell_launchers_forward_unicode_and_spaced_arguments(self):
        shell = shutil.which("pwsh") or shutil.which("powershell")
        with tempfile.TemporaryDirectory(prefix="im-powershell-") as temporary:
            base = Path(temporary) / "한글 folder with spaces"
            base.mkdir()
            for name in ("upload", "install"):
                shutil.copy2(ROOT / "scripts/launchers" / (name + ".ps1"), base / (name + ".ps1"))
                (base / (name + ".py")).write_text("import json, sys\nprint(json.dumps(sys.argv[1:]))\n", encoding="utf-8")
                result = subprocess.run([shell, "-NoProfile", "-NonInteractive", "-File", str(base / (name + ".ps1")),
                                         "--target", "한글 value with spaces"], capture_output=True, text=True, encoding="utf-8", errors="replace")
                if result.returncode and "PSSecurityException" in result.stderr:
                    self.skipTest("Local PowerShell execution policy blocks scripts; direct Python commands remain available")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout), ["--target", "한글 value with spaces"])


if __name__ == "__main__":
    unittest.main()
