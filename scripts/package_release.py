#!/usr/bin/env python3
"""Package only the committed im-poet main source, complete bundle and app folder."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
import tempfile

from install import ROOT, package_files


def git(source: Path, *arguments: str) -> bytes:
    return subprocess.check_output(['git', '-C', str(source), *arguments])


def build(source: Path, output: Path) -> Path:
    source = source.expanduser().resolve()
    if git(source, 'status', '--porcelain').strip():
        raise ValueError('Commit source changes before packaging')
    commit = git(source, 'rev-parse', 'HEAD').decode('ascii').strip()
    if commit != git(source, 'rev-parse', 'refs/heads/main').decode('ascii').strip():
        raise ValueError('The checkout must match the committed main branch')
    version = json.loads((source / 'VERSION.json').read_text(encoding='utf-8'))['version']
    with tempfile.TemporaryDirectory(prefix='impoet-release-') as temp:
        package = Path(temp) / 'im-poet-update'
        checkout = package / 'im-poet'
        checkout.mkdir(parents=True)
        archive_bytes = git(source, 'archive', '--format=tar', 'main')
        with tarfile.open(fileobj=io.BytesIO(archive_bytes)) as archive:
            for member in archive.getmembers():
                relative = PurePosixPath(member.name)
                if relative.is_absolute() or '..' in relative.parts or '\\' in member.name:
                    raise ValueError('Unsafe path in committed source')
                target = checkout.joinpath(*relative.parts)
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                elif member.isfile():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    stream = archive.extractfile(member)
                    if stream is None:
                        raise ValueError('Unreadable source archive member')
                    with stream:
                        target.write_bytes(stream.read())
                else:
                    raise ValueError('Special source archive entries are not supported')
        subprocess.run(['git', '-C', str(source), 'bundle', 'create',
                        str(package / 'im-poet.bundle'), 'main'], check=True)
        app = package / 'gemini-app/im-poet'
        for relative, data in package_files(checkout).items():
            target = app / ('LICENSE.txt' if relative == 'LICENSE' else relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        usage = (checkout / 'docs/package-usage.md').read_text(encoding='utf-8')
        for name in ('compatibility.md', 'evaluation.md'):
            usage = usage.replace(f']({name})', f'](im-poet/docs/{name})')
        (package / 'UPLOAD.md').write_text(usage, encoding='utf-8', newline='\n')
        (package / 'VERSION.json').write_text(json.dumps(dict(
            package='im-poet-update', skill_version=version, source_commit=commit,
            repository='https://github.com/jhchoi0309/im-poet',
            contents='im-poet only; source, complete main bundle, and Gemini app folder',
        ), ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
        paths = sorted(p for p in package.rglob('*') if p.is_file())
        (package / 'SHA256SUMS').write_text(''.join(
            hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + p.relative_to(package).as_posix() + '\n'
            for p in paths), encoding='utf-8', newline='\n')
        output = output.expanduser().absolute()
        output.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(output, 'w:gz') as archive:
            archive.add(package, arcname=package.name)
    return output


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='backslashreplace')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        print(build(args.source, args.output))
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f'Packaging stopped: {exc}\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
