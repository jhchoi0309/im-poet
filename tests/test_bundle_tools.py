"""Exercise publishing with real local Git repositories and a simulated GitHub API."""

from pathlib import Path
import contextlib
import hashlib
import importlib.util
import io
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import bundle_upload
from install import NAME as SOURCE_NAME


class LocalGitHub(bundle_upload.Runner):
    """Only GitHub API calls are simulated; cloning, ancestry, pushes, and refs are real Git."""
    def __init__(self, remotes):
        env = dict(os.environ, GIT_CONFIG_COUNT="1",
                   GIT_CONFIG_KEY_0=f"url.{remotes.as_uri()}/.insteadOf",
                   GIT_CONFIG_VALUE_0="https://github.com/jhchoi0309/")
        super().__init__(env)
        self.remotes = remotes
        self.calls = []
        self.login = "jhchoi0309"
        self.lookup_error = None

    def require(self, command):
        if command != "gh":
            super().require(command)

    def run(self, args, *, check=True):
        args = list(map(str, args))
        self.calls.append(args)
        if args[0] != "gh":
            return super().run(args, check=check)
        code, out, error = 0, "", ""
        if args[1:3] in (["auth", "status"], ["auth", "setup-git"]):
            pass
        elif args[1] == "api" and "user" in args:
            out = self.login + "\n"
        elif args[1] == "api":
            endpoint = next(x for x in args if x.startswith("repos/"))
            name = endpoint.rsplit("/", 1)[1]
            if self.lookup_error:
                code, error = 1, self.lookup_error
            elif (self.remotes / (name + ".git")).exists():
                out = "jhchoi0309/" + name + "\n"
            else:
                code, error = 1, "gh: Not Found (HTTP 404)"
        elif args[1:3] == ["repo", "create"]:
            name = args[3].rsplit("/", 1)[1]
            super().run(["git", "init", "--bare", "--initial-branch=main", self.remotes / (name + ".git")])
        else:
            raise AssertionError(f"Unexpected GitHub call: {args}")
        result = subprocess.CompletedProcess(args, code, out, error)
        if check and code:
            raise bundle_upload.UploadError(error)
        return result


@unittest.skipUnless(shutil.which("git"), "Git is required for offline integration tests")
class BundleToolsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="im-bundle-test-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name) / "한글 package folder"
        self.base.mkdir()
        self.package = self.base / "package"
        self.package.mkdir()
        self.remotes = self.base / "remotes"
        self.remotes.mkdir()
        self.runner = LocalGitHub(self.remotes)
        for name in bundle_upload.NAMES:
            source = self.package / name
            source.mkdir()
            # Source packages exercise the real installer under both skill identities.
            for rel in ("SKILL.md", "VERSION.json", "references", "agents", "LICENSE", "scripts", "docs"):
                original, target = ROOT / rel, source / rel
                if original.is_dir():
                    shutil.copytree(original, target, ignore=shutil.ignore_patterns("__pycache__"))
                else:
                    shutil.copy2(original, target)
            for rel in ("SKILL.md", "scripts/install.py"):
                file = source / rel
                file.write_text(file.read_text(encoding="utf-8").replace(SOURCE_NAME, name), encoding="utf-8", newline="\n")
            self.git("init", "-b", "main", source)
            self.git("-C", source, "config", "user.name", "Test")
            self.git("-C", source, "config", "user.email", "test@example.org")
            self.git("-C", source, "config", "core.autocrlf", "false")
            self.git("-C", source, "add", "--all")
            self.git("-C", source, "-c", "commit.gpgsign=false", "commit", "-m", "Fixture")
            self.git("-C", source, "bundle", "create", self.package / (name + ".bundle"), "main")
        self.write_checksums()

    def git(self, *args):
        return self.runner.run(["git", *args]).stdout.strip()

    def write_checksums(self):
        lines = [hashlib.sha256((self.package / (name + ".bundle")).read_bytes()).hexdigest()
                 + "  " + name + ".bundle\n" for name in bundle_upload.NAMES]
        (self.package / "SHA256SUMS").write_text("".join(lines), encoding="utf-8", newline="\n")

    def upload(self, *flags):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return bundle_upload.main(["--package-dir", str(self.package), "--work-dir",
                                       str(self.base / ("restore-" + str(len(self.runner.calls)))), *flags], runner=self.runner)

    def create_remote(self, name):
        self.git("init", "--bare", "--initial-branch=main", self.remotes / (name + ".git"))
        self.git("-C", self.package / name, "remote", "add", "origin", self.remotes / (name + ".git"))
        self.git("-C", self.package / name, "push", "origin", "main")

    def tip(self, name):
        return self.git("--git-dir", self.remotes / (name + ".git"), "rev-parse", "main")

    def test_create_both_repositories_and_verify_remote_main(self):
        self.assertEqual(self.upload("--private"), 0)
        for name in bundle_upload.NAMES:
            self.assertEqual(self.tip(name), self.git("-C", self.package / name, "rev-parse", "main"))
        creates = [call for call in self.runner.calls if call[:3] == ["gh", "repo", "create"]]
        self.assertEqual(len(creates), 2)
        self.assertTrue(all("--private" in call for call in creates))

    def test_existing_repositories_are_idempotent(self):
        for name in bundle_upload.NAMES:
            self.create_remote(name)
        self.assertEqual(self.upload("--public"), 0)
        self.assertFalse(any(call[:3] == ["gh", "repo", "create"] for call in self.runner.calls))

    def test_divergent_main_prevents_writes_to_both_repositories(self):
        for name in bundle_upload.NAMES:
            self.create_remote(name)
        source = self.package / "im-novelist"
        (source / "new-file.txt").write_text("newer independent change", encoding="utf-8")
        self.git("-C", source, "add", "new-file.txt")
        self.git("-C", source, "-c", "commit.gpgsign=false", "commit", "-m", "Advance remote")
        self.git("-C", source, "push", "origin", "main")
        previous = {name: self.tip(name) for name in bundle_upload.NAMES}
        self.runner.calls.clear()
        self.assertEqual(self.upload("--public"), 1)
        self.assertFalse(any(call[:3] == ["gh", "repo", "create"] or "push" in call for call in self.runner.calls))
        self.assertEqual({name: self.tip(name) for name in bundle_upload.NAMES}, previous)

    def test_wrong_account_cannot_publish(self):
        self.runner.login = "different-account"
        self.assertEqual(self.upload("--public"), 1)
        self.assertEqual(list(self.remotes.iterdir()), [])

    def test_network_error_is_not_treated_as_missing_repository(self):
        self.runner.lookup_error = "network connection failed"
        self.assertEqual(self.upload("--public"), 1)
        self.assertFalse(any(call[:3] == ["gh", "repo", "create"] for call in self.runner.calls))

    def test_damaged_bundle_fails_before_any_github_request(self):
        self.runner.calls.clear()
        with (self.package / "im-poet.bundle").open("ab") as stream:
            stream.write(b"damage")
        self.assertEqual(self.upload("--public"), 1)
        self.assertEqual(self.runner.calls, [])

    def test_offline_check_does_not_require_or_contact_github(self):
        self.assertEqual(self.upload("--check"), 0)
        self.assertFalse(any(call[0] == "gh" for call in self.runner.calls))

    def test_install_both_source_packages_without_git_or_github(self):
        project = self.base / "프로젝트 with spaces"
        command = [sys.executable, str(ROOT / "scripts/bundle_install.py"), "--package-dir", str(self.package),
                   "--target", "all", "--project", str(project)]
        preview = subprocess.run([*command, "--dry-run"], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertFalse(project.exists())
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        for name in bundle_upload.NAMES:
            for folder in (".claude", ".gemini", ".agents"):
                self.assertTrue((project / folder / "skills" / name / "SKILL.md").is_file())

    def test_install_preflight_preserves_all_destinations_when_one_conflicts(self):
        project = self.base / "project"
        conflict = project / ".agents/skills/im-poet"
        conflict.mkdir(parents=True)
        (conflict / "notes.txt").write_text("keep", encoding="utf-8")
        result = subprocess.run([sys.executable, str(ROOT / "scripts/bundle_install.py"), "--package-dir",
                                 str(self.package), "--target", "all", "--project", str(project)], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((conflict / "notes.txt").read_text(encoding="utf-8"), "keep")
        self.assertFalse((project / ".claude").exists())
        self.assertFalse((project / ".gemini").exists())

    def test_archive_contains_committed_source_bundles_and_native_launchers(self):
        import package_pair
        output = self.base / "paired.tar.gz"
        with contextlib.redirect_stdout(io.StringIO()):
            package_pair.build(self.package / "im-novelist", self.package / "im-poet", output)
        restored = self.base / "archive restored"
        restored.mkdir()
        # This archive was generated from the temporary fixtures immediately above.
        with tarfile.open(output) as archive:
            for member in archive.getmembers():
                target = restored / member.name
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                elif member.isfile():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with archive.extractfile(member) as stream:
                        target.write_bytes(stream.read())
        package = restored / "im-writing-skills"
        bundle_upload.verify_checksums(package)
        for name in bundle_upload.NAMES:
            self.assertTrue((package / name / "SKILL.md").is_file())
            self.assertTrue((package / (name + ".bundle")).is_file())
            app = package / "gemini-app" / name
            self.assertEqual((app / "SKILL.md").read_bytes(), (package / name / "SKILL.md").read_bytes())
            self.assertTrue((app / "references").is_dir())
            self.assertTrue((app / "LICENSE.txt").is_file())
            self.assertFalse((app / "scripts/install.py").exists())
            self.assertFalse((app / "scripts/bundle_upload.py").exists())
            self.assertFalse((app / ".git").exists())
            for file in app.rglob("*"):
                if file.is_file():
                    self.assertNotIn("\x00", file.read_text(encoding="utf-8"))
        for name in ("install.py", "upload.py", "install.ps1", "upload.ps1", "install.sh", "upload.sh"):
            self.assertTrue((package / name).is_file(), name)


if __name__ == "__main__":
    unittest.main()
