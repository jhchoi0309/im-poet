#!/usr/bin/env python3
"""Build one portable source-and-bundle archive from two clean main checkouts."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile
import tempfile


def git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), *args])


def build(novelist: Path, poet: Path, output: Path) -> None:
    roots = {"im-novelist": novelist.expanduser().resolve(), "im-poet": poet.expanduser().resolve()}
    for name, root in roots.items():
        if git(root, "status", "--porcelain").strip():
            raise ValueError(f"Commit or set aside source changes before packaging: {name}")
        if git(root, "rev-parse", "HEAD") != git(root, "rev-parse", "refs/heads/main"):
            raise ValueError(f"Checkout must match main: {name}")
    with tempfile.TemporaryDirectory(prefix="im-writing-package-") as temporary:
        package = Path(temporary) / "im-writing-skills"
        package.mkdir()
        versions = {}
        for name, root in roots.items():
            versions[name] = git(root, "rev-parse", "main").decode("ascii").strip()
            subprocess.run(["git", "-C", str(root), "bundle", "create", str(package / (name + ".bundle")), "main"], check=True)
            source = package / name
            source.mkdir()
            with tarfile.open(fileobj=io.BytesIO(git(root, "archive", "--format=tar", "main"))) as archive:
                for member in archive.getmembers():
                    relative = PurePosixPath(member.name)
                    if relative.is_absolute() or ".." in relative.parts or "\\" in member.name:
                        raise ValueError("Unsafe source path in Git archive")
                    destination = source.joinpath(*relative.parts)
                    if member.isdir():
                        destination.mkdir(parents=True, exist_ok=True)
                    elif member.isfile():
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        with archive.extractfile(member) as stream:
                            destination.write_bytes(stream.read())
                    else:
                        raise ValueError("Linked or special source entries are not supported")
            # Gemini Apps import folders include skill content only, without developer
            # installers, Git objects, networking scripts, or compiled files.
            app = package / "gemini-app" / name
            app.mkdir(parents=True)
            app_files = ["SKILL.md", "references", "agents", "LICENSE", "scripts/count_text.py"]
            if (source / "scripts/check_output.py").is_file():
                app_files.append("scripts/check_output.py")
            if (source / "VERSION.json").is_file():
                app_files.append("VERSION.json")
            for relative in app_files:
                original, destination = source / relative, app / ("LICENSE.txt" if relative == "LICENSE" else relative)
                if original.is_dir():
                    shutil.copytree(original, destination)
                else:
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(original, destination)
        common = {
            "upload.py": "scripts/bundle_upload.py",
            "install.py": "scripts/bundle_install.py",
            "uninstall-im-poetry.py": "scripts/uninstall_legacy.py",
            "UPLOAD.md": "docs/package-usage.md",
            **{tool + extension: "scripts/launchers/" + tool + extension
               for tool in ("upload", "install") for extension in (".sh", ".ps1")},
        }
        for destination, relative in common.items():
            first = (package / "im-poet" / relative).read_bytes()
            if first != (package / "im-novelist" / relative).read_bytes():
                raise ValueError(f"Shared distribution file differs between repositories: {relative}")
            (package / destination).write_bytes(first)
        (package / "VERSIONS.json").write_text(json.dumps(versions, indent=2) + "\n", encoding="utf-8", newline="\n")
        hashes = [hashlib.sha256(path.read_bytes()).hexdigest() + "  " + path.name + "\n"
                  for path in sorted(package.iterdir()) if path.is_file()]
        (package / "SHA256SUMS").write_text("".join(hashes), encoding="utf-8", newline="\n")
        output = output.expanduser().absolute()
        output.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(output, "w:gz") as archive:
            archive.add(package, arcname=package.name)
        print(output)


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--novelist", type=Path, required=True)
    parser.add_argument("--poet", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        build(args.novelist, args.poet, args.output)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Packaging stopped: {error}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
