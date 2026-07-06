# 소스 후보

run_slug: plan2agent-memory
title: Plan2Agent Memory 다음 이터레이션 조사
mode: existing-project
local_project: D:/projects/plan2agent-memory
created_at: 2026-07-06T00:00:00+00:00
status: complete

## 로컬 소스 (현재 구현의 원본)

| id | source type | path | 관련성 | 신뢰도 |
| --- | --- | --- | --- | --- |
| LOCAL-1 | local_doc | README.md | 제품 정의, 11-엔드포인트 REST 명세, 멱등성/버전관리 규칙 | high |
| LOCAL-2 | local_doc | product-spec.md | non-goal + 명시된 향후 방향(HNSW/IVFFlat, BM25, hybrid, OpenSearch seam) | high |
| LOCAL-3 | local_doc | READINESS_REVIEW.md | v1-mvp handoff 준비 상태 | high |
| LOCAL-4 | local_doc | docs/package-structure-review.md | DTO/mapper/validation 분리 권고 | high |
| LOCAL-5 | local_config | build.gradle.kts | Kotlin 2.2.21, Spring Boot 4.1.0, Java 21, JDBC/Flyway 의존성 | high |
| LOCAL-6 | local_schema | src/.../db/migration/V1__create_artifact_store_schema.sql | 스키마, pgvector 확장, 미사용 GIN FTS 인덱스, untyped vector 컬럼 | high |
| LOCAL-7 | local_api | src/.../adapter/in/rest/*RestController.kt | 구현된 엔드포인트 | high |
| LOCAL-8 | local_file | src/.../adapter/out/postgres/PostgresSearchAdapters.kt | Keyword(LIKE) + vector(pgvector exact) 검색 내부 | high |
| LOCAL-9 | local_file | src/.../adapter/out/postgres/PostgresStoreAdapters.kt | 멱등성, 스냅샷 버전관리, null document_id 버그, row-by-row bulk | high |
| LOCAL-10 | local_test | src/test/.../ApiIntegrationTest.kt | sync/proposal/error/health flow의 Testcontainers 커버리지 | high |

## 외부 소스 — agent-memory 백엔드

| id | source type | url | 관련성 | 신뢰도 |
| --- | --- | --- | --- | --- |
| WEB-1 | github_repository | https://github.com/mem0ai/mem0 | semantic+BM25+entity hybrid retrieval을 갖춘 memory layer | high |
| WEB-2 | github_repository | https://github.com/letta-ai/letta | 계층형 memory; Agent File(.af) 버전관리 agent-state 포맷 | high |
| WEB-3 | github_repository | https://github.com/letta-ai/agent-file | .af serialize/checkpoint/version-control 포맷 (git-like framing) | high |
| WEB-4 | github_repository | https://github.com/getzep/graphiti | temporal knowledge graph, bi-temporal fact validity, provenance | high |
| WEB-5 | github_repository | https://github.com/topoteretes/cognee | graph+vector+relational store with provenance; pgvector 백엔드 | high |
| WEB-6 | github_repository | https://github.com/langchain-ai/langmem | outdated memory의 background consolidation/dedup | high |
| WEB-7 | github_repository | https://github.com/GibsonAI/Memori | SQL-native portable/auditable memory (Postgres 백엔드) | high |

## 외부 소스 — vector / RAG 백엔드

| id | source type | url | 관련성 | 신뢰도 |
| --- | --- | --- | --- | --- |
| WEB-8 | github_repository | https://github.com/pgvector/pgvector | exact retrieval substrate; HNSW/IVFFlat, iterative scan, dim cap | high |
| WEB-9 | github_repository | https://github.com/timescale/pgvectorscale | StreamingDiskANN, binary quantization, filtered vector search | high |
| WEB-10 | official_docs | https://supabase.com/docs/guides/ai/hybrid-search | 튜닝 가능 가중치의 tsvector+pgvector hybrid 레퍼런스(near-copyable) | high |
| WEB-11 | github_repository | https://github.com/run-llama/llama_index | hash 기반 transform caching + docstore dedup/upsert(멱등성 병행) | high |
| WEB-12 | official_docs | https://docs.weaviate.io/weaviate/search/hybrid | BM25F+vector, 튜닝 alpha, RRF/relativeScore fusion | high |
| WEB-13 | github_repository | https://github.com/qdrant/qdrant | payload-filtered ANN, quantization, named vectors(multi-embedding) | high |
| WEB-14 | github_repository | https://github.com/chroma-core/chroma | dense+sparse retrieval + metadata filtering; chroma-mcp | high |

## 외부 소스 — artifact / lineage 카탈로그

| id | source type | url | 관련성 | 신뢰도 |
| --- | --- | --- | --- | --- |
| WEB-15 | official_docs | https://mlflow.org/docs/latest/ml/model-registry/ | run→artifact lineage, version/alias/tag, Postgres store | high |
| WEB-16 | github_repository | https://github.com/iterative/dvc | git-for-data; content-hash 포인터; status/diff/push/pull 청사진 | high |
| WEB-17 | github_repository | https://github.com/open-metadata/OpenMetadata | metadata knowledge graph, column-level lineage, 관계 | high |
| WEB-18 | github_repository | https://github.com/datahub-project/datahub | column-level lineage, data contract, ingestion connector | high |
| WEB-19 | github_repository | https://github.com/treeverse/lakeFS | 스토리지 위 git-like commit/branch/merge/diff; Postgres 메타데이터 | high |

## 외부 소스 — GitHub 개발자 pain 신호 (개발자 도구 신호이며 시장 수요 아님)

| id | source type | url | 신호 | 신뢰도 |
| --- | --- | --- | --- | --- |
| GH-1 | github_issue | https://github.com/getzep/graphiti/issues/1166 | temporal/bi-temporal non-destructive 버전관리 요청 | high |
| GH-2 | github_issue | https://github.com/mem0ai/mem0/issues/4573 | ingest 시 content-hash dedup("97.8% junk") | high |
| GH-3 | github_issue | https://github.com/mem0ai/mem0/issues/5330 | forgetting/decay + contradiction 처리 요청 | high |
| GH-4 | github_issue | https://github.com/letta-ai/letta/issues/3116 | forgetting/GC + provenance/citation 요청 | high |
| GH-5 | github_issue | https://github.com/topoteretes/cognee/issues/3390 | stale memory의 TTL/decay/GC(미해결) | high |
| GH-6 | github_issue | https://github.com/topoteretes/cognee/issues/3699 | conflict/contradiction 감지(진행 중) | high |
| GH-7 | github_issue | https://github.com/topoteretes/cognee/issues/633 | query 시 provenance/citation | med-high |
| GH-8 | github_issue | https://github.com/mem0ai/mem0/issues/2800 | retrieval eval 재현 불가(LOCOMO) | high |
| GH-9 | github_issue | https://github.com/spring-projects/spring-ai/issues/517 | hybrid 검색 약 2년째 미출시 | high |
| GH-10 | github_issue | https://github.com/spring-projects/spring-ai/issues/6524 | 2.0 GA에 portable RerankModel 없음 | high |
| GH-11 | github_issue | https://github.com/langchain4j/langchain4j/issues/4087 | langchain4j는 이미 RRF hybrid 제공(JVM parity 증거) | high |
| GH-12 | github_issue | https://github.com/pgvector/pgvector/issues/259 | filter-then-ANN recall 함정(iterative_scan 0.8.0) | high |
| GH-13 | github_issue | https://github.com/pgvector/pgvector/issues/761 | native metadata-filtered/multicolumn ANN 인덱스 없음(open) | high |
| GH-14 | github_issue | https://github.com/pgvector/pgvector/issues/461 | 2000-dim 인덱스 cap + halfvec 우회 | high |
| GH-15 | github_issue | https://github.com/pgvector/pgvector/issues/941 | native hybrid 연산자 없음(문서 레시피만) | med-high |
| GH-16 | github_issue | https://github.com/jupyter/nbdime/issues/303 | content-aware diff/merge, derived field 무시(analog) | high |
| GH-17 | github_issue | https://github.com/dolthub/dolt/issues/3468 | content-addressed store 위 structural diff/merge conflict UX | high |
| GH-18 | github_issue | https://github.com/benjamine/jsondiffpatch/issues/79 | element-identity + array-move 감지가 어려운 문제 | high |

## 소스 위생 노트

- 모든 GH-* 신호는 개발자 도구 신호(약 4개 OSS 커뮤니티의 반복 엔지니어링 요청)이며, 일반 시장/구매 수요의 근거가 아니다.
- DVC의 canonical repo는 `github.com/iterative/dvc`; 검색에 잡힌 `treeverse/dvc`는 잘못 라벨된 fork(treeverse는 lakeFS org) — 인용하지 않음.
- Motorhead(getmetal/motorhead)는 비활성/아카이브된 것으로 보임 — 살아있는 비교 대상에서 제외.
- getzep/zep OSS는 동결(issue 비활성화); Zep 신호는 Graphiti만으로 대체.
