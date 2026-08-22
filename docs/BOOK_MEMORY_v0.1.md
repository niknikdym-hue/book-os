# BOOK OS — BOOK MEMORY v0.1

**Status:** ACCEPTED FOR V0.1 IMPLEMENTATION  
**Version:** 0.1.0  
**Date:** 2026-08-22

## 1. Goal

BOOK OS must remember the book as structured authority and searchable content, not as whatever happens to fit in one model context window.

## 2. Four memory layers

1. **Structured Book Graph** — Book Contract, architecture, concepts, claims, sources, chapter contracts, current authority.
2. **Lexical memory** — exact/phrase/full-text retrieval.
3. **Semantic memory** — meaning-level similarity across manuscript and notes.
4. **Whole-book context** — use entire relevant manuscript when model context/cost allows and the task genuinely benefits.

No single layer replaces the others.

## 3. Stable indexing unit

Semantic/lexical indexes reference `ManuscriptUnit` stable IDs + exact revision IDs.

Index entries are derived artifacts. If the canonical text changes, affected entries are invalidated/rebuilt.

## 4. v0.1 lexical retrieval

Use SQLite FTS5 with BM25/rank for:

- exact words/phrases;
- repeated phrases;
- names/terms;
- lexical near-duplicates;
- targeted search with chapter/unit filters.

FTS index can be rebuilt from canonical manuscript state.

## 5. v0.1 semantic retrieval

For first-book scale, do not introduce a remote vector database.

Baseline:

- embed bounded manuscript units and selected structured objects;
- store embedding vector + embedding model/version + source revision;
- perform exact cosine similarity locally for the first-book scale;
- expose a `SemanticIndex` interface so implementation can later switch to an embedded ANN engine without changing domain logic.

Rationale: a single nonfiction book is normally only thousands, not billions, of useful retrieval units. Exact local similarity is simpler, reproducible and fast enough for v0.1. It avoids making an alpha extension or remote vector service a core dependency.

If benchmarks show need, preferred future candidates include embedded LanceDB or another stable local index. `sqlite-vec` is intentionally not a hard v0.1 dependency while its current public release remains alpha.

## 6. Hybrid retrieval

A Book Memory query may combine:

- FTS lexical score;
- semantic similarity;
- graph constraints (chapter, concept, claim, status);
- recency/revision authority;
- optional reranker score.

Retrieval result always returns stable IDs/revisions so a model/editor can cite its context back to the book.

## 7. Retrieval policies by task

### Drafting

Prefer Book Contract + Chapter Contract + relevant research + nearby chapter context + reserved ideas/examples. Add whole-book summary/targeted retrieval as needed.

### Repetition audit

Search all accepted/current manuscript units, not only the active chapter. Combine lexical n-gram detection and semantic similarity/clustering.

### Contradiction audit

Retrieve claims/concepts with potentially conflicting predicates/values across chapters, then run semantic/judge analysis.

### Voice/style

Compare target passage against approved Style Profile and representative accepted samples across the book.

### Fact check

Retrieve the Claim object and Evidence/Source records; manuscript retrieval alone is insufficient.

## 8. Memory correctness rules

- only exact/current authority revisions are treated as authoritative unless task explicitly requests history;
- proposed/experimental text is clearly marked and not mixed into current manuscript retrieval by default;
- embeddings are versioned by model/configuration;
- changing embedding model triggers rebuild, not silent mixed-vector use;
- retrieval failures are observable and testable;
- Book Memory cannot invent missing content.

## 9. Book summaries

Hierarchical summaries may be generated as **derived caches**, never as source of truth:

`Text Block → Section summary → Chapter summary → Whole-book map`.

Each summary stores input revision hashes and becomes stale when any referenced authority changes.

## 10. Required memory evals

v0.1 must test:

- exact phrase retrieval;
- known semantic paraphrase retrieval;
- chapter/authority filtering;
- stale-index invalidation;
- current-vs-proposed isolation;
- repeated-idea recall;
- contradiction candidate recall;
- latency on a representative full book.

## 11. Current technology notes

SQLite FTS5 is an official full-text search module with phrase/prefix/NEAR/boolean queries and BM25-style ranking. LanceDB OSS is currently documented as an open-source embedded retrieval library suitable for local search. These support the local-first strategy without binding BOOK OS to a remote vector database.
