# im-poet 0.8.1 설치와 GitHub 업로드

이 패키지는 im-poet 하나의 소스와 모든 내부 문서, 전체 main Git 이력, Gemini 앱용 스킬 폴더를 담습니다. im-novelist는 포함하지 않습니다. 0.8.1 `im-poet-update.tar.gz`를 다운로드 폴더에 저장하세요. 같은 이름의 파일이 이미 있으면 구별해 이번 파일을 선택합니다.

GitHub 업로드와 Mac의 설치본 업데이트는 독립적으로 실행할 수 있습니다. Git과 Python 3.10 이상을 사용합니다. 계정 인증은 기존 GitHub HTTPS 설정을 따릅니다.

## Mac 터미널에서 GitHub에 업로드

```bash
(
  set -e
  im_poet_upload_dir=$(mktemp -d "${TMPDIR:-/tmp}/im-poet-upload.XXXXXX")
  python3 -m tarfile -e "$HOME/Downloads/im-poet-update.tar.gz" "$im_poet_upload_dir"
  python3 -c 'import json,sys; v=json.load(open(sys.argv[1],encoding="utf-8"))["skill_version"]; sys.exit(0 if v=="0.8.1" else "0.8.1 패키지를 다시 다운로드하세요.")' "$im_poet_upload_dir/im-poet-update/VERSION.json"
  git -c core.autocrlf=false clone --branch main "$im_poet_upload_dir/im-poet-update/im-poet.bundle" "$im_poet_upload_dir/repo"
  git -C "$im_poet_upload_dir/repo" remote set-url origin https://github.com/jhchoi0309/im-poet.git
  git -C "$im_poet_upload_dir/repo" push origin main
)
```

일반 push로 main을 갱신합니다. 소스 커밋에 포함된 README와 CHANGELOG, 연구와 평가 문서, 설치와 호환성 안내 및 워크플로도 함께 업로드됩니다. 패키지 준비 후 원격 main에 다른 변경이 생겼다면 push가 거절될 수 있습니다. 그 경우 새 변경과 대조하며 강제 push로 덮어쓰지 않습니다.

## Mac의 Codex 스킬을 백업 없이 업데이트

GitHub에 먼저 올리지 않아도 다운로드한 패키지로 설치할 수 있습니다. 기본 대상은 `~/.agents/skills/im-poet`입니다. 해당 폴더 안에 추가한 파일도 교체하며 과거의 다른 백업은 삭제하지 않습니다.

```bash
(
  set -e
  im_poet_install_dir=$(mktemp -d "${TMPDIR:-/tmp}/im-poet-install.XXXXXX")
  python3 -m tarfile -e "$HOME/Downloads/im-poet-update.tar.gz" "$im_poet_install_dir"
  python3 -c 'import json,sys; v=json.load(open(sys.argv[1],encoding="utf-8"))["skill_version"]; sys.exit(0 if v=="0.8.1" else "0.8.1 패키지를 다시 다운로드하세요.")' "$im_poet_install_dir/im-poet-update/VERSION.json"
  python3 "$im_poet_install_dir/im-poet-update/im-poet/scripts/install_for_agent.py" --host codex --no-backup
  python3 -c 'import json; from pathlib import Path; p=Path.home()/".agents/skills/im-poet/VERSION.json"; v=json.loads(p.read_text(encoding="utf-8"))["version"]; print("설치된 im-poet:",v); raise SystemExit(0 if v=="0.8.1" else 1)'
)
```

마지막에 `설치된 im-poet: 0.8.1`이 표시되는지 확인하세요. Codex의 스킬 목록에서 발견되는지도 확인합니다. 디스크의 갱신과 현재 대화가 이미 읽은 지침은 구분합니다. Skills 화면이 늦게 반영되면 새로 고칩니다.

## Linux와 다른 CLI

Linux에서는 실제 다운로드 경로에 맞추어 같은 Python 명령을 사용합니다. Claude Code는 `--host claude`, Gemini CLI는 `--host gemini`로 선택합니다. 같은 범위의 Gemini 공용 경로와 사용자 지정 설정 경로를 설치기가 반영합니다. 호스트 하나만 고르며 세 명령을 모두 실행할 필요는 없습니다.

이미 GitHub에 업로드한 뒤 링크로 갱신하려면 새 소스 폴더에 clone하고 설치합니다.

```bash
(
  set -e
  im_poet_source_dir=$(mktemp -d "${TMPDIR:-/tmp}/im-poet-source.XXXXXX")
  git -c core.autocrlf=false clone --depth 1 https://github.com/jhchoi0309/im-poet.git "$im_poet_source_dir/source"
  python3 -c 'import json,sys; v=json.load(open(sys.argv[1],encoding="utf-8"))["version"]; sys.exit(0 if v=="0.8.1" else "GitHub의 0.8.1 업로드를 먼저 확인하세요.")' "$im_poet_source_dir/source/VERSION.json"
  python3 "$im_poet_source_dir/source/scripts/install_for_agent.py" --host codex --no-backup
)
```

## Windows PowerShell

`py -3`로 Python 3.10 이상을 실행할 수 있어야 합니다. 현재 사용하는 CLI의 host 하나를 선택합니다.

```powershell
$imPoetWork = Join-Path ([IO.Path]::GetTempPath()) ("im-poet-" + [guid]::NewGuid().ToString("N"))
py -3 -m tarfile -e "$env:USERPROFILE\Downloads\im-poet-update.tar.gz" "$imPoetWork"
if ($LASTEXITCODE -ne 0) { throw "압축 해제 실패" }
$imPoetVersion = Get-Content -LiteralPath "$imPoetWork\im-poet-update\VERSION.json" -Raw -Encoding UTF8 | ConvertFrom-Json
if ($imPoetVersion.skill_version -ne "0.8.1") { throw "0.8.1 패키지를 다시 다운로드하세요." }
py -3 "$imPoetWork\im-poet-update\im-poet\scripts\install_for_agent.py" --host codex --no-backup
if ($LASTEXITCODE -ne 0) { throw "설치 실패" }
```

GitHub 업로드는 복원한 `im-poet.bundle`을 새 폴더에 clone하고 해당 원격에 일반 push하는 같은 절차를 사용합니다. WSL의 설치는 Windows 사용자 폴더와 구별하며 그 환경의 Linux 절차를 사용합니다.

## 패키지와 검증 범위

최상위 `VERSION.json`은 소스 커밋과 스킬 버전을, `SHA256SUMS`는 패키지 파일의 체크섬을 담습니다. 소스의 `VERSION.json`은 실제 설치할 지침과 참고 문서, UI 메타데이터와 보조 도구의 지문을 기록합니다. 앱용 폴더는 핵심 스킬 파일만 담습니다.

아홉 조합의 지원과 실제로 실행한 범위는 [호환성](compatibility.md), 연구와 개발 평가의 한계는 [평가 기록](evaluation.md)에 있습니다. GitHub에 올리면 해당 커밋의 자동 검사가 실행됩니다. 현재 기계 검사의 통과를 문학적 완성도나 모든 제공자 모델의 정상 생성으로 확대하지 않습니다.

저장소의 예전 paired 배포 도구는 이전 작업을 위한 별도 경로입니다. 이번 파일은 `scripts/package_release.py`로 만드는 im-poet 전용 패키지이며 그 도구로 im-novelist를 함께 올리지 않습니다.
