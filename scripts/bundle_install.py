#!/usr/bin/env python3
"""Install both source packages without Git, GitHub CLI, Bash, or network access."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--target", action="append", choices=("all", "claude", "gemini", "codex", "antigravity", "antigravity-cli"), required=True)
    parser.add_argument("--project", type=Path)
    parser.add_argument("--update", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    targets = ("claude", "gemini", "codex", "antigravity", "antigravity-cli") if "all" in args.target else tuple(dict.fromkeys(args.target))
    root = args.package_dir.expanduser().resolve()
    env = dict(os.environ, PYTHONUTF8="1")
    commands = []
    for name in ("im-novelist", "im-poet"):
        script = root / name / "scripts/install.py"
        if not script.is_file():
            parser.exit(1, f"Source package not found: {name}\n")
        for target in targets:
            command = [sys.executable, str(script), "--target", target]
            if args.project is not None:
                command += ["--project", str(args.project.expanduser().resolve())]
            if args.update:
                command.append("--update")
            commands.append(command)
    try:
        for command in commands:
            result = subprocess.run([*command, "--dry-run"], env=env, capture_output=True,
                                    text=True, encoding="utf-8", errors="replace", check=True)
            if args.dry_run:
                print(result.stdout.strip())
        if not args.dry_run:
            for command in commands:
                subprocess.run(command, env=env, check=True, shell=False)
    except (OSError, subprocess.CalledProcessError) as error:
        detail = getattr(error, "stderr", None) or str(error)
        parser.exit(1, f"Installation stopped: {detail}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
