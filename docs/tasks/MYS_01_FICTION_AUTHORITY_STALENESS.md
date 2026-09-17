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
- explicit HUMAN provenance for APPROVED/LOCKED transitions;
- separate **working/latest** and **effective/accepted** authority heads;
- strict revision lineage through `supersedes_revision_id`;
- dependency graph and transitive staleness propagation;
- exact dependent-revision + upstream-revision dependency binding;
- immutable dependencies after acceptance;
- dependency-cycle rejection;
- acceptance rejection when a dependent consumes an unaccepted/stale upstream revision;
- deterministic writing-admission checks against governing fresh authority;
- tests proving no AI self-approval, no mutation of accepted revisions, no draft leakage into governing authority, transitive staleness and fail-closed writing admission.

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
3. New content always begins as `DRAFT`; content identity, hash and lineage are immutable for a revision.
4. A material change creates a new revision that directly supersedes the current working revision.
5. A working DRAFT/PROPOSED/REVIEWED revision **does not replace** the currently effective APPROVED/LOCKED authority.
6. Only a HUMAN-approved exact revision becomes effective and can invalidate downstream effective authority.
7. Dependencies bind both the exact dependent revision and exact upstream revision, not only entity names.
8. Dependency edits occur before acceptance. APPROVED/LOCKED/SUPERSEDED revision dependencies are frozen.
9. By default a new dependency binds to governing effective authority; binding to a parallel working upstream must be explicit.
10. A dependent cannot become APPROVED while any bound upstream revision is unaccepted, replaced or transitively stale.
11. When effective upstream authority changes, accepted dependents bound to the old revision become stale transitively.
12. `WRITING_ALLOWED` is derived from effective APPROVED/LOCKED authority only. Unaccepted working revisions cannot impersonate governing authority.
13. AI/SYSTEM may draft/propose/review diagnostics but cannot grant APPROVED/LOCKED authority.
14. All tests are local/deterministic and perform zero provider/model calls.

## Why working/effective separation is mandatory

BOOK OS Authority Protocol requires that a rejected or unaccepted proposal leave prior accepted authority unchanged.

Therefore:

- `StoryDefinition v1 APPROVED` remains governing while `v2 DRAFT` is explored;
- existing `CaseSolution` / scenes do not become stale merely because v2 exists;
- only HUMAN acceptance of `StoryDefinition v2` promotes v2 to effective authority;
- that promotion then makes downstream objects bound to v1 stale;
- downstream repairs must be new revisions, not silent dependency rewrites.

This prevents experimental edits from destabilizing an in-progress book while still making material accepted changes propagate fail-closed.

## Acceptance evidence

Required before this slice can be considered technically GREEN:

- new deterministic unit tests pass;
- existing local-core test suite remains green;
- `ruff format --diff .` passes;
- `ruff check .` passes;
- strict `mypy src` passes;
- zero paid/provider calls;
- no schema/database migration;
- Central Brain review of the stacked diff.

Apple signing/notarization credentials are an unrelated external distribution gate and are not MYS-01 acceptance evidence.

Software GREEN is not MYSTERY OS product acceptance. Task 022 remains separately human-gated.
