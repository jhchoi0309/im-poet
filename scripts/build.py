#!/usr/bin/env python3
"""Build the standalone prompt from SKILL.md without third-party packages."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START = "<!-- portable:omit:start -->"
END = "<!-- portable:omit:end -->"
SKILL_VERSION = "0.5.0"
REVISED_ON = "2026-10-29"


def render(skill: str) -> str:
    """Drop frontmatter and native-only references; keep editorial rules intact."""
    lines = skill.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("SKILL.md must start with YAML frontmatter")
    try:
        stop = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("Unclosed frontmatter") from exc
    output: list[str] = []
    omitted = False
    for line in lines[stop + 1 :]:
        if line == START:
            if omitted:
                raise ValueError("Nested portable omission block")
            omitted = True
        elif line == END:
            if not omitted:
                raise ValueError("Unexpected portable omission end")
            omitted = False
        elif not omitted:
            output.append(line)
    if omitted:
        raise ValueError("Unclosed portable omission block")
    return "\n".join(output).strip() + "\n"


def manifest_text(root: Path) -> str:
    paths = [root / "SKILL.md", *sorted((root / "references").rglob("*")),
             root / "scripts/count_text.py", root / "scripts/check_output.py"]
    hashes = {}
    for path in paths:
        if path.is_symlink():
            raise ValueError("Version manifest cannot follow symbolic links")
        if path.is_file():
            hashes[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    prompt = render((root / "SKILL.md").read_text(encoding="utf-8")).encode("utf-8")
    hashes["prompts/im-poet.md"] = hashlib.sha256(prompt).hexdigest()
    hashes["prompts/gemini-app.txt"] = hashes["prompts/im-poet.md"]
    return json.dumps(
        {"schema_version": 1, "name": "im-poet", "version": SKILL_VERSION,
         "revised_on": REVISED_ON, "sha256": hashes},
        ensure_ascii=False, sort_keys=True, indent=2,
    ) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check without writing")
    args = parser.parse_args()
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    expected = render(skill)
    outputs = {ROOT / "prompts" / "im-poet.md": expected,
               ROOT / "prompts" / "gemini-app.txt": expected,
               ROOT / "VERSION.json": manifest_text(ROOT)}
    if args.check:
        for output, content in outputs.items():
            if not output.is_file() or output.read_text(encoding="utf-8") != content:
                print(f"Out of date: {output.name}; run the build script")
                return 1
        print("Prompts and version manifest match the current skill content")
        return 0
    for output, content in outputs.items():
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8", newline="\n")
    print(f"Built standalone and Gemini App prompts ({len(expected)} characters each)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
