# BOOK OS — PROJECT STATE

**Status:** ACTIVE — M7 DELIVERY RECOVERY  
**Version:** 1.4.6  
**Date:** 2026-08-27  
**Canonical repository:** `https://github.com/niknikdym-hue/book-os`

## Current phase

**IMPLEMENTATION MILESTONE 7 — TASK 008 / BOOKBENCH v0.1**

Active contract: `docs/tasks/CODEX_TASK_008_BOOKBENCH.md`  
Implementation branch: `brain/task-008-bookbench`  
Active pull request: `PR #11 — Task 008 — BookBench v0.1`

Canonical `main` at this checkpoint:

`02eebbacf98462889d43ff2fafda1860420bb29a`

Current published PR #11 HEAD:

`709880e35d93ea87dead4e8f1d5aabe36a669e99`

PR status: DRAFT, mergeable, **not acceptance-complete**.

## Accepted milestones

- **M0 / Task 001 — ACCEPTED AND MERGED**
- **M1 / Task 002 — ACCEPTED AND MERGED**
- **M2 / Task 003 — ACCEPTED AND MERGED**
- **M3 / Task 004 — ACCEPTED AND MERGED**
- **M4 / Task 005 — ACCEPTED AND MERGED**
- **M5 / Task 006 — ACCEPTED AND MERGED**
- **M6 / Task 007 — ACCEPTED AND MERGED:** PR `#10`, accepted implementation HEAD `8fcdd725b5c6ece2d7b9500ae87c55478e008bd4`, canonical merge `9cfa9b9e8966715c243410e44dbe011e363974c1`, final CI `32961531865` SUCCESS.

Do not return to M0–M6 without a new concrete defect.

## M7 published evidence

The current published PR slice includes migration `0008`, exact evaluation snapshots/currentness, immutable EvaluationRun/EvaluationFinding persistence, deterministic BookBench registry/reporting, initial AI-prose pathology signals, Author Voice Fingerprint foundations, typed BookBench judge/pairwise Model Gateway foundations, deterministic fake judge/pairwise outputs, mocked OpenAI structured-output regression preserving `store=false`, and authenticated BookBench API foundations.

Authoritative GitHub CI run `33086202850` on published HEAD `709880e35d93ea87dead4e8f1d5aabe36a669e99` is fully green.

Normal CI external/model/judge live calls = `0`; paid calls = `0` remains mandatory.

## M7 continuation — environment recovered

The previously existing Codex cloud environment is usable again.

PR #11 comment `5441395177` records a successful Codex continuation from published HEAD `709880e35d93ea87dead4e8f1d5aabe36a669e99`.

Codex reports the remaining M7 implementation completed locally as commit:

`e4d832add38002e08664e2b0dde480e6d65318ab`

Reported local evidence includes:

- semantic duplication/novelty/contract-coverage checks through the existing EmbeddingGateway with exact config/currentness gates;
- persisted judge execution with `INDEPENDENT | SAME_CONFIG | UNKNOWN` release gating;
- deterministic blind pairwise mapping;
- immutable versioned M6 decision datasets;
- two-configuration per-dimension scorecards with no universal score;
- explicit current-safe BookBench → M6 handoff with no automatic proposal/decision;
- complete authenticated BookBench operations for the remaining flows;
- native BookBench desktop workspace and tests;
- **74 pytest PASS**;
- desktop lint/typecheck/Vitest/build PASS.

The Codex local commit is **not present in GitHub**; querying GitHub for `e4d832add...` returns no commit and PR #11 still points to `709880e35...`.

Therefore M7 is not accepted yet.

## Active blocker — delivery publication, not Owner action

Current blocker:

`CODEX_LOCAL_COMMIT_NOT_PUBLISHED`

This is an execution-delivery issue, not a product/Owner decision and not an environment-creation issue.

Central Brain recovery contract is PR #11 comment `5441840609`:

- recover exact remaining-M7 diff against published parent `709880e35...`;
- produce byte-exact unified patch + gzip + SHA256 + complete base64 transport payload;
- do not recompute scope, do not create another PR, do not start M8;
- after publication, run authoritative GitHub CI and independently review all Task 008 gates.

No Owner action is currently required.

## Remaining acceptance sequence

Before M7 ACCEPT/MERGE:

1. Publish the exact completed remaining-M7 bytes to `brain/task-008-bookbench`.
2. Verify PR #11 HEAD changed from `709880e35...` to the published implementation descendant.
3. Run full authoritative GitHub CI: local-core, desktop, Tauri/Rust, audit and secret scan.
4. Review every numbered REQUIRED ACCEPTANCE item in `docs/tasks/CODEX_TASK_008_BOOKBENCH.md`.
5. Verify human authority, privacy, no-universal-score, independence and zero-normal-CI-live/paid-call invariants.
6. Synchronize final project state/hash.
7. Only then ACCEPT + merge M7.

## Repository hygiene

Only PR #11 is open/draft. PRs #1–#10 are closed/merged.

Historical milestone branches are retired and are not project authority. Only these refs are active for implementation:

- `main`
- `brain/task-008-bookbench`
- PR `#11`

The stale temporary `.github/workflows/m7-control-sync.yml` has been removed.

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

1. Complete the exact transport recovery from Codex local commit/worktree.
2. Publish the recovered bytes to PR #11 branch.
3. Run and review authoritative full CI.
4. Central Brain ACCEPT + merge M7 only if every Task 008 gate passes.
5. Synchronize canonical state/hashes.
6. Immediately create and execute bounded M8.

## Operational rule

`main` is accepted project-development authority. Implementation code uses bounded branches/PRs. Central Brain may make small project-control updates directly to `main` when a separate PR adds no review value.

## Recovery rule

If chat context disappears:

1. Open repository `main`.
2. Read README recovery order + `DESIGN_INDEX.md`.
3. Read this file and `TASK_EXECUTION_PROTOCOL_v0.1.md`.
4. Read `BOOKBENCH_v0.1.md` and `docs/tasks/CODEX_TASK_008_BOOKBENCH.md`.
5. Inspect PR #11 / `brain/task-008-bookbench`.
6. Treat published PR HEAD `709880e35...` or its verified descendant as GitHub implementation authority.
7. Treat local-only Codex commit reports as evidence only until their bytes are published and CI passes.
8. Do not merge M7 until every Task 008 acceptance gate passes.
9. Then follow M8 → M9 → M10 → GO/NO-GO.

## Change log

### 1.4.6 — 2026-08-27
- Confirmed the existing Codex environment is usable again through successful M7 execution.
- Recorded local completion report `e4d832add...` and 74-test evidence.
- Corrected the active blocker from environment resolution to local-commit delivery/publication.
- Recorded exact transport-recovery contract and made clear that no Owner action is required.

### 1.4.5 — 2026-08-27
- Corrected the false diagnosis that the BOOK OS Codex environment had never been created.
- Recorded GitHub evidence that the environment was created/enabled and used on PR #3.
- Reclassified the then-current blocker as Codex environment resolution/binding/visibility failure.
- Recorded branch/PR hygiene and removed stale temporary M7 control workflow.
