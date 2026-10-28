# im-novelist · im-poet 공통 배포 패키지

패키지를 풀면 두 스킬의 소스와 이력, 설치와 업로드에 쓸 도구가 함께 나옵니다. Windows·macOS·Linux에서는 Python 3.10 이상으로 같은 핵심 도구를 실행합니다. 설치와 업로드를 Python 표준 라이브러리로 구현했으므로 운영체제마다 별도의 셸 명령이나 체크섬 프로그램을 준비할 필요는 없습니다.

## 들어 있는 파일

| 파일 | 용도 |
| --- | --- |
| `im-novelist/`, `im-poet/` | Git 없이 설치할 수 있는 전체 소스 |
| `gemini-app/im-novelist/`, `gemini-app/im-poet/` | Gemini 앱에서 가져오는 스킬 전용 폴더 |
| `im-novelist.bundle`, `im-poet.bundle` | GitHub에 올릴 각 저장소의 전체 main 이력 |
| `install.py` | 두 스킬의 로컬 설치·업데이트·미리보기 |
| `upload.py` | 번들 확인·복원·GitHub 업로드, 선택적인 설치 |
| `install.ps1`, `upload.ps1` | 선택적으로 사용하는 PowerShell 실행 도구 |
| `install.sh`, `upload.sh` | macOS·Linux 셸 실행 도구. 이전 `bash upload.sh` 명령도 사용 가능 |
| `uninstall-im-poetry.py` | 이전 로컬 스킬을 백업하면서 제거·복구 |
| `VERSIONS.json`, `SHA256SUMS` | 소스 커밋과 최상위 배포 파일의 체크섬 |

설치할 때에는 Python을 준비하고, GitHub에 업로드할 때에는 Git과 GitHub CLI(`gh`)도 준비합니다. 실제로 글을 다듬으려면 Agent Skills를 읽는 도구와 그 도구의 모델 연결이 필요합니다. 각 도구가 요구하는 운영체제 조건은 제공자의 문서를 따릅니다.

## 사용자는 GitHub 링크로 설치 요청

Codex·Claude Code·Gemini CLI와 Antigravity에 저장소 URL을 주고 “이 스킬 설치해줘”라고 요청하면, 에이전트가 README·AGENTS.md·CLAUDE.md·GEMINI.md를 따라 현재 도구에 맞는 설치 절차를 찾도록 구성했습니다. 사용자가 경로와 명령을 외우기보다 에이전트가 확인하고 수행하는 방식입니다. 호스트의 파일 접근과 권한 정책은 그대로 따릅니다.

Gemini 앱에서는 계정의 Skills 기능에 지침을 저장합니다. 링크를 읽고 스킬을 생성할 수 있는 앱에는 같은 요청으로 진행하도록 안내했으며, 직접 가져올 때에는 Skills 업로드에서 이 패키지의 `gemini-app/<skill-name>/` 폴더를 선택하면 됩니다. 앱에 저장했는지와 CLI에 설치했는지는 따로 확인하세요. 사용 방법과 계정별 제공 범위는 각 소스의 `docs/gemini-app.md`에 적었습니다.

## Windows: PowerShell에서 실행

압축 파일을 다운로드 폴더에 저장했다면 다음처럼 풉니다. Python의 압축 해제를 사용하므로 Git Bash나 WSL이 필요하지 않습니다.

```powershell
Set-Location "$env:USERPROFILE\Downloads"
py -3 -m tarfile -e im-writing-skills.tar.gz .
```

두 스킬을 지원 도구의 로컬 경로에 설치하거나 업데이트합니다.

```powershell
py -3 .\im-writing-skills\install.py --target all --update
```

`py`가 없는 설치 방식이라면 Python 3.10 이상을 실행하는 `python` 명령으로 `py -3` 부분을 바꾸세요. 명령을 찾지 못하면 [Python 공식 설치 안내](https://www.python.org/downloads/)를 확인하세요.

GitHub 업로드는 별도로 실행합니다.

```powershell
gh auth login --hostname github.com --git-protocol https --web --scopes workflow
py -3 .\im-writing-skills\upload.py --public
```

PowerShell 실행 도구를 사용하려면 `./im-writing-skills/upload.ps1 --public`처럼 실행할 수도 있습니다. 실행 정책으로 `.ps1` 파일이 차단되면 위의 Python 명령을 사용하세요. 실행 정책을 낮추는 절차는 필요하지 않습니다.

## macOS · Linux: 터미널에서 실행

압축 파일을 저장한 폴더에서 실행합니다. 다음 예시는 다운로드 폴더입니다. Linux에서 다운로드 폴더 이름을 바꿨다면 실제 경로를 사용하세요.

```bash
cd ~/Downloads
python3 -m tarfile -e im-writing-skills.tar.gz .
python3 im-writing-skills/install.py --target all --update
```

GitHub 업로드:

```bash
gh auth login --hostname github.com --git-protocol https --web --scopes workflow
python3 im-writing-skills/upload.py --public
```

기존 명령 `bash im-writing-skills/upload.sh --public`도 Python 업로더로 연결됩니다.

## 필요한 도구·프로젝트만 선택

`--target all`은 Claude Code·Gemini CLI·Codex·Antigravity App/IDE·Antigravity CLI의 사용자 스킬 경로에 각각 설치합니다. 한 도구만 원하면 `--target codex`, `--target claude`, `--target gemini`, `--target antigravity`, `--target antigravity-cli` 중 선택하세요. Gemini 일반 앱은 이 명령으로 계정 스킬을 생성하지 않으며 앱용 가져오기 폴더를 사용합니다. 특정 도구만 원하면 다음처럼 선택하세요. Windows에서는 `python3` 대신 `py -3`를 사용합니다.

```bash
python3 im-writing-skills/install.py --target codex --update
python3 im-writing-skills/install.py --target claude --target gemini --update
python3 im-writing-skills/install.py --target all --project "/path/with spaces/project" --update
python3 im-writing-skills/install.py --target all --dry-run
```

사용자 설치 경로는 각 운영체제의 실제 홈을 기준으로 계산합니다. 설치 위치를 따로 설정한 도구라면 개별 소스의 `scripts/install.py --destination "정확한 경로"`를 사용하세요. Windows에 설치한 스킬은 WSL의 홈에 자동 복사되지 않습니다. WSL에서 도구를 실행한다면 WSL 터미널에서 Linux 명령으로 설치하세요.


이 패키지는 운영체제별 CI 파일도 업로드하므로 OAuth 로그인에는 workflow 권한을 포함합니다. 기존 인증에서 workflow 파일 변경이 거절되면 `gh auth refresh --hostname github.com --scopes workflow`로 해당 권한을 추가한 뒤 다시 실행하세요. 업로드 스크립트가 인증 범위를 자동으로 확장하지는 않습니다. 관련 명령은 [GitHub 공식 문서](https://cli.github.com/manual/gh_auth_refresh)를 참고하세요.

## 공개 범위와 업로드 보호

- `--public`: 새 저장소를 공개로 생성합니다. `--private`: 새 저장소를 비공개로 생성합니다. 생략하면 업로드를 시작하지 않습니다.
- 기본 대상은 `jhchoi0309/im-novelist`와 `jhchoi0309/im-poet`입니다. 해당 계정으로 로그인해야 합니다. 다른 계정에 배포하려면 `--owner 계정명`을 지정하세요.
- 기존 저장소의 공개 범위는 바꾸지 않습니다. 기존 main이 패키지 main의 조상일 때만 일반 push를 합니다. 다른 이력이나 더 앞선 변경이 있으면 중단합니다.
- 두 저장소의 이력을 모두 확인한 뒤 업로드를 시작합니다. 강제 push·기존 저장소 삭제·이름 변경은 수행하지 않습니다.
- 인증·네트워크 오류는 '없는 저장소'로 처리하지 않습니다. 생성 또는 push가 중간에 실패하면 이미 완료한 저장소는 남고, 복원한 소스 폴더도 출력된 위치에 보관합니다. 재실행은 새 작업 폴더를 사용합니다.
- 업로드 후 원격 main의 SHA가 패키지와 일치하는지 확인합니다. 새 GitHub 저장소에는 이 패키지에 들어 있는 CI가 함께 올라갑니다.

오프라인으로 체크섬과 번들 복원을 확인하려면:

```bash
python3 im-writing-skills/upload.py --check
```

업로드와 설치를 한 번에 실행하려면 `--install`을 추가합니다. `--target`을 생략하면 지원하는 로컬 도구 경로에 모두 설치하고 같은 이름의 이전 설치본은 백업합니다.

```bash
python3 im-writing-skills/upload.py --public --install
python3 im-writing-skills/upload.py --private --install --target codex
```

## 기존 im-poetry 제거

```bash
python3 im-writing-skills/uninstall-im-poetry.py --dry-run
python3 im-writing-skills/uninstall-im-poetry.py
```

기존 로컬 `im-poetry`만 도구의 스킬 경로 밖에 있는 백업 폴더로 옮기고 복구 명령을 출력합니다. `im-novelist`와 `im-poet`은 남깁니다. 프로젝트 설치는 `--project "경로"`로 지정합니다. ChatGPT 개인 스킬과 로컬 설치본은 별개입니다.

## 검증 범위

이번 작업에서 직접 실행한 환경은 Linux의 Python 3.12입니다. 이 환경에서 설치와 업데이트, 백업과 실패 복구를 확인하고 CRLF/BOM과 한글·공백·이모지 경로, 번들 복원, 로컬 Git 업로드와 이력 충돌을 살폈습니다. GitHub API에는 모의 응답을 사용했습니다. 이 업로드 도구로 실제 계정에 올리는 단계는 사용자가 실행합니다.

두 저장소의 CI는 Windows·macOS·Linux와 Python 3.10·3.13의 6개 조합으로 구성했습니다. 구성 파일을 추가한 것과 실제 CI 통과는 다릅니다. Windows·macOS의 네이티브 실행 결과는 아직 확인하지 않았습니다. Windows 전용 junction 검사와 PowerShell 실행 도구 검사는 해당 환경의 CI에서 실행됩니다. 셸 도구는 핵심 Python 구현으로 연결되며, 설치 경로에 있는 링크나 junction은 임의로 교체하지 않습니다.

## 공식 참고 문서

- [Python Windows 실행 도구](https://docs.python.org/3.10/using/windows.html)
- [Python 경로 처리](https://docs.python.org/3/library/pathlib.html)
- [GitHub CLI 설치](https://cli.github.com/)
- [GitHub CLI 저장소 생성](https://cli.github.com/manual/gh_repo_create)
- [GitHub Actions 매트릭스](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/run-job-variations)
