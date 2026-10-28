# 호환성과 사용 방법

기존 im-poetry 프로젝트의 호환성 안내를 계승했습니다. 공식 문서 확인 기록: 2026-10-28. 새 im-poet에서는 같은 설치 경로를 사용하는 설치기를 임시 환경에서 점검했습니다. 개별 서비스의 모델 출력을 모두 실행한 기록은 아닙니다. 플랫폼의 경로와 기능은 바뀔 수 있으므로 아래 공식 문서를 기준으로 확인하세요. 계정별 기능 제공 여부와 문체 지시 준수 정도는 다를 수 있습니다.

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

일반 대화창에는 독립 프롬프트 전문을 먼저 붙여 넣고 다음 메시지에 원고를 보내세요. 프로젝트 지침을 사용하는 경우 프롬프트를 해당 지침에 넣을 수 있습니다. 프로젝트 지침은 해당 프로젝트 대화에 적용됩니다. 프로젝트 지식에 파일을 추가하는 동작과 지침을 지정하는 동작을 구분하세요.

출처: [Claude — Create and manage projects](https://support.claude.com/en/articles/9519177-how-can-i-create-and-manage-projects).

## Gemini

### Gemini CLI

`python3 scripts/install.py --target gemini`를 실행하고 `im-poet를 사용해 아래 글을 다듬어줘`라고 요청하세요. 목록에 보이지 않으면 `/skills list`로 확인하고 `/skills reload`로 다시 읽을 수 있습니다.

공식 문서는 `~/.gemini/skills/`, `.gemini/skills/`, 공용 별칭 `.agents/skills/`를 설명합니다. 같은 단계에 동일한 이름이 있으면 `.agents/skills/` 별칭이 우선됩니다. 따라서 Gemini와 Codex 설치본을 따로 유지한다면 버전 차이를 확인하세요.

출처: [Gemini CLI — Agent Skills](https://geminicli.com/docs/cli/skills/).

### Gemini 대화창과 Gems

독립 프롬프트를 첫 메시지로 보내거나 Gem의 지침에 넣으세요. 원고는 후속 메시지로 전달합니다. 파일을 추가할 수 있어도 프롬프트의 규칙을 지침 영역에서 전달하는 편이 명확합니다.

출처: [Gemini Apps — Tips for creating custom Gems](https://support.google.com/gemini/answer/15235603?hl=en).

## GPT · ChatGPT · Codex

### Codex

`python3 scripts/install.py --target codex`를 실행하고 `$im-poet`를 명시해 요청하세요. 사용자 설치 위치는 `~/.agents/skills/`, 프로젝트 설치 위치는 `.agents/skills/`입니다. 이 설치기는 ChatGPT의 클라우드 계정 설정을 변경하지 않습니다.

출처: [OpenAI — Build skills](https://learn.chatgpt.com/docs/build-skills).

### 일반 ChatGPT 대화창

독립 프롬프트 전체를 첫 메시지로 보내고, 원고와 요청을 다음 메시지로 전달하세요. 이 방법은 스킬 설치나 모델 학습이 아니라 해당 대화에 편집 지침을 전달하는 방법입니다. 계정의 스킬 설치 기능을 사용하는 환경에서는 그 환경의 설치 절차를 따르세요.

### GPT API를 사용하는 앱

앱 개발자는 독립 프롬프트를 서비스가 지원하는 지침 메시지에, 원고를 별도의 사용자 입력에 전달할 수 있습니다. 이 저장소는 API 실행기, 모델 선택, 키 관리, 과금 기능을 제공하지 않습니다. 별도의 API 호출 검증도 수행하지 않았습니다.

출처: [OpenAI — Prompt engineering](https://developers.openai.com/api/docs/guides/prompt-engineering).

## 형식 호환성과 실제 실행

위 경로와 지침 방식은 공식 문서를 확인해 작성했습니다. 설치기와 공통 파일의 검증은 특정 Claude·Gemini·GPT 모델을 실제로 모두 실행했다는 뜻이 아닙니다. 모델별 실제 결과는 [평가 기록](evaluation.md)을 확인하세요.

공통 형식 출처: [Agent Skills specification](https://agentskills.io/specification).
