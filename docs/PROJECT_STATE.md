# BOOK OS — PROJECT STATE

**Status:** ACTIVE CHECKPOINT  
**Version:** 1.4.3  
**Date:** 2026-08-26  
**Canonical repository:** `https://github.com/niknikdym-hue/book-os`

## Current phase

**IMPLEMENTATION MILESTONE 7 — TASK 008 RECOVERY SLICE 1 PUBLISHED**

Canonical `main` control baseline before this state update:

`627eca9b5eabaa1bac52d21849f1ae0591f3f8bd`

Active contract:

`docs/tasks/CODEX_TASK_008_BOOKBENCH.md`

Implementation branch:

`brain/task-008-bookbench`

Active pull request:

`PR #11 — Task 008 — BookBench v0.1`

Current authoritative GitHub PR HEAD:

`ac1a6cff2b316460a96bfcb1aebcac1a5a1f22e6`

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

PR #11 remains DRAFT and is **not accepted**.

### Authoritative GitHub implementation now present

The original M7 backend slice from HEAD `198455286335e9a0ea5203d2497449fe282d5102` included:
- schema migration `0008`;
- exact evaluation snapshots/currentness;
- immutable EvaluationRun/EvaluationFinding persistence;
- deterministic BookBench registry/suite;
- repetition/evidence/statistical checks;
- initial deterministic AI-prose pathology signals;
- grouped report without a universal magic score;
- M7 schema regression updates.

The first reconstructed recovery slice has now been transferred byte-exactly into GitHub and is part of authoritative PR HEAD:

`ac1a6cff2b316460a96bfcb1aebcac1a5a1f22e6`

Transport evidence:
- source PR comment: `5427446407`;
- exact recovery parent: `198455286335e9a0ea5203d2497449fe282d5102`;
- raw unified patch SHA256: `d90dfb0b98da2ac9c9bd9863a1293e9ebd6c5bf8c13d688018af4ad8a3a31a48`;
- gzip SHA256: `6c26523ac13d2e0f0313dbe324b421529d7f28758b3c172968cac8e3e0a63f04`;
- raw patch size: `34015` bytes;
- gzip size: `9039` bytes;
- diff stat: `8 files changed, 513 insertions(+), 31 deletions(-)`;
- both SHA256 values were independently reassembled and verified before application.

This first recovery slice adds:
- removal of the known Ruff F401 blocker;
- versioned Author Voice Fingerprints from explicit exact revision references;
- deterministic voice-feature extraction and diagnostic target deltas;
- typed `BOOKBENCH_JUDGE/EVALUATOR` and `BOOKBENCH_PAIRWISE/EVALUATOR` Model Gateway foundations;
- deterministic fake judge/pairwise outputs for normal CI;
- mocked OpenAI structured-output regression path preserving `store=false`;
- authenticated BookBench snapshot/deterministic/report/Voice Fingerprint API foundations.

Codex local evidence for the exact transported slice reported:
- Ruff format/check PASS;
- mypy PASS over 21 source files;
- pytest `71 passed`;
- desktop lint/typecheck PASS;
- desktop tests `5 files / 6 tests passed`;
- desktop production build PASS;
- `git diff --check` PASS.

These local results are supporting evidence only. M7 acceptance still requires authoritative GitHub CI on the actual PR HEAD.

## Still required before M7 ACCEPT/MERGE

1. Synchronize the current canonical project-state/hash files into PR #11 and obtain authoritative GitHub CI on the first recovered slice.
2. M5-based semantic checks with exact embedding-config identity and stale/incompatible-config gates.
3. Complete judge/pairwise persistence/execution and required dimension/rubric evidence.
4. Judge independence `INDEPENDENT | SAME_CONFIG | UNKNOWN` and release-grade gate.
5. Immutable M6 decision-dataset snapshots/version/hash.
6. Two-configuration role/dimension scorecards without a universal score.
7. Explicit BookBench → M6 EditorialFinding handoff with exact-current validation and stale block.
8. Complete authenticated API operations required by Task 008.
9. Native desktop BookBench workspace and tests.
10. Backup/restore migration regressions through `0008`.
11. Full M0–M6 regression suite and every numbered REQUIRED ACCEPTANCE item in `docs/tasks/CODEX_TASK_008_BOOKBENCH.md`.
12. Final authoritative PR CI PASS including dependency audit, Rust/Tauri and secret-scan.
13. Final project-state/hash synchronization.

Normal CI must keep external/model/judge live calls = `0` and paid calls = `0`.

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

1. Synchronize this canonical project state and its design hash into PR #11.
2. Trigger and inspect authoritative GitHub CI on the resulting PR HEAD.
3. Fix objective first-slice blockers if any.
4. Continue only the remaining M7 Task 008 gates on that accepted first-slice baseline.
5. ACCEPT + merge PR #11 only after every M7 acceptance gate and CI pass.
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
6. Treat GitHub PR HEAD `ac1a6cff2b316460a96bfcb1aebcac1a5a1f22e6` (or its verified descendants) as authoritative implementation evidence.
7. Do not treat local-only SHAs as evidence.
8. Continue only M7 until objective ACCEPT/merge.
9. Then follow the fixed launch path M8 → M9 → M10 → GO/NO-GO.

## Change log

### 1.4.3 — 2026-08-26
- Reassembled the complete recovery payload from PR comment `5427446407`.
- Independently verified gzip SHA256 and raw-patch SHA256 and exact byte sizes.
- Transferred the first M7 recovery slice byte-exactly into PR #11.
- Advanced authoritative GitHub implementation HEAD to `ac1a6cff...`.
- Removed the transport-only execution blocker; remaining work is now normal M7 implementation/acceptance.

### 1.4.2 — 2026-08-26
- Recorded first reconstructed M7 recovery slice `0dca25cf...` as local-only, not authoritative.
- Recorded byte-exact patch hashes, size, diff stat and local test evidence.
- Recorded which M7 gates the first slice covers and which remain.

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
