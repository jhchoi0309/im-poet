#!/usr/bin/env python3
"""Install the skill; updates back up the previous folder unless explicitly disabled."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
NAME = "im-poet"
PACKAGE = ("SKILL.md", "VERSION.json", "references", "agents", "LICENSE",
           "scripts/count_text.py", "scripts/check_output.py")
LOCATIONS = {
    "claude": Path(".claude/skills"),
    "gemini": Path(".gemini/skills"),
    "codex": Path(".agents/skills"),
    "antigravity": Path(".gemini/config/skills"),
    "antigravity-cli": Path(".gemini/antigravity-cli/skills"),
}
PROJECT_LOCATIONS = {**LOCATIONS, "antigravity": Path(".agents/skills"), "antigravity-cli": Path(".agents/skills")}


def is_link(path: Path) -> bool:
    """Reject symbolic links and Windows junctions without following their targets."""
    if path.is_symlink():
        return True
    try:
        return getattr(path.lstat(), "st_reparse_tag", None) == getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", 0xA0000003)
    except FileNotFoundError:
        return False


def has_skill_name(data: bytes, name: str) -> bool:
    """Accept UTF-8 BOM and LF/CRLF checkouts while retaining the exact skill identity."""
    try:
        return data.decode("utf-8-sig").splitlines()[:2] == ["---", f"name: {name}"]
    except UnicodeDecodeError:
        return False


def destination_for(tool: str, *, project: Path | None = None, home: Path | None = None) -> Path:
    base = project.expanduser().resolve() if project is not None else (home or Path.home())
    locations = PROJECT_LOCATIONS if project is not None else LOCATIONS
    return base / locations[tool] / NAME


def checked_files(root: Path) -> list[Path]:
    """Inspect directory entries before descending into them (also for Windows junctions)."""
    result = []
    pending = [root]
    while pending:
        path = pending.pop()
        if is_link(path):
            raise ValueError(f"Refusing a link or junction: {path}")
        if path.is_dir():
            pending.extend(sorted(path.iterdir()))
        elif path.is_file():
            result.append(path)
    return result


def package_files(source: Path) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    if is_link(source):
        raise ValueError("Package root cannot be a link or junction")
    for entry in PACKAGE:
        path = source / entry
        if is_link(path):
            raise ValueError(f"Package contains a link or junction: {entry}")
        if not path.exists():
            raise ValueError(f"Missing package entry: {entry}")
        candidates = checked_files(path)
        for candidate in candidates:
            if is_link(candidate):
                raise ValueError(f"Package contains a symlink: {candidate.name}")
            if candidate.is_file():
                result[candidate.relative_to(source).as_posix()] = candidate.read_bytes()
    if not has_skill_name(result.get("SKILL.md", b""), NAME):
        raise ValueError("Unexpected skill name or missing frontmatter")
    return result


def existing_files(target: Path) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for path in checked_files(target):
        if is_link(path):
            raise FileExistsError(f"Refusing to replace symlink inside {target}")
        if path.is_file():
            result[path.relative_to(target).as_posix()] = path.read_bytes()
    return result


def install(source: Path, target: Path, *, dry_run: bool = False, update: bool = False,
            no_backup: bool = False) -> str:
    if no_backup and not update:
        raise ValueError("--no-backup requires --update")
    files = package_files(source)
    if is_link(target):
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
        if not has_skill_name(previous.get("SKILL.md", b""), NAME):
            raise ValueError(f"Existing destination is not an im-poet skill: {target}")
    if dry_run:
        verb = ("update without backup" if no_backup else "update with backup") if updating else "install"
        return f"Would {verb} {len(files)} files: {target}"
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".im-poet-stage-", dir=target.parent))
    try:
        for relative, data in files.items():
            destination = stage / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        if updating:
            # Keep the old folder until the new folder is in place, so a failed
            # swap can restore it even when persistent backup was disabled.
            if is_link(target) or not target.is_dir() or existing_files(target) != previous:
                raise FileExistsError(f"Destination changed during installation: {target}")
            prefix = ".im-poet-previous-" if no_backup else ".im-poet-backup-"
            previous_folder = Path(tempfile.mkdtemp(prefix=prefix, dir=target.parent))
            previous_folder.rmdir()
            target.rename(previous_folder)
            try:
                if os.path.lexists(target):
                    raise FileExistsError(f"Destination appeared during installation: {target}")
                stage.rename(target)
            except BaseException as exc:
                if not os.path.lexists(target):
                    try:
                        previous_folder.rename(target)
                    except OSError as restore_exc:
                        raise OSError(f"Could not restore previous skill; it remains at {previous_folder}") from restore_exc
                else:
                    raise FileExistsError(
                        f"Destination appeared during installation: {target}. "
                        f"Previous skill remains at {previous_folder}"
                    ) from exc
                raise
            if no_backup:
                try:
                    shutil.rmtree(previous_folder)
                except OSError as exc:
                    raise OSError(f"Updated, but could not remove previous folder: {previous_folder}: {exc}") from exc
                return f"Updated without backup: {target}"
            return f"Updated: {target}\nBackup: {previous_folder}"
        # Refuse a destination that appeared during copying, including broken links.
        if os.path.lexists(target):
            raise FileExistsError(f"Destination appeared during installation: {target}")
        stage.rename(target)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return f"Installed: {target}"


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--target", choices=sorted(LOCATIONS))
    choice.add_argument("--destination", type=Path, help="Exact destination skill directory")
    parser.add_argument("--project", type=Path, help="Project root; default is the user home")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--update", action="store_true", help="Back up and replace an existing im-poet skill")
    parser.add_argument("--no-backup", action="store_true", help="With --update, remove the previous skill after a successful replacement")
    args = parser.parse_args()
    if args.destination and args.project:
        parser.error("--project cannot be combined with --destination")
    if args.no_backup and not args.update:
        parser.error("--no-backup requires --update")
    target = (
        args.destination.expanduser().absolute()
        if args.destination
        else destination_for(args.target, project=args.project)
    )
    try:
        print(install(ROOT, target, dry_run=args.dry_run, update=args.update, no_backup=args.no_backup))
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Installation stopped: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
