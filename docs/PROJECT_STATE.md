# BOOK OS — PROJECT STATE

**Status:** BLOCKED — OWNER ACTION REQUIRED
**Version:** 1.4.4
**Date:** 2026-08-26
**Canonical repository:** `https://github.com/niknikdym-hue/book-os`

## Current phase

**IMPLEMENTATION MILESTONE 7 — TASK 008 / BOOKBENCH v0.1**

Active contract: `docs/tasks/CODEX_TASK_008_BOOKBENCH.md`  
Implementation branch: `brain/task-008-bookbench`  
Active pull request: `PR #11 — Task 008 — BookBench v0.1`

Canonical `main` at this checkpoint:

`fbfce0e50c0d170ea149fa08c0696db0a7a0b715`

Current authoritative PR HEAD:

`3c13b8de8972c2ebffe7034f05dc2f37892252d8`

PR status: DRAFT, mergeable, synchronized with current `main` at the verified checkpoint, **not acceptance-complete**.

## Accepted milestones

- **M0 / Task 001 — ACCEPTED AND MERGED:** executable Tauri/React desktop + Python local-core baseline, authenticated loopback health, SQLite migration infrastructure and CI.
- **M1 / Task 002 — ACCEPTED AND MERGED:** Authority & Persistence Engine; immutable revisions, authority states, exact-base proposals, decisions/approvals/provenance, stale-baseline protection and backup/restore.
- **M2 / Task 003 — ACCEPTED AND MERGED:** Book creation, Book Contract, Architecture and Chapter Contract workflow.
- **M3 / Task 004 — ACCEPTED AND MERGED:** provider-neutral Model Gateway + bounded controlled drafting.
- **M4 / Task 005 — ACCEPTED AND MERGED:** Research Engine + Claim Ledger.
- **M5 / Task 006 — ACCEPTED AND MERGED:** Book Memory lexical/semantic/hybrid retrieval and authority isolation.
- **M6 / Task 007 — ACCEPTED AND MERGED:** PR `#10`, accepted implementation HEAD `8fcdd725b5c6ece2d7b9500ae87c55478e008bd4`, canonical merge `9cfa9b9e8966715c243410e44dbe011e363974c1`, final CI `32961531865` SUCCESS.

Do not return to M0–M6 without a new concrete defect.

## M7 authoritative implementation evidence

The accepted first M7 recovery slice is published in PR #11. It includes:

- schema migration `0008`;
- exact evaluation snapshots/currentness;
- immutable EvaluationRun/EvaluationFinding persistence;
- deterministic BookBench registry/suite and grouped report without a universal magic score;
- repetition/evidence/statistical and initial AI-prose pathology signals;
- versioned Author Voice Fingerprint foundations from exact revision references;
- typed `BOOKBENCH_JUDGE/EVALUATOR` and `BOOKBENCH_PAIRWISE/EVALUATOR` Model Gateway foundations;
- deterministic fake judge/pairwise outputs for normal CI;
- mocked OpenAI structured-output regression preserving `store=false`;
- authenticated BookBench snapshot/deterministic/report/Voice Fingerprint API foundations.

The branch includes the control-state merge and is at authoritative HEAD:

`3c13b8de8972c2ebffe7034f05dc2f37892252d8`

Authoritative GitHub CI run `32993219899` is fully green:

- `local-core`: Ruff format/check PASS, mypy PASS, pytest PASS;
- `desktop`: lint/typecheck/Vitest/build/production dependency audit PASS;
- `tauri-smoke`: `cargo test --locked` PASS, `cargo check --locked` PASS;
- `secret-scan`: PASS.

Normal CI external/model/judge live calls = `0`; paid calls = `0` remains mandatory.

## Remaining M7 acceptance gates

M7 is **not accepted** until all remaining Task 008 gates are implemented and evidenced on this same PR:

1. M5-based semantic checks with exact embedding-config identity and stale/incompatible-config gates.
2. Full judge/pairwise persistence/execution and required dimension/rubric evidence.
3. Judge independence `INDEPENDENT | SAME_CONFIG | UNKNOWN` and release-grade gate.
4. Immutable M6 decision-dataset snapshots/version/hash.
5. Two-configuration role/dimension scorecards without a universal score.
6. Explicit BookBench → M6 EditorialFinding handoff with exact-current validation and stale block.
7. Complete authenticated BookBench API operations required by Task 008.
8. Native desktop BookBench workspace and tests.
9. Backup/restore migration regressions through `0008`.
10. Full M0–M6 regression suite and every numbered REQUIRED ACCEPTANCE item in `docs/tasks/CODEX_TASK_008_BOOKBENCH.md`.
11. Final authoritative PR CI PASS and final project-state/hash synchronization.

Do not merge PR #11 and do not start M8 before these gates pass.

## Execution blocker

The current implementation blocker is external to the code tree.

Continuation contract comment `5428599218` attempted to resume Codex from exact PR HEAD `3c13b8de8972c2ebffe7034f05dc2f37892252d8`.

The Codex connector replied in comment `5428601106`:

`To use Codex here, create an environment for this repo`.

Therefore the remaining M7 implementation cannot currently be delegated/executed through the repository Codex loop.

### Required Owner action

Create or re-enable a Codex cloud environment for repository:

`niknikdym-hue/book-os`

Codex environment settings:

`https://chatgpt.com/codex/cloud/settings/environments`

After the environment exists, resume the existing continuation contract from exact PR #11 HEAD (or its verified descendant). Do not create a replacement M7 PR.

## Fixed critical path to launch

`M7 BookBench → M8 Russia/no-VPN provider lane → M9 Literary Master + exports → M10 real Business Nonfiction pilot → GO/NO-GO`

No MVP/Russia-ready claim is permitted before the applicable M7–M10 acceptance gates pass.

## Scope guard

Do not implement inside M7:

- M8 Russia/no-VPN provider promotion;
- Yandex/GigaChat production routing;
- M9 Literary Master/release/export;
- Audio Studio production handoff implementation;
- M10 real-book pilot;
- cloud/accounts/billing/sync;
- any weakening of human authority, privacy, model-quality floors or zero-live/paid-call normal CI.

## Next permitted action

1. Owner creates/re-enables the Codex environment for `niknikdym-hue/book-os`.
2. Re-trigger the existing M7 continuation contract on PR #11.
3. Complete only the remaining Task 008 acceptance gates.
4. Review exact final HEAD and authoritative full CI.
5. Central Brain ACCEPT + merge M7 only after all gates pass.
6. Synchronize canonical state/hashes.
7. Immediately create and execute bounded M8.

## Operational rule

`main` is accepted project-development authority. Implementation code uses bounded branches/PRs. Central Brain may make small project-control updates directly to `main` when a separate PR adds no review value.

## Recovery rule

If chat context disappears:

1. Open repository `main`.
2. Read README recovery order + `DESIGN_INDEX.md`.
3. Read this file and `TASK_EXECUTION_PROTOCOL_v0.1.md`.
4. Read `BOOKBENCH_v0.1.md` and `docs/tasks/CODEX_TASK_008_BOOKBENCH.md`.
5. Inspect PR #11 / `brain/task-008-bookbench`.
6. Treat PR HEAD `3c13b8de8972c2ebffe7034f05dc2f37892252d8` or a verified descendant as authoritative implementation evidence.
7. Do not merge M7 until every Task 008 acceptance gate passes.
8. Then follow M8 → M9 → M10 → GO/NO-GO.

## Change log

### 1.4.4 — 2026-08-26
- Recorded current authoritative PR HEAD `3c13b8de...`.
- Recorded fully green authoritative CI run `32993219899`.
- Recorded remaining M7 acceptance gates.
- Recorded the active Codex execution blocker: repository environment missing.
- Made creation/re-enablement of the Codex environment the only required Owner action before implementation can continue.

### 1.4.3 — 2026-08-26
- Reassembled and published the first M7 recovery slice into PR #11.
- Verified byte-exact transport and preserved M7 scope/authority gates.

### 1.4.2 — 2026-08-26
- Recorded local-only recovery slice evidence and remaining M7 gates.

### 1.4.1 — 2026-08-26
- Recorded authoritative Ruff blocker and M7 recovery protocol.

### 1.4.0 — 2026-08-26
- Corrected stale M6 state and made M7 / Task 008 / PR #11 the sole active path.
- Recorded the fixed launch critical path.
