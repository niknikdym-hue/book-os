# BOOK OS — PROJECT STATE

**Status:** ACTIVE CHECKPOINT  
**Version:** 1.3.0  
**Date:** 2026-08-26  
**Canonical repository:** `https://github.com/niknikdym-hue/book-os`

## Current phase

**IMPLEMENTATION MILESTONE 6 — TASK 007 READY**

Active contract:

`docs/tasks/CODEX_TASK_007_EDITORIAL_WORKFLOWS.md`

Planned implementation branch:

`brain/task-007-editorial-workflows`

## Accepted authority

- Product/Authority baseline: `BOOK_OS_AUTHORITY.md`
- Product spec: `PRODUCT_SPEC_v0.1.md`
- Core Ontology: `CORE_ONTOLOGY.md` v0.2.0
- Editorial contracts/gates: `EDITORIAL_PROTOCOLS_v0.1.md`
- Model Gateway: `MODEL_GATEWAY_v0.1.md`
- Research/Claim authority: `RESEARCH_AND_CLAIMS_v0.1.md`
- Book Memory authority: `BOOK_MEMORY_v0.1.md`
- Technical Architecture: `TECHNICAL_ARCHITECTURE_v0.1.md`
- Security/availability: `SECURITY_AVAILABILITY_v0.1.md`
- Implementation roadmap: `IMPLEMENTATION_ROADMAP_v0.1.md`
- Execution control: `TASK_EXECUTION_PROTOCOL_v0.1.md`
- Complete recovery map: `DESIGN_INDEX.md`

## Completed milestones

### M0 / Task 001 — ACCEPTED AND MERGED

- PR `#3`
- canonical merge: `b2bbe3dd208e15cbca0420e90c1b4adadab7acda`
- Owner-Mac `Local Core healthy`: PASS
- deterministic sidecar shutdown after normal close + Cmd-Q: PASS

### M1 / Task 002 — ACCEPTED AND MERGED

- PR `#5 — Authority & Persistence Engine`
- canonical merge: `c2cf2e88c81797ff3f67873b1d406ecc7f806e84`
- immutable revisions, Authority statuses, exact-base ChangeProposal, Decision/Approval/Provenance, transactional stale-baseline protection and WAL-safe backup/restore accepted.

### M2 / Task 003 — ACCEPTED AND MERGED

- PR `#6 — Book Creation, Contracts & Architecture`
- accepted source HEAD: `182b8e45ae7092fd2655ee61e42126af4cac1542`
- canonical merge: `5bd6c1af5dd1b502696e359c813f8e6544919cb8`
- final CI `32882543129`: SUCCESS
- accepted native product path:
  `Projects → New Business Book → Book Contract approval → Architecture approval → Chapter → Chapter Contract approval`.

### M3 / Task 004 — ACCEPTED AND MERGED

- PR `#7 — Model Gateway + Controlled Drafting`
- accepted source tree first reached at `16b724f056da5e2213b3e99dd003965573b41de0`
- canonical merge: `1814ac7fffe9f9a6666ea59125439f32b0cff879`
- final CI `32893389579`: SUCCESS
  - `local-core`: Ruff format/check + mypy + **30/30 pytest PASS**
  - `desktop`: lint + typecheck + Vitest + build + dependency audit PASS
  - `tauri-smoke`: cargo test/check PASS
  - `secret-scan`: PASS
- provider-neutral gateway, Keychain secret boundary, mocked OpenAI development adapter and DRAFT-only ManuscriptUnit generation accepted.

### M4 / Task 005 — ACCEPTED AND MERGED

- PR `#8 — Research Engine + Claim Ledger`
- accepted implementation HEAD: `f0967229c2f0eb7a7b089e006a9a76b8ac1aa8c9`
- canonical M4 merge: `c15d2f12b3edd878720d1e2e251d4665525de688`
- final CI `32955967341`: SUCCESS
  - `local-core`: Ruff format/check + mypy + **43/43 pytest PASS**
  - `desktop`: lint + typecheck + Vitest + build + dependency audit PASS
  - `tauri-smoke`: cargo test/check PASS
  - `secret-scan`: PASS
- Claim / Source / Evidence persistence, research metadata adapters, evidence gates and native ResearchPanel accepted.

### M5 / Task 006 — ACCEPTED AND MERGED

- PR `#9 — Book Memory`
- accepted implementation HEAD: `1f831545dcde64cea992b2c57dedd5d16fd9671e`
- canonical M5 merge: `eb073659d77b57b58cb28702d95e35e891005a4d`
- final PR CI `32958990695`: SUCCESS
  - `local-core`: Ruff format/check + mypy + **55/55 pytest PASS** (`55 passed in 14.29s`)
  - `desktop`: lint + typecheck + Vitest + build + dependency audit PASS
  - `tauri-smoke`: `cargo test --locked` + `cargo check --locked` PASS
  - `secret-scan`: PASS
- SQLite FTS5 lexical memory, local NumPy exact cosine semantic retrieval and deterministic hybrid fusion accepted.
- provider/model/version/config/dimension embedding identity and deterministic rebuild accepted.
- CURRENT/HISTORY isolation, stale semantic invalidation and exact stable revision references accepted.
- deterministic fake embeddings in CI and mocked/Keychain-bounded OpenAI development adapter accepted.
- authenticated Book Memory API and native Book Memory panel accepted.
- 2,000-document exact local semantic benchmark is covered by acceptance tests.
- CI external/model/embedding calls: `0`; paid calls: `0`.

## Active implementation task — M6

`Task 007 — Editorial Workflows + Decision Inbox`

M6 implements the controlled editorial loop:

`exact revision → EditorialFinding → exact-base ChangeProposal → Decision Inbox → human decision → accepted new authority or preserved prior authority`.

Core rules:

- finding is diagnosis, not edit;
- proposal is not authority;
- existing M1 ChangeProposal/Decision/Approval remains the only authority-transition path;
- every material manuscript proposal uses exact base revision ID/hash;
- AI/SYSTEM cannot accept, reject or waive material editorial changes for the Owner;
- stale proposals cannot be accepted;
- Decision Inbox preserves original → diagnosis → proposal → decision/reason → final revision.

First deterministic v0.1 diagnostics are bounded to Developmental Chapter-Contract coverage, Cross-book repetition and Fact Checker Claim-state checks. Literary Editor and Style Guardian use the same typed finding/proposal/decision workflow without inventing M7 BookBench scoring.

## Scope guard

Do not implement yet:

- M7 BookBench scoring, LLM judges, Author Voice Fingerprint or AI-prose pathology detector;
- automatic whole-book/global rewrite;
- autonomous editor agents;
- Yandex/GigaChat Russia provider lane;
- Literary Master/export/audio handoff;
- accounts/cloud/billing/sync;
- silent Claim rebinding after manuscript edits.

## Next permitted action

1. Synchronize `docs/DESIGN_FILE_HASHES.sha256` for this state + Task 007.
2. Create `brain/task-007-editorial-workflows` from the resulting exact `main` HEAD.
3. Implement only `docs/tasks/CODEX_TASK_007_EDITORIAL_WORKFLOWS.md`.
4. Open one PR, fix objective CI/acceptance blockers, then Central Brain ACCEPT + merge M6.
5. Only then start M7 BookBench v0.1.

## Known blockers

No Owner decision blocker for the bounded M6 workflow implementation. AI material acceptance, weakened exact-base protection, automatic Claim rebinding, mandatory paid/live editorial model calls or M7 scope are stop conditions.

## Operational rule

`main` is accepted project-development authority. Implementation code uses bounded branches/PRs. Central Brain may make small project-control updates directly to `main` when a separate PR adds no review value.

## Recovery rule

If chat context disappears:

1. Open repository `main`.
2. Read README recovery order + `DESIGN_INDEX.md`.
3. Read this file and `TASK_EXECUTION_PROTOCOL_v0.1.md`.
4. Read `EDITORIAL_PROTOCOLS_v0.1.md` and `docs/tasks/CODEX_TASK_007_EDITORIAL_WORKFLOWS.md`.
5. Inspect `origin/main` and `brain/task-007-editorial-workflows`.
6. Continue only M6 until Central Brain ACCEPT/merge; do not start M7 automatically.
