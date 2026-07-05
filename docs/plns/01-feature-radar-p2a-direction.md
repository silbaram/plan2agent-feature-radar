# Feature Radar 구현 방향과 P2A 연동 방향

작성일: 2026-07-04

## 1. 핵심 방향

Feature Radar는 "무엇을 만들지 계속 갱신하는 근거 시스템"으로 두고, P2A는 그 근거 중 사용자가 승인한 범위를 기획과 개발 task로 바꾸는 실행 하네스로 둔다.

```text
Feature Radar = 사전 조사, 외부 신호 수집, 기능 우선순위 갱신
P2A = 승인 게이트, 제품/구현 명세, task graph, 감독형 개발 실행
```

중요한 구현 원칙은 Feature Radar를 처음부터 P2A artifact exporter로 만들지 않는 것이다. Feature Radar는 독립적인 agent harness이며, P2A 연동은 그 결과를 소비하는 optional export target이다.

```text
Feature Radar native loop
  -> idea/research seed
  -> 필요하면 local project read-only scan
  -> skill이 조사 계획 수립
  -> subagent들이 조사/분석/검증 수행
  -> tools가 검색, 수집, 파싱, scoring, 저장을 담당
  -> Radar native artifact 생성
  -> 필요할 때만 target project로 handoff/export
  -> 필요할 때만 P2A context로 export
```

두 시스템은 경쟁 관계가 아니다. Feature Radar는 더 좋은 제품 판단 근거를 만들고, P2A는 그중 승인된 범위만 검토 가능한 spec과 실행 가능한 task로 변환한다.

## 2. 문제 정의

초기 제품 아이디어는 보통 짧고 모호하다.

예:

```text
Jira 같은 시스템을 만들고 싶다.
GitHub를 조사해서 사람들이 불편해하는 점과 필요한 기능을 정리하고,
그걸 기반으로 MVP와 고도화 방향을 만들고 싶다.
```

이때 바로 개발 task로 들어가면 다음 문제가 생긴다.

- 경쟁 제품이 이미 해결한 기본 기능을 놓칠 수 있다.
- GitHub issue, PR, discussion에 반복적으로 나타나는 실제 불편을 반영하지 못할 수 있다.
- 기능 우선순위가 개인 직관에만 의존할 수 있다.
- 한번 정한 MVP가 이후 새 근거를 반영하지 못하고 고정될 수 있다.
- P2A가 만드는 spec은 깔끔하지만, 외부 시장/커뮤니티 근거가 약할 수 있다.

Feature Radar는 이 문제를 해결하기 위해 아이디어 주변의 근거를 계속 수집하고, 기능 후보와 우선순위를 갱신한다.

## 3. 전체 제품 루프

권장 루프는 다음과 같다.

```text
아이디어 입력
  -> Feature Radar skill 실행
  -> 필요하면 로컬 프로젝트 read-only scan
  -> subagent task graph 생성
  -> 경쟁 제품, 공식 문서, GitHub repo/issue/PR/discussion 조사
  -> 현재 구현과 외부 신호 비교
  -> 기능 후보와 불편점 클러스터링
  -> 우선순위 점수화
  -> Feature Brief 생성
  -> Radar native artifact 저장
  -> 필요하면 target project `.feature-radar`로 handoff
  -> 필요하면 P2A Gate A/B 참고 자료로 export
  -> P2A가 intake, spec, task graph, review 생성
  -> MVP 개발 및 검증
  -> 실행 결과, 사용자 피드백, 신규 외부 신호를 Radar에 반영
  -> 다음 iteration 우선순위 갱신
```

즉, Radar는 한 번 쓰고 버리는 리포트가 아니라 제품 방향을 계속 갱신하는 레이더다. P2A는 그중 사용자가 승인한 범위만 개발로 전환한다.

## 4. 역할 분리

| 영역 | Feature Radar | P2A |
| --- | --- | --- |
| 주 목적 | 외부 근거 수집과 기능 우선순위 갱신 | 기획 승인과 개발 실행 |
| 입력 | 아이디어, 키워드, 경쟁 제품, repo, URL, 선택적 로컬 프로젝트 경로 | 아이디어, research bundle, 사용자 결정 |
| 출력 | research bundle, signal map, feature opportunities, priority index, feature brief, 선택적 local project scan과 next iteration recommendation | intake, spec, task graph, review, run log |
| 판단 방식 | 근거 기반 추천 | 승인 게이트 기반 결정 |
| 변경 주기 | 지속 갱신 | iteration 단위 반영 |
| 실패 시 | 조사 품질 저하 또는 근거 부족 | Gate blocker 또는 open decision |

핵심 원칙:

```text
Radar는 우선순위를 제안한다.
P2A는 승인된 범위만 개발한다.
```

## 5. 구현 아키텍처 방향

Feature Radar는 "하나의 크롤러"나 "P2A 파일 생성기"가 아니라, Codex 같은 AI 개발 환경에서 동작하는 skill, subagent, tool 조합으로 구현한다.

권장 구조:

```text
Feature Radar Skill
  -> run 계획 생성
  -> 필요한 subagent 선택
  -> tool 사용 정책과 산출물 계약 제공
  -> 결과 검증과 native artifact 저장
  -> optional exporter 실행

Subagents
  -> local project scan
  -> handoff/export packaging
  -> reference discovery
  -> GitHub/community signal scan
  -> docs/changelog analysis
  -> opportunity synthesis
  -> priority scoring
  -> evidence review
  -> brief/export packaging

Tools
  -> Codex/Claude Code가 이미 제공하는 web search, browser, fetch, read-only file inspection, file write 도구 우선 사용
  -> 반복 작업이 명확해진 뒤에만 별도 JS/Python 도구화
  -> 필요해지면 GitHub API/search, URL fetch/parser, source normalizer, artifact writer 추가
```

각 계층의 책임은 다음처럼 분리한다.

| 계층 | 책임 |
| --- | --- |
| Skill | 사용자의 아이디어를 받아 실행 전략을 세우고, subagent와 tool 사용을 조율한다. |
| Subagent | 특정 조사/분석 역할을 수행한다. 판단, 요약, 비교, 근거 해석은 subagent가 맡는다. |
| Tool | agent 환경이 제공하는 검색, 브라우징, 파일 작업을 먼저 사용한다. 반복적이고 결정론적인 부분만 나중에 별도 도구로 만든다. |
| Exporter | Radar native 결과를 P2A, Markdown, JSON 등 외부 소비 형식으로 변환한다. |
| Handoff Packager | 완료된 Radar run을 대상 프로젝트의 `.feature-radar` 또는 `.plan2agent` 디렉토리로 복사하고 manifest를 남긴다. |

언어 선택은 초기 결정사항이 아니다. 먼저 skill/subagent workflow를 검증한 뒤, 도구화가 필요한 부분만 기능 단위로 결정한다.

- TypeScript는 Codex/Claude plugin, MCP/tool adapter, JSON schema, UI/웹 콘솔과 잘 맞을 때 사용한다.
- Python은 HTML/문서 파싱, 텍스트 처리, 데이터 분석, ranking 실험에 더 유리할 때 사용한다.
- 한 언어로 고정하지 않는다. subagent와 tool 경계는 JSON artifact, CLI, MCP tool contract로 연결한다.
- 중요한 것은 언어가 아니라 "agent가 판단하고 tool이 반복 가능한 작업을 수행한다"는 경계다.

초기 구현은 다음 순서가 적절하다.

1. Feature Radar skill 정의
2. Radar native run/artifact 구조 정의
3. Claude Code project subagents 정의
4. Codex repo skill에서 subagent 분할 지시 정의
5. agent가 기존 web/search/fetch 도구로 실제 조사 수행
6. research output 형식을 반복 개선
7. 반복 작업이 확인된 뒤에만 JS/Python tool adapter 추가
8. P2A exporter를 별도 optional 단계로 추가
9. target project handoff/export를 optional 단계로 추가

기본 저장 위치도 P2A 중심이 아니라 Radar 중심으로 둔다.

```text
.feature-radar/
  runs/<project-slug>/
    run.json
    tasks/
    agent-outputs/
    artifacts/
      research-plan.md
      source-candidates.md
      research-bundle.md
      signal-map.md
      local-project-scan.md                 # optional existing project mode
      capability-gap-analysis.md            # optional existing project mode
      next-iteration-recommendations.md     # optional existing project mode
      collection-report.md
    exports/
      p2a-context.json  # optional
```

초기 authoring artifact는 Markdown을 우선 사용한다. `feature-opportunities.json`, `priority-index.json` 같은 구조화 JSON은 반복 실행으로 schema가 안정된 뒤 추가한다.

`<project-slug>`는 숫자 timestamp가 아니라 사람이 읽을 수 있는 영어 프로젝트 이름을 kebab-case로 쓴다. 예: `on-device-character-chat-app`.

`.plan2agent/artifacts/...` 아래에 바로 쓰는 것은 P2A export를 실행했을 때만 한다.

완료된 run을 실제 개발 프로젝트에 넘길 때는 handoff/export 단계를 사용한다.

```text
radar-native
  -> <target-project>/.feature-radar/runs/<project-slug>/

p2a-preflight
  -> <target-project>/.plan2agent/artifacts/<project-id>/preflight-research/

both
  -> both destinations
```

각 destination에는 `handoff-manifest.md`를 생성해 source run, target project, mode, copied files, missing optional files, overwrite policy를 기록한다.

## 6. Feature Radar가 조사할 내용

초기 MVP에서 Radar는 아래 정보를 수집한다.

- 공식 홈페이지와 문서에서 확인되는 핵심 기능
- 유사 SaaS와 오픈소스 프로젝트 목록
- GitHub repository의 README, release, issue, PR, discussion 신호
- 반복적으로 요청되는 기능
- 자주 등장하는 불편, 버그, 누락 기능
- 오래 열려 있거나 논쟁이 많은 issue
- merged PR에서 확인되는 최근 기능 방향
- 경쟁 제품 대비 빠진 영역
- MVP에 넣을 기능과 후순위로 둘 기능

기존 로컬 프로젝트를 입력받은 경우에는 아래 정보도 수집한다.

- README, docs, package/build/config에서 확인되는 제품 목적과 실행 방식
- route, screen, API handler, model, schema, job, integration에서 확인되는 현재 기능
- 테스트, fixture, story, example에서 드러나는 기대 동작
- TODO, FIXME, placeholder, disabled test, 미완성 flow
- 구현되어 있음, 부분 구현, 없음, 위험함, 불명확함으로 나눈 capability 상태
- 외부 신호 대비 현재 코드베이스에서 추가/보강하기 쉬운 지점
- 다음 iteration 전에 먼저 손봐야 할 foundation risk

후속 확장에서는 다음 데이터도 붙일 수 있다.

- 제품 changelog
- 커뮤니티 글
- Reddit, Hacker News, Discord, Slack community
- 사용자 인터뷰
- 고객 피드백
- support ticket
- 자체 제품 analytics

## 7. 기능 우선순위 점수 기준

Feature Radar는 단순히 많이 언급된 기능을 높은 우선순위로 두면 안 된다. 다음 기준을 조합해 점수화한다.

| 기준 | 의미 |
| --- | --- |
| 수요 빈도 | 여러 repo, 제품, 사용자 그룹에서 반복되는가 |
| 고통 강도 | 댓글, 반응, 논쟁, 강한 불만이 있는가 |
| 최신성 | 최근에도 계속 등장하는 문제인가 |
| 미해결성 | 기존 제품이나 프로젝트에서 아직 잘 해결되지 않았는가 |
| 경쟁 차별성 | 만들면 경쟁 제품 대비 강점이 되는가 |
| MVP 적합성 | 초기 버전에 넣을 수 있는 크기인가 |
| 구현 비용 | 개발 난이도와 리스크는 어느 정도인가 |
| 로컬 적합성 | 현재 코드 구조와 자연스럽게 맞는가 |
| 구현 레버리지 | 이미 있는 구조를 활용해 작은 변경으로 효과를 낼 수 있는가 |
| 테스트 가능성 | 빠르게 검증할 수 있는 테스트/관찰 지점이 있는가 |
| 아키텍처 리스크 | 추가 시 구조적 부채나 큰 재설계가 필요한가 |
| 전략 적합도 | 만들려는 제품 방향과 맞는가 |
| 근거 신뢰도 | 출처가 명확하고 충분한가 |

예시 scoring model:

```text
priority_score =
  demand_frequency * 0.20
  + pain_intensity * 0.20
  + recency * 0.10
  + unresolved_gap * 0.15
  + differentiation * 0.15
  + mvp_fit * 0.10
  + evidence_confidence * 0.10
  - implementation_cost_penalty
```

기존 로컬 프로젝트 모드에서는 다음 기준을 함께 본다.

```text
next_iteration_score =
  external_demand
  + pain_intensity
  + competitive_gap
  + strategic_fit
  + local_code_fit
  + implementation_leverage
  + testability
  - architecture_risk
  - scope_size
```

점수는 자동 결정이 아니라 추천 근거다. P2A Gate A/B에서 사용자가 최종 범위를 승인한다.

## 8. Radar 산출물

초기 산출물은 다음처럼 나눈다.

```text
research-plan.md
source-candidates.md
research-bundle.md
signal-map.md
collection-report.md
local-project-scan.md
capability-gap-analysis.md
next-iteration-recommendations.md
```

각 파일 역할:

| 파일 | 역할 |
| --- | --- |
| `research-plan.md` | 조사 범위, 가정, 질문, source theme |
| `source-candidates.md` | 공식 문서, 비교 서비스, GitHub 출처, source type, 신뢰도 |
| `research-bundle.md` | 수집한 근거를 바탕으로 한 분석 본문 |
| `signal-map.md` | 반복 요청, 불편, gap, 최신 방향 같은 조사 신호와 source/evidence 매핑 |
| `collection-report.md` | 최종 실행 판단, 추천 방향, 리스크, 다음 작업 |
| `local-project-scan.md` | 기존 프로젝트의 현재 기능, 구조, 제약, 테스트, 파일 근거 |
| `capability-gap-analysis.md` | 외부 신호 대비 현재 구현의 already/partial/missing/risky/not relevant 분류 |
| `next-iteration-recommendations.md` | 기존 프로젝트의 다음 고도화 후보, 이유, 비용/리스크, 근거 |

Radar의 기본 산출물은 `.feature-radar` 아래의 native artifact다. P2A에는 전체 raw data를 그대로 넣지 않는다. P2A 연동이 필요할 때만 `p2a-context.json`처럼 정제된 입력을 optional export로 만들고, 원천 근거는 URL과 source id로 추적한다.

## 9. P2A 연동 방식

P2A 시작 시 research 자료가 있으면 그 자료를 먼저 사용하고, 없으면 기존처럼 P2A의 lightweight web lookup으로 진행한다.

```text
p2a-harness 시작
  -> research bundle 존재 확인
  -> 있으면:
       - freshness 확인
       - source/citation 확인
       - P2A evidence/reference_reconnaissance로 변환
  -> 없으면:
       - Feature Radar skill 실행 가능 여부 확인
       - 가능하면 Radar run 생성 후 P2A context export
       - 불가능하면 기존 P2A web lookup 규칙으로 진행
  -> Gate A intake
  -> Gate B spec
  -> Gate C task graph
  -> Gate D review
  -> supervised execution
```

권장 옵션:

```bash
p2a harness --idea "Jira 같은 시스템" --research optional
p2a harness --idea "Jira 같은 시스템" --research required
p2a harness --idea "Jira 같은 시스템" --research off
```

기본값은 `optional`이 좋다.

- `optional`: 있으면 쓰고, 없으면 기존 P2A 흐름으로 진행
- `required`: 조사 근거가 없거나 오래되면 Gate A/B 진행 차단
- `off`: 외부 조사 없이 사용자가 준 정보와 로컬 근거만 사용

## 10. P2A artifact 매핑

Radar 결과는 P2A 정본을 대체하지 않는다. Radar native artifact는 `.feature-radar` 아래에 두고, P2A export를 실행한 경우에만 `.plan2agent/artifacts/<project_id>/` 아래 JSON artifact로 변환한다.

P2A export 저장 구조:

```text
.plan2agent/artifacts/<project_id>/
  preflight-research/
    research-bundle.json
    local-project-scan.md              # optional existing project mode
    capability-gap-analysis.md         # optional existing project mode
    feature-opportunities.json
    priority-index.json
    next-iteration-recommendations.md  # optional existing project mode
    feature-brief.md
    p2a-context.json
  gate-a-intake/
    intake.json
  gate-b-spec/
    spec.json
  gate-c-task-graph/
    task-graph.json
  gate-d-review/
    review.json
```

매핑 규칙:

| Radar | P2A |
| --- | --- |
| source URL, repo, issue, PR | `evidence`의 `WEB-n` 또는 `LOCAL-n` |
| local file path, line reference | `evidence`의 `LOCAL-n` |
| 경쟁 제품/오픈소스 후보 | `reference_reconnaissance.candidates` |
| 선택할 패턴 | `reference_reconnaissance.selected_patterns` |
| 제외할 패턴 | `reference_reconnaissance.rejected_patterns` |
| 불확실하거나 영향 큰 선택 | `needs_user_decision` 또는 `open_decisions` |
| MVP 기능 후보 | `product.goals`, `core_flows`, `success_criteria` |
| 기존 프로젝트 보강 후보 | `iteration_candidates` 또는 Gate A/B delta draft |
| 후순위 기능 | `product.non_goals` 또는 next iteration 후보 |

## 11. Iteration 운영 방식

Radar 우선순위는 계속 바뀔 수 있지만, 진행 중인 P2A task graph를 자동으로 흔들면 안 된다. 변경 반영은 iteration 경계에서 한다.

```text
Iteration 시작 전:
  Radar refresh
  -> 새 신호와 기존 roadmap 비교
  -> 추가/보류/제외 후보 생성
  -> P2A Gate A/B delta draft
  -> 사용자 승인
  -> 다음 task graph 생성
```

진행 중인 iteration에는 다음 원칙을 둔다.

- 이미 승인된 MVP task는 자동 취소하지 않는다.
- 새로 발견된 기능은 current iteration blocker가 아니면 next iteration 후보로 보낸다.
- critical signal만 Gate 재검토 대상으로 승격한다.
- 우선순위 변경은 항상 근거와 함께 기록한다.

## 12. 기존 로컬 프로젝트 모드

기존 프로젝트가 있는 사용자는 로컬 프로젝트 경로를 Feature Radar 입력으로 줄 수 있다. 이 모드는 코드를 수정하는 기능이 아니라, 현재 구현 상태를 읽고 외부 신호와 비교해 다음 고도화 후보를 추천하는 조사 모드다.

```text
사용자 입력
  -> 로컬 프로젝트 경로
  -> 선택적 제품 설명/목표 사용자/관심 방향
  -> 코드 수정 금지 기본값
  -> local project scanner가 read-only scan
  -> reference discovery/web/GitHub scan
  -> capability gap analysis
  -> next iteration recommendation
```

로컬 프로젝트 스캔은 다음 원칙을 따른다.

- 기본값은 read-only다.
- `.env`, credentials, private key, token, secret config는 읽지 않는다.
- `node_modules`, `.venv`, `vendor`, `build`, `dist`, `target`, `.next`, `coverage`, generated artifact는 제외한다.
- 로컬 근거는 URL이 아니라 `path:line` 형식으로 남긴다.
- 로컬 코드 근거는 현재 구현 상태와 변경 난이도 근거이며, 시장 수요 근거로 쓰지 않는다.
- 외부 신호와 로컬 코드 추론을 분리해서 저장한다.

추천 후보는 다음 action으로 분류한다.

| Action | 의미 |
| --- | --- |
| `add` | 현재 없고 외부/전략 근거가 있는 새 기능 |
| `strengthen` | 이미 있지만 제품 수준으로 보강할 기능 |
| `fix_foundation` | 기능보다 먼저 손볼 구조, 데이터, 테스트, 품질, 성능, 보안, 관찰성, 문서 기반 |
| `defer` | 가능성은 있지만 비용, 리스크, 근거 부족, 타이밍 문제로 미룰 후보 |
| `reject` | 외부 신호는 있지만 프로젝트 방향과 맞지 않거나 하지 않는 편이 나은 후보 |

권장 산출물:

```text
local-project-scan.md
capability-gap-analysis.md
next-iteration-recommendations.md
```

`next-iteration-recommendations.md`의 기본 표 형식:

```text
rank | recommendation | action | why now | local evidence | external evidence | expected impact | cost/risk | confidence | next step
```

이 모드의 결과는 바로 구현 지시가 아니다. 사용자가 승인하면 P2A Gate A/B나 별도 구현 작업으로 넘긴다.

## 13. MVP 범위

처음 만들 MVP는 "Codex류 agent가 조사하고, Feature Radar skill/harness가 이를 조율해 Radar native artifact를 만드는 구조"로 좁힌다.

MVP 기능:

1. 아이디어 입력
2. Feature Radar skill이 run 계획과 subagent task graph 생성
3. 로컬 프로젝트 경로가 있으면 local project scanner가 read-only scan 수행
4. reference discovery subagent가 경쟁 제품, 공식 문서, GitHub 후보 조사
5. signal scan subagent가 issue, PR, discussion, changelog 신호 정리
6. synthesis subagent가 기능 후보와 불편점 클러스터링
7. 기존 프로젝트 모드에서는 capability gap과 next iteration 후보 정리
8. scoring tool/subagent가 우선순위 점수화
9. review subagent가 근거 부족, 과대 해석, stale source 확인
10. Radar native artifact 생성
11. 필요할 때만 target project로 handoff/export
12. 필요할 때만 `p2a-context.json` export

MVP 비목표:

- 완전 자동 제품 전략 결정
- P2A Gate 자동 승인
- 모든 웹 데이터 무제한 크롤링
- 유료 SaaS 내부 데이터 무단 수집
- GitHub issue/PR를 시장 전체 의견으로 과대 해석
- 진행 중인 P2A task graph 자동 변경
- 로컬 프로젝트를 사용자 승인 없이 수정
- 로컬 secret이나 private credential 수집
- handoff/export 시 기존 조사 파일을 사용자 승인 없이 덮어쓰기
- Feature Radar를 P2A artifact generator로 축소
- TypeScript 또는 Python 중 하나만 강제

## 14. 고도화 방향

MVP 이후에는 Radar를 "계속 갱신되는 제품 기획 시스템"으로 확장한다.

후속 기능:

- scheduled refresh
- repository watchlist
- competitor watchlist
- changelog diff
- feature trend timeline
- stale research detection
- roadmap impact analysis
- existing project mode의 local scan diff
- P2A iteration draft 자동 생성
- 사용자 피드백 import
- P2A run/eval/proposal 결과를 Radar priority에 반영
- subagent별 평가/eval
- skill marketplace 또는 Codex plugin 형태 배포
- 도구별 provider 교체 구조

장기적으로는 다음 루프를 만든다.

```text
외부 신호 -> Radar priority -> P2A planning -> 개발/run/eval -> 내부 결과 -> Radar priority 갱신
```

이 구조가 잡히면 제품 개발은 "아이디어를 한 번 기획하고 구현"하는 방식이 아니라 "근거를 계속 갱신하며 다음 개발 범위를 조정"하는 방식이 된다.

## 15. 안전 원칙

- Radar 결과는 참고 근거이며, P2A 승인 절차를 대체하지 않는다.
- 출처 URL, repo, issue, PR은 항상 보존한다.
- 로컬 프로젝트 근거는 파일 경로와 line reference를 보존한다.
- 사용자가 명시하기 전에는 로컬 프로젝트를 수정하지 않는다.
- handoff/export는 기존 파일을 조용히 덮어쓰지 않는다.
- secret, credential, token, private key, 개인 설정 파일을 조사 산출물에 포함하지 않는다.
- 오래된 조사 결과는 stale로 표시한다.
- 근거가 약한 추천은 confidence를 낮게 둔다.
- GitHub 데이터는 개발자 중심 신호이므로 일반 시장 수요와 구분한다.
- 외부 API rate limit과 라이선스, 약관을 지킨다.
- 수집한 내용을 그대로 복사하지 않고 요약과 링크 중심으로 보존한다.
- 개발 task로 전환하기 전에는 P2A Gate A/B에서 사용자 승인을 받는다.
- AI agent가 만든 조사 결과는 reviewer subagent 또는 검증 tool로 최소 1회 검토한다.
- tool이 가져온 원문과 agent 요약은 구분해서 저장한다.
- 로컬 코드에서 추론한 내용과 외부 출처에서 확인한 내용을 구분해서 저장한다.

## 16. 결론

Feature Radar는 P2A의 앞단을 강화할 수 있지만, P2A에 종속된 파일 생성기가 아니다. Radar는 skill, subagent, tool을 조합해 "필요한 기능과 우선순위의 근거"를 계속 갱신하는 독립 시스템이다. P2A는 그 결과를 optional export로 받아 "승인된 기획과 실행 가능한 개발 작업"으로 바꾼다.

가장 좋은 제품 정의:

```text
Feature Radar는 skill/subagent/tool 기반 agent harness로 외부 신호와 내부 실행 결과를 수집해 기능 우선순위를 계속 갱신하고,
P2A는 그중 승인된 범위를 optional handoff로 받아 MVP 개발과 기능 고도화 task로 실행한다.
```

따라서 초기 구현은 Feature Radar를 독립적인 agent harness로 만들고, P2A에는 optional research provider/exporter로 연결하는 방식이 적절하다.
