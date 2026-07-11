# Tool Gap 프로필 통합 방향

작성일: 2026-07-11

상태: 단계적 통합 채택

## 1. 결정 요약

Tool Gap Finder의 문제 정의와 근거 중심 후보 생성 방식을 Feature Radar의 첫 특화 프로필로 통합한다. 별도 제품이나 세 번째 실행 모드로 만들지 않는다.

```text
mode: idea | existing-project
profile: general | tool-gap
```

- `mode`는 조사 대상을 나타낸다.
- `profile`은 근거를 수집·해석하고 결과를 합성하는 방법을 나타낸다.
- 기본 프로필은 `general`이다.
- 기존 run에 `profile`이 없으면 `general`로 해석한다.
- `tool-gap`은 `idea`, `existing-project` 어느 모드와도 조합할 수 있다.
- research artifact의 `mode`, `profile`, `status` header는 정본 metadata이며 expected artifact set 안에서 유효하고 일관되어야 한다.

이 결정은 Feature Radar를 skill/subagent 중심의 독립 조사 하네스로 유지하고 P2A를 선택적 소비자로 두는 기존 방향을 변경하지 않는다. `docs/plns/01-feature-radar-p2a-direction.md`의 native artifact, 사용자 승인, read-only local scan, optional handoff 원칙을 그대로 따른다.

## 2. 프로필의 책임과 경계

`tool-gap` 프로필은 아이디어 또는 기존 프로젝트 주변의 반복된 개발자 불편, 우회 방법, 호환성 문제, 운영 공백을 조사해 독립적인 지원 도구 후보로 합성한다.

포함 범위:

- 아이디어, 대상 사용자, 검색 키워드, 제외 조건, 선택적 seed repository 정리
- 관련 저장소 후보 탐색과 선택·제외 이유 기록
- README, 문서, release, issue, PR, discussion의 원문 근거 보존
- 동일 문제를 설명하는 신호의 클러스터링
- 기존 대안과 반대 근거 조사
- 근거를 통과한 지원 도구 후보 0~3개 생성
- 근거 신뢰도, 불확실성, 좁은 MVP 범위 설명

후보 분류:

- 플러그인 및 확장
- 프레임워크 간 어댑터
- 테스트·평가 도구
- 디버깅·관찰성 도구
- CLI 및 개발자 경험
- 마이그레이션·호환성 도구
- 보안·권한 관리
- 배포·운영 자동화
- 데이터 변환·시각화
- 에이전트 하네스 구성

이 분류는 `tool-gap` 프로필에만 적용한다. `general` 프로필의 일반 기능 조사와 기존 프로젝트 고도화 추천 범위를 축소하지 않는다.

비목표:

- 원본 프로젝트의 핵심 제품을 다시 만드는 대규모 후보
- GitHub 신호만으로 시장 규모, 수익성, 방어력을 단정하는 것
- 사용자의 승인 없이 후보를 P2A task나 구현 작업으로 전환하는 것
- 후보 수를 채우기 위해 근거가 약한 추천을 생성하는 것

## 3. 실행 아키텍처

현재 Feature Radar skill이 Manager 역할을 유지한다. 기존 조사 역할은 재사용하고, `opportunity-synthesizer`만 새로운 명시적 합성 역할로 추가한다.

| 역할 | 책임 | 프로필 영향 |
| --- | --- | --- |
| Feature Radar skill | 계획, 의존 순서, 종료 조건, native artifact 조율 | `mode`와 `profile`을 함께 전달 |
| reference discovery | 서비스, 저장소, 문서, 대안 후보 탐색 | 선택적 seed repository를 anchor로 받고, seed/discovered 상태와 선택·제외 이유 기록 |
| web source collector | 공식 기능, 포지셔닝, 변경 방향, 생태계 근거 수집 | 비-GitHub 대안·시장 주장 근거 보완 |
| GitHub signal scanner | README, release, issue, PR, discussion 신호 수집 | 선택적으로 tool-gap evidence type과 counter-signal 기록 |
| local project scanner | 기존 프로젝트를 read-only로 확인 | `existing-project`일 때만 현재 역량과 결합 지점 제공 |
| opportunity synthesizer | 승인된 ProblemCluster 표와 0~3개 후보 합성 | cluster ID 선행 정의, tool-gap 분류, 대안, 반대 근거, MVP 범위 적용 |
| evidence reviewer | 과대 해석, stale source, 반증 누락 검토 | 후보별 trace, taxonomy, 0~3 규칙, 점수 출처 검증 |
| handoff packager | 완료된 native run을 선택적으로 전달 | 기존 artifact와 overwrite 안전 원칙 유지 |

실행 의존성:

```text
plan
  -> reference discovery
  -> web / GitHub / optional local collection
       (독립적인 수집 작업은 병렬 가능)
  -> evidence normalization
  -> problem clustering
  -> opportunity synthesis
  -> alternatives and counter-evidence review
  -> qualitative assessment
  -> final evidence review
  -> collection-report.md
```

수집 병렬화가 합성 게이트를 건너뛰게 해서는 안 된다. `opportunity-synthesizer`는 source와 signal 입력이 준비된 뒤 실행하며, 최종 보고서는 evidence review 이후 확정한다.

## 4. 후보 수와 종료 규칙

Tool Gap 결과는 정확히 세 개가 아니라 **0개 이상 3개 이하**다.

후보를 유지하려면 최소한 다음을 설명해야 한다.

- 어떤 문제 클러스터에서 나왔는가
- 어떤 사용자에게 필요한가
- 어떤 source/evidence가 지지하는가
- 이미 존재하는 대안은 무엇이며 어디까지 해결하는가
- 어떤 반대 근거 또는 불확실성이 있는가
- 독립 도구로 검증할 수 있는 가장 작은 MVP는 무엇인가

근거가 이 기준을 통과하지 못하면 후보를 약화하거나 제외한다. 모든 후보가 제외되어도 정상적으로 run을 완료하되 결과를 구분한다.

- `insufficient_evidence`: 수집 품질이나 범위가 판단하기에 부족하다.
- `no_supported_opportunity`: 근거는 충분하지만 모든 후보가 이미 해결됨, 반증됨, 범위 밖임 등의 이유로 유지되지 않았다.

형식을 맞추기 위한 후보 padding은 금지한다.

단일 issue, 반응 수, 오래 열린 기간만으로 반복 수요를 판단하지 않는다. 서로 다른 저장소에서의 재현, 실제 workaround, maintainer disposition, 해결 여부를 분리해 본다. `duplicate`, `out_of_scope`, `wont_fix`, `stale`, `implemented`는 기회 신호가 될 수도 있지만 동시에 반증 또는 이미 해결된 신호가 될 수 있다.

## 5. 근거 추적 계약

초기 단계에서는 별도 JSON 모델을 요구하지 않고 기존 Markdown의 source ID와 참조를 사용한다.

```text
collection-report recommendation
  -> Opportunity
  -> ProblemCluster
  -> Evidence / counter-evidence
  -> SourceRecord canonical URL
```

기존 프로젝트 근거는 다음 경로를 추가한다.

```text
Opportunity
  -> local capability or constraint
  -> local-project-scan.md path:line
```

각 계층의 최소 필드:

| 계층 | 최소 기록 |
| --- | --- |
| SourceRecord | source ID, source type, canonical URL 또는 `path:line`, 관찰 시점, confidence, caveat |
| Evidence | evidence type, source ID, 문제/우회/maintainer signal 요약, 해결 상태 |
| ProblemCluster | cluster ID, 대표 문제, evidence refs, 저장소 범위, recurrence, counter-signals |
| Opportunity | 후보 ID, category, target users, cluster refs, evidence refs, alternatives, counter-evidence refs, MVP scope, confidence 설명 |

원문 사실과 agent의 요약·분류를 구분한다. 링크가 없는 외부 주장이나 파일 근거가 없는 로컬 주장은 최종 후보의 핵심 근거로 사용하지 않는다. 로컬 구현은 적합성과 비용 근거이지 외부 수요 근거가 아니다.

`opportunity-synthesizer`는 후보 표보다 먼저 승인된 cluster를 다음 Markdown shape으로 출력한다.

```text
cluster id | representative problem | evidence refs | repository scope / recurrence | counter-signals | caveat
```

모든 cluster ID는 고유해야 하고, 후보의 cluster ref는 이 표의 행으로 해석되어야 한다. 제외된 cluster는 별도 표에 제외 이유와 함께 남긴다.

## 6. 현재 native artifact 매핑

Tool Gap 전용 정본 파일 세트를 추가하지 않는다.

| Tool Gap 제안 개념 | 현재 Feature Radar 정본 |
| --- | --- |
| 정규화된 아이디어, 키워드, 제외 조건, seed repositories | `research-plan.md` |
| ecosystem/repository shortlist와 선택·제외 이유 | `source-candidates.md`와 `research-bundle.md` |
| evidence와 counter-signal | `signal-map.md`, canonical source는 `source-candidates.md` |
| 승인된 ProblemCluster 표와 분석 | `research-bundle.md` |
| 후보 0~3개와 `insufficient_evidence` 또는 `no_supported_opportunity` 판단 | `collection-report.md` |
| 기존 프로젝트 로컬 근거 | `local-project-scan.md` |
| 기존 프로젝트 비교 | `capability-gap-analysis.md` |
| 기존 프로젝트의 다음 후보 | `next-iteration-recommendations.md` |
| 실행 metadata | 정본 artifact header와 여기서 재생성하는 `_INDEX.md` |

따라서 제안 문서의 `final-report.md`는 `collection-report.md`로 흡수한다. `ecosystem-map.md`는 우선 `research-bundle.md`의 section으로 표현한다. `evidence.json`, `opportunities.json`, `run.json`은 schema가 안정된 이후의 선택적 구조화 표현이며 현재 정본이 아니다.

Handoff는 기존 native artifact를 복사하고 각 destination에서 정본 metadata로 `_INDEX.md`를 재생성하며 source `run_mode`, source `profile`, destination `handoff_mode`, `source_complete`를 manifest에 보존한다. 불완전 handoff는 missing required와 유일한 optional 파일인 `p2a-context.json`을 구분한다. Tool Gap 프로필이 P2A export를 의무화하지 않는다.

`existing-project` run에서는 `local-project-scan.md`, `capability-gap-analysis.md`, `next-iteration-recommendations.md` 세 파일이 현재 런타임 계약상 필수다. 적용할 내용이 없으면 파일을 생략하지 않고 이유와 함께 명시적 `N/A`를 기록한다.

## 7. 점수 원칙

기회 점수와 근거 신뢰도는 서로 다른 개념으로 유지한다. 그러나 현재 단계에서 agent가 임의의 숫자를 만들지 않는다.

- versioned deterministic scorer가 없으면 수치 점수는 `not_scored`다.
- qualitative assessment는 근거와 caveat를 함께 기록한다.
- 같은 정규화 근거와 같은 rule version이 같은 수치를 만드는 단계에서만 numeric score를 정본으로 사용한다.
- 높은 기회 점수가 낮은 confidence를 상쇄하지 않는다.
- market size, monetization, defensibility는 비-GitHub 근거가 없으면 `unknown`이다.
- 초기 Build/Prototype/Watch/Skip threshold는 검증된 정책이 아니라 calibration hypothesis로 취급한다.

현재 qualitative rubric:

| 차원 | 허용 값 | 해석 |
| --- | --- | --- |
| opportunity assessment | `strong`, `moderate`, `weak`, `unknown` | counter-evidence 검토 후 남은 문제 강도, 대안 공백, 좁은 MVP 타당성 |
| evidence confidence | `high`, `medium`, `low`, `unknown` | 근거의 품질, 독립성, 최신성, 추적 가능성 |

두 값은 근거 ref와 caveat로 각각 설명하고 숨은 숫자로 변환하지 않는다. 사용자의 요청만으로 numeric score를 만들 수 없으며, 이름과 버전이 있는 결정론적 scorer 결과가 제공될 때만 수치를 사용한다.

## 8. 단계와 승인 게이트

### Stage 0 — 호환 가능한 프로필 계약

범위:

- `profile: general | tool-gap` 추가와 `general` 기본값
- 기존 `idea | existing-project` mode 유지
- research artifact header의 일관된 `mode`, `profile`, `status` metadata와, 그 header에서 재생성되는 비정본 `_INDEX.md`
- mode를 변경하는 `init --overwrite` 거부
- handoff의 `run_mode`, `profile`, `handoff_mode`, `source_complete` 분리와 manifest 보존
- Codex/Claude agent 정의와 문서 동기화
- 현재 run/handoff 동작의 회귀 테스트

통과 조건:

- 기존 run이 수정 없이 `general`로 처리된다.
- 두 mode 모두 두 profile로 초기화·검증할 수 있다.
- 모든 research artifact에 profile metadata가 없는 legacy run만 `general`로 fallback하고, expected artifact의 `mode`, `profile`, `status`가 유효하지 않거나 충돌하면 오류로 처리한다. `_INDEX.md`는 정본 판정에 참여하지 않고 artifact metadata에서 재생성한다.
- 기존 run의 mode를 바꾸는 `init --overwrite`는 거부하고 새 slug 또는 명시적 migration을 요구한다.
- handoff가 source `run_mode`, source `profile`, destination `handoff_mode`, `source_complete`를 별도로 보존한다. CLI에서 `both`를 선택하면 destination별 manifest 두 개를 만들며 각 `handoff_mode`는 `radar-native` 또는 `p2a-preflight`다. 호환용 `mode` 필드가 남으면 `handoff_mode`의 alias이며 `run_mode`가 아니다.
- `--run-type`은 source header override가 아니라 expected run type assertion이다.
- intentional incomplete handoff는 `source_complete: false`를 기록하고 missing required와 유일한 optional 파일 `p2a-context.json`을 별도 section으로 남긴다.
- handoff는 self-destination과 non-file artifact 충돌을 쓰기 전에 거부한다. 명시적 `--overwrite`에서는 알려진 managed artifact만 동기화하고 source에 없는 stale managed 파일을 제거해 manifest와 destination을 일치시킨다.
- 새 프로필 때문에 일반 조사 산출물이나 필수 파일 세트가 바뀌지 않는다.

### Stage 1 — Markdown 기반 수직 검증

범위:

- 현재 host 검색·브라우징 도구와 subagent를 사용한다.
- AI agent 개발 도구 분야의 서로 다른 아이디어를 최소 5개 실행한다.
- accepted ProblemCluster 표, 대안, counter-evidence, 0~3개 후보를 사람과 함께 검토한다.
- 숫자 점수 없이 정의된 opportunity assessment와 evidence confidence rubric을 사용한다.

통과 조건:

- 최소 2개 아이디어에서 사람이 프로토타입 검증 가치가 있다고 판단한 후보가 나온다.
- 유지된 모든 후보가 source URL과 counter-evidence로 추적된다.
- 수작업 검토와 핵심 evidence classification이 실질적으로 일치한다.
- 후보가 없는 run도 오류나 padding 없이 완료되고 `insufficient_evidence`와 `no_supported_opportunity`를 구분한다.

### Stage 2 — 구조화 계약과 결정론적 점수

범위:

- versioned `run.json`, `evidence.json`, `opportunities.json` 검토
- JSON Schema와 reference integrity validation
- artifact type, required/optional, profile applicability를 한 곳에서 관리
- scoring rule version, factor evidence, unknown factor, tie-break 기록
- profile-aware validation과 handoff

통과 조건:

- 모든 ID 참조가 유효하다.
- 같은 normalized evidence와 rule version이 같은 score와 decision을 만든다.
- 경계값, recency, duplicate, counter-evidence, tie-break golden test가 통과한다.
- JSON을 추가해도 legacy Markdown run과 handoff가 유지된다.

### Stage 3 — GitHub data plane 자동화

범위:

- 직접 GitHub API adapter
- 인증, 작은 단위 pagination, cache/conditional request
- rate-limit telemetry, retry/backoff, incomplete result 기록
- fixture 기반 collector test와 제한된 integration test

통과 조건:

- 동일 fixture에서 재현 가능한 Evidence가 생성된다.
- timeout, rate limit, partial result가 보고서의 caveat로 전달된다.
- token, credential, raw cache가 run artifact나 handoff에 포함되지 않는다.
- 결과가 GitHub 전체가 아닌 범위가 명시된 evidence sample임을 기록한다.

### Stage 4 — 제품화 판단

Stage 1~3의 품질, 비용, 반복 사용 데이터를 본 뒤에만 별도 CLI, 저장소, scheduled refresh, UI, provider abstraction을 결정한다. 구현 언어도 이 시점의 실제 adapter와 배포 경계에 따라 선택한다.

## 9. 명시적으로 미룬 범위

다음 항목은 이번 통합의 선행 조건이 아니다.

- standalone Commander 기반 Node/TypeScript 제품 CLI
- repository 전체의 단일 언어 고정
- SQLite 또는 DuckDB
- host agent runtime과 중복되는 custom `LlmProvider`
- required JSON artifact와 즉시 schema migration
- GitHub 전체 장기 데이터 수집
- scheduled refresh, watchlist, web UI
- 자동 P2A Gate 승인 또는 진행 중 task graph 변경
- 검증되지 않은 수익성·방어력 점수

연기 사유는 기술을 배제하기 위해서가 아니라, 반복 실행에서 안정된 계약과 실제 병목이 확인된 뒤 가장 작은 도구 경계를 선택하기 위해서다.

## 10. 첫 통합 완료 기준

이번 통합 단계는 다음 상태를 목표로 한다.

- mode, profile, status의 정본 metadata 의미가 코드·agent·문서에서 일치한다.
- handoff의 `run_mode`, `profile`, `handoff_mode`, `source_complete` 의미가 분리된다.
- `opportunity-synthesizer`가 Codex와 Claude 양쪽에 존재한다.
- GitHub scanner와 evidence reviewer가 general 동작을 유지하면서 tool-gap 전용 검사를 선택적으로 수행한다.
- native artifact 정본과 P2A optional boundary가 유지된다.
- 새 CLI 제품, JSON 정본, DB, custom LLM 계층 없이 수동 수직 검증을 시작할 수 있다.

이후 구현 투자는 Stage 1의 실제 후보 품질과 근거 추적 결과를 기준으로 결정한다.
