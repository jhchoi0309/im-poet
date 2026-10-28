#!/usr/bin/env python3
"""Uninstall local im-poetry skill copies by moving them into a recoverable backup.

Run: python3 uninstall-im-poetry.py [--dry-run] [--project /path/to/project]
Restore: python3 uninstall-im-poetry.py --restore /path/printed/by/this/script
Only local installations are handled; no account or repository is changed.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shlex
import sys
import tempfile


def present(path: Path) -> bool:
    return os.path.lexists(path)


def is_old_skill(path: Path) -> bool:
    # Archive an installation symlink itself; never follow or delete its target.
    if path.is_symlink():
        return True
    skill = path / "SKILL.md"
    if not path.is_dir() or skill.is_symlink() or not skill.is_file():
        return False
    with skill.open(encoding="utf-8-sig") as stream:
        text = stream.read(8192)
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", text, re.S)
    if not match:
        return False
    names = re.findall(r"^name:[ \t]*(.*?)[ \t]*$", match.group(1), re.M)
    return len(names) == 1 and names[0].strip().strip("\"'") == "im-poetry"


def write_manifest(directory: Path, entries: list[dict]) -> None:
    temporary = directory / "manifest.json.tmp"
    temporary.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(directory / "manifest.json")


def restore(directory: Path, dry_run: bool) -> int:
    directory = directory.expanduser().absolute()
    entries = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    plans = []
    if not isinstance(entries, list):
        raise ValueError("복구 목록의 형식이 올바르지 않습니다.")
    for entry in entries:
        original = Path(entry["original"])
        name = entry["backup"]
        if not original.is_absolute() or original.name != "im-poetry" or original.parent.name != "skills":
            raise ValueError("복구 대상은 skills/im-poetry 경로여야 합니다.")
        if not isinstance(name, str) or Path(name).name != name or name in (".", ".."):
            raise ValueError("백업 항목의 경로가 올바르지 않습니다.")
        archived = directory / name
        if not present(archived):
            continue
        if present(original):
            raise FileExistsError(f"복구 위치가 이미 존재합니다. 덮어쓰지 않습니다: {original}")
        plans.append((archived, original))
    for archived, original in plans:
        print(f"{'복구 예정' if dry_run else '복구'}: {original}")
        if not dry_run:
            original.parent.mkdir(parents=True, exist_ok=True)
            if present(original):
                raise FileExistsError(f"복구 도중 대상이 생겼습니다: {original}")
            archived.rename(original)
    print(f"{'복구 대상' if dry_run else '복구 완료'}: {len(plans)}개")
    return 0


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser(description="로컬 im-poetry만 백업 폴더로 옮겨 설치를 제거합니다.")
    parser.add_argument("--dry-run", action="store_true", help="이동하지 않고 대상만 확인")
    parser.add_argument("--project", type=Path, action="append", default=[], help="프로젝트별 설치도 확인; 여러 번 지정 가능")
    parser.add_argument("--home", type=Path, help="사용자 홈 경로; 기본값은 현재 사용자의 홈")
    parser.add_argument("--restore", type=Path, help="출력된 백업 폴더에서 복구")
    args = parser.parse_args(argv)
    if args.restore:
        if args.project or args.home:
            parser.error("--restore는 --project 또는 --home과 함께 사용할 수 없습니다.")
        return restore(args.restore, args.dry_run)

    home = (args.home or Path.home()).expanduser().absolute()
    candidates = [(label, home / location / "skills/im-poetry") for label, location in
                  (("claude", ".claude"), ("gemini", ".gemini"), ("codex", ".agents"))]
    codex_home = Path(os.environ.get("CODEX_HOME", str(home / ".codex"))).expanduser() if args.home is None else home / ".codex"
    candidates.append(("codex-legacy", codex_home.absolute() / "skills/im-poetry"))
    for number, project in enumerate(args.project, 1):
        base = project.expanduser().absolute()
        if not base.is_dir():
            raise NotADirectoryError(f"프로젝트 폴더가 없습니다: {base}")
        for label, location in (("claude", ".claude"), ("gemini", ".gemini"), ("codex", ".agents"), ("codex-legacy", ".codex")):
            candidates.append((f"project{number}-{label}", base / location / "skills/im-poetry"))

    plans, seen = [], set()
    for label, target in candidates:
        if not present(target):
            continue
        stat = target.lstat()
        identity = (stat.st_dev, stat.st_ino)
        if identity in seen:
            continue
        seen.add(identity)
        if not is_old_skill(target):
            print(f"건너뜀 (im-poetry 스킬임을 확인하지 못함): {target}")
            continue
        plans.append((label, target, identity))
        print(f"제거 대상{' (링크만)' if target.is_symlink() else ''}: {target}")
    if not plans:
        print("확인한 기본 경로에서 제거할 im-poetry 설치본을 찾지 못했습니다.")
        return 0
    if args.dry_run:
        print(f"미리보기: {len(plans)}개. 파일을 이동하지 않았습니다.")
        return 0

    backup_root = home / ".local/share/im-poetry-uninstall-backups"
    backup_root.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix=datetime.now().strftime("%Y%m%d-%H%M%S-"), dir=backup_root))
    entries = [{"original": str(target), "backup": f"{i:02d}-{label}", "moved": False}
               for i, (label, target, _) in enumerate(plans, 1)]
    write_manifest(directory, entries)
    print(f"백업 폴더: {directory}", flush=True)
    for entry, (_, target, identity) in zip(entries, plans):
        stat = target.lstat()
        if (stat.st_dev, stat.st_ino) != identity:
            raise RuntimeError(f"실행 중 대상이 바뀌었습니다: {target}")
        target.rename(directory / entry["backup"])
        entry["moved"] = True
        write_manifest(directory, entries)
    print(f"설치 제거 완료: {len(entries)}개")
    print("복구: " + shlex.join(["python3", str(Path(__file__).absolute()), "--restore", str(directory)]))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        print(f"중단: {error}\n일부 항목을 옮겼다면 위에 출력된 백업 폴더에 남아 있습니다.", file=sys.stderr)
        sys.exit(1)
