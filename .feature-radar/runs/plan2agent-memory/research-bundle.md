# 조사 번들

run_slug: plan2agent-memory
title: Plan2Agent Memory 다음 이터레이션 조사
mode: existing-project
local_project: D:/projects/plan2agent-memory
created_at: 2026-07-06T00:00:00+00:00
status: complete

## 요약

Plan2Agent Memory Server는 P2A 산출물을 위한, 일관되고 잘 테스트되었으며 깔끔하게 계층화된(hexagonal) headless artifact store다. v1-mvp는 자체 readiness review 기준 handoff-ready 상태다: content-hash 멱등성과 스냅샷 버전관리를 서비스와 DB 제약 양쪽에서 강제하고, lineage와 canonical/source ID를 저장하며, 명세와 일치하는 11개 REST 엔드포인트를 노출하고, keyword + pgvector vector 검색을 제공한다 — 이 모두를 임베딩 생성, agent 실행, AI API 호출 없이 수행한다(그 경계는 아키텍처 테스트로 강제됨). 가장 강한 다음 이터레이션은 새 제품 표면이 아니라 **검색 품질과 그것을 게이트하는 기반**이며, 여기에 유망하지만 수요 미검증인 소수의 설계 주도 차별화 베팅을 더한다.

## 로컬 근거 (오늘 존재하는 것)

read-only 스캔으로 검증했고, 4개 핵심 주장은 evidence reviewer가 파일에서 직접 spot-verify:

- **멱등성 & 버전관리**는 실재하며 두 번(서비스 + unique 제약) 강제됨; snapshotVersion은 CTE에서 MAX+1 (`PostgresStoreAdapters.kt:178-215`, `V1__...sql:80-96`).
- **Keyword 검색**은 `lower(col) LIKE '%q%'` 사용 (`PostgresSearchAdapters.kt:357-359,700-704`). GIN `to_tsvector('simple')` 인덱스가 존재하나(`V1__...sql:109-110,281-282`) 어떤 LIKE 형태도 이를 사용 불가라 죽은 무게이며 모든 keyword 쿼리가 순차 스캔. ranking 없음 — score는 정적 CASE 가중치.
- **Vector 검색**은 **untyped `vector` 컬럼**(`V1__...sql:323`) 위 pgvector exact search라, ANN 인덱스가 없고 모든 vector 쿼리가 full scan. `MAX_VECTOR_DIMENSION=2000` guard가 pgvector 인덱스 차원 cap을 우회하나 큰 임베딩도 차단.
- **Multi-embedding-set 설계**(model+dimension+version+metric으로 unique한 `embedding_sets`)가 이미 버전화 임베딩 비교와 점진 마이그레이션을 지원 — 진짜 강점.
- **알려진 내부 버그**: task-graph insert 시 `document_id`가 null로 하드코딩(`PostgresStoreAdapters.kt:328`). 리뷰어가 확인한 중요한 뉘앙스: `sourceDocumentId`가 저장되고(`:329`) artifacts join에서 `COALESCE(tg.source_document_id, d.source_document_id)`(`PostgresSearchAdapters.kt:230`)로 전달되므로 canonical lineage는 생존. 실제의 더 좁은 결함은 task-graph/task 행의 내부 FK null과 파생 `source_path` null.
- **Gap**: pagination 없음(맨 List + limit-only), delete/soft-delete/GC 없음, actuator health 외 관측성 없음, row-by-row bulk insert(`saveAll` 루프).
- **문서**(`product-spec.md:93,97`)가 이미 의도 방향을 명시: HNSW/IVFFlat 인덱스, BM25 ranking, 한국어 analyzer, phrase/highlight, faceted filtering, hybrid retrieval, 기존 포트 seam을 통한 교체 가능 OpenSearch/ES 어댑터. 즉 최고 가치 추천이 팀 자체 로드맵과 상충하지 않고 정렬됨.

## 외부 근거 (비교 대상과 개발자 신호)

두 독립 서브에이전트(reference-discovery, github-signal-scanner)가 같은 그림으로 수렴.

- **포지셔닝**: 이 제품은 소비자 챗봇 memory가 아니라 (a) agent-memory 백엔드(mem0, Letta, Zep/Graphiti, Cognee, Memori, LangMem), (b) vector/RAG substrate(pgvector, pgvectorscale, Supabase Vector, Weaviate, Qdrant, Chroma), (c) artifact/lineage 카탈로그(MLflow, DVC, OpenMetadata, DataHub, lakeFS)의 혼합으로 비교하는 게 맞다. "lineage와 stored-not-generated 임베딩을 갖춘 코딩 에이전트 plan + task graph + run record의 synced REST artifact store"를 정확히 하는 널리 채택된 제품은 없다 — 그 특정 카테고리는 대체로 **whitespace**.
- **Table-stakes**: 튜닝 가능 fusion(RRF이 표준 combiner)을 갖춘 hybrid keyword+vector retrieval은 Supabase, Weaviate, Mem0, Chroma, langchain4j 전반에서 이제 표준. Supabase는 near-copyable tsvector+pgvector hybrid 레시피를 공개. 이는 차별화가 아니라 parity 작업.
- **pgvector 지뢰**(잘 문서화된 고engagement 이슈): filter-then-ANN은 `hnsw.iterative_scan`/`ef_search` 미설정 시 recall을 조용히 낮춤(#259, #761); 2000-dim 인덱스 cap은 큰 임베딩에 `halfvec` cast 필요(#461); native hybrid 연산자가 없어(#941) fusion은 직접 구축. ANN 도입 후에만 문제되지만 설계에 녹여야 함.
- **차별점 신호**(개발자 도구 신호일 뿐): stale memory의 forgetting/decay/GC가 4개 memory framework에서 요청되고 대부분 userland로 미뤄짐; temporal/non-destructive 버전관리("시점 T에 시스템이 무엇을 믿었나")가 요청되고 open; content-hash dedup을 junk 필터로 쓰는 것을 인큐번트가 덧붙임(P2A는 이미 보유); query 시 provenance/citation이 요청됨; 안정적 element identity를 갖춘 구조적 diff/merge가 실제로 원해지고 content-hash identity가 정확히 도움이 되는 지점(nbdime/dolt/DVC/lakeFS가 analog).

## 비교 (로컬 vs 외부)

| 테마 | P2A 오늘 | 비교 대상 기대 | 해석 |
| --- | --- | --- | --- |
| Content-hash 멱등성/dedup | 이미 강제 | 인큐번트가 덧붙임 | 드러낼 강점 |
| Lineage + 스냅샷 버전관리 | 저장됨 | 요청되나 자주 부재 | 강점; as-of 조회 표면 추가 |
| Multi-embedding-set 마이그레이션 | 설계됨 | named vector / multi-column | 강점; ANN 있어야 빠름 |
| Ranked keyword 검색 | LIKE, ranking 없음 | BM25/tsvector 표준 | 수정(인덱스 이미 존재) |
| Hybrid retrieval | 부재 | table-stakes(RRF) | parity 도달 |
| ANN vector 인덱스 | 부재(untyped 컬럼) | HNSW/IVFFlat/DiskANN 표준 | foundation 재설계 |
| Filter 하 recall | 잠재(오늘 exact scan) | pgvector는 iterative_scan 필요 | ANN과 함께 설계 |
| Delete/GC/forgetting | 부재 | 요청되나 대부분 미해결 | 차별화 베팅(수요 게이트) |
| task-graph 구조적 diff | 서버에 content-hash identity 있음; GUI 별도 | 원해짐; DAG엔 niche | 차별화 베팅(수요 게이트) |
| Auth/멀티유저, 임베딩 생성, agent, 웹 UI | 설계상 없음 | 인큐번트엔 존재 | reject 유지(정의적 경계) |

## 해석

추천 세트는 세 계층으로 깔끔히 나뉜다:

1. **Foundation & 품질 수정**(FTS ranking 활성화, task-graph 내부 링크 수정, pagination envelope, batched insert, 관측성). 로컬 근거 주도이고 저렴하며 대부분 팀 자체 로드맵에 있음. 로컬 단일 leg 정당화 — 품질 작업엔 적절하나 독립적 시장 수요에 의해 뒷받침되지 않으며, 그렇게 라벨됨.
2. **검색 품질 코어**(hybrid RRF → eval 하네스 → ANN 재설계). hybrid는 table-stakes parity. ANN 재설계는 유일하게 진짜 고비용 항목이며 retrieval-eval 하네스와 명시적 pgvector recall-under-filter 처리로 지켜야 함; 따라서 eval 하네스를 그 앞에 배치.
3. **차별화 베팅**(lineage 기반 되돌릴 수 있는 forgetting/GC + as-of 시점 조회; companion git-like GUI를 위한 identity-keyed 구조적 diff). 인큐번트가 미루는 진짜 whitespace를 노리나, 뒷받침 근거가 개발자 도구 신호이지 검증된 구매 수요가 아님. 명시적으로 수요 게이트: 구축 노력 전 실제 코딩 에이전트 팀과 검증.

## 미해결 질문

- 저장 corpus가 한국어/CJK 위주인가? 그렇다면 `to_tsvector('simple')`은 한국어 analyzer 확장 안착 전까지 부분적 keyword-ranking 개선에 그침(rank 1의 기대 효과에 영향).
- task-graph insert 시점에 내부 document UUID가 resolvable한가, 아니면 null이 sync 순서 산물인가? 이는 task-graph 링크 수정이 진짜 저비용인지를 결정.
- 실제 클라이언트가 쓸 임베딩 차원은? >2000(예: 3072)이면 halfvec 경로 강제 및 ANN 설계 변경.
- P2A/코딩 에이전트 사용자에게 서버 측 forgetting/GC와 구조적 task-graph diff의 실제 수요가 있는가, 아니면 인큐번트가 우선순위가 낮아 미루는가? 이는 3계층 투자를 게이트하며 GitHub로는 답할 수 없음.
- 이것이 localhost를 넘어 배포되는가? 그렇다면 "token 빈 값이면 인증 개방" 기본값이 편의가 아니라 실제 리스크가 됨.
