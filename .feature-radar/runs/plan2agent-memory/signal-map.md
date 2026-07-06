# 신호 맵

run_slug: plan2agent-memory
title: Plan2Agent Memory 다음 이터레이션 조사
mode: existing-project
local_project: D:/projects/plan2agent-memory
created_at: 2026-07-06T00:00:00+00:00
status: complete

신호 유형: `LOCAL-*` id에서 온 신호(S6, S7, S20, S21, S22, S23)는 **로컬 코드 관찰(local-derived)**이며 외부 시장/커뮤니티 신호가 아니다. 이들은 "무엇이 존재하고 무엇을 바꾸기 싸거나 위험한가"에 대한 근거이지, 수요에 대한 근거가 아니다. 모든 `GH-*` 소스는 개발자 도구 신호(약 4개 OSS 커뮤니티의 반복 엔지니어링 요청)이며, 일반 시장/구매 수요의 근거가 명시적으로 아니다.

| signal id | 신호 | source ids | P2A memory 함의 | 유의점 | 신뢰도 |
| --- | --- | --- | --- | --- | --- |
| S1 | 튜닝 가능 fusion(RRF 기본)을 갖춘 hybrid keyword+vector가 memory + vector store 전반에서 table-stakes | WEB-1, WEB-10, WEB-12, WEB-14, GH-11 | keyword-only + vector-only 엔드포인트를 hybrid retrieval 경로로 융합해야 신뢰 유지 | 차별화가 아니라 parity; 현재 로컬 keyword 검색은 LIKE 기반 | high |
| S2 | 내장 reranking이 기대됨; Spring AI는 2.0 GA(2026-06)에 hybrid/rerank 없이 출시, langchain4j는 둘 다 보유 | GH-9, GH-10, GH-11 | hybrid/rerank가 생태계 table-stakes임을 확인. 단, 이는 retrieval 품질 맥락이지 P2A-vs-SpringAI 경쟁 우위가 아님 — P2A는 headless artifact store이지 Spring AI 대체재가 아님. rerank는 보통 모델이 필요해 P2A의 no-AI-generation 경계와 충돌; 추진 시 pluggable score-fusion 또는 optional external hook이어야 함 | 개발자 도구 신호일 뿐. 시점 민감: Spring AI 2.0 GA 범위는 2026-06 기준 — 의존 전 재확인. 시장 수요로 읽지 말 것 | med |
| S3 | pgvector filter-then-ANN은 iterative_scan/ef_search 미설정 시 recall을 조용히 낮춤 | GH-12, GH-13 | P2A의 metadata-filter-then-search 패턴은 iterative_scan 활성화, filter 컬럼 인덱싱, ef_search 노출, 선택적 필터 하 recall 테스트가 필요 | ANN 도입 후에만 문제됨; 오늘은 exact full scan | high |
| S4 | pgvector 2000-dim 인덱스 cap; >2000-dim 임베딩(예: 3072)은 halfvec cast 필요 | GH-14 | ANN 추가 시 halfvec(N)에 인덱스 구축, 반정밀도 recall 검증 | 현재 `MAX_VECTOR_DIMENSION=2000` guard가 이를 우회하나 큰 임베딩도 차단 | high |
| S5 | native pgvector hybrid 연산자 없음; tsvector+vector+RRF은 직접 구축 레시피 | GH-15, WEB-10 | P2A가 fusion + pagination 로직을 소유 — 통제 가능한 가치 표면 | fusion을 정확히 구현/유지해야 함(IDF scoping, 결정론적 tie) | med-high |
| S6 | 현재 스키마의 untyped/미인덱스 vector 컬럼이 exact full scan 강제 | LOCAL-6, LOCAL-8 | vector 검색이 확장 불가; ANN은 고정 차원 컬럼 + 마이그레이션 선행 | 소규모에선 무난, chunk 증가 시 벽 | high |
| S7 | 로컬 keyword 검색이 기존 GIN FTS 인덱스를 우회(leading-wildcard LIKE) | LOCAL-6, LOCAL-8 | 가장 싼 고가치 수정: to_tsvector/ts_rank로 전환해 죽은 인덱스 활성화 + ranked 관련성 | 한국어 analyzer는 PG 확장 필요; public score는 이미 opaque라 ranking 자유 변경 가능 | high |
| S8 | stale memory의 forgetting/decay/TTL/GC가 4개 memory framework 전반에서 요청되며 대부분 미해결(userland로 미룸) | GH-3, GH-4, GH-5, WEB-6 | 미충족 primitive; P2A lineage로 decay를 되돌릴 수 있음(archive-not-delete) = 잠재 차별점. 단 P2A는 오늘 delete/GC 경로가 전혀 없음 | 인큐번트가 미루는 이유가 "어려워서"만이 아니라 "우선순위 낮아서"일 수 있음 — 수요 검증 필요 | high |
| S9 | temporal / non-destructive 버전관리("시점 T에 시스템이 무엇을 믿었는가") 요청되고 open | GH-1, WEB-4 | P2A의 snapshotVersion + lineage 설계가 on-thesis임을 직접 확인 | chat-memory framing; 코딩 에이전트 artifact와 인접하나 동일하지 않음 | high |
| S10 | content-hash dedup을 ingest 시 junk 필터로 쓰는 것이 인큐번트가 덧붙이는 활성 pain | GH-2, WEB-11 | P2A의 content-hash 멱등성이 이미 이 필터임 — 만들 게 아니라 드러낼 강점 | — | high |
| S11 | conflict/contradiction 감지(update-vs-append, 어느 버전이 supersede)가 우선순위화되는 중 | GH-6, GH-3 | P2A diff + lineage가 blind upsert 대신 supersession을 표현 가능 | diff/버전관리 계층이 정말 좋아야 함 | high |
| S12 | provenance/citation을 query 시 1급 출력으로(내부 메타데이터가 아니라) 요청 | GH-7, GH-4 | retrieval 응답이 lineage/source ref를 citation으로 노출해야; P2A는 이미 저장 중 | med-high | med-high |
| S13 | 재현 가능한 retrieval 평가/벤치마킹 요청(mem0 LOCOMO 재현 불가) | GH-8 | 작은 재현 가능 eval 하네스(고정 corpus의 recall@k)가 검색 변경 전 유용한 회귀 guardrail | 단일 출처(mem0 이슈 하나) — 생태계 전반의 "credibility gap"으로 일반화하지 말 것; eval corpus 구축은 실제 비용 | med |
| S14 | BYO-embeddings / self-host / Postgres 백엔드가 memory framework 전반의 반복 요청 | WEB-4, WEB-5, WEB-7 | P2A 스택과 "서버는 임베딩을 생성하지 않는다" 자세를 검증 | — | high |
| S15 | 구조적(텍스트가 아닌) diff/merge가 실제로 원해짐; element-identity + array-move가 난제; nbdime/dolt가 analog | GH-16, GH-17, GH-18 | P2A content-hash가 각 node/task에 이들 도구가 갖지 못한 안정적 identity 부여 → reorder가 delete+add가 아닌 move로 읽힘; "task-graph용 nbdime" companion이 방어 가능한 whitespace | task-graph/DAG 특화 diff는 niche 안의 niche — engagement 낮음; 과투자 전 검증 | high |
| S16 | diff/sync는 휘발/파생 필드(timestamp, run 출력)를 무시해야 하며, 그렇지 않으면 매 sync가 허위 변경 표시 | GH-16 | P2A status/diff가 휘발 필드를 분리/무시해야 | med-high | med-high |
| S17 | Multi-embedding-set 비교(named vector / multi-column)가 점진 마이그레이션 지원 | WEB-13, WEB-8 | P2A의 embedding_sets 설계가 이미 버전화 임베딩 비교 가능 — 강점 | 성능을 위해 ANN + set별 인덱싱 필요 | med |
| S18 | Lineage graph + registry(run→artifact, version/alias/tag)가 artifact 카탈로그의 표준 | WEB-15, WEB-17, WEB-18 | P2A run→artifact lineage와 registry식 조회 표면을 MLflow/OpenMetadata 패턴으로 모델링 | data-warehouse framing; 모든 기능이 전이되진 않음 | med-high |
| S19 | content-hash 저장 위 git-like diff/snapshot/merge가 검증된 패턴(DVC, lakeFS, Letta .af) | WEB-16, WEB-19, WEB-3 | companion GUI/CLI의 git-client 시맨틱과 no-silent-overwrite 정책에 직접 시사 | 광의의 "git over DB"는 niche이며 스키마 마이그레이션과 혼동되기 쉬움 | high |
| S20 | Row-by-row bulk insert가 sync 처리량 상한 | LOCAL-9 | Batched multi-row insert가 대용량 sync batch에 싸고 계약 없는 처리량 개선 | 오늘은 정확성 무문제; 버그가 아닌 상한 | med |
| S21 | task-graph→document canonical 링크 유실(document_id 항상 null) | LOCAL-9, LOCAL-8 | 싼 foundation 수정; 더 많은 기능이 join에 의존하기 전에 lineage 혼동 예방 | 로컬 코드 추론, 어댑터 + 검색 join에서 확인됨 | high |
| S22 | Pagination 계약 없음(맨 List + limit-only) | LOCAL-7 | 지금 응답 envelope 결정; 나중 추가는 파괴 변경 | — | high |
| S23 | actuator가 classpath에 있음에도 관측성(metrics/tracing) 없음 | LOCAL-5 | actuator 확대 + Micrometer counter/timer는 싸게 가능; 성능 주장 전 필요 | — | med-high |
