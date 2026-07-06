# 조사 계획

run_slug: plan2agent-memory
title: Plan2Agent Memory 다음 이터레이션 조사
mode: existing-project
local_project: D:/projects/plan2agent-memory
created_at: 2026-07-06T00:00:00+00:00
status: complete

## 범위

- 대상 제품/프로젝트: Plan2Agent Memory Server — Plan2Agent(P2A) 산출물의 canonical 보조 저장소 역할을 하는 headless Kotlin/Spring Boot + PostgreSQL/pgvector REST 서비스. 로컬 md/json 파일이 원본(source of truth)이고, 서버는 canonical ID, lineage, content hash, 관계, keyword/vector 검색 인덱스를 저장한다. 임베딩 생성, 에이전트 실행, 외부 AI API 호출은 하지 않는다.
- 사용자 요청: 로컬 프로젝트를 read-only로 검토하고, 현재 구현을 외부 서비스/문서/GitHub 신호와 비교해 다음 고도화 후보를 추천.
- 조사 모드: existing-project (read-only 로컬 스캔 + 외부 신호 비교).
- 범위 내: `path:line` 근거를 갖춘 현재 capability 인벤토리, 비교 서비스, pgvector / agent-memory / RAG / structured-diff 생태계의 개발자 도구 신호, capability-gap 분석, 우선순위화된 다음 이터레이션 추천.
- 범위 외: 코드 수정, P2A export/handoff(요청 없음), 시장 규모 주장, GitHub 활동을 일반 시장 수요로 확대 해석.

## 질문

- v1-mvp가 실제로 무엇을 구현했고, 테스트는 얼마나 되어 있는가?
- 비교 서비스가 제공하는 capability 중 빠진 것은 무엇이고, 현재 아키텍처 기준으로 추가가 싼 것과 비싼 것은 무엇인가?
- 기능 추가 전에 먼저 손봐야 할 foundation risk는 무엇인가?
- 가장 레버리지가 큰 다음 이터레이션 후보는 무엇이며 각각의 근거는?
- 제품이 실제로 차별화된 지점(whitespace)은 어디이고, 단순히 parity(table-stakes)인 지점은 어디인가?

## 방법

- local-project-scanner: D:/projects/plan2agent-memory read-only 심층 스캔 (build, 계층, 엔드포인트, 영속성, 검색, 인증, 테스트, 문서, gap, 레버리지).
- reference-discovery: 비교 agent-memory 백엔드, vector store, artifact/lineage 카탈로그를 canonical URL과 함께 발굴.
- github-signal-scanner: pgvector, mem0/Letta/Zep-Graphiti/Cognee/LangMem, Spring AI, structured-diff 도구 전반의 반복 개발자 pain/요청 스캔.
- web-source-collector: 생략 — reference-discovery와 github-signal-scanner가 이미 문서 수준 근거(Supabase 하이브리드 검색 레시피, pgvector 릴리스 세부사항, Spring AI 2.0 GA 범위, Weaviate/Qdrant fusion 문서)를 커버함. 중복 수집을 피하기 위해 명시적으로 생략.
- evidence-reviewer: 최종 확정 전 과대 해석, source-type 혼동, stale source 관점에서 결론을 검증.

## 산출 예정 파일

- research-plan.md
- source-candidates.md
- local-project-scan.md
- research-bundle.md
- signal-map.md
- capability-gap-analysis.md
- next-iteration-recommendations.md
- collection-report.md
- _raw-github-signal/ (GitHub 스캐너 원본 근거, 보존)
