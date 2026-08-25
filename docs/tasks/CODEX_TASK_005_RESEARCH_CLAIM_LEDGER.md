# CODEX TASK 005 — RESEARCH ENGINE + CLAIM LEDGER

**Status:** READY  
**Milestone:** M4 — Research Engine & Claim Ledger  
**Owner:** BOOK OS Central Brain

## WHY NOW

M0–M3 are accepted and merged. BOOK OS can create a Business Nonfiction book, approve Book/Chapter authority, and generate a bounded manuscript DRAFT with exact model provenance. The next critical-path risk is factual reliability: material claims must be traceable to explicit evidence and real source metadata before later editorial/release gates.

## GOAL

Implement one bounded local-first research vertical:

`ManuscriptUnit revision → Claim → research search candidates → normalized Source → Evidence → verification state`

A source candidate or source record is never proof by itself. A claim becomes `SUPPORTED` or `PARTIALLY_SUPPORTED` only through explicit Evidence linking a real normalized Source and a concrete evidence pointer/limitations record.

## BASELINE / AUTHORITY

Read current `main`, then `CORE_ONTOLOGY.md`, `IMPLEMENTATION_ROADMAP_v0.1.md`, `EDITORIAL_PROTOCOLS_v0.1.md`, `TECHNICAL_ARCHITECTURE_v0.1.md`, `SECURITY_AVAILABILITY_v0.1.md`, and this contract.

Required prior milestone: Task 004 / M3 ACCEPTED AND MERGED.

Normal CI external calls = 0. Paid calls = 0. All provider HTTP tests use mocked transports/fixtures.

## IN SCOPE

### A. Persistence / migration `0005`

Add only M4 persistence needed for:
- stable `claims`;
- exact claim-to-manuscript-revision locations;
- normalized `sources`;
- `source_identifiers` or equivalent canonical identifiers;
- explicit `evidence` relationships;
- optional persisted research-search/candidate metadata if required for auditability.

Claim verification states:
`UNREVIEWED | SUPPORTED | PARTIALLY_SUPPORTED | DISPUTED | UNSUPPORTED | REJECTED`.

Evidence relationships:
`SUPPORTS | PARTIALLY_SUPPORTS | CONTRADICTS | CONTEXT_ONLY`.

### B. Claim ledger service

Implement typed local operations to:
- create/edit a Claim against an exact ManuscriptUnit revision;
- preserve stable `claim_id` while claim metadata changes;
- store materiality, claim type and required evidence level;
- reject links to unknown/stale manuscript revisions;
- list claims by project/chapter/manuscript unit and verification state.

Do not auto-extract claims with an LLM in M4. Human-created claims are enough for the first vertical.

### C. Research adapter interface

Define a provider-neutral scholarly metadata search interface and normalize results from:
- OpenAlex;
- Crossref;
- Semantic Scholar Academic Graph.

Normal tests use mocked HTTP only. No web crawl/full-text scraping framework.

Normalized candidate fields where available:
- provider/provider record ID;
- title;
- authors/organization;
- publication year/date;
- DOI;
- canonical/landing URL;
- publication/container;
- work/source type;
- abstract/summary metadata only when legally/API-provided;
- citation-count metadata when provided;
- provider provenance/raw identifier.

### D. Source normalization / dedup

Canonicalize identifiers deterministically:
1. DOI (case-insensitive normalized DOI) is strongest dedup key;
2. then provider-stable identifiers;
3. URL normalization only as a weaker fallback;
4. title similarity alone must never silently merge two records.

Importing the same DOI from OpenAlex/Crossref/Semantic Scholar must resolve to one stable `Source` with recoverable provider identifiers/provenance.

### E. Candidate ≠ verified source/evidence

Research search results are candidates. The system must not mark a claim supported merely because a candidate exists.

Persist/import a Source only through an explicit user/system action whose semantics are `add source metadata`, not `verify claim`.

### F. Evidence workflow

Allow an Evidence record to link exact Claim + Source and include:
- relationship;
- supporting location/pointer (page/section/URL fragment/bibliographic locator/free-form bounded pointer);
- concise evidence note;
- strength;
- limitations;
- reviewer/actor + timestamp.

Evidence is append-only/history-preserving where material fields change: replacement creates a new record or explicit superseding event, never silently rewrites audit history.

### G. Verification gate

Claim state changes must be deterministic and explicit:
- `SUPPORTED` requires at least one active `SUPPORTS` Evidence with non-empty pointer and no unresolved contradictory evidence marked material;
- `PARTIALLY_SUPPORTED` requires explicit supporting evidence plus recorded limitation;
- `DISPUTED` requires contradictory evidence or explicit reviewer decision;
- `UNSUPPORTED` may be explicit after review/search failure;
- `REJECTED` is a reviewer decision and cannot be set by metadata search alone.

Do not silently infer truth from citation count, source existence or provider rank.

### H. Citation-hallucination gate due at M4

Implement a deterministic check for manuscript/claim citation references used by BOOK OS:
- a referenced DOI/source identifier must resolve to an actual stored Source;
- an Evidence record must point to that Source;
- fabricated/unresolved source identifiers remain visibly unresolved and cannot satisfy the claim gate.

No LLM citation generation in this milestone.

### I. Local API + desktop research UI

Expose minimal authenticated endpoints and native UI for a selected manuscript draft:
- create/list Claims;
- research search query across selected adapter(s);
- inspect normalized candidates;
- import Source metadata;
- add Evidence with pointer/limitations;
- change/recalculate verification state under the deterministic rules;
- visibly show `Source ≠ Evidence ≠ Claim` and unresolved state.

Keep the UI bounded; no full literature-review workspace.

### J. Backup/regression

Advance schema compatibility to `0005` while preserving restores from supported M1–M4 backups and migration-forward behavior.

M0–M3 tests remain green.

## STRICT OUT OF SCOPE

- automatic LLM claim extraction;
- full-text scraping/paywall bypass;
- autonomous browsing agents;
- embeddings/Book Memory;
- developmental/fact/literary editor workflows;
- BookBench;
- Yandex/GigaChat provider lane;
- Literary Master/export;
- accounts/cloud/billing;
- citation-style formatting beyond minimal metadata display.

## REQUIRED ACCEPTANCE

1. Fresh DB migrates `0001→0005`; existing M3 DB upgrades to M4.
2. A Claim attaches to exact ManuscriptUnit revision and survives restart.
3. Unknown/stale revision links are rejected.
4. OpenAlex/Crossref/Semantic Scholar adapters are typed and HTTP-mocked in CI.
5. Same DOI from multiple adapters deduplicates to one Source while preserving provider identifiers.
6. Title-only collision does not silently merge sources.
7. Search candidate alone cannot change claim verification state.
8. Source alone cannot change claim verification state.
9. Evidence requires exact Claim+Source and a non-empty locator/pointer.
10. `SUPPORTED` cannot be set without qualifying Evidence.
11. `PARTIALLY_SUPPORTED` requires an explicit limitation.
12. Contradictory evidence can place claim in `DISPUTED` and is never silently discarded.
13. Unresolved/fabricated DOI/source reference fails the citation-hallucination gate.
14. API authentication boundary remains intact.
15. Desktop test covers Claim → mocked research search → Source import → Evidence → supported/partial visible state.
16. Python Ruff/mypy/pytest green.
17. TypeScript lint/type/test/build green.
18. Rust cargo test/check green.
19. secret/dependency scans green.
20. CI external/model calls = 0; paid calls = 0.
21. No M5+ scope.

## STOP CONDITIONS

Stop and surface a Central Brain/Owner decision rather than broadening scope if implementation would require copyrighted full-text ingestion, paywall circumvention, a paid research API subscription, silent truth inference, AI self-verification, or cloud state ownership.

## UNLOCKS NEXT

Central Brain ACCEPT of M4 unlocks M5 — Book Memory.

Do not start M5 before M4 acceptance/merge.
