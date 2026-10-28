#!/usr/bin/env python3
"""Publish the paired Git bundles from Windows, macOS, or Linux (Python 3.10+)."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

NAMES = ("im-novelist", "im-poet")
TOOLS = ("claude", "gemini", "codex", "antigravity", "antigravity-cli")


class UploadError(RuntimeError):
    pass


class Runner:
    def __init__(self, env: dict[str, str] | None = None):
        self.env = dict(os.environ if env is None else env)
        self.env.update(PYTHONUTF8="1", GIT_TERMINAL_PROMPT="0")

    def require(self, command: str) -> None:
        if not shutil.which(command, path=self.env.get("PATH")):
            raise UploadError(f"Required command not found: {command}")

    def run(self, args: list[str | Path], *, check: bool = True) -> subprocess.CompletedProcess:
        # Argument arrays avoid shell quoting, including paths with spaces or Korean text.
        command = [str(value) for value in args]
        result = subprocess.run(command, env=self.env, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", shell=False)
        if check and result.returncode:
            raise UploadError(f"Command failed ({result.returncode}): {command[0]} {command[1:]}\n{result.stderr or result.stdout}")
        return result


def verify_checksums(package: Path) -> None:
    manifest = package / "SHA256SUMS"
    recorded: dict[str, str] = {}
    for line in manifest.read_text(encoding="utf-8-sig").splitlines():
        match = re.fullmatch(r"([0-9a-fA-F]{64})  ([^/\\]+)", line)
        if not match or match[2] in recorded or match[2] in (".", ".."):
            raise UploadError("Invalid or duplicate checksum entry")
        name = match[2]
        path = package / name
        if path.is_symlink() or not path.is_file():
            raise UploadError(f"Missing or linked package file: {name}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != match[1].lower():
            raise UploadError(f"Checksum mismatch: {name}")
        recorded[name] = digest
    if not all(name + ".bundle" in recorded for name in NAMES):
        raise UploadError("Both skill bundles must appear in SHA256SUMS")


def prepare(package: Path, work: Path, runner: Runner) -> dict[str, Path]:
    verify_checksums(package)
    runner.require("git")
    checkouts = {}
    for name in NAMES:
        destination = work / name
        runner.run(["git", "-c", "core.autocrlf=false", "clone", "--branch", "main",
                    package / (name + ".bundle"), destination])
        runner.run(["git", "-C", destination, "bundle", "verify", package / (name + ".bundle")])
        runner.run(["git", "-C", destination, "remote", "remove", "origin"])
        checkouts[name] = destination
    return checkouts


def install_checkouts(checkouts: dict[str, Path], runner: Runner, *, targets: list[str],
                      project: Path | None, update: bool) -> None:
    commands = []
    for source in checkouts.values():
        for tool in targets:
            command: list[str | Path] = [sys.executable, source / "scripts/install.py", "--target", tool]
            if project is not None:
                command += ["--project", project]
            if update:
                command.append("--update")
            commands.append(command)
    # Check every destination before the first installed copy is changed.
    for command in commands:
        runner.run([*command, "--dry-run"])
    for command in commands:
        print(runner.run(command).stdout.strip())


def publish(checkouts: dict[str, Path], runner: Runner, *, owner: str, visibility: str) -> None:
    runner.require("gh")
    if runner.run(["gh", "auth", "status", "--hostname", "github.com"], check=False).returncode:
        raise UploadError("Sign in first: gh auth login --hostname github.com --git-protocol https --web")
    login = runner.run(["gh", "api", "--hostname", "github.com", "user", "--jq", ".login"]).stdout.strip()
    if login.casefold() != owner.casefold():
        raise UploadError(f"Active account is {login}, expected {owner}. Use: gh auth switch --hostname github.com --user {owner}")
    runner.run(["gh", "auth", "setup-git", "--hostname", "github.com"])
    exists: dict[str, bool] = {}
    # Check both repositories for divergence before any remote repository write.
    for name, checkout in checkouts.items():
        remote = f"https://github.com/{owner}/{name}.git"
        runner.run(["git", "-C", checkout, "remote", "add", "origin", remote])
        lookup = runner.run(["gh", "api", "--hostname", "github.com", f"repos/{owner}/{name}",
                             "--jq", ".full_name"], check=False)
        if lookup.returncode:
            if not re.search(r"\bHTTP\s+404\b", lookup.stderr):
                raise UploadError(f"Repository lookup failed for {name}: {lookup.stderr}")
            exists[name] = False
            continue
        exists[name] = True
        runner.run(["git", "-C", checkout, "fetch", "origin"])
        has_main = runner.run(["git", "-C", checkout, "show-ref", "--verify", "--quiet",
                               "refs/remotes/origin/main"], check=False)
        if has_main.returncode == 0:
            ancestor = runner.run(["git", "-C", checkout, "merge-base", "--is-ancestor", "origin/main", "main"], check=False)
            if ancestor.returncode:
                raise UploadError(f"{name}: existing main is not an ancestor of this package. No force push was attempted.")
        elif has_main.returncode == 1:
            refs = runner.run(["git", "-C", checkout, "for-each-ref", "--format=%(refname)", "refs/remotes/origin"]).stdout
            if refs.strip():
                raise UploadError(f"{name}: existing repository uses a branch other than main")
        else:
            raise UploadError(f"Cannot inspect main for {name}: {has_main.stderr}")
    for name, checkout in checkouts.items():
        if not exists[name]:
            description = ("Korean prose editing with meaning and voice preserved" if name == "im-novelist"
                           else "Korean literary and poetic editing grounded in public literature research")
            runner.run(["gh", "repo", "create", f"{owner}/{name}", "--" + visibility, "--description", description])
        runner.run(["git", "-C", checkout, "push", "--set-upstream", "origin", "main:main"])
        expected = runner.run(["git", "-C", checkout, "rev-parse", "main"]).stdout.strip()
        refs = runner.run(["git", "-C", checkout, "ls-remote", "origin", "refs/heads/main"]).stdout.split()
        if not refs or refs[0] != expected:
            raise UploadError(f"Remote main verification failed: {name}")
        print(f"Uploaded: https://github.com/{owner}/{name}")


def main(argv: list[str] | None = None, *, runner: Runner | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser(description=__doc__)
    visibility = parser.add_mutually_exclusive_group()
    visibility.add_argument("--public", action="store_true")
    visibility.add_argument("--private", action="store_true")
    parser.add_argument("--check", action="store_true", help="Verify and restore bundles without GitHub access")
    parser.add_argument("--package-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--work-dir", type=Path, help="New directory to retain the restored source")
    parser.add_argument("--owner", default="jhchoi0309")
    parser.add_argument("--install", action="store_true", help="Also install the two skills after uploading")
    parser.add_argument("--target", action="append", choices=TOOLS)
    parser.add_argument("--project", type=Path, help="Install only in this project")
    args = parser.parse_args(argv)
    if not args.check and not (args.public or args.private):
        parser.error("Choose --public or --private, or use --check for offline verification")
    if args.check and args.install:
        parser.error("--check cannot be combined with --install")
    if (args.target or args.project) and not args.install:
        parser.error("--target and --project require --install")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}", args.owner):
        parser.error("Invalid GitHub owner")
    runner = runner or Runner()
    work = None
    try:
        # Fail before creating a working directory if the package is damaged.
        package = args.package_dir.expanduser().resolve()
        verify_checksums(package)
        if args.work_dir:
            work = args.work_dir.expanduser().absolute()
            work.mkdir(parents=True, exist_ok=False)
        else:
            work = Path(tempfile.mkdtemp(prefix="im-writing-upload-"))
        print(f"Source folder: {work}", flush=True)
        checkouts = prepare(package, work, runner)
        if args.check:
            print("Both bundles are complete and readable; no GitHub request was made.")
            return 0
        publish(checkouts, runner, owner=args.owner, visibility="public" if args.public else "private")
        if args.install:
            install_checkouts(checkouts, runner, targets=list(dict.fromkeys(args.target or TOOLS)),
                              project=args.project, update=True)
        return 0
    except (OSError, ValueError, UploadError) as error:
        print(f"Stopped: {error}", file=sys.stderr)
        if work is not None:
            print(f"Restored source, if any, remains at: {work}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
