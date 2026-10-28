#!/usr/bin/env python3
"""Check final UTF-8 text for forbidden middle-dot separators without echoing it."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

FORBIDDEN = frozenset(("\u00b7", "\u2027", "\u30fb", "\u318d"))


def positions(text: str) -> list[tuple[int, int, str]]:
    return [
        (line_number, column, f"U+{ord(character):04X}")
        for line_number, line in enumerate(text.splitlines(), 1)
        for column, character in enumerate(line, 1)
        if character in FORBIDDEN
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Final UTF-8 text to check")
    args = parser.parse_args()
    try:
        text = args.path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as error:
        print(f"Cannot read final text: {error}", file=sys.stderr)
        return 2
    found = positions(text)
    for line, column, codepoint in found:
        print(f"{codepoint} at line {line}, column {column}")
    if found:
        print(f"Remove {len(found)} forbidden separator(s), then check again.")
        return 1
    print("Final text contains no forbidden middle-dot separators.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
