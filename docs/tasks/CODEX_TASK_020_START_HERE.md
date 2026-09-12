# CODEX TASK 020 — START HERE

**Status:** IMPLEMENTATION HANDOFF  
**Date:** 2026-09-09  
**Canonical repository:** `https://github.com/niknikdym-hue/book-os`  
**Implementation branch:** `codex/task-020-implementation-20260909`  
**Baseline main:** `3011b4781a6f548b5869571d6be643b95d4cd30b`

## HARD REPOSITORY GUARD

Before doing any implementation, verify the checkout remote repository is exactly:

`https://github.com/niknikdym-hue/book-os.git`

or an authenticated equivalent that resolves to repository full name:

`niknikdym-hue/book-os`

If the current checkout is `eksamio-brain`, `ege`, `books-for-litres`, or any other repository, **do not use it** and do not infer BOOK OS state from it. Switch to / clone `niknikdym-hue/book-os` instead.

`niknikdym-hue/book-os` is the BOOK OS source of truth. It is not `niknikdym-hue/eksamio-brain`.

After fetching, verify:

- `origin/main` contains `docs/BOOK_OS_AUTHORITY.md` v0.7.0;
- `origin/main` contains `docs/tasks/TASK_020_FRONTIER_QUALITY_LOOP_LOCAL_BRAIN.md`;
- `origin/main` contains `docs/decisions/2026-09-09-frontier-plus-independent-local-brain.md`;
- `origin/main` includes accepted Task 017 / PR #25 merge `3011b4781a6f548b5869571d6be643b95d4cd30b`;
- implementation must reconcile from this current `main`, not from the superseded `dc52fcf6...` baseline.

## REQUIRED READING

Read fully before editing:

1. `docs/BOOK_OS_AUTHORITY.md`
2. `docs/PROJECT_STATE.md`
3. `docs/tasks/TASK_020_FRONTIER_QUALITY_LOOP_LOCAL_BRAIN.md`
4. `docs/decisions/2026-09-09-frontier-plus-independent-local-brain.md`
5. `docs/tasks/TASK_017_SERIES_PRODUCTION_GATES.md`
6. merged PR #25 / exact-head CI `34438329008` because Task 017 is now an accepted dependency.

## EXECUTION ORDER

1. Verify exact repository and current `main`.
2. Treat Task 017 as accepted dependency; do not duplicate its semantics.
3. Implement Task 020 in bounded slices on this branch.
4. Reuse mature commodity modules where the Task 020 contract says REUSE/ADOPT; do not rebuild them without a documented product reason.
5. Keep BOOK OS-specific editorial authority/evidence/BookBench/Series/Literary Master semantics canonical and local.
6. Run deterministic tests/CI with zero provider/model/paid calls.
7. Push commits to this branch and update the implementation PR.

## FIRST BOUNDED SLICE

Implement only the first Task 020 foundation before broader orchestration/UI work:

1. explicit quality-loop domain types/state machine with no model calls;
2. provider-neutral local model manifest + hardware/readiness abstraction;
3. local executor adapter seam with deterministic fake-adapter tests;
4. prove Task 017 `WRITING_ALLOWED` remains the precondition where Writer execution is involved;
5. no paid/provider calls and no manuscript generation.

## PROHIBITED

- Do not work from `eksamio-brain`.
- Do not reconstruct Task 020 from chat memory.
- Do not write the SMM manuscript.
- Do not make paid/provider model calls in implementation/tests/CI.
- Do not bypass Task 017 / `WRITING_ALLOWED` semantics.
- Do not self-accept or self-merge.
- Do not use OpenAI output as training/distillation/fine-tuning targets for a competing local model.

## RETURN FORMAT

Return:

- resolved repo + remote;
- baseline `main` SHA;
- implementation branch HEAD;
- Task 017 dependency disposition;
- files/commits changed;
- acceptance matrix for Task 020 slice;
- test/CI results;
- external/model/paid calls = 0;
- architecture deviations/blockers;
- next safe action.
