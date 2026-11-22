# im-poet에서 참고한 연구

텍스트 문체 변환 연구에서는 문체의 변화와 원래 뜻의 보존을 각각 어떻게 평가하는지 살폈다. 한국 문학과 문체론에서는 반복과 화자의 시선, 말끝이 글에서 하는 일을 읽었다. 0.8.0은 이 기준을 지침에 담았고, 0.8.1은 시험 에세이 여섯 편을 바탕으로 빠진 근거, 달라진 확신의 정도, 비슷해진 결말을 확인하는 절차를 보강했다. [에세이 6편의 평가](feedback-0.8.1.md)

## 대표 문헌과 지침에 반영한 부분

| 문헌 | 확인한 범위 | 윤문에 반영한 기준 | 출처 |
| --- | --- | --- | --- |
| Evaluating Style Transfer for Text (2019) | 방법과 결과 구간 | 문체가 얼마나 달라졌는지와 원래 뜻이 얼마나 남았는지 따로 읽는다. | [ACL Anthology](https://aclanthology.org/N19-1049/) |
| A Review of Human Evaluation for Style Transfer (2021) | 검토 방법과 인간 평가 관련 구간 | 원고에 어떤 제약을 두었고 누가 무엇을 평가했는지 기록한다. | [ACL Anthology](https://aclanthology.org/2021.gem-1.6/) |
| A large-scale computational study of content preservation measures for text style transfer and paraphrase generation (2022) | 방법과 결과 구간 | 유사도 수치에서 놓칠 수 있는 조건과 근거를 원문과 직접 대조한다. | [ACL Anthology](https://aclanthology.org/2022.acl-srw.23/) |
| 작가의 문체적 지문을 찾아서 (장성현, 2024) | 서지와 국문 초록 | 한국어 글에서도 어휘와 문장에 나타나는 문체 단서를 살핀다. 이 문헌은 스타일로메트리의 배경을 확인하는 데 참고했다. | [KCI](https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART003152327) |
| LiTransProQA (2025) | 평가 자료, 질문 설계, 결과와 한계 | ‘누가 이 일을 했는가’, ‘화자가 직접 본 것인가’처럼 독자가 원고를 읽어 답할 수 있는 검수 질문을 만든다. | [ACL Anthology](https://aclanthology.org/2025.emnlp-main.1482/) |
| Evaluating Creativity (2025) | 설계와 결과, 결론 | AI 평가자끼리 같은 판단을 내렸는지와 원고의 결함을 실제로 찾았는지 따로 기록한다. | [Applied Sciences](https://www.mdpi.com/2076-3417/15/6/2971) |
| Style over Story (2026) | 방법과 결과, 한계 | 표현이 매끄럽게 읽힐 때도 사건과 인물, 배경이 원문대로 남았는지 살핀다. | [ACL Anthology](https://aclanthology.org/2026.findings-acl.1361/) |
| LitBench (2026) | 자료 구축과 평가, 한계 | 긴 글에 점수가 쏠리는지와 선호 신호가 어디에서 왔는지 확인한다. | [ACL Anthology](https://aclanthology.org/2026.eacl-long.362/) |

국내 연구에서 이정인의 「정지용 수필의 문체적 특성 연구」는 초록을 확인했다. 반복과 병치, 소리를 닮은 말이 수필의 묘사를 만드는 방식에 주목했다. 이 관점은 같은 표현을 덜기 전에 문장 속에서 하는 일을 먼저 보는 기준으로 이어졌다. [논문 서지와 초록](https://www.kci.go.kr/kciportal/landing/article.kci?arti_id=ART002358261), [선행 문헌 목록](../references/research.md#논문과-읽은-범위)

문헌의 대상 언어와 과제, 편집에 참고한 범위를 함께 기록했다. 연구는 편집 지침과 검수 절차에 반영했다. 모델을 추가로 학습시키거나 자료를 외부 임베딩 서비스로 보내지 않았다. 윤문 중 문헌을 자동 검색하는 기능도 도입하지 않았다. [문헌별 적용과 한계](../references/research-0.8.0.md), [자료별 확인 범위](../references/research-evidence-0.8.0.json)

## 어디까지 읽었는가

| 자료 | 확인 범위 |
| --- | --- |
| 0.8.0 첫 조사 논문 50편 | 본문 구간 6편, 초록 31편, 색인 조각 2편, 서지 11편 |
| 후속 문헌 5편 | 본문 구간 4편, 초록 1편 |
| 중복을 제외한 작품 100편 | 판본을 확인했다. 97편에서 문장 길이 등 텍스트로 셀 수 있는 특징을 계산했고, 판본과 번역, 본문 완전성에 문제가 있는 3편은 보류했다. |
| 기능을 따로 읽은 작품 12편 | 자료원 본문 전체 8편, 선택 구간 4편에서 반복과 화자의 시선, 종결을 읽었다. |

자료별 확인 범위는 아래 목록에서 볼 수 있다. 작품의 정본 확정과 독립 전문가 평가, 논문 1,000편과 작품 2,000편의 탐색은 후속 과제로 남았다. 앞선 조사와 이번 목록은 중복을 확인한 뒤에만 합산한다. [0.8.0 근거 목록](../references/research-evidence-0.8.0.json), [이전 조사 목록](../references/research-catalog-2026-11-14.json)

## 국립국어원 자료

공식 설명서 네 종에서 문어 2025의 문학 분류 3,410종, 첨삭 2024 버전 1.1의 1,500건, 채점 2024의 2,629건, 역사 2024의 32종을 확인했다. 문어의 문학 분류에는 번역 작품도 들어간다. 이번에 읽은 것은 설명서다. 원자료는 이용 신청과 승인을 받아야 하며 배포 파일에는 담지 않았다. [국립국어원 말뭉치 이용 안내](https://kli.korean.go.kr/corpus/boards/faqList.do)
