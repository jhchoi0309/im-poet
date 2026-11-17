#!/usr/bin/env python3
"""Read-only comparison of common local im-poet installations with this checkout."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Mapping

from install import NAME, ROOT, has_skill_name

LOCATIONS = {
    "shared": Path(".agents/skills") / NAME,
    "claude": Path(".claude/skills") / NAME,
    "gemini": Path(".gemini/skills") / NAME,
}


def inspect(path: Path, expected: dict) -> dict:
    result = {"path": str(path), "status": "missing", "version": None, "issues": []}
    if not path.exists():
        return result
    if not path.is_dir():
        result.update(status="invalid", issues=["Destination is not a directory"])
        return result
    try:
        skill = path / "SKILL.md"
        if not skill.is_file() or not has_skill_name(skill.read_bytes(), NAME):
            result.update(status="invalid", issues=["Missing or unrecognized SKILL.md"])
            return result
        version_file = path / "VERSION.json"
        if not version_file.is_file():
            result.update(status="unversioned", issues=["No VERSION.json; version is unknown"])
            return result
        actual = json.loads(version_file.read_text(encoding="utf-8-sig"))
        if not isinstance(actual, dict) or not isinstance(actual.get("sha256"), dict):
            raise ValueError("Malformed VERSION.json")
        result["version"] = actual.get("version")
        issues = result["issues"]
        if actual.get("name") != NAME or actual.get("version") != expected["version"]:
            issues.append("Manifest name or version differs from this checkout")
        # Compare only trusted paths from this checkout, never paths from the installed manifest.
        if actual["sha256"] != expected["sha256"]:
            issues.append("Manifest hashes differ from this checkout")
        for relative, digest in expected["sha256"].items():
            target = path / relative
            if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                issues.append(f"Missing or different: {relative}")
        result["status"] = "different" if issues else "current"
    except (OSError, ValueError, UnicodeError) as exc:
        result.update(status="invalid", issues=[str(exc)])
    return result


def audit(home: Path, project: Path | None, expected: dict,
          env: Mapping[str, str] | None = None) -> dict:
    scopes = {"user": home}
    if project is not None:
        scopes["project"] = project
    locations = {
        scope: {name: inspect(root / relative, expected) for name, relative in LOCATIONS.items()}
        for scope, root in scopes.items()
    }
    settings = os.environ if env is None else env
    if settings.get("CLAUDE_CONFIG_DIR"):
        custom = Path(settings["CLAUDE_CONFIG_DIR"]).expanduser().absolute() / "skills" / NAME
        locations["user"]["claude"] = inspect(custom, expected)
    if settings.get("GEMINI_CLI_HOME"):
        custom_home = Path(settings["GEMINI_CLI_HOME"]).expanduser().absolute()
        locations["user"]["gemini"] = inspect(custom_home / LOCATIONS["gemini"], expected)
        locations["user"]["gemini_shared_override"] = inspect(custom_home / LOCATIONS["shared"], expected)
    warnings = []
    for scope, entries in locations.items():
        alias = entries.get("gemini_shared_override", entries["shared"])
        if alias["status"] != "missing" and entries["gemini"]["status"] != "missing":
            warnings.append(
                f"{scope}: Gemini can prefer .agents/skills over .gemini/skills at the same scope; "
                "verify the active skill in Gemini."
            )
    if project is not None:
        for name, tool in (("shared", "Codex"), ("claude", "Claude"), ("gemini", "Gemini")):
            if all(locations[scope][name]["status"] != "missing" for scope in ("user", "project")):
                warnings.append(f"{tool}: same-name user and project installations both exist; verify selection.")
    warnings.append("File inspection does not establish CLI discovery, activation or model output.")
    return {"checkout_version": expected["version"], "locations": locations, "warnings": warnings}


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, help="Also inspect a project's skill locations")
    parser.add_argument("--json", action="store_true", help="Print machine-readable output")
    args = parser.parse_args()
    try:
        expected = json.loads((ROOT / "VERSION.json").read_text(encoding="utf-8"))
        report = audit(Path.home(), args.project.expanduser().resolve() if args.project else None, expected)
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"Could not inspect installations: {exc}\n")
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Compared with checkout version {report['checkout_version']}")
        for scope, entries in report["locations"].items():
            for name, entry in entries.items():
                print(f"{scope}/{name}: {entry['status']} (version: {entry['version'] or 'unknown'}) {entry['path']}")
                for issue in entry["issues"]:
                    print(f"  - {issue}")
        for warning in report["warnings"]:
            print(f"Note: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
