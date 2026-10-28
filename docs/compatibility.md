# 호환성과 사용 방법

im-poet을 사용하는 자리는 컴퓨터의 설치 폴더일 수도, 계정에 저장한 스킬이나 한 번의 대화일 수도 있습니다. 이 안내는 그 자리를 구분하고 각각의 사용법을 찾도록 돕습니다. 기존 im-poetry의 호환성 안내를 이어받아 같은 경로의 임시 환경에서 설치기를 점검했으며, 공식 문서는 2026-10-28에 확인했습니다. 서비스별 모델 출력은 모두 실행하지 않았습니다. 경로와 기능, 문체 지시를 따르는 정도는 계정과 환경에 따라 달라질 수 있으니 아래 공식 문서도 함께 확인하세요.

## 운영체제별 실행

| 항목 | Windows | macOS, Linux |
| --- | --- | --- |
| Python 실행 | `py -3` 또는 Python 3.10 이상의 `python` | `python3` |
| 개별 설치 | `py -3 scripts/install.py --target codex` | `python3 scripts/install.py --target codex` |
| 홈 경로 | `Path.home()`으로 실제 사용자 프로필 확인 | `Path.home()`으로 실제 홈 확인 |
| 셸 실행 도구 | 선택적 `.ps1` 또는 Python 직접 실행 | `.sh` 또는 Python 직접 실행 |

설치기는 각 홈의 `.claude/skills`, `.gemini/skills`, `.agents/skills` 아래에 스킬 이름으로 폴더를 만듭니다. `--project`를 지정하면 그 프로젝트 아래의 같은 상대 경로를 쓰고, 별도 위치를 사용하는 도구에는 `--destination`으로 정확한 경로를 전달합니다. Windows 네이티브와 WSL은 각각의 홈을 기준으로 설치합니다. 두 환경에서는 따로 실행하세요.

패키지 공통 설치, 업로드, 압축 해제와 이전 스킬 제거는 [공통 패키지 안내](package-usage.md)를 참고하세요. 핵심 동작은 Python 표준 라이브러리로 구현했고 GitHub 업로드에만 Git, GitHub CLI가 필요합니다. 각 모델 도구 자체의 Windows 실행 환경은 제공자의 요구 사항을 따릅니다.

## Antigravity와 Gemini 앱

Antigravity App, IDE는 `--target antigravity`, Antigravity CLI는 `--target antigravity-cli`를 사용합니다. App, IDE 사용자 경로는 `~/.gemini/config/skills`, CLI 사용자 경로는 `~/.gemini/antigravity-cli/skills`이며 프로젝트 범위는 모두 `.agents/skills`입니다. [공식 문서](https://antigravity.google/docs/skills)를 2026-10-28 확인했습니다.

Gemini 앱에서 사용할 지침은 Skills 생성, 가져오기 기능으로 계정에 저장합니다. 배포 패키지의 `gemini-app/<skill-name>/` 폴더나 `prompts/gemini-app.txt`를 사용하고, 링크로 생성하는 절차와 기능의 제공 범위는 [앱용 안내](gemini-app.md)에서 확인하세요. 로컬 CLI 폴더를 복사하는 일은 Gemini CLI의 설치입니다. 앱의 저장 결과와 각각 확인해야 합니다.

GitHub URL만 주고 설치를 요청한 에이전트는 [설치 담당 에이전트 안내](agent-install.md)를 읽고 현재 도구를 선택하도록 구성했습니다. Codex, Claude Code, Gemini CLI와 Antigravity용 경로를 구분하며, 호스트가 제공하지 않는 파일 접근이나 앱 계정 쓰기 기능을 있다고 가정하지 않습니다.

## 공통 파일

- `SKILL.md`: Agent Skills 형식. `name`, `description`만 frontmatter에 사용합니다. 핵심 규칙은 이 파일만으로 적용할 수 있습니다.
- `references/`: 파일을 읽을 수 있는 환경에서 선택적으로 참고합니다.
- `agents/openai.yaml`: OpenAI 계열 도구의 선택적 표시용 메타데이터입니다. 다른 도구는 이 파일을 사용할 필요가 없습니다.
- `prompts/im-poet.md`: `SKILL.md` 본문에서 생성합니다. frontmatter와 로컬 참조 부분을 제외한 독립 지침으로, 상대 경로의 파일을 읽을 필요가 없습니다. 프로젝트 자체의 길이 예산은 8,000자 이내입니다. 이것은 모든 서비스의 입력 한도가 같다는 뜻이 아닙니다.

## Claude

### Claude Code

`python3 scripts/install.py --target claude`를 실행하면 사용자 스킬 경로에 필요한 파일만 복사합니다. `/im-poet` 뒤에 원고와 요청을 전달하세요. 프로젝트 설치에는 `--project`를 사용합니다.

공식 문서는 사용자 경로 `~/.claude/skills/`, 프로젝트 경로 `.claude/skills/`, `SKILL.md` 형식과 명시적 스킬 호출을 설명합니다.

출처: [Claude Code — Extend Claude with skills](https://code.claude.com/docs/en/skills).

### Claude 대화창과 프로젝트

일반 대화창에서는 독립 프롬프트 전문을 먼저 보내고, 다음 메시지로 원고를 건네세요. 프로젝트 지침을 사용한다면 그 지침 영역에 프롬프트를 넣어 해당 프로젝트의 대화에 적용할 수 있습니다. 프로젝트 지식에 파일을 추가했는지와 지침을 지정했는지는 각각 확인하세요.

출처: [Claude — Create and manage projects](https://support.claude.com/en/articles/9519177-how-can-i-create-and-manage-projects).

## Gemini

### Gemini CLI

`python3 scripts/install.py --target gemini`를 실행하고 `im-poet를 사용해 아래 글을 다듬어줘`라고 요청하세요. 목록에 보이지 않으면 `/skills list`로 확인하고 `/skills reload`로 다시 읽을 수 있습니다.

공식 문서는 `~/.gemini/skills/`, `.gemini/skills/`, 공용 별칭 `.agents/skills/`를 설명합니다. 같은 단계에 동일한 이름이 있으면 `.agents/skills/` 별칭이 우선됩니다. 따라서 Gemini와 Codex 설치본을 따로 유지한다면 버전 차이를 확인하세요.

출처: [Gemini CLI — Agent Skills](https://geminicli.com/docs/cli/skills/).

### Gemini 대화창과 Gems

독립 프롬프트를 첫 메시지로 보내거나 Gem의 지침에 넣으세요. 원고는 후속 메시지로 전달합니다. 파일을 추가할 수 있어도 프롬프트의 규칙을 지침 영역에서 전달하는 편이 명확합니다.

출처: [Gemini Apps — Tips for creating custom Gems](https://support.google.com/gemini/answer/15235603?hl=en).

## GPT, ChatGPT, Codex

### Codex

`python3 scripts/install.py --target codex`를 실행하고 `$im-poet`를 명시해 요청하세요. 사용자 설치 위치는 `~/.agents/skills/`, 프로젝트 설치 위치는 `.agents/skills/`입니다. 이 설치기는 ChatGPT의 클라우드 계정 설정을 변경하지 않습니다.

출처: [OpenAI — Build skills](https://learn.chatgpt.com/docs/build-skills).

### 일반 ChatGPT 대화창

첫 메시지로 독립 프롬프트 전체를 보내고 다음 메시지로 원고와 요청을 전달하면, 해당 대화에 편집 지침을 건넬 수 있습니다. 이 과정에서 스킬을 설치하거나 모델을 학습시키는 것은 아닙니다. 계정의 스킬 설치 기능을 사용하는 환경이라면 그 환경의 절차를 따르세요.

### GPT API를 사용하는 앱

앱 개발자는 독립 프롬프트를 서비스가 지원하는 지침 메시지에, 원고를 별도의 사용자 입력에 전달할 수 있습니다. 이 저장소는 API 실행기, 모델 선택, 키 관리, 과금 기능을 제공하지 않습니다. 별도의 API 호출 검증도 수행하지 않았습니다.

출처: [OpenAI — Prompt engineering](https://developers.openai.com/api/docs/guides/prompt-engineering).

## 형식 호환성과 실제 실행

위의 경로와 지침 방식은 공식 문서를 확인해 정리했습니다. 설치기와 공통 파일의 동작을 살핀 기록, 각 모델이 실제로 글을 다듬은 기록은 구별해 두었습니다. 모델별로 확인한 결과는 [평가 기록](evaluation.md)에서 볼 수 있습니다.

공통 형식 출처: [Agent Skills specification](https://agentskills.io/specification).
