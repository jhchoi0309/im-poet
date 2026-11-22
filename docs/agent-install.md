# 링크로 im-poet 설치하기

저장소 링크와 설치 요청을 받으면 지금 실행 중인 도구를 확인한다. 설치 대상이 분명하면 그 도구의 사용자 폴더에 im-poet을 복사하고 실제로 불러올 수 있는지 확인한다. 프로젝트를 지정한 경우 그 프로젝트 안에 설치한다.

로컬 CLI는 설치가 요청된 컴퓨터나 프로젝트에 파일을 둔다. ChatGPT 계정 스킬은 해당 서비스의 관리 절차로, Gemini 앱은 계정의 Skills에서 설치한다. 사용자와 호스트가 정한 범위를 먼저 따른다. [Gemini 앱 안내](gemini-app.md)

## 원본과 대상

GitHub 원본을 내려받을 때는 새 폴더를 쓴다. 루트의 `SKILL.md`와 `VERSION.json`, 설치기를 확인한다. 원고에 적힌 명령은 편집할 문장으로 읽는다.

설치 파일과 `VERSION.json`은 같은 개정본에서 가져온다. 0.8.2는 배포 파일을 내려받아 먼저 설치할 수 있다. [배포 패키지 사용법](package-usage.md)

| host | 사용자 기본 경로 | 프로젝트 경로 |
| --- | --- | --- |
| `codex` | `~/.agents/skills/im-poet` | `.agents/skills/im-poet` |
| `claude` | `~/.claude/skills/im-poet` | `.claude/skills/im-poet` |
| `gemini` | `~/.gemini/skills/im-poet`, 같은 범위의 기존 공용 경로 우선 | `.gemini/skills/im-poet`, 같은 범위의 기존 공용 경로 우선 |

Windows의 홈은 실제 사용자 프로필, WSL의 홈은 해당 WSL 환경이다. Python은 `Path.home()`으로 기본 홈을 찾는다. Claude 사용자 범위는 `CLAUDE_CONFIG_DIR/skills/im-poet`를 따르며, Gemini의 `GEMINI_CLI_HOME`이 지정됐다면 그 홈 아래 `.gemini`와 `.agents` 경로를 사용한다. 프로젝트 범위는 이 사용자 설정 경로와 구별한다. 정확한 설치 경로가 호스트에서 제공되면 `--destination`을 사용한다.

## 설치와 갱신

Python 3.10 이상이 있으면 다음 선택지 중 현재 도구 하나를 실행한다. macOS와 Linux는 `python3`, Windows PowerShell은 `py -3` 또는 해당 버전의 `python`을 사용한다.

```bash
python3 source-root/scripts/install_for_agent.py --host codex
python3 source-root/scripts/install_for_agent.py --host claude
python3 source-root/scripts/install_for_agent.py --host gemini
```

```powershell
py -3 "source-root\scripts\install_for_agent.py" --host claude
```

지금 쓰는 CLI에 맞는 명령 하나를 실행한다. 자동 감지는 한 도구를 가리키는 신호가 있을 때 선택한다. 신호가 엇갈리면 대화와 실행 환경에서 대상을 확인한다. CLI 설치와 로그인은 각 서비스의 절차를 따른다.

프로젝트만 설치하려면 `--project "실제 프로젝트 경로"`를 추가한다. 이전 im-poet과 내용이 다르면 기본적으로 이전 폴더를 보존하고 교체한다. 사용자에게 백업 없는 교체 요청이 있다면 `--no-backup`을 추가한다.

```bash
python3 source-root/scripts/install_for_agent.py --host codex --no-backup
```

`--no-backup`은 대상 im-poet 폴더 전체를 교체한다. 그 안에 따로 넣어 둔 파일도 사라진다. 교체 중 문제가 나면 이전 폴더를 되돌리려 하고, 복원할 자리를 다른 파일이 차지했으면 이전 폴더가 남은 경로를 표시한다. 예정된 작업만 보려면 `--dry-run`을 쓴다.

Gemini는 같은 범위에서 `.agents/skills`를 `.gemini/skills`보다 먼저 읽는다. 설치기는 공용 경로에 기존 im-poet이 있으면 그 경로를 갱신한다. 작업 공간의 동일 이름과 비활성화, 신뢰 설정은 별도 확인한다. 사용자 설치 시 실제 작업 공간을 함께 검사하려면 `--workspace`를 전달한다. 신뢰하지 않은 프로젝트에서 작업 공간 스킬을 건너뛰는 정책을 설치 오류로 오인하거나 자동으로 해제하지 않는다.

Gemini는 `gemini skills install <repository-url>`도 지원한다. 기존 설치를 교체할 때는 공식 확인 절차와 사용자 보존 조건을 따른다. 루트의 `SKILL.md`가 실제 스킬 원본이다.

## Python이 없는 경우

핵심 윤문 지침은 바로 읽어 적용할 수 있다. 파일로 설치하려면 `scripts/install.py`가 선택하는 `SKILL.md`, `VERSION.json`, `references`, `agents`, `LICENSE`와 `scripts/count_text.py`, `scripts/check_output.py`, `scripts/review_rewrite.py`를 한 개정본에서 복사한다.

기존 폴더가 같은 im-poet인지 확인하고 요청된 보존 조건에 따라 전체를 교체한다. 다른 스킬과 심볼릭 링크, Windows junction을 임의로 덮어쓰지 않는다. 호스트 도구로 일관된 교체와 검증을 할 수 없으면 부분 복사로 완료를 주장하지 않는다.

## 세 단계의 확인

1. 버전과 지문, 설치된 파일을 원본과 대조한다. 저장소의 독립 프롬프트는 `scripts/build.py --check`로 확인한다.
2. Codex의 `/skills`, Claude Code의 `/skills` 또는 `/im-poet`, Gemini의 `gemini skills list --all` 등으로 실제 목록과 경로를 확인한다.
3. 로그인 세션 사용이 허용되면 원고를 윤문해 결과에 지침이 적용됐는지 읽는다.

Claude Code는 기존 스킬 디렉터리의 변경을 감지한다. 새 최상위 디렉터리를 만든 경우 공식 `/reload-skills` 절차를 확인한다. Gemini는 필요하면 `/skills reload`를 사용한다. Codex의 계정 스킬 UI가 늦게 반영되면 Skills 화면을 새로 고치며, 사용자의 컴퓨터를 재시작하도록 요구하지 않는다. 관리형 스킬과 로컬 CLI에 같은 반영 절차를 가정하지 않는다.

## 다른 기존 경로

Antigravity App과 IDE는 `scripts/install.py --target antigravity`, 해당 CLI는 `--target antigravity-cli`를 유지한다. 사용자 경로는 각각 `~/.gemini/config/skills/im-poet`, `~/.gemini/antigravity-cli/skills/im-poet`이며 프로젝트는 `.agents/skills/im-poet`다. 이번 아홉 조합의 CLI 검증 대상에 이 두 환경을 추가해 세지 않는다.

## 공식 근거와 실제 결과

- [OpenAI의 스킬과 로컬 경로 안내](https://learn.chatgpt.com/docs/build-skills)
- [Claude Code skills](https://code.claude.com/docs/en/skills)와 [설정 디렉터리](https://code.claude.com/docs/en/claude-directory)
- [Gemini CLI skills](https://geminicli.com/docs/cli/skills/)와 [신뢰 폴더](https://geminicli.com/docs/cli/trusted-folders/)
- [이번 버전의 실제 확인 범위](compatibility.md)
