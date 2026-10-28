#!/usr/bin/env python3
"""Count a UTF-8 text file using an explicitly chosen output encoding."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys


def newline_counts(text: str) -> tuple[int, int, int]:
    crlf = text.count("\r\n")
    return crlf, text.count("\n") - crlf, text.count("\r") - crlf


def prepare(text: str, newline_mode: str) -> str:
    if newline_mode == "preserve":
        return text
    if newline_mode not in ("lf", "crlf"):
        raise ValueError("Unknown newline mode")
    newline = "\n" if newline_mode == "lf" else "\r\n"
    return re.sub(r"\r\n|\r|\n", lambda _: newline, text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="Text file encoded as UTF-8")
    parser.add_argument("--encoding", required=True, help="Encoding used to count bytes")
    parser.add_argument("--newlines", choices=("preserve", "lf", "crlf"), default="preserve")
    parser.add_argument("--max-bytes", type=int)
    args = parser.parse_args()
    if args.max_bytes is not None and args.max_bytes < 0:
        parser.error("--max-bytes must be zero or greater")
    try:
        original = args.file.read_bytes().decode("utf-8")
        measured = prepare(original, args.newlines)
        total = len(measured.encode(args.encoding))
    except (OSError, UnicodeError, LookupError) as exc:
        parser.exit(1, f"Count stopped: {exc}\n")
    crlf, lf, cr = newline_counts(original)
    print(f"input_encoding: utf-8; count_encoding: {args.encoding}")
    print(f"input_newlines: CRLF={crlf}, LF={lf}, CR={cr}; counted_as: {args.newlines}")
    print("spaces_and_final_newline: included; input_BOM: included if present")
    print(f"bytes: {total}")
    if args.max_bytes is not None:
        within = total <= args.max_bytes
        print(f"max_bytes: {args.max_bytes}; status: {'within limit' if within else 'over limit'}")
        return 0 if within else 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
