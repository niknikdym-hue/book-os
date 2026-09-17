# MYS-01 — FICTION AUTHORITY / REVISION / STALENESS CORE

**Status:** IMPLEMENTATION / STACKED DRAFT  
**Date:** 2026-09-18  
**Repository:** `niknikdym-hue/book-os`  
**Base:** `brain/task-022-mystery-os-foundation-20260917` @ `cabb66ec541b76a1bd91e920ecd3ffa788e89186`  
**Branch:** `codex/mys-01-fiction-authority-20260918`

## Purpose

Implement the smallest executable core needed to turn MYSTERY OS authority from documentation into a fail-closed editorial machine without coupling fiction semantics to the current nonfiction database/UI.

This slice implements:

- typed mystery authority kinds;
- immutable revision envelopes bound to exact content hashes;
- human-only acceptance/locking transitions;
- dependency graph and transitive staleness propagation;
- exact-revision dependency binding;
- deterministic writing-admission checks against required fresh authority;
- tests proving no AI self-approval, no mutation of accepted revisions, transitive staleness and fail-closed writing admission.

## Deliberately OUT

- database migrations;
- FastAPI routes;
- Desktop UI;
- Case/timeline/clue semantic validators (`MYS-02`);
- NarrativeContract semantics beyond authority binding (`MYS-03+`);
- model/provider/API calls;
- Agents API execution;
- real manuscript or `Линия 112` private story data;
- merge to the Task 022 design branch or `main`.

## Design rules

1. Reuse BOOK OS authority primitives where semantics are shared (`AuthorityStatus`, hashes, IDs, human-approval errors).
2. Do not create a second generic authority system.
3. Accepted/locked revision content is immutable; a material change creates a new DRAFT revision.
4. Dependencies bind to exact upstream revision IDs, not only entity names.
5. If an upstream entity moves to a newer revision, dependents bound to the old revision become stale transitively.
6. `WRITING_ALLOWED` is derived only when every required authority kind is present at an allowed accepted status and no bound dependency is stale.
7. AI/SYSTEM may create/propose/review diagnostics but cannot grant APPROVED/LOCKED authority.
8. All tests are local/deterministic and perform zero provider/model calls.

## Acceptance evidence

Required before this slice can be considered technically GREEN:

- new deterministic unit tests pass;
- existing local-core test suite remains green;
- `ruff check` passes;
- `mypy` strict passes;
- zero paid/provider calls;
- no schema/database migration;
- Central Brain review of the stacked diff.

Software GREEN is not MYSTERY OS product acceptance. Task 022 remains separately human-gated.
