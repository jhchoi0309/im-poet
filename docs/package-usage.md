# im-poet 0.8.2 설치와 GitHub 업로드

`im-poet-0.8.2-update.tar.gz`를 다운로드 폴더에 저장하세요. 파일 안에는 im-poet의 소스와 문서, main 브랜치의 전체 Git 이력, Gemini 앱용 스킬 폴더가 들어 있습니다.

GitHub에 올릴 때는 Git과 기존 GitHub HTTPS 인증을, Mac에서 갱신할 때는 Python 3.10 이상을 사용합니다. 다운로드한 파일로 각각 실행할 수 있습니다.

## Mac 터미널에서 GitHub에 업로드

```bash
(
  set -e
  im_poet_upload_dir=$(mktemp -d "${TMPDIR:-/tmp}/im-poet-upload.XXXXXX")
  tar -xzf "$HOME/Downloads/im-poet-0.8.2-update.tar.gz" -C "$im_poet_upload_dir"
  cd "$im_poet_upload_dir/im-poet-update"
  shasum -a 256 -c --quiet SHA256SUMS
  grep -F '"skill_version": "0.8.2"' VERSION.json
  git -c core.autocrlf=false clone --branch main ./im-poet.bundle "$im_poet_upload_dir/repo"
  cd "$im_poet_upload_dir/repo"
  git remote set-url origin https://github.com/jhchoi0309/im-poet.git
  git tag v0.8.2
  git push --atomic origin main refs/tags/v0.8.2
)
```

README부터 내부 문서까지 담긴 커밋으로 main을 갱신하고 `v0.8.2` 태그를 함께 올립니다. 두 참조는 함께 반영됩니다. 원격 main에 별도 커밋이 추가되어 일반 push가 거절되면 그 변경을 먼저 확인하세요. 성공하면 태그 링크를 공유할 수 있습니다. [im-poet 0.8.2](https://github.com/jhchoi0309/im-poet/tree/v0.8.2)

## Mac의 Codex 스킬을 백업 없이 업데이트

다운로드한 패키지로 `~/.agents/skills/im-poet`을 바로 갱신할 수 있습니다. `--no-backup`은 그 폴더를 통째로 교체하므로 안에 직접 추가한 파일도 사라집니다.

```bash
(
  set -e
  im_poet_install_dir=$(mktemp -d "${TMPDIR:-/tmp}/im-poet-install.XXXXXX")
  tar -xzf "$HOME/Downloads/im-poet-0.8.2-update.tar.gz" -C "$im_poet_install_dir"
  cd "$im_poet_install_dir/im-poet-update"
  shasum -a 256 -c --quiet SHA256SUMS
  grep -F '"skill_version": "0.8.2"' VERSION.json
  python3 im-poet/scripts/install_for_agent.py --host codex --no-backup
  python3 -c 'import json; from pathlib import Path; v=json.loads((Path.home()/".agents/skills/im-poet/VERSION.json").read_text(encoding="utf-8"))["version"]; print("설치된 im-poet:",v); raise SystemExit(0 if v=="0.8.2" else 1)'
)
```

마지막 줄이 `설치된 im-poet: 0.8.2`이면 파일 갱신을 확인한 것입니다. 새 Codex 대화의 스킬 목록에서 im-poet을 확인하세요.

## Linux와 다른 CLI

Linux에서도 다운로드 경로를 맞추어 같은 명령을 실행할 수 있습니다. `shasum`이 없으면 `sha256sum -c SHA256SUMS --quiet`를 사용하세요. Claude Code는 `--host claude`, Gemini CLI는 `--host gemini`를 지정합니다. 설치기는 Gemini의 공용 경로와 사용자가 지정한 설정 경로를 확인합니다.

GitHub에 올린 뒤에는 `v0.8.2` 태그에서 바로 설치할 수 있습니다.

```bash
(
  set -e
  im_poet_source_dir=$(mktemp -d "${TMPDIR:-/tmp}/im-poet-source.XXXXXX")
  git -c core.autocrlf=false clone --quiet --depth 1 --branch v0.8.2 https://github.com/jhchoi0309/im-poet.git "$im_poet_source_dir/source"
  python3 "$im_poet_source_dir/source/scripts/install_for_agent.py" --host codex --no-backup
)
```

## Windows PowerShell

`py -3`로 Python 3.10 이상을 실행할 수 있어야 합니다. 현재 사용하는 CLI의 host 하나를 선택합니다.

```powershell
$imPoetWork = Join-Path ([IO.Path]::GetTempPath()) ("im-poet-" + [guid]::NewGuid().ToString("N"))
py -3 -m tarfile -e "$env:USERPROFILE\Downloads\im-poet-0.8.2-update.tar.gz" "$imPoetWork"
if ($LASTEXITCODE -ne 0) { throw "압축 해제 실패" }
$imPoetVersion = Get-Content -LiteralPath "$imPoetWork\im-poet-update\VERSION.json" -Raw -Encoding UTF8 | ConvertFrom-Json
if ($imPoetVersion.skill_version -ne "0.8.2") { throw "0.8.2 패키지를 다시 다운로드하세요." }
py -3 "$imPoetWork\im-poet-update\im-poet\scripts\install_for_agent.py" --host codex --no-backup
if ($LASTEXITCODE -ne 0) { throw "설치 실패" }
```

GitHub 업로드는 복원한 `im-poet.bundle`을 새 폴더에 clone하고 해당 원격에 일반 push하는 같은 절차를 사용합니다. WSL의 설치는 Windows 사용자 폴더와 구별하며 그 환경의 Linux 절차를 사용합니다.

## 패키지와 검증 범위

최상위 `VERSION.json`에는 소스 커밋과 스킬 버전이 적혀 있습니다. `SHA256SUMS`로 받은 파일이 패키지 기록과 일치하는지 확인합니다. 소스의 `VERSION.json`은 실제로 설치하는 지침과 참고 문서, 메타데이터와 보조 도구의 지문을 담습니다. 앱용 폴더에는 앱으로 가져갈 스킬 파일이 모여 있습니다.

GitHub에 올리면 해당 커밋의 자동 검사가 시작됩니다. 실행 환경과 결과, 윤문 결과를 읽은 범위는 각 문서에 남겼습니다. [호환성](compatibility.md), [평가 기록](evaluation.md)

이 배포 파일은 im-poet 전용 `scripts/package_release.py`로 만들었습니다. 이 저장소의 기존 두 스킬용 도구는 이전 배포에 쓰였습니다.
