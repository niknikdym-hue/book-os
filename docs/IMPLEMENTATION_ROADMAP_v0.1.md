# BOOK OS — IMPLEMENTATION ROADMAP v0.1

**Status:** ACCEPTED IMPLEMENTATION SEQUENCE  
**Version:** 0.1.0  
**Date:** 2026-08-22

## 1. Principle

Implement vertical authority-bearing slices, not a giant agent platform. Every milestone must produce a testable product capability and preserve recovery/traceability.

## 2. Milestone 0 — Repository baseline and executable skeleton

### Deliver

- design/authority docs committed to `main`;
- Tauri 2 + React/TypeScript desktop skeleton;
- Python 3.12 local core sidecar;
- local authenticated health endpoint;
- SQLite migration infrastructure;
- CI for lint/type/unit/build smoke;
- no paid API calls.

### Acceptance

- fresh clone builds/runs on Owner's Mac;
- desktop launches sidecar and health check succeeds;
- tests green;
- app binds local core only to loopback;
- no secrets committed;
- `PROJECT_STATE.md` points to exact accepted HEAD.

## 3. Milestone 1 — Authority & persistence engine

### Deliver

- core ontology persistence;
- immutable Revision;
- Authority statuses;
- Decision/Approval/Provenance;
- ChangeProposal with stale-baseline protection;
- transactions/invariants;
- backup/export primitive.

### Acceptance

Automated tests prove:

- approved/locked revision cannot be mutated;
- new accepted proposal supersedes prior authority without deleting history;
- rejected proposal leaves authority unchanged;
- stale proposal cannot be accepted;
- release/revision hashes deterministic;
- restore reproduces state.

## 4. Milestone 2 — Book creation, Book Contract, Architecture, Chapter Contract

### Deliver

- New Book / Business profile/subtype UI;
- BookProject;
- Book Contract editor/approval;
- architecture editor/approval;
- chapters and Chapter Contracts;
- project dashboard/current stage.

### Acceptance

User can create a Business book from zero and reach an approved Chapter Contract without AI or chat memory.

## 5. Milestone 3 — Model Gateway + first controlled drafting

### Deliver

- typed ModelTaskRequest/Run;
- prompt registry;
- SecretStore interface + macOS Keychain adapter;
- OpenAI adapter for Owner development/benchmark lane;
- structured outputs validation;
- cost/usage/run provenance;
- bounded section drafting;
- no direct mutation of approved text.

### Acceptance

A Chapter Contract can produce a DRAFT manuscript unit through a BoundedTask with exact provenance, while tests prove provider adapter isolation and no authority auto-approval.

## 6. Milestone 4 — Research Engine & Claim Ledger

### Deliver

- Source/Claim/Evidence objects;
- OpenAlex/Crossref/Semantic Scholar adapters;
- source normalization/dedup;
- claim verification states;
- evidence pointer/limitations;
- citation hallucination gate;
- research UI.

### Acceptance

A material claim can be traced from manuscript → Claim → Evidence → real Source metadata/location, and an unresolved source candidate cannot become “verified”.

## 7. Milestone 5 — Book Memory

### Deliver

- FTS5 lexical index;
- embedding/version tables;
- local exact semantic search;
- hybrid retrieval;
- current/proposed authority filters;
- invalidation/rebuild;
- retrieval references stable unit/revision IDs.

### Acceptance

Known exact and paraphrased references are found across a representative full book; stale/proposed content cannot leak into current-authority retrieval by default.

## 8. Milestone 6 — Editorial workflows

### Deliver

- Developmental Editor findings;
- Cross-book repetition/contradiction audit;
- Fact Checker;
- Literary Editor;
- Style Guardian;
- Decision Inbox with diff/accept/reject/revise/waive.

### Acceptance

Every material edit is reviewable as a proposal and cannot change authority until accepted.

## 9. Milestone 7 — BookBench v0.1

### Deliver

- deterministic/lexical/statistical checks;
- semantic checks;
- LLM judge/pairwise framework;
- Author Voice Fingerprint baseline;
- AI-prose pathology detector;
- versioned eval datasets/runs;
- model role scorecards.

### Acceptance

BookBench runs against exact revisions, produces actionable findings, and regression tests compare at least two model/configurations on representative editorial tasks.

## 10. Milestone 8 — Russia/no-VPN provider lane

### Deliver

- region/provider policy engine;
- Yandex AI Studio adapter;
- GigaChat adapter;
- provider capability matrix;
- BookBench evaluation against critical roles;
- fallback/unavailable UX.

### Acceptance

At least one region-compliant route meets defined minimum quality for the core product tasks required for the Russia-ready claim; no VPN/personal foreign AI subscription is required.

If no available model passes a critical Writer/Editor threshold, the milestone reports a product-quality blocker rather than silently lowering the bar. Self-hosted/open-weight fallback may then be evaluated.

## 11. Milestone 9 — Literary Master and exports

### Deliver

- final release gate;
- immutable Literary Master manifest;
- checksums;
- rebuild/export from exact revisions;
- at least human-readable manuscript export (Markdown/DOCX as product need dictates);
- production handoff manifest for Audio Studio.

### Acceptance

Rebuilding the same Literary Master produces identical ordered authority content/checksums, and derivative export cannot mutate the master.

## 12. Milestone 10 — Real-book pilot

Use a real new Business Nonfiction book.

Run full path:

`Idea → Literary Master`.

Collect:

- defects found;
- edits proposed/accepted/rejected;
- human reasons;
- cost/time by stage;
- model scorecards;
- workflow friction;
- missed errors;
- BookBench false positives/negatives.

## 13. MVP acceptance

Only after real-book pilot passes the criteria in `PRODUCT_SPEC_v0.1.md` is v0.1 declared successful.

## 14. Post-MVP sequence

1. Existing Manuscript / Materials mode.
2. Stronger regional/self-hosted routing and backend brokerage.
3. Sync/backup and multi-device if needed.
4. More Business profile specialization.
5. Additional nonfiction profiles.
6. Private editorial corpus analytics/model training evaluation.
7. Fine-tuning only if real decision data demonstrates benefit.
8. Publisher/team collaboration later.

## 15. Owner / Central Brain / Codex operating loop

### Owner

Product/creative authority; major cost/risk decisions; real user testing; Literary Master.

### Central Brain

Reads current `main`, owns architecture/specification, issues bounded tasks, defines acceptance, reviews Codex evidence and updates authority/state.

### Codex

Implements only the bounded task against exact baseline, runs tests/build/evals and reports exact HEAD/diff/evidence. No silent product decisions.

## 16. Stop conditions requiring Owner decision

Codex/Central Brain must surface an owner decision before proceeding when implementation would:

- change product promise/target user;
- weaken human authority;
- weaken no-VPN/no-personal-subscription requirement;
- expose real manuscripts/editorial corpus publicly;
- create significant new recurring infrastructure cost;
- require accepting a model below agreed quality floor;
- merge BOOK OS and Audio Studio domain authority;
- make one model/provider mandatory.
