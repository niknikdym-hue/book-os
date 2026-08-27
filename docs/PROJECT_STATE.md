# BOOK OS — PROJECT STATE

**Status:** M7 IMPLEMENTED — CENTRAL BRAIN REVIEW REQUIRED
**Version:** 1.5.0
**Date:** 2026-08-27
**Canonical repository:** `https://github.com/niknikdym-hue/book-os`

## Current phase

**IMPLEMENTATION MILESTONE 7 — TASK 008 / BOOKBENCH v0.1**

Active contract: `docs/tasks/CODEX_TASK_008_BOOKBENCH.md`
Implementation branch: `brain/task-008-bookbench`
Active pull request: `PR #11 — Task 008 — BookBench v0.1`

Verified canonical `main` before this control correction:

`d3053a93a790d75d0b6cd2996f0df6e1d7ae2a01`

Current PR #11 HEAD at verification:

`8f9235cf1df7c0342c23f9f9479e9ffcb0d93ff7`

PR status: DRAFT, mergeable, ahead of current `main`, **not acceptance-complete**.

## Accepted milestones

- **M0 / Task 001 — ACCEPTED AND MERGED**
- **M1 / Task 002 — ACCEPTED AND MERGED**
- **M2 / Task 003 — ACCEPTED AND MERGED**
- **M3 / Task 004 — ACCEPTED AND MERGED**
- **M4 / Task 005 — ACCEPTED AND MERGED**
- **M5 / Task 006 — ACCEPTED AND MERGED**
- **M6 / Task 007 — ACCEPTED AND MERGED:** PR `#10`, accepted implementation HEAD `8fcdd725b5c6ece2d7b9500ae87c55478e008bd4`, canonical merge `9cfa9b9e8966715c243410e44dbe011e363974c1`, final CI `32961531865` SUCCESS.

Do not return to M0–M6 without a new concrete defect.

## M7 authoritative implementation evidence

PR #11 contains the published first M7 recovery slice and current control merges. Verified BookBench foundations include:

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

Authoritative published-slice CI run `32993219899` is fully green:

- `local-core`: Ruff format/check PASS, mypy PASS, pytest PASS;
- `desktop`: lint/typecheck/Vitest/build/production dependency audit PASS;
- `tauri-smoke`: `cargo test --locked` PASS, `cargo check --locked` PASS;
- `secret-scan`: PASS.

Normal CI external/model/judge live calls = `0`; paid calls = `0` remains mandatory.

## Remaining M7 acceptance gates

The remaining Task 008 implementation is now present locally for Central Brain review:

- M5 EmbeddingGateway semantic candidates retain exact revision and embedding-config identity and reject stale/incompatible inputs;
- bounded judge and blind pairwise execution persist versioned evidence with explicit independence/release-grade state;
- immutable M6 decision datasets and two deterministic fake-configuration per-dimension scorecards preserve zero-live/paid normal CI;
- explicit current-safe BookBench-to-M6 handoff preserves provenance and creates no proposal or decision;
- authenticated API and native desktop BookBench workspace expose all M7 operations without an overall score;
- synthetic acceptance regressions cover semantic config gates, judge independence, pairwise mapping, datasets, scorecards, and handoff.

M7 is **not self-accepted**. Central Brain must review the exact implementation, verify authoritative CI, and decide ACCEPT/MERGE. M8 remains forbidden until that decision.

## Codex environment — corrected diagnosis

The Codex cloud environment for `niknikdym-hue/book-os` **was previously created and used**.

Repository evidence:

- PR #3 comment `5384011524` initially returned `To use Codex here, create an environment for this repo`.
- PR #3 comment `5384070812` then explicitly recorded: `Environment for niknikdym-hue/book-os is now created and enabled`.
- Subsequent Codex connector runs on PR #3 produced real task execution reports and task links, proving that a working Codex execution environment existed.

Therefore current PR #11 comment `5428601106` repeating `To use Codex here, create an environment for this repo` is **not evidence that no environment was ever created**.

Current blocker is classified as:

`CODEX_ENVIRONMENT_RESOLUTION / BINDING / VISIBILITY FAILURE`

Possible causes include an existing environment being disabled, deleted, detached from this repository, no longer visible to the current Codex connector context, or requiring re-save/re-selection. Do **not** create duplicate environments blindly.

### Required verification

Open Codex environment settings and inspect the existing entry for:

`niknikdym-hue/book-os`

If it exists and is enabled, re-select/re-save the repository binding and then re-trigger the existing PR #11 continuation contract. If the entry is absent, only then recreate it.

## GitHub branch / draft hygiene

There is only **one open draft pull request**:

`PR #11 — Task 008 — BookBench v0.1`

All PRs `#1–#10` are closed/merged.

Historical implementation branches remain in GitHub and make the branch list look cluttered:

- `brain/pre-implementation-hardening`
- `brain/task-governance`
- `codex/task-001-bootstrap`
- `codex/task-002-authority-persistence`
- `brain/task-003-book-creation-contracts`
- `brain/task-004-model-gateway-drafting`
- `brain/task-005-research-claim-ledger`
- `brain/task-006-book-memory`
- `brain/task-007-editorial-workflows`
- `codex/fix-ci-workflow-for-secret-scan-job`

The first nine are verified historical/merged lines fully superseded by `main`. The old `codex/fix-ci-workflow-for-secret-scan-job` branch is not a current ancestry line, but its intended gitleaks v3 + `GITHUB_TOKEN` behavior is present in current `main`; PR #4 is merged. It is obsolete and must not be used as project authority.

Only these refs are active authority for implementation:

- `main`
- `brain/task-008-bookbench`
- PR `#11`

Retired branches may be deleted for repository hygiene after confirming no external automation points at them. Branch cleanup is not a launch blocker.

## Temporary-control defect removed

The temporary workflow:

`.github/workflows/m7-control-sync.yml`

was an implementation-control helper intended to self-delete after synchronizing the initial M7 baseline. It remained in `main` and contained stale v1.4.0 project-state text while triggering on every push to `main`.

It is removed in this control correction. Canonical state must not be rewritten by a stale temporary workflow.

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

1. Verify the **existing** Codex environment binding for `niknikdym-hue/book-os`; do not create a duplicate blindly.
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
6. Treat current PR #11 HEAD or a verified descendant as active M7 implementation evidence.
7. Do not merge M7 until every Task 008 acceptance gate passes.
8. Then follow M8 → M9 → M10 → GO/NO-GO.

## Change log

### 1.4.5 — 2026-08-27
- Corrected the false diagnosis that the BOOK OS Codex environment had never been created.
- Recorded GitHub evidence that the environment was created/enabled and used on PR #3.
- Reclassified the current blocker as Codex environment resolution/binding/visibility failure.
- Recorded branch/PR hygiene: one active draft PR (#11); historical merged branches are not authority.
- Removed the stale temporary `m7-control-sync.yml` workflow from the canonical tree.

### 1.4.4 — 2026-08-26
- Recorded current authoritative M7 checkpoint and green CI.
- Recorded current Codex connector response, but incorrectly classified it as a missing-environment blocker; superseded by v1.4.5.
