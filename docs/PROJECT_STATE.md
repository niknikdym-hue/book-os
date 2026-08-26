# BOOK OS — PROJECT STATE

**Status:** ACTIVE CHECKPOINT  
**Version:** 1.4.1  
**Date:** 2026-08-26  
**Canonical repository:** `https://github.com/niknikdym-hue/book-os`

## Current phase

**IMPLEMENTATION MILESTONE 7 — TASK 008 RECOVERY IN PROGRESS**

Canonical `main` baseline at M7 start:

`b5fc8e52233b57bc976954044d430cd7a4f612e3`

Active contract:

`docs/tasks/CODEX_TASK_008_BOOKBENCH.md`

Implementation branch:

`brain/task-008-bookbench`

Active pull request:

`PR #11 — Task 008 — BookBench v0.1`

Current authoritative GitHub PR HEAD:

`198455286335e9a0ea5203d2497449fe282d5102`

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

Authoritative GitHub implementation currently includes:
- schema migration `0008`;
- exact evaluation snapshots/currentness;
- immutable EvaluationRun/EvaluationFinding persistence;
- deterministic BookBench registry/suite;
- repetition/evidence/statistical checks;
- initial deterministic AI-prose pathology signals;
- grouped report without a universal magic score;
- M7 schema regression updates.

Last authoritative GitHub CI on HEAD `198455286335e9a0ea5203d2497449fe282d5102`:
- workflow run `32970871777`;
- `desktop`: PASS;
- `tauri-smoke`: PASS;
- `secret-scan`: PASS;
- `local-core`: FAIL at Ruff `F401` before mypy/pytest because `BookBenchDimension` is imported but unused in `bookbench.py`.

## M7 recovery state

A Codex execution reported a larger local follow-up commit:

`9b3b5a0bb3600cd1eb0ae3d29f789b816fe1b182`

That object was **never published to GitHub**. A later Codex workspace proved it is neither reachable nor dangling, and GitHub confirms no such commit exists in this repository. Therefore:

- the reported local implementation is treated as LOST;
- it is not acceptance evidence;
- no acceptance gate may cite that local-only SHA;
- reconstruction from the authoritative GitHub HEAD is permitted;
- reconstruction must stay inside PR #11 and M7 scope;
- because the Codex execution environment cannot push, recovery output must include a byte-exact transport artifact (gzip+base64 unified diff + SHA256) before it can be transferred into GitHub.

Still required before M7 ACCEPT/MERGE:
- remove the objective Ruff F401 blocker without weakening lint policy;
- Author Voice Fingerprint;
- M5-based semantic checks with exact embedding-config identity and stale-config gates;
- bounded BookBench judge + pairwise framework through the existing M3 Model Gateway;
- mocked OpenAI structured judge path and zero-live-call CI proof;
- judge independence gate;
- immutable M6-decision evaluation datasets;
- two-configuration role/dimension scorecards;
- explicit BookBench → M6 EditorialFinding handoff with currentness validation;
- authenticated BookBench API;
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

1. Continue only PR #11 on `brain/task-008-bookbench` from GitHub HEAD `198455286335e9a0ea5203d2497449fe282d5102`.
2. Reconstruct the lost M7 follow-up under the exact Task 008 contract.
3. Transfer reconstructed bytes into the actual GitHub branch; local-only commits do not count.
4. Close every missing Task 008 acceptance item on the same PR.
5. Run full PR CI with zero live/paid external model calls in normal CI.
6. Central Brain reviews objective evidence.
7. If all M7 gates pass: ACCEPT + merge PR #11.
8. Synchronize canonical project state to M7 accepted.
9. Immediately create and execute M8 bounded contract.

## Owner-decision blockers

None for completing the bounded M7 contract as currently accepted.

The current recovery problem is an execution/delivery defect, not an Owner product decision.

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
6. Treat `198455286335e9a0ea5203d2497449fe282d5102` as the current authoritative GitHub M7 implementation until a newer PR HEAD is actually published.
7. Do not treat lost local Codex commit `9b3b5a0b...` as evidence.
8. Continue only M7 until objective ACCEPT/merge.
9. Then follow the fixed launch path M8 → M9 → M10 → GO/NO-GO.

## Change log

### 1.4.1 — 2026-08-26
- Recorded actual authoritative PR #11 HEAD `198455286335e9a0ea5203d2497449fe282d5102`.
- Recorded authoritative CI run `32970871777` and exact Ruff F401 blocker.
- Marked unpublished Codex commit `9b3b5a0b...` as irrecoverably lost and non-authoritative.
- Defined M7 reconstruction/transport recovery protocol while preserving the fixed launch path.

### 1.4.0 — 2026-08-26
- Corrected stale state that still showed M6 as active after PR #10 had been accepted and merged.
- Recorded M6 canonical acceptance evidence.
- Made M7 / Task 008 / PR #11 the sole active implementation path.
- Recorded the fixed launch critical path: M7 → M8 → M9 → M10 → GO/NO-GO.
