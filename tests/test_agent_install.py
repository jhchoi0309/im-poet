from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import install_for_agent as agent


class AgentInstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "home 한글"
        self.project = self.root / "project with spaces"

    def test_host_detection_requires_an_unambiguous_signal(self):
        self.assertEqual(agent.detect_host({"CLAUDECODE": "1"}), "claude")
        self.assertEqual(agent.detect_host({"GEMINI_CLI": "1"}), "gemini")
        self.assertEqual(agent.detect_host({"CODEX_THREAD_ID": "thread"}), "codex")
        for env in ({}, {"CLAUDECODE": "1", "GEMINI_CLI": "1"}):
            with self.assertRaises(ValueError):
                agent.detect_host(env)

    def test_fresh_install_uses_expected_host_path(self):
        for host, relative in (("codex", ".agents"), ("claude", ".claude"), ("gemini", ".gemini")):
            home = self.home / host
            _, target = agent.run(ROOT, host, home)
            self.assertEqual(target, home / relative / "skills/im-poet")
            self.assertEqual(json.loads((target / "VERSION.json").read_text(encoding="utf-8"))["version"], "0.6.2")

    def test_gemini_updates_existing_shared_alias_and_keeps_backup(self):
        _, native = agent.run(ROOT, "gemini", self.home)
        _, shared = agent.run(ROOT, "codex", self.home)
        original = (shared / "SKILL.md").read_bytes()
        (shared / "SKILL.md").write_bytes(original + b"\nold version\n")
        message, target = agent.run(ROOT, "gemini", self.home)
        self.assertEqual(target, shared)
        self.assertIn("Backup:", message)
        self.assertEqual((shared / "SKILL.md").read_bytes(), original)
        self.assertTrue((native / "SKILL.md").is_file())
        backups = list(shared.parent.glob(".im-poet-backup-*"))
        self.assertEqual(len(backups), 1)
        self.assertTrue((backups[0] / "SKILL.md").read_bytes().endswith(b"old version\n"))

    def test_project_install_and_dry_run(self):
        _, target = agent.run(ROOT, "claude", self.home, self.project, dry_run=True)
        self.assertFalse(target.exists())
        _, target = agent.run(ROOT, "claude", self.home, self.project)
        self.assertEqual(target, self.project.resolve() / ".claude/skills/im-poet")
        self.assertTrue((target / "SKILL.md").is_file())

    def test_manifest_drift_stops_before_installation(self):
        source = self.root / "source"
        shutil.copytree(ROOT, source, ignore=shutil.ignore_patterns("__pycache__", ".git"))
        (source / "references/craft.md").write_text("modified", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "manifest"):
            agent.run(source, "codex", self.home)
        self.assertFalse((self.home / ".agents").exists())

    def test_command_installs_to_explicit_project(self):
        completed = subprocess.run([sys.executable, str(ROOT / "scripts/install_for_agent.py"),
                                    "--host", "gemini", "--project", str(self.project)],
                                   capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Verified package files", completed.stdout)
        self.assertTrue((self.project / ".gemini/skills/im-poet/SKILL.md").is_file())

    def test_command_auto_detects_gemini_and_rejects_ambiguous_hosts(self):
        env = os.environ.copy()
        for name in ("CLAUDECODE", "GEMINI_CLI", "CODEX_THREAD_ID"):
            env.pop(name, None)
        env["GEMINI_CLI"] = "1"
        command = [sys.executable, str(ROOT / "scripts/install_for_agent.py"), "--project", str(self.project)]
        result = subprocess.run(command, env=env, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Agent: gemini", result.stdout)
        env["CLAUDECODE"] = "1"
        ambiguous = subprocess.run(command, env=env, capture_output=True, text=True, encoding="utf-8")
        self.assertNotEqual(ambiguous.returncode, 0)
        self.assertIn("ambiguous", ambiguous.stderr)


if __name__ == "__main__":
    unittest.main()
