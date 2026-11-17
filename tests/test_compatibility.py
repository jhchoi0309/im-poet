from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import diagnose_installations as diagnostic
import install


class InstallationDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        configuration = patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": "", "GEMINI_CLI_HOME": ""})
        configuration.start()
        self.addCleanup(configuration.stop)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "home with spaces"
        self.project = self.root / "project 한글"
        self.expected = json.loads((ROOT / "VERSION.json").read_text(encoding="utf-8"))

    def test_missing_current_and_changed_files(self):
        target = self.home / ".agents/skills/im-poet"
        self.assertEqual(diagnostic.inspect(target, self.expected)["status"], "missing")
        install.install(ROOT, target)
        self.assertEqual(diagnostic.inspect(target, self.expected)["status"], "current")
        (target / "references/craft.md").write_text("changed", encoding="utf-8")
        result = diagnostic.inspect(target, self.expected)
        self.assertEqual(result["status"], "different")
        self.assertIn("Missing or different: references/craft.md", result["issues"])

    def test_unversioned_and_invalid_are_not_called_current(self):
        target = self.home / ".claude/skills/im-poet"
        install.install(ROOT, target)
        (target / "VERSION.json").unlink()
        self.assertEqual(diagnostic.inspect(target, self.expected)["status"], "unversioned")
        (target / "VERSION.json").write_text("not json", encoding="utf-8")
        self.assertEqual(diagnostic.inspect(target, self.expected)["status"], "invalid")

    def test_warns_about_shared_gemini_and_project_collisions(self):
        for scope, name in ((self.home, "shared"), (self.home, "gemini"), (self.project, "shared")):
            install.install(ROOT, scope / diagnostic.LOCATIONS[name])
        report = diagnostic.audit(self.home, self.project, self.expected)
        self.assertTrue(any("Gemini can prefer" in w for w in report["warnings"]))
        self.assertTrue(any("Codex" in w and "both exist" in w for w in report["warnings"]))
        self.assertEqual(report["locations"]["project"]["shared"]["status"], "current")

    def test_custom_claude_config_is_inspected_without_redirecting_project_scope(self):
        custom = self.root / "사용자 설정"
        target = custom / "skills/im-poet"
        install.install(ROOT, target)
        report = diagnostic.audit(self.home, self.project, self.expected,
                                  env={"CLAUDE_CONFIG_DIR": str(custom)})
        self.assertEqual(report["locations"]["user"]["claude"]["status"], "current")
        self.assertEqual(report["locations"]["user"]["claude"]["path"], str(target))
        self.assertEqual(report["locations"]["project"]["claude"]["status"], "missing")

    def test_custom_gemini_home_is_inspected_separately_from_codex_home(self):
        custom = self.root / "gemini home"
        install.install(ROOT, custom / ".agents/skills/im-poet")
        install.install(ROOT, custom / ".gemini/skills/im-poet")
        report = diagnostic.audit(self.home, None, self.expected,
                                  env={"GEMINI_CLI_HOME": str(custom)})
        entries = report["locations"]["user"]
        self.assertEqual(entries["shared"]["status"], "missing")
        self.assertEqual(entries["gemini_shared_override"]["status"], "current")
        self.assertEqual(entries["gemini"]["status"], "current")
        self.assertTrue(any("Gemini can prefer" in w for w in report["warnings"]))


if __name__ == "__main__":
    unittest.main()
