#!/usr/bin/env python3
"""Install im-poet for the current local agent, preserving previous installations."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Mapping

from build import ROOT, manifest_text
from install import NAME, destination_for, existing_files, install, package_files


def detect_host(env: Mapping[str, str]) -> str:
    """Use host signals only when exactly one identifies the running agent."""
    detected = []
    if env.get("CLAUDECODE") == "1":
        detected.append("claude")
    if env.get("GEMINI_CLI") == "1":
        detected.append("gemini")
    if env.get("CODEX_THREAD_ID"):
        detected.append("codex")
    if len(detected) != 1:
        raise ValueError("Agent host is unknown or ambiguous; specify --host codex, claude, or gemini")
    return detected[0]


def choose_destination(host: str, home: Path, project: Path | None) -> Path:
    """Gemini's existing shared alias has precedence over its native folder."""
    if host == "gemini":
        shared = destination_for("codex", project=project, home=home)
        if os.path.lexists(shared):
            return shared
    return destination_for(host, project=project, home=home)


def verify_source(source: Path) -> None:
    actual = json.loads((source / "VERSION.json").read_text(encoding="utf-8"))
    expected = json.loads(manifest_text(source))
    if actual != expected:
        raise ValueError("Source version manifest does not match the package; nothing was installed")


def run(source: Path, host: str, home: Path, project: Path | None = None,
        *, destination: Path | None = None, dry_run: bool = False) -> tuple[str, Path]:
    verify_source(source)
    target = destination if destination is not None else choose_destination(host, home, project)
    message = install(source, target, update=True, dry_run=dry_run)
    if not dry_run and existing_files(target) != package_files(source):
        raise ValueError(f"Installed files differ from source: {target}")
    return message, target


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=("auto", "codex", "claude", "gemini"), default="auto")
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--project", type=Path, help="Install for this project instead of the user")
    scope.add_argument("--destination", type=Path, help="Exact skill directory for a custom host configuration")
    parser.add_argument("--workspace", type=Path, help="Also check this workspace for higher-priority Gemini skills")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        host = detect_host(os.environ) if args.host == "auto" else args.host
        project = args.project.expanduser().resolve() if args.project else None
        target = args.destination.expanduser().absolute() if args.destination else None
        message, target = run(ROOT, host, Path.home(), project, destination=target, dry_run=args.dry_run)
        print(f"Agent: {host}\n{message}")
        if not args.dry_run:
            print(f"Verified package files against source: {target}")
        if host == "claude" and os.environ.get("CLAUDE_CONFIG_DIR"):
            print("Note: custom Claude configuration detected; verify its active skill path in Claude Code.")
        if host == "gemini":
            workspace = args.workspace.expanduser().resolve() if args.workspace else None
            if project is None and workspace is not None:
                candidates = [destination_for(k, project=workspace) for k in ("codex", "gemini")]
                if any(os.path.lexists(path) for path in candidates):
                    print("Note: a workspace im-poet may have higher priority; verify Gemini's selected path.")
            print("Note: use gemini skills list --all or /skills list to verify discovery; reload if needed.")
        print("File verification does not establish activation or model output.")
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"Installation stopped: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
