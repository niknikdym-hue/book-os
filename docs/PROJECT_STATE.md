# BOOK OS — PROJECT STATE

**Status:** BLOCKED — OWNER ACTION REQUIRED / CODEX ENVIRONMENT UNSTABLE  
**Version:** 1.4.7  
**Date:** 2026-08-27  
**Canonical repository:** `https://github.com/niknikdym-hue/book-os`

## Current phase

**IMPLEMENTATION MILESTONE 7 — TASK 008 / BOOKBENCH v0.1**

Active contract: `docs/tasks/CODEX_TASK_008_BOOKBENCH.md`  
Implementation branch: `brain/task-008-bookbench`  
Active pull request: `PR #11 — Task 008 — BookBench v0.1`

Canonical `main` before this correction:

`7f82d585f7bb554502a41e1a01e9dc7426a72d39`

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

## M7 local completion evidence

PR #11 comment `5441395177` proves that the existing Codex environment was usable at 2026-08-27 15:28 UTC and that Codex executed the remaining M7 work.

Codex reported local commit:

`e4d832add38002e08664e2b0dde480e6d65318ab`

Reported local evidence:

- semantic duplication/novelty/contract-coverage checks through the existing EmbeddingGateway with exact config/currentness gates;
- persisted judge execution with `INDEPENDENT | SAME_CONFIG | UNKNOWN` release gating;
- deterministic blind pairwise mapping;
- immutable versioned M6 decision datasets;
- two-configuration per-dimension scorecards with no universal score;
- explicit current-safe BookBench → M6 handoff with no automatic proposal/decision;
- remaining authenticated BookBench operations;
- native BookBench desktop workspace and tests;
- **74 pytest PASS**;
- desktop lint/typecheck/Vitest/build PASS.

This local commit is **not present in GitHub**. PR #11 still points to `709880e35...`. Therefore it is evidence only, not accepted implementation.

## Current blocker — intermittent Codex environment binding

Central Brain issued exact transport recovery in PR #11 comment `5441840609`.

At 2026-08-27 16:05 UTC the Codex connector immediately replied in comment `5441843623`:

`To use Codex here, create an environment for this repo`

This happened after a successful Codex run less than one hour earlier, so the problem is not “environment never existed.” It is an **intermittent environment binding/visibility failure**.

Classification:

`CODEX_ENVIRONMENT_UNSTABLE / BINDING_VISIBILITY_FAILURE`

Because the local commit is inaccessible to GitHub and the transport recovery cannot run while Codex cannot resolve the environment, M7 is fully blocked at publication.

## Required Owner action

Do **not** create a duplicate blindly.

Open Codex environment settings and inspect the existing environment bound to:

`niknikdym-hue/book-os`

Required result:

- the existing environment entry is present;
- it is enabled;
- repository binding is exactly `niknikdym-hue/book-os`;
- re-select/re-save/update the binding if the UI offers that action.

If the existing entry is actually absent, recreate it only then.

After the environment is stably visible, re-trigger PR #11 recovery contract `5441840609`.

## Remaining acceptance sequence

Before M7 ACCEPT/MERGE:

1. Recover and publish the exact remaining-M7 bytes to `brain/task-008-bookbench`.
2. Verify PR #11 HEAD advances from `709880e35...`.
3. Run full authoritative GitHub CI: local-core, desktop, Tauri/Rust, audit and secret scan.
4. Review every numbered REQUIRED ACCEPTANCE item in `docs/tasks/CODEX_TASK_008_BOOKBENCH.md`.
5. Verify human authority, privacy, no-universal-score, independence and zero-normal-CI-live/paid-call invariants.
6. Synchronize final project state/hash.
7. Only then ACCEPT + merge M7.
8. Immediately advance to M8 Russia/no-VPN provider lane.

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

## Recovery rule

If chat context disappears:

1. Open repository `main`.
2. Read README recovery order + `DESIGN_INDEX.md`.
3. Read this file and `TASK_EXECUTION_PROTOCOL_v0.1.md`.
4. Read `BOOKBENCH_v0.1.md` and `docs/tasks/CODEX_TASK_008_BOOKBENCH.md`.
5. Inspect PR #11 / `brain/task-008-bookbench`.
6. Treat published PR HEAD `709880e35...` or its verified descendant as GitHub implementation authority.
7. Treat local-only Codex commit `e4d832add...` as evidence only until exact bytes are published and CI passes.
8. Resolve Codex environment binding, then execute transport recovery comment `5441840609`.
9. Do not merge M7 until every Task 008 acceptance gate passes.
10. Then follow M8 → M9 → M10 → GO/NO-GO.

## Change log

### 1.4.7 — 2026-08-27
- Recorded successful Codex M7 execution followed by immediate recurrence of the environment-resolution failure.
- Reclassified the blocker as intermittent Codex environment binding/visibility failure.
- Restored Owner-action requirement because exact local M7 bytes cannot be recovered/published while Codex cannot resolve the environment.
- Preserved local commit/test evidence without treating it as GitHub authority or M7 acceptance.

### 1.4.6 — 2026-08-27
- Recorded local M7 completion report and delivery blocker before the environment failure recurred.
