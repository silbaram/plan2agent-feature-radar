# 로컬 프로젝트 스캔

run_slug: plan2agent-memory
title: Plan2Agent Memory 다음 이터레이션 조사
mode: existing-project
local_project: D:/projects/plan2agent-memory
created_at: 2026-07-06T00:00:00+00:00
status: complete

## 제품 목적 & 런타임

Plan2Agent의 canonical 보조 artifact store 역할을 하는 headless Kotlin/Spring Boot REST 서비스. 로컬 md/json 파일이 원본으로 유지되고, 서버는 canonical ID, lineage, content hash, 관계, keyword/vector 검색 인덱스를 보관한다. 임베딩 생성 없음, 에이전트 실행 없음, AI API 호출 없음 (`README.md:3-5`, `product-spec.md:36-42`).

- Kotlin 2.2.21, Spring Boot 4.1.0, Java 21 toolchain (`build.gradle.kts:4-21`), Gradle wrapper 9.1.0 (`gradle/wrapper/gradle-wrapper.properties:3`).
- 순수 JDBC (`spring-boot-starter-jdbc`, JPA 아님), Flyway, Actuator, Jackson-Kotlin; runtime PostgreSQL 드라이버 (`build.gradle.kts:24-37`).
- 실행: `docker compose up -d postgres` 후 `./gradlew bootRun`, 포트 8080 (`README.md:20-48`, `application.yml:31-33`).
- 사소한 이미지 불일치: compose는 `pgvector/pgvector:pg17` (`compose.yaml:3`), Testcontainers/README는 `pg16` (`ApiIntegrationTest.kt:361`, `README.md:63`).
- 진입점 `Plan2AgentMemoryApplication.kt:7-13`.

## 아키텍처 & 계층

Hexagonal(ports/adapters), 아키텍처 테스트로 강제.

- `domain/` — 순수 모델/value object (`Models.kt`, `Identifiers.kt`, `ArtifactType.kt`, `SourceReference.kt`).
- `application/usecase/` — `WriteUseCaseService`, `ReadUseCaseService`, `UseCaseModels`.
- `application/port/in|out/` — 인바운드 use-case 포트와 아웃바운드 store/query/search 포트 (`StorePorts.kt`, `QueryPorts.kt`, `UseCasePorts.kt`).
- `adapter/in/rest/` — `WriteRestController`, `QueryRestController`, `HealthRestController`, DTO/mapper/validation, `RestErrors.kt`.
- `adapter/out/postgres/` — JDBC store & search 어댑터 + `PostgresJsonSupport`.
- `adapter/out/security/` — `LocalTokenAuthInterceptor`.
- `adapter/out/search/` — 비어 있음(`.gitkeep`), 향후 OpenSearch/ES 어댑터를 위한 예약 seam (`product-spec.md:97`).
- `CoreArchitectureTest.kt:13-55` — application/domain이 Spring MVC/JDBC/java.sql/pgvector/어댑터를 import하거나, main source 또는 build.gradle.kts에 AI-provider 문자열이 나타나면 빌드를 실패시킴.

## Capability 인벤토리

| capability | 상태 | 로컬 근거 path:line | 비고 |
| --- | --- | --- | --- |
| 11개 REST 엔드포인트가 README와 일치 | 구현됨 | `WriteRestController.kt:29-65`, `QueryRestController.kt:20-93` | write 7 + artifacts + keyword + vector + api/health; actuator/health는 actuator 경유. 미문서화/누락 라우트 없음. |
| Project/iteration/document/task-graph/task/run upsert | 구현됨 | `WriteUseCaseServices.kt:57-207` | 엔티티별 관계 + canonical-id/source-ref 검증. |
| Content-hash 멱등성 & 스냅샷 버전관리 | 구현됨 | `WriteUseCaseServices.kt:277-300`, `PostgresStoreAdapters.kt:178-215`, `V1__...sql:80-96` | 같은 hash → 기존 반환; 같은 scope에 새 hash → 새 snapshotVersion; DB unique 제약이 뒷받침. |
| Bulk chunk + optional embedding write | 구현됨 | `WriteUseCaseServices.kt:210-275`, `UseCaseModels.kt:122-126` | embeddingSet+embedding은 함께 제공해야 함; 결정론적 chunk-embedding id. |
| Embedding-set / chunk-embedding conflict guard | 구현됨 | `PostgresRunChunkAdapters.kt:347-359,489-507` | 같은 (chunk,set)에 다른 vector/hash → 409; 동일 → 멱등. |
| 관계형 artifact lookup | 구현됨 | `PostgresSearchAdapters.kt:39-318` | AND-filter + limit을 갖춘 7-branch UNION ALL CTE. |
| Keyword 검색 (결정론적 lexical) | 구현됨 | `PostgresSearchAdapters.kt:328-441` | `lower(col) LIKE '%q%'`, chunk.content(3.0)/path(1.5)/type(1.0), document.content(2.0); opaque score; tie-break score/version/timestamp/chunkIndex. |
| Vector 검색 (pgvector exact) | 구현됨 | `PostgresSearchAdapters.kt:451-524,733-745` | Cosine/L2/IP; same-set scoping; 저장된 set 대비 dimension 검증 (`:526-546`). |
| PROPOSAL을 1급 artifact로 | 구현됨 | `ArtifactType.kt:10`, `ApiIntegrationTest.kt:182-247` | document처럼 저장/조회/검색. |
| Local token 인증 | 구현됨 | `LocalTokenAuthInterceptor.kt:23-31,55-59` | constant-time 비교; health 제외; token 빈 값이면 전면 개방. |
| Path 정규화 | 구현됨 | `WriteUseCaseServices.kt:394-398` | trim, `\`→`/`, `//` 축약, `./` 제거; raw path 보존. |
| Pagination (offset/cursor/total) | 없음 | `QueryRestController.kt:37,69`, `UseCaseModels.kt:144,160,187` | `limit`만 존재(기본 50/20); 응답이 맨 List, total/next cursor 없음. |
| Delete / soft-delete / stale artifact GC | 없음 | (DELETE 라우트 없음; `StorePorts.kt:22-79`) | `deleted_at` 없음, FK cascade만. 저장소가 무한 증가. |
| ANN vector index (HNSW/IVFFlat) | 없음 | `V1__...sql:319-339` | `embedding vector` 컬럼이 untyped/무제한 차원 → ANN 불가 → exact full scan만. |
| Full-text ranked keyword 검색 | 부분/위험 | `V1__...sql:109-110,281-282` vs `PostgresSearchAdapters.kt:357-359` | GIN `to_tsvector('simple')` 인덱스가 존재하나 미사용 — leading-wildcard `LIKE`는 사용 불가 → 순차 스캔 + 죽은 인덱스. |
| task-graph→document canonical 링크 저장 | 위험 | `PostgresStoreAdapters.kt:328` | insert 시 `document_id`가 항상 null; artifacts CTE의 LEFT JOIN(`PostgresSearchAdapters.kt:215`)이 항상 null → task-graph/task source_path 공백. |
| 관측성(metrics/tracing/req-log) | 없음 | `application.yml:11-15` | Actuator 노출이 health로 한정; Micrometer/Prometheus/tracing 없음. |
| Bean Validation 배선 | 부분 | `build.gradle.kts:25` | starter-validation은 있으나 `@Valid`/JSR-380 없음; 모든 검증이 수동 `require()`. |

## 영속성 & 검색 내부

- 마이그레이션: Flyway `V1__create_artifact_store_schema.sql` (전체 스키마, `CREATE EXTENSION vector`) + `V2__allow_document_source_snapshots.sql` (document unique index → NULLS NOT DISTINCT). 9개 테이블: projects, iterations, documents, task_graphs, tasks, runs, document_chunks, embedding_sets, chunk_embeddings.
- 멱등성은 서비스(`WriteUseCaseServices.kt:277-308`)와 DB 제약(`V1:80-96,264,332-333`) 양쪽에서 강제; snapshotVersion = CTE에서 MAX+1 (`PostgresStoreAdapters.kt:191-198`).
- 임베딩 모델: `embedding_sets`는 model+dimension+version+metric으로 unique (`V1:307-313`); `chunk_embeddings.embedding vector` (`V1:319-334`); 새 model/version = 새 set으로 점진 마이그레이션 (`README.md:428-434`); `MAX_VECTOR_DIMENSION = 2000` guard (`PostgresRunChunkAdapters.kt:246,605`).
- Keyword scoring: 정적 CASE 가중치, opaque score, tie-break 순서 (`PostgresSearchAdapters.kt:435`); LIKE는 `%_\` escape (`:700-704`).
- Vector scoring: metric별 distance 연산자; IP는 `GREATEST(0,(x<#>q)*-1)` clamp (`:737`); 저장 set 대비 요청 dimension 검증 (`:526-546`).
- Row-by-row bulk: `saveAll`이 `save()`를 하나씩 INSERT로 매핑 (`PostgresStoreAdapters.kt:401-402`, `PostgresRunChunkAdapters.kt:160-161,332-333`) — batch 아님.
- 메타데이터는 예약 `p2a.*` 키의 jsonb sidecar (`PostgresJsonSupport.kt:56-114`).

## 테스트 커버리지 & 주목할 gap

테스트 클래스 9개; `@Disabled`/`@Ignore` 없음, src에 TODO/FIXME 없음(grep clean).

- 아키텍처 guardrail: `CoreArchitectureTest.kt` (core 격리 + no-AI-provider scan).
- 단위(mocked ports): `ReadUseCaseServiceTest.kt`, `WriteUseCaseServiceTest.kt`, `QueryRestControllerTest.kt`, `PostgresJsonSupportTest.kt`, `LocalTokenAuthInterceptorTest.kt`.
- Testcontainers 통합(pg16): `ApiIntegrationTest.kt` (멱등 sync flow, proposal flow, auth/validation/not-found/conflict error, compose+actuator health), `PostgresStorageIntegrationTest.kt`, `PostgresSearchIntegrationTest.kt`.
- 미검증/얇음: pagination(부재), 동시 write/optimistic locking, 대용량 batch/검색 성능, ANN 동작, 항상 null인 task-graph document_id 링크. load/관측성 테스트 없음.

## 문서에 명시된 방향 & 알려진 gap

- `READINESS_REVIEW.md:13-57` (task-17, 2026-06-29): v1-mvp handoff-ready; 전체 test suite, typecheck, architecture/no-AI/no-UI scan, runtime-dependency guard, Docker Compose health smoke 모두 통과. 유일한 잔여 노트: 환경별 `docker-compose` vs `docker compose` 명명 차이.
- `product-spec.md:36-42,122-125` non-goal/future: 멀티유저 auth/OAuth, 클라우드 배포, queue ingestion, 임베딩 생성, RAG 응답 생성, auto-apply, 웹 UI 모두 MVP 범위 밖. 명시된 향후 방향: (1) pgvector HNSW/IVFFlat 인덱스가 "available"이나 미사용 (`:93`); (2) keyword 검색은 BM25 ranking, 한국어 analyzer, phrase 검색, highlight/snippet, faceted filtering, recency boost, hybrid retrieval로 진화 예정이며, 기존 KeywordSearchPort/VectorSearchPort seam을 통해 OpenSearch/ES 어댑터로 교체 가능하게 설계 (`:97`).
- `docs/package-structure-review.md:57-78`: 주요 유지보수 냄새 — WriteRestDtos.kt/QueryRestDtos.kt가 DTO+mapper+validation을 혼재; 분리 권장. blocking risk 낮음(아키텍처 테스트가 core 보호), maintainability risk 중간.
- Stale P2A 부기(코드 gap 아님): `.plan2agent/.../task-graph.json:307-412`와 `status.md:51`이 task 13-17을 여전히 `todo`로 표시하나, 해당 테스트/README/readiness review는 존재하고 통과. 계획 원장이 최신이 아님; 코드는 v1-mvp 완료로 간주.

## Foundation risk (기능 추가 전 수정)

1. 현재 설계로는 keyword 검색이 확장 불가 — leading-wildcard LIKE가 GIN tsvector 인덱스를 우회(`PostgresSearchAdapters.kt:357-359` vs `V1:109-110,281-282`); 순차 스캔이 선형 증가, FTS 인덱스는 죽은 무게. 가장 가치 높고 파장 낮은 수정.
2. Untyped `vector` 컬럼이 ANN 차단 — `embedding vector`에 고정 차원 없음(`V1:323`) → HNSW/IVFFlat 불가 → 모든 vector 쿼리가 exact full scan. ANN 로드맵은 스키마 재설계가 선행되어야 함.
3. task-graph→document canonical 링크 유실 — `document_id`가 null로 하드코딩(`PostgresStoreAdapters.kt:328`)되어 downstream doc join이 항상 null(`PostgresSearchAdapters.kt:215,245`). 수정 저렴, lineage 혼동 예방.
4. Pagination 계약 없음 — 맨 List + limit-only(`QueryRestController.kt`, `UseCaseModels.kt:144,160,187`). 나중에 paging 추가는 응답 형태 파괴 변경; 지금 envelope 결정.
5. Delete/GC 경로 없음 — 저장소가 증가만; sync 클라이언트가 superseded 스냅샷을 서버 측에서 prune 불가.
6. token 빈 값일 때 인증 전면 개방(`LocalTokenAuthInterceptor.kt:23`) — 로컬은 안전, 노출 시 배포 footgun.
7. Row-by-row bulk insert(`saveAll` 루프) — 정확성은 문제없으나 대용량 sync batch의 처리량 상한.

## 고도화 레버리지 지점 (저렴 → 비쌈)

- 저렴 / 어댑터 메서드 하나에 국한:
  - Ranked keyword 관련성(BM25류): `PostgresKeywordSearchAdapter.search`에서 LIKE를 `to_tsvector`/`plainto_tsquery` + `ts_rank`로 교체(`PostgresSearchAdapters.kt:344-441`); GIN 인덱스 이미 존재(`V1:109-110,281-282`); public score는 이미 backend-opaque 선언(`README.md:370`).
  - Batched bulk insert: `saveAll` 루프를 multi-row insert로 전환; 어댑터에 국한, 계약 변경 없음.
  - 기본 관측성: actuator가 이미 classpath에 있음; 노출 확대(`application.yml:11-15`) + Micrometer counter/timer.
  - DTO/mapper/validation 분리: `docs/package-structure-review.md`에서 이미 범위화; 순수 리팩터.
- 중간:
  - Hybrid keyword+vector: 두 포트 모두 존재하며 ReadUseCaseService에서 함께 오케스트레이션(`ReadUseCaseServices.kt:16-54`); 둘을 융합하는 hybrid use case 추가. 비어 있는 `adapter/out/search/` seam이 바로 이 확장을 의도.
  - Pagination: 쿼리가 이미 포트/어댑터로 limit을 전달; keyset/offset + 응답 envelope 추가. 계약 변경, 스키마 변경 없음.
- 비쌈 / 스키마 수준:
  - ANN 인덱싱: 고정 차원 vector 컬럼 + 마이그레이션 필요; 현재 단일 untyped vector 테이블이 이를 막음.
  - Soft-delete / stale-artifact GC: 오늘 delete 표면이 전혀 없음; 엔드포인트, use case, 포트, `deleted_at`, 쿼리 필터를 end-to-end로 추가 필요.
  - 대체 검색 백엔드(OpenSearch/ES): 포트 경계 덕에 아키텍처적으로는 깔끔하나, 어댑터 + 인덱스 sync 구축/운영은 큰 vertical.

정리: v1-mvp는 강력한 멱등성/lineage 보장을 갖춘, 잘 테스트되고 깔끔하게 계층화된 store다. 가장 레버리지가 큰 다음 이터레이션은 검색 품질/성능(FTS 인덱스 활성화; typed-vector 스키마로 ANN 계획)과 pagination, delete/GC 경로이며, 모두 포트/어댑터 seam으로 실현 가능하다. 먼저 고칠 비자명한 foundation 버그: 항상 null인 task-graph document_id 링크.
