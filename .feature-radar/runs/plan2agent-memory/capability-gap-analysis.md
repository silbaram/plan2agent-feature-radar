# Capability Gap 분석

run_slug: plan2agent-memory
title: Plan2Agent Memory 다음 이터레이션 조사
mode: existing-project
local_project: D:/projects/plan2agent-memory
created_at: 2026-07-06T00:00:00+00:00
status: complete

현재 구현을 외부 신호와 대조한 분류. 로컬 상태는 로컬 스캔 기준; 외부/레퍼런스 신호는 비교 서비스 + GitHub 개발자 pain 기준. "not relevant" = product-spec non-goal에 따라 의도적으로 범위 밖.

| 영역 | 로컬 상태 | 외부/레퍼런스 신호 | gap | 권고 | 신뢰도 |
| --- | --- | --- | --- | --- | --- |
| Ranked keyword 관련성 | 부분 — LIKE `%q%`, GIN FTS 인덱스는 있으나 미사용(LOCAL-6, LOCAL-8) | BM25/tsvector ranking 표준; product-spec이 이미 BM25를 의도(LOCAL-2, S7) | 죽은 FTS 인덱스; 진짜 ranking 없음 | strengthen: 기존 keyword 어댑터에서 to_tsvector/ts_rank 활성화 | high |
| Hybrid keyword+vector retrieval | 없음 — keyword/vector 엔드포인트 분리만(LOCAL-7, LOCAL-8) | table-stakes: Supabase, Weaviate, Mem0, Chroma, langchain4j 모두 융합; Spring AI는 아님(S1, S2) | fusion 경로 없음 | add: 기존 두 포트를 RRF로 융합하는 hybrid use case | high |
| ANN vector 인덱스 | 없음 — untyped `vector` 컬럼, exact full scan(LOCAL-6, S6) | HNSW/IVFFlat 표준; pgvectorscale DiskANN; product-spec이 HNSW/IVFFlat를 future로 명시(LOCAL-2) | 인덱스 없음; 확장 불가 | fix_foundation 후 add: 고정 차원 컬럼으로 재설계 후 인덱스 | high |
| Metadata 필터 하 recall | 아직 해당 없음(exact scan)이나 잠재 | pgvector filter-then-ANN recall 함정이 잘 알려짐(S3) | ANN 추가 시 "결과 누락"으로 표면화 | fix_foundation: ANN 작업에 iterative_scan/ef_search + filter 컬럼 인덱스를 설계 | high |
| Pagination | 없음 — limit-only, 맨 List(LOCAL-7, S22) | 모든 카탈로그/store API의 표준 | 미루면 파괴 변경 | fix_foundation: 지금 응답 envelope + keyset paging 추가 | high |
| Delete / soft-delete / stale artifact GC | 없음 — delete 표면 없음, 저장소 무한 증가(LOCAL-9) | forgetting/decay/GC가 4개 memory framework에서 요청되나 대부분 미해결(S8) | prune 경로 없음; 단 인큐번트도 부재 | add(설계 주도): lineage 활용 되돌릴 수 있는 archive/supersede — 수요 검증 시 차별점 | med-high |
| Content-hash dedup / 멱등성 | 이미 — 서비스 + DB 제약으로 강제(LOCAL-9) | 인큐번트가 덧붙이는 활성 pain(S10) | 없음 — 강점 | strengthen framing: 1급 "junk 필터" capability로 드러내기 | high |
| Temporal / non-destructive 버전관리 | 이미(부분) — snapshotVersion + lineage(LOCAL-9) | memory framework 전반에서 요청되고 open(S9) | 버전관리 존재; 시점 조회 표면은 없음 | strengthen: 기존 스냅샷 위에 "as-of version/time" 조회 시맨틱 추가 | med-high |
| Provenance / query 시 citation | 부분 — lineage 저장, lookup에서 반환하나 citation으로 framing 안 됨(LOCAL-8) | 1급 retrieval 출력으로 요청(S12) | 검색 응답에 citation으로 노출 안 됨 | strengthen: 검색 hit payload에 lineage/source ref 포함 | med-high |
| Conflict / contradiction / supersession | 부분 — embedding conflict guard 있음; 새 hash→새 버전이나 diff/supersede 시맨틱 없음(LOCAL-9) | cognee/mem0에서 우선순위화 중(S11) | 구조적 diff/supersession 없음 | diff 계층으로 defer: companion GUI diff 작업과 짝 | med |
| task-graph/스냅샷의 구조적 diff/merge | 없음(서버 측); companion GUI는 별도 | 실제로 원해짐; content-hash identity가 다른 곳의 missing piece; DAG엔 niche(S15, S16, S19) | identity-keyed diff의 서버 지원 없음 | add(설계 주도): content-hash 기반 version/diff 조회 지원 노출; 휘발 필드 무시 | med-high |
| Retrieval 평가 하네스 | 없음 | 재현 가능 eval이 미해결 credibility gap(S13) | 검색 품질 측정 수단 없음 | add(소규모): 검색 변경을 지키는 고정 corpus recall@k 하네스 | med-high |
| Multi-embedding-set 비교 | 이미 — model/version/dimension/metric별 embedding_sets(LOCAL-6) | 점진 마이그레이션용 named vector / multi-column(S17) | 설계 존재; 성능 조회는 ANN 필요 | strengthen(ANN 이후): set별 인덱싱 | med |
| Batched bulk insert | 부분 — saveAll이 하나씩 INSERT(LOCAL-9, S20) | bulk ingestion 표준 | 처리량 상한 | strengthen: multi-row insert, 어댑터 국한 | med |
| 관측성(metrics/tracing) | 없음 — actuator health만(LOCAL-5, S23) | 표준 운영 기대 | 성능 주장 전 metrics 없음 | strengthen: actuator 확대 + Micrometer | med-high |
| task-graph→document 링크 | 위험 — document_id 항상 null(LOCAL-9) | 해당 없음(내부 정확성) | 깨진 lineage join | fix_foundation: 링크 저장 | high |
| 인증 / 접근 제어 | 부분 — 단일 local token, 빈 값이면 개방(LOCAL scan) | 멀티유저/OAuth는 명시적 non-goal(LOCAL-2) | MVP엔 gap 아님 | 지금은 not relevant; 로컬 넘어 배포 시에만 재검토 | high |
| 임베딩 생성 / RAG 응답 / agent / 웹 UI | 설계상 없음(LOCAL-2 non-goal) | 인큐번트엔 존재 | 의도적 경계 | reject: 범위 밖 유지; 제품의 정의적 제약 | high |
| 대체 검색 백엔드(OpenSearch/ES) | 없음 — 빈 seam(LOCAL scan) | 명시된 future 방향(LOCAL-2) | 어댑터 없음 | defer: 큰 vertical; Postgres 검색을 최대화한 뒤 | med |

## 읽는 법

- 지키고 알릴 강점: content-hash 멱등성/dedup(S10), lineage + 스냅샷 버전관리(S9), multi-embedding-set 설계(S17), "서버는 임베딩을 생성하지 않는다" 경계(S14). 모두 on-thesis이며 이미 구축됨.
- 도달할 table-stakes: ranked keyword 검색(S7), hybrid retrieval(S1), 그리고 어떤 ANN보다 먼저 — 인덱싱 가능한 스키마(S6)와 recall-under-filter 처리(S3).
- 탐색할 차별점(설계 주도, 수요 게이트): lineage 기반 되돌릴 수 있는 forgetting/GC(S8), 시점(as-of) 조회(S9), task-graph의 identity-keyed 구조적 diff(S15). 셋 다 인큐번트가 미루는 영역이나, 수요는 개발자 신호일 뿐 — 큰 투자 전 검증.
- 위를 게이트하는 foundation 수정: keyword FTS 활성화(S7), ANN용 typed-vector 스키마(S6), pagination envelope(S22), task-graph document_id 링크(S21).
