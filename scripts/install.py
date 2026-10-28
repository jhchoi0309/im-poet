#!/usr/bin/env python3
"""Install the skill; updates require --update and preserve the previous folder."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]
NAME = "im-poet"
PACKAGE = ("SKILL.md", "references", "agents", "LICENSE", "scripts/count_text.py")
LOCATIONS = {
    "claude": Path(".claude/skills"),
    "gemini": Path(".gemini/skills"),
    "codex": Path(".agents/skills"),
}


def package_files(source: Path) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for entry in PACKAGE:
        path = source / entry
        if not path.exists():
            raise ValueError(f"Missing package entry: {entry}")
        candidates = [path, *sorted(path.rglob("*"))] if path.is_dir() else [path]
        for candidate in candidates:
            if candidate.is_symlink():
                raise ValueError(f"Package contains a symlink: {candidate.name}")
            if candidate.is_file():
                result[candidate.relative_to(source).as_posix()] = candidate.read_bytes()
    if not result.get("SKILL.md", b"").startswith(b"---\nname: im-poet\n"):
        raise ValueError("Unexpected skill name or missing frontmatter")
    return result


def existing_files(target: Path) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for path in target.rglob("*"):
        if path.is_symlink():
            raise FileExistsError(f"Refusing to replace symlink inside {target}")
        if path.is_file():
            result[path.relative_to(target).as_posix()] = path.read_bytes()
    return result


def install(source: Path, target: Path, *, dry_run: bool = False, update: bool = False) -> str:
    files = package_files(source)
    if target.is_symlink():
        raise FileExistsError(f"Refusing to replace symlink: {target}")
    updating = target.exists()
    if updating:
        if not target.is_dir():
            raise FileExistsError(f"Destination is not a directory: {target}")
        previous = existing_files(target)
        if previous == files:
            return f"Already current: {target}"
        if not update:
            raise FileExistsError(
                f"Existing destination differs: {target}. "
                "Use --update to keep a backup and replace it, or choose --destination. "
                "Nothing was overwritten."
            )
        if not previous.get("SKILL.md", b"").startswith(b"---\nname: im-poet\n"):
            raise ValueError(f"Existing destination is not an im-poet skill: {target}")
    if dry_run:
        verb = "update with backup" if updating else "install"
        return f"Would {verb} {len(files)} files: {target}"
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".im-poet-stage-", dir=target.parent))
    try:
        for relative, data in files.items():
            destination = stage / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        if updating:
            # Preserve all existing files, including user additions, before replacing.
            if target.is_symlink() or not target.is_dir() or existing_files(target) != previous:
                raise FileExistsError(f"Destination changed during installation: {target}")
            backup = Path(tempfile.mkdtemp(prefix=".im-poet-backup-", dir=target.parent))
            backup.rmdir()
            target.rename(backup)
            try:
                if os.path.lexists(target):
                    raise FileExistsError(f"Destination appeared during installation: {target}")
                stage.rename(target)
            except BaseException:
                if not os.path.lexists(target):
                    backup.rename(target)
                raise
            return f"Updated: {target}\nBackup: {backup}"
        # Refuse a destination that appeared during copying, including broken links.
        if os.path.lexists(target):
            raise FileExistsError(f"Destination appeared during installation: {target}")
        stage.rename(target)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return f"Installed: {target}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--target", choices=sorted(LOCATIONS))
    choice.add_argument("--destination", type=Path, help="Exact destination skill directory")
    parser.add_argument("--project", type=Path, help="Project root; default is the user home")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--update", action="store_true", help="Back up and replace an existing im-poet skill")
    args = parser.parse_args()
    if args.destination and args.project:
        parser.error("--project cannot be combined with --destination")
    base = args.project.expanduser().resolve() if args.project else Path.home()
    target = (
        args.destination.expanduser().absolute()
        if args.destination
        else base / LOCATIONS[args.target] / NAME
    )
    try:
        print(install(ROOT, target, dry_run=args.dry_run, update=args.update))
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Installation stopped: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
