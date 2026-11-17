#!/usr/bin/env python3
"""Exercise one host's installation and helpers without a model request.

Run on each native OS for OS coverage. Native discovery is an optional check.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile

from build import ROOT
from install import existing_files, package_files
from install_for_agent import run as install_for_agent


def command(host: str, *arguments: str) -> list[str]:
    if host not in ('codex', 'claude', 'gemini'):
        raise ValueError('Unknown CLI host')
    if not shutil.which(host):
        raise ValueError(f'CLI not found: {host}')
    if os.name == 'nt':
        if any(not re.fullmatch(r'[A-Za-z0-9_-]+', x) for x in arguments):
            raise ValueError('Unsupported native Windows probe argument')
        return ['cmd.exe', '/d', '/s', '/c', ' '.join((host, *arguments))]
    return [host, *arguments]


def execute(arguments: list[str], *, cwd: Path, timeout: int = 45,
            env: dict[str, str] | None = None) -> str:
    completed = subprocess.run(arguments, cwd=cwd, capture_output=True, text=True,
                               encoding='utf-8', errors='replace', timeout=timeout, env=env)
    if completed.returncode:
        raise ValueError(f'Probe failed ({completed.returncode}): {completed.stderr or completed.stdout}')
    return completed.stdout.strip()


def verify(host: str, root: Path, *, discovery: bool = False) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix=f'impoet-{host}-', dir=root)).resolve()
    home, project = work / '사용자 home', work / '프로젝트 space'
    project.mkdir()
    _, target = install_for_agent(ROOT, host, home, project, env={})
    expected = package_files(ROOT)
    if existing_files(target) != expected:
        raise ValueError('Fresh installation differs from source')
    (target / 'SKILL.md').write_bytes(expected['SKILL.md'] + b'\nprevious release\n')
    (target / 'local-extra.txt').write_text('previous local content', encoding='utf-8')
    neighbor = target.parent / 'unrelated-skill'
    neighbor.mkdir()
    (neighbor / 'keep.txt').write_text('keep', encoding='utf-8')
    install_for_agent(ROOT, host, home, project, no_backup=True, env={})
    if existing_files(target) != expected:
        raise ValueError('No-backup upgrade did not replace the complete skill')
    if list(target.parent.glob('.im-poet-backup-*')) or list(target.parent.glob('.im-poet-previous-*')):
        raise ValueError('An upgrade backup or temporary previous folder remains')
    if (neighbor / 'keep.txt').read_text(encoding='utf-8') != 'keep':
        raise ValueError('Unrelated skill was modified')
    original, revised = work / '원문.txt', work / '윤문.txt'
    original.write_text('편지는 세 번 고쳐 썼다. 보내지 않았다.\n', encoding='utf-8')
    revised.write_text('세 번 고쳐 쓴 편지. 보내지는 않았다.\n', encoding='utf-8')
    execute([sys.executable, str(target / 'scripts/check_output.py'), str(revised)], cwd=work)
    execute([sys.executable, str(target / 'scripts/count_text.py'), str(revised), '--encoding', 'utf-8'], cwd=work)
    execute([sys.executable, str(target / 'scripts/review_rewrite.py'), str(original),
             '--rewrite', str(revised)], cwd=work)
    report = dict(host=host, operating_system=platform.system(), python=platform.python_version(),
                  package_version=json.loads((target / 'VERSION.json').read_text(encoding='utf-8'))['version'],
                  target=str(target), fresh_install='passed', no_backup_update='passed',
                  complete_file_comparison='passed', unicode_and_space_paths='passed',
                  installed_helpers='passed', unrelated_skill_preserved=True,
                  cli_startup='not_requested', native_discovery='not_requested',
                  model_generation='not_executed', literary_quality='not_measured')
    if discovery:
        try:
            report['cli_version'] = execute(command(host, '--version'), cwd=project)
            report['cli_startup'] = 'passed'
            if host == 'codex':
                execute([sys.executable, str(ROOT / 'scripts/probe_codex_skill.py'),
                         str(project)], cwd=project, timeout=75)
                report['native_discovery'] = 'passed'
            elif host == 'gemini':
                # Use a new user configuration to preserve the caller's trust rules.
                probe_env = os.environ.copy()
                probe_env['GEMINI_CLI_HOME'] = str(home)

                def listed(expected_path: Path, label: str) -> None:
                    text = execute(command(host, 'skills', 'list', '--all'), cwd=project, env=probe_env)
                    (work / f'gemini-{label}-discovery.txt').write_text(text, encoding='utf-8')
                    clean = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', text)
                    normalized = clean.replace('\\', '/')
                    if not re.search(r'(?m)^im-poet\s+\[Enabled\]', clean) or expected_path.as_posix() + '/SKILL.md' not in normalized:
                        raise ValueError(f'Gemini did not list the enabled {label} skill; inspect {work}')

                _, native = install_for_agent(ROOT, host, home, env={'GEMINI_CLI_HOME': str(home)})
                listed(native, 'native-user')
                _, shared = install_for_agent(ROOT, 'codex', home, env={})
                (shared / 'SKILL.md').write_bytes(expected['SKILL.md'] + b'\nprevious alias release\n')
                install_for_agent(ROOT, host, home, no_backup=True, env={'GEMINI_CLI_HOME': str(home)})
                listed(shared, 'shared-user')
                report.update(native_discovery='passed', native_discovery_scope='isolated_user',
                              native_discovery_target=str(shared), alias_precedence='passed')
            else:
                report['native_discovery'] = 'not_verified_no_authenticated_session'
                report['discovery_note'] = 'Use /skills and /im-poet in a permitted Claude Code session; no model request was made here.'
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            if report['cli_startup'] != 'passed':
                report['cli_startup'] = 'failed'
            else:
                report['native_discovery'] = 'failed'
            report['probe_error'] = str(exc)
    return report


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='backslashreplace')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', required=True, choices=('codex', 'claude', 'gemini'))
    parser.add_argument('--root', required=True, type=Path, help='Parent for a new isolated test directory')
    parser.add_argument('--discovery', action='store_true')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.host, args.root.expanduser().absolute(), discovery=args.discovery)
        encoded = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(encoded, encoding='utf-8', newline='\n')
        print(encoded, end='')
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        parser.exit(1, f'Compatibility check stopped: {exc}\n')
    return 1 if any(result[k] == 'failed' for k in ('cli_startup', 'native_discovery')) else 0


if __name__ == '__main__':
    raise SystemExit(main())
