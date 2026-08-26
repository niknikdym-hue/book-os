# BOOK OS — PROJECT STATE

**Status:** ACTIVE CHECKPOINT  
**Version:** 1.4.0  
**Date:** 2026-08-26  
**Canonical repository:** `https://github.com/niknikdym-hue/book-os`

## Current phase

**IMPLEMENTATION MILESTONE 7 — TASK 008 IN PROGRESS**

Canonical `main` baseline at M7 start:

`b5fc8e52233b57bc976954044d430cd7a4f612e3`

Active contract:

`docs/tasks/CODEX_TASK_008_BOOKBENCH.md`

Implementation branch:

`brain/task-008-bookbench`

Active pull request:

`PR #11 — Task 008 — BookBench v0.1`

Observed implementation HEAD at this checkpoint:

`cefdd1c8ee868c81a2c292a459c77d3f485191cc`

## Accepted authority

- Product/Authority baseline: `BOOK_OS_AUTHORITY.md`
- Product spec: `PRODUCT_SPEC_v0.1.md`
- Core Ontology: `CORE_ONTOLOGY.md`
- Editorial contracts/gates: `EDITORIAL_PROTOCOLS_v0.1.md`
- Model Gateway: `MODEL_GATEWAY_v0.1.md`
- Research/Claim authority: `RESEARCH_AND_CLAIMS_v0.1.md`
- Book Memory authority: `BOOK_MEMORY_v0.1.md`
- BookBench authority: `BOOKBENCH_v0.1.md`
- Technical Architecture: `TECHNICAL_ARCHITECTURE_v0.1.md`
- Security/availability: `SECURITY_AVAILABILITY_v0.1.md`
- Implementation roadmap: `IMPLEMENTATION_ROADMAP_v0.1.md`
- Execution control: `TASK_EXECUTION_PROTOCOL_v0.1.md`
- Complete recovery map: `DESIGN_INDEX.md`

## Completed milestones

### M0 / Task 001 — ACCEPTED AND MERGED
Executable Tauri/React desktop + Python local-core baseline, authenticated loopback health, SQLite migration infrastructure and CI accepted.

### M1 / Task 002 — ACCEPTED AND MERGED
Authority & Persistence Engine accepted: immutable revisions, authority states, exact-base proposals, decisions/approvals/provenance, stale-baseline protection and backup/restore.

### M2 / Task 003 — ACCEPTED AND MERGED
Book creation, Book Contract, Architecture and Chapter Contract workflow accepted.

### M3 / Task 004 — ACCEPTED AND MERGED
Provider-neutral Model Gateway + bounded controlled drafting accepted.

### M4 / Task 005 — ACCEPTED AND MERGED
Research Engine + Claim Ledger accepted.

### M5 / Task 006 — ACCEPTED AND MERGED
Book Memory lexical/semantic/hybrid retrieval and authority isolation accepted.

### M6 / Task 007 — ACCEPTED AND MERGED
- PR `#10`
- accepted implementation HEAD `8fcdd725b5c6ece2d7b9500ae87c55478e008bd4`
- canonical merge `9cfa9b9e8966715c243410e44dbe011e363974c1`
- final CI `32961531865`: SUCCESS
- exact-revision editorial findings → exact-base ChangeProposal → Decision Inbox → HUMAN decision workflow accepted
- normal CI external/model calls = `0`; paid calls = `0`

## Active milestone — M7 / Task 008

Goal:

`exact revision snapshot → versioned BookBench evaluation → actionable dimension findings → optional explicit M6 handoff → human review`

Current PR #11 is a DRAFT and is **not yet accepted**.

Observed recovery implementation includes:
- schema migration `0008`;
- exact evaluation snapshots/currentness;
- immutable EvaluationRun/EvaluationFinding persistence;
- deterministic BookBench registry/suite;
- repetition/evidence/statistical checks;
- initial deterministic AI-prose pathology signals;
- grouped report without a universal magic score;
- versioned Author Voice Fingerprints from explicitly selected exact revisions and diagnostic deltas;
- bounded typed `BOOKBENCH_JUDGE/EVALUATOR` and `BOOKBENCH_PAIRWISE/EVALUATOR` Model Gateway tasks;
- versioned injection-safe judge/pairwise prompts, deterministic fake outputs, and a mocked
  OpenAI structured judge regression that asserts `store=false`;
- authenticated snapshot, deterministic report, and Voice Fingerprint API operations;
- M7 schema regression updates.

Still required before M7 ACCEPT/MERGE:
- M5-based semantic checks with exact embedding-config identity and stale-config gates;
- judge independence gate;
- immutable M6-decision evaluation datasets;
- two-configuration role/dimension scorecards;
- explicit BookBench → M6 EditorialFinding handoff with currentness validation;
- remaining semantic/judge/pairwise/dataset/scorecard/handoff BookBench API operations;
- native desktop BookBench workspace;
- backup/restore through `0008`;
- full M0–M6 regression + every Task 008 REQUIRED ACCEPTANCE gate;
- final project-state/hash synchronization.

## Scope guard

Do not implement M8+ inside PR #11.

In particular, do not start yet:
- Russia/no-VPN provider promotion;
- Yandex/GigaChat production routing;
- Literary Master/release/export;
- Audio Studio production handoff implementation;
- real-book M10 pilot.

## Critical path to launch

No return to already accepted milestones.

`M7 BookBench → M8 Russia/no-VPN provider lane → M9 Literary Master + exports → M10 real Business Nonfiction pilot → GO/NO-GO`

MVP/Russia-ready cannot be declared before the applicable M7–M10 acceptance gates pass.

## Next permitted action

1. Continue only PR #11 on `brain/task-008-bookbench`.
2. Close every missing Task 008 acceptance item on the same PR.
3. Run full PR CI with zero live/paid external model calls in normal CI.
4. Central Brain reviews objective evidence.
5. If all M7 gates pass: ACCEPT + merge PR #11.
6. Synchronize canonical project state to M7 accepted.
7. Immediately create and execute M8 bounded contract.

## Owner-decision blockers

None for completing the bounded M7 contract as currently accepted.

Stop and request Owner decision only if implementation would weaken human authority, expose private manuscript/evaluation data, require material recurring infrastructure cost, weaken the Russia/no-VPN requirement, or lower a critical model-quality floor.

## Operational rule

`main` is accepted project-development authority. Implementation code uses bounded branches/PRs. Central Brain may make small project-control updates directly to `main` when a separate PR adds no review value.

## Recovery rule

If chat context disappears:

1. Open repository `main`.
2. Read README recovery order + `DESIGN_INDEX.md`.
3. Read this file and `TASK_EXECUTION_PROTOCOL_v0.1.md`.
4. Read `BOOKBENCH_v0.1.md` and `docs/tasks/CODEX_TASK_008_BOOKBENCH.md`.
5. Inspect PR #11 / `brain/task-008-bookbench`.
6. Continue only M7 until objective ACCEPT/merge.
7. Then follow the fixed launch path M8 → M9 → M10 → GO/NO-GO.

## Change log

### 1.4.0 — 2026-08-26
- Corrected stale state that still showed M6 as active after PR #10 had been accepted and merged.
- Recorded M6 canonical acceptance evidence.
- Made M7 / Task 008 / PR #11 the sole active implementation path.
- Recorded the fixed launch critical path: M7 → M8 → M9 → M10 → GO/NO-GO.
