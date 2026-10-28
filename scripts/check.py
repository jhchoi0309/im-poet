#!/usr/bin/env python3
"""Check packaging, source links, prompt drift, and evaluation fixture shape."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

from build import render
from install import package_files

ROOT = Path(__file__).resolve().parents[1]


def check(root: Path) -> list[str]:
    errors: list[str] = []
    required = (
        "SKILL.md", "README.md", "LICENSE", "agents/openai.yaml", ".gitattributes",
        "scripts/bundle_upload.py", "scripts/bundle_install.py", "scripts/package_pair.py",
        "scripts/uninstall_legacy.py", "docs/package-usage.md", "docs/agent-install.md",
        "AGENTS.md", "CLAUDE.md", "GEMINI.md", "docs/gemini-app.md", "prompts/gemini-app.txt",
        "scripts/launchers/upload.sh", "scripts/launchers/upload.ps1",
        "scripts/launchers/install.sh", "scripts/launchers/install.ps1",
        "references/craft.md", "references/genres.md", "references/examples.md",
        "references/research.md", "references/source-catalog.json", "scripts/count_text.py",
        "docs/compatibility.md", "docs/research.md", "docs/evaluation.md",
        "prompts/im-poet.md", "evals/cases.json",
    )
    for name in required:
        if not (root / name).is_file():
            errors.append(f"Missing: {name}")
    if errors:
        return errors
    skill = (root / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", skill, re.S)
    metadata: dict[str, str] = {}
    if match:
        for line in match.group(1).splitlines():
            key, sep, value = line.partition(":")
            if not sep or key in metadata:
                errors.append("Invalid or duplicate frontmatter key")
                continue
            value = value.strip()
            try:
                metadata[key] = json.loads(value) if value.startswith('"') else value
            except json.JSONDecodeError:
                errors.append(f"Invalid quoted frontmatter: {key}")
    else:
        errors.append("Missing frontmatter")
    if set(metadata) != {"name", "description"}:
        errors.append("Keep portable frontmatter to name and description")
    if metadata.get("name") != "im-poet":
        errors.append("Wrong skill name")
    if not 1 <= len(metadata.get("description", "")) <= 1024:
        errors.append("Description must have 1..1024 characters")
    if len(skill.splitlines()) >= 500:
        errors.append("SKILL.md must stay below 500 lines")
    try:
        expected = render(skill)
        if (root / "prompts/im-poet.md").read_text(encoding="utf-8") != expected:
            errors.append("Standalone prompt is out of date")
        if (root / "prompts/gemini-app.txt").read_text(encoding="utf-8") != expected:
            errors.append("Gemini App prompt is out of date")
        if len(expected) > 8000:
            errors.append("Standalone prompt exceeds the project's 8000-character budget")
        if "references/" in expected or "portable:omit" in expected:
            errors.append("Standalone prompt depends on native-only references")
        package_files(root)
    except ValueError as exc:
        errors.append(str(exc))
    for file in sorted(root.rglob("*.md")):
        if ".git" in file.parts:
            continue
        text = file.read_text(encoding="utf-8")
        if "[TODO" in text:
            errors.append(f"Unfinished template: {file.relative_to(root)}")
        if "\ue200genui" in text or "\ue200cite" in text:
            errors.append(f"Conversation-only citation in {file.relative_to(root)}")
        for link in re.findall(r"\[[^\]]*\]\(([^\s)]+)\)", text):
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            destination = (file.parent / unquote(parsed.path)).resolve()
            if not destination.is_relative_to(root.resolve()) or not destination.exists():
                errors.append(f"Broken local link in {file.relative_to(root)}: {link}")
    data = json.loads((root / "evals/cases.json").read_text(encoding="utf-8"))
    ids: set[str] = set()
    for case in data.get("cases", []):
        if not all(case.get(key) for key in ("id", "request", "text", "must_preserve")):
            errors.append("Evaluation case missing required fields")
        if case.get("id") in ids:
            errors.append(f"Duplicate evaluation case: {case.get('id')}")
        ids.add(case.get("id"))
    if not ids:
        errors.append("No evaluation cases")
    return errors


def main() -> int:
    errors = check(ROOT)
    if errors:
        print("\n".join(f"ERROR: {item}" for item in errors))
        return 1
    print("Package, Markdown links, standalone prompt, and evaluation fixtures are consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
