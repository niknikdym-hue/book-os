# CODEX TASK 006 — BOOK MEMORY

**Status:** READY  
**Milestone:** M5 — Book Memory  
**Owner:** BOOK OS Central Brain

## WHY NOW

M0–M4 are accepted and merged. BOOK OS can create a real Business Nonfiction project, generate bounded manuscript DRAFTs, and trace factual Claims through Evidence to normalized Sources. The next critical-path capability is whole-book recall that does not depend on chat memory or one model context window.

## GOAL

Implement one local-first, rebuildable Book Memory vertical:

`current book state → lexical index + semantic index → hybrid query → stable object/revision references`

Known exact phrases and known semantic paraphrases must be retrievable across a representative full book, while stale/non-current revisions are excluded from default current-book retrieval.

## BASELINE / AUTHORITY

Read current `main`, then:

- `BOOK_MEMORY_v0.1.md`;
- `CORE_ONTOLOGY.md`;
- `TECHNICAL_ARCHITECTURE_v0.1.md`;
- `IMPLEMENTATION_ROADMAP_v0.1.md`;
- `SECURITY_AVAILABILITY_v0.1.md`;
- `MODEL_GATEWAY_v0.1.md`;
- `TASK_EXECUTION_PROTOCOL_v0.1.md`;
- `PROJECT_STATE.md`;
- this contract.

Required prior milestone: Task 005 / M4 ACCEPTED AND MERGED.

Normal CI external/model/embedding calls = 0. Paid calls = 0.

## ARCHITECTURAL RULE

Book Memory is **derived state, never authority**.

Canonical Book/Chapter Contracts, Claims, Sources, manuscript revisions and Authority Protocol history remain in their existing canonical tables. FTS rows, embedding vectors, summaries and retrieval caches may be deleted and rebuilt without changing book authority.

## IN SCOPE

### A. Persistence / migration `0006`

Add only rebuildable M5 persistence required for:

- normalized memory documents referencing stable object IDs and exact revision IDs/hashes;
- SQLite FTS5 lexical index;
- versioned embedding records;
- embedding/index configuration metadata and rebuild state;
- stale/invalidation markers or equivalent deterministic state.

Every indexed record must retain enough identity to return:

- book ID;
- object kind;
- stable object/unit ID;
- chapter ID when applicable;
- exact revision ID + revision hash;
- authority/currentness state;
- content hash;
- index/embedding configuration version.

Do not duplicate canonical manuscript/Claim/Contract content as a new authority layer.

### B. Indexed object set for M5

Index these bounded sources:

1. current ManuscriptUnit heads;
2. current Book Contract;
3. current Chapter Contracts;
4. current Claim records from M4.

Source/Evidence metadata may be returned through graph links for fact-check context, but do not build a general knowledge graph/vector corpus in M5.

### C. Lexical memory — SQLite FTS5

Implement a `LexicalIndex` interface/service using SQLite FTS5.

Required behavior:

- exact word/phrase search;
- prefix/term search supported by FTS5;
- BM25-style rank;
- project/chapter/object-kind filters;
- stable result references to exact revisions;
- deterministic rebuild from canonical current state.

FTS entries must be removed/invalidated when their referenced current revision changes.

### D. Semantic memory — local exact cosine

Implement a provider-neutral `EmbeddingGateway` / adapter interface and `SemanticIndex` interface.

v0.1 storage/search rules:

- vectors are stored locally with provider/model/version/configuration metadata;
- vector dimension is validated;
- exact cosine similarity is computed locally with NumPy;
- do not add a remote vector database;
- do not add LanceDB/sqlite-vec/ANN as a required dependency in M5;
- one semantic query never silently mixes vectors produced by incompatible embedding configurations.

### E. Embedding adapters

Provide:

1. deterministic fake embedding adapter for all normal CI and reproducible semantic retrieval tests;
2. OpenAI embeddings development/benchmark adapter behind the provider-neutral interface, using `httpx` + existing `SecretStore`/macOS Keychain boundary.

OpenAI adapter constraints:

- development/benchmark lane only;
- model explicitly configured, not silently hard-coded as product authority;
- secret never enters React, SQLite content/provenance, logs or API response;
- mocked HTTP contract tests only in normal CI;
- no live/paid calls in normal CI;
- no Russia-ready claim.

Do not implement Yandex/GigaChat embedding routing in M5; that belongs to the later regional provider milestone unless a separate task explicitly changes the sequence.

### F. Current / non-current isolation

Default Book Memory query scope is `CURRENT`.

For default current-book retrieval:

- ManuscriptUnit result revision must still match that unit's current `authority_heads` revision ID/hash;
- Book/Chapter Contract result must match current project authority reference/head;
- Claim result must match the current Claim record and exact manuscript revision reference;
- `SUPERSEDED`/stale/non-current historical revisions must not appear.

An explicit `HISTORY`/diagnostic mode may include historical/non-current records, but every such result must be visibly marked non-current. Proposed/experimental/history content can never leak into default current retrieval.

### G. Invalidation / rebuild

Implement deterministic invalidation.

At minimum:

- manuscript revision/hash change invalidates lexical + semantic entries for the old revision;
- current Contract revision change invalidates its prior entry;
- Claim edit/rebinding invalidates its prior entry;
- embedding provider/model/config change requires semantic rebuild for the affected scope;
- failed embedding/index operations leave canonical authority untouched and are observable/retryable;
- a full index rebuild reconstructs the same logical current document set from canonical state.

### H. Hybrid retrieval

Implement one deterministic hybrid query service combining:

- lexical rank;
- semantic similarity;
- graph filters (project/chapter/object kind/currentness);
- deterministic fusion/reranking such as weighted reciprocal-rank fusion or another documented stable rule.

Return result objects with:

- stable object/unit ID;
- exact revision ID/hash;
- object kind/chapter;
- visible current/non-current state;
- lexical score/rank when present;
- semantic score/rank when present;
- fused score/rank;
- bounded text/snippet required to identify the match.

Retrieval results are context references, not new authority.

### I. Minimal authenticated API + desktop UI

Expose minimal local authenticated operations to:

- inspect Book Memory index status/configuration;
- rebuild/synchronize current index;
- run lexical search;
- run semantic search;
- run hybrid search;
- filter by chapter/object kind;
- inspect stable result references and currentness.

Desktop adds one bounded Book Memory panel/workspace:

- query;
- `Lexical | Semantic | Hybrid` mode;
- optional chapter/object-kind filters;
- visible index/model version;
- Rebuild/Sync control;
- ranked results with stable revision references/current state.

No general chatbot, RAG agent, editor workflow or autonomous tool execution in M5.

### J. Required memory evals/tests

Normal tests must prove:

1. exact phrase retrieval finds the known unit;
2. lexical chapter/object-kind filters work;
3. a deterministic fake-embedding semantic paraphrase retrieves the intended unit above unrelated units;
4. hybrid retrieval recovers a target supported by either/both channels and returns deterministic ordering;
5. stale manuscript revision disappears from default current retrieval after authority/current-head change and replacement is indexed;
6. non-current/historical content cannot leak into default `CURRENT` scope;
7. explicit history mode visibly marks non-current results;
8. Contract replacement invalidates prior Contract index entry;
9. Claim edit/rebinding invalidates prior Claim entry;
10. embedding model/config change cannot silently reuse/mix incompatible vectors;
11. index rebuild is idempotent for unchanged canonical state;
12. failed fake embedding run does not mutate canonical authority;
13. OpenAI embeddings adapter is HTTP-mocked and secret-safe;
14. API authentication boundary remains intact;
15. desktop component test covers Rebuild → Hybrid query → stable current result reference;
16. representative-book benchmark exercises at least 2,000 indexed retrieval documents and records semantic/hybrid latency without remote calls; exact local similarity must remain comfortably interactive on CI-class hardware (hard failure threshold: 2.0 seconds for one 2,000-document semantic query after vectors are already indexed).

### K. Backup/regression

Advance schema compatibility to `0006` while preserving restore/migrate-forward behavior from supported older backups.

M0–M4 regressions remain green.

## STRICT OUT OF SCOPE

- remote vector database;
- ANN/vector infrastructure dependency;
- autonomous RAG/chat agent;
- automatic whole-book summarization as authority;
- M6 Developmental/Literary/Fact editorial workflows;
- BookBench;
- Yandex/GigaChat Russia provider lane;
- Literary Master/export/audio handoff;
- cloud/accounts/billing/sync;
- training/fine-tuning;
- cross-book/private-corpus indexing.

## REQUIRED ACCEPTANCE

1. Fresh DB migrates `0001→0006`; existing M4 DB upgrades to M5.
2. FTS5 exact phrase retrieval passes.
3. Lexical result returns exact stable object/unit + revision ID/hash.
4. Fake semantic paraphrase retrieval passes with exact local cosine.
5. Semantic records persist provider/model/config/dimension/revision identity.
6. Hybrid ranking is deterministic and test-covered.
7. Default retrieval contains only valid current references.
8. Stale/non-current revision invalidation passes.
9. Explicit history retrieval cannot masquerade as current.
10. Embedding config change requires rebuild/no mixed-vector query.
11. Rebuild is deterministic/idempotent for unchanged canonical state.
12. OpenAI embedding adapter uses mocked HTTP only in normal CI and secrets do not enter returned/persisted content.
13. Representative 2,000-document exact semantic query meets the 2.0s CI threshold after indexing.
14. Authenticated API + Book Memory desktop test pass.
15. Python Ruff/mypy/pytest green.
16. TypeScript lint/type/test/build green.
17. Rust cargo test/check green.
18. secret/dependency scans green.
19. external/model/embedding calls = 0 and paid calls = 0 in normal CI.
20. no M6+ scope.

## STOP CONDITIONS

Stop and surface a Central Brain/Owner decision rather than broadening scope if implementation would require:

- mandatory remote vector infrastructure;
- a paid embedding subscription for normal tests/product bootstrap;
- sending manuscript content to an unapproved provider by default;
- weakening current/non-current isolation;
- making embeddings or summaries authority;
- cloud ownership of manuscript state;
- editorial M6 behavior to make M5 work.

## UNLOCKS NEXT

Central Brain ACCEPT of M5 unlocks M6 — Editorial Workflows.

Do not start M6 before M5 acceptance/merge.
