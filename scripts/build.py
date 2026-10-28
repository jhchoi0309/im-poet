#!/usr/bin/env python3
"""Build the standalone prompt from SKILL.md without third-party packages."""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START = "<!-- portable:omit:start -->"
END = "<!-- portable:omit:end -->"


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check without writing")
    args = parser.parse_args()
    output = ROOT / "prompts" / "im-poet.md"
    expected = render((ROOT / "SKILL.md").read_text(encoding="utf-8"))
    if args.check:
        if not output.is_file() or output.read_text(encoding="utf-8") != expected:
            print("Out of date: prompts/im-poet.md; run python3 scripts/build.py")
            return 1
        print("Standalone prompt matches SKILL.md")
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(expected, encoding="utf-8")
    print(f"Built prompts/im-poet.md ({len(expected)} characters)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
