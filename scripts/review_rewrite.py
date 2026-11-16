#!/usr/bin/env python3
"""Read-only surface profiles and explicit literal checks; never a quality score."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import statistics
import sys

from check_output import positions


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def prose_lines(text: str) -> list[str]:
    """Ignore fenced code; this is intentionally not a full Markdown parser."""
    result: list[str] = []
    fence = ""
    for line in text.splitlines():
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if fence:
            if re.fullmatch(r"\s*" + re.escape(fence[0]) + "{" + str(len(fence)) + r",}\s*", line):
                fence = ""
            continue
        if marker:
            fence = marker.group(1)
            continue
        result.append(line)
    return result


def sentences(text: str) -> list[str]:
    """A decimal such as 3.3 is retained; abbreviations can still be mis-split."""
    text = "\n".join(prose_lines(text))
    return [part.strip() for part in re.split(r"(?<=[.!?。！？])\s+|\n+", text) if part.strip()]


def ending_kind(sentence: str) -> str:
    tail = sentence.rstrip().rstrip('.!?。！？”’"\'」』) ]')
    if re.search(r"(?:습니다|습니까|합니다|합니까|입니다|입니까|겠습니다)$", tail):
        return "formal"
    if tail.endswith("요"):
        return "polite_yo"
    if tail.endswith("다"):
        return "plain_da"
    if tail.endswith(("까", "니", "냐")):
        return "other_question"
    return "unclassified"


def profile(text: str) -> dict:
    parts = sentences(text)
    lengths = sorted(len(part) for part in parts)
    counts = {key: 0 for key in ("formal", "polite_yo", "plain_da", "other_question", "unclassified")}
    for part in parts:
        counts[ending_kind(part)] += 1
    plain = "\n".join(prose_lines(text))
    return {
        "characters": len(text),
        "non_whitespace_characters": sum(not c.isspace() for c in text),
        "paragraphs_approximate": len([p for p in re.split(r"\n\s*\n", plain) if p.strip()]),
        "sentences_approximate": len(parts),
        "sentence_length_characters": {
            "minimum": min(lengths) if lengths else None,
            "median": statistics.median(lengths) if lengths else None,
            "maximum": max(lengths) if lengths else None,
        },
        "surface_ending_counts": counts,
        "surface_ending_coverage": round((len(parts) - counts["unclassified"]) / len(parts), 4) if parts else None,
        "method": "heuristic; not morphological analysis or a measure of certainty",
    }


def review(source: str, rewrite: str | None = None, *, samples: list[str] | None = None,
           literals: list[str] | None = None) -> tuple[dict, int]:
    if literals is not None:
        if not isinstance(literals, list) or any(not isinstance(s, str) or not s for s in literals):
            raise ValueError("Protected literals must be a JSON array of nonempty strings")
        if len(set(literals)) != len(literals):
            raise ValueError("Protected literals must not contain duplicate entries")
        if rewrite is None:
            raise ValueError("Protected-literal checks require --rewrite")
        for index, literal in enumerate(literals):
            if literal not in source:
                raise ValueError(f"Protected literal {index + 1} is absent from the source")
    checks = [{"index": index + 1, "present_in_rewrite": literal in rewrite}
              for index, literal in enumerate(literals or [])]
    hits = positions(rewrite) if rewrite is not None else []
    report = {
        "schema_version": 1,
        "profiles": {
            "source": profile(source),
            "rewrite": profile(rewrite) if rewrite is not None else None,
            "samples": [profile(sample) for sample in samples or []],
        },
        "literal_checks": {"scope": "only explicitly supplied strings; not count, order, or meaning",
                           "requested": literals is not None, "items": checks},
        "output_separator_check": {
            "performed": rewrite is not None,
            "hits": [{"line": line, "column": column, "codepoint": codepoint}
                     for line, column, codepoint in hits],
        },
        "semantic_equivalence": "not_measured",
        "literary_quality": "not_measured",
        "manual_review_required": True,
    }
    return report, int(bool(hits) or any(not item["present_in_rewrite"] for item in checks))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--rewrite", type=Path)
    parser.add_argument("--sample", type=Path, action="append", default=[])
    parser.add_argument("--protected", type=Path, help="JSON array of exact strings that must occur in source and rewrite")
    args = parser.parse_args()
    try:
        literals = json.loads(read_text(args.protected)) if args.protected else None
        if args.protected and literals is None:
            raise ValueError("Protected literals must be a JSON array, not null")
        report, code = review(read_text(args.source), read_text(args.rewrite) if args.rewrite else None,
                              samples=[read_text(path) for path in args.sample], literals=literals)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"Review stopped: {exc}", file=sys.stderr)
        return 2
    output = json.dumps(report, ensure_ascii=True, indent=2) + "\n"
    if hasattr(sys.stdout, "buffer"):
        sys.stdout.buffer.write(output.encode("utf-8"))
    else:
        sys.stdout.write(output)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
