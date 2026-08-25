# CODEX TASK 003 — BOOK CREATION / CONTRACTS / ARCHITECTURE

**Status:** READY  
**Milestone:** M2 — Book Creation, Book Contract, Architecture, Chapter Contract  
**Owner:** BOOK OS Central Brain  
**Execution role:** bounded implementation executor

## WHY NOW

Task 002 / M1 is accepted and merged. BOOK OS now has durable immutable revisions, exact-baseline proposals, human Decision/Approval/Provenance, stale-write protection and verified backup/restore. The next critical-path dependency is the first real book-authoring vertical: create a Business Nonfiction project and materialize/approve the contracts that later drafting must obey.

## PRODUCT / SYSTEM VALUE

After acceptance, the Owner can use the native BOOK OS app to:

`Projects → New Business Book → Book Contract → approved Architecture → Chapter → approved Chapter Contract`

All durable material state is local and first-class. Chat memory and AI are not required.

## DEPENDENCIES / BASELINE

- Repository: `niknikdym-hue/book-os`
- Exact execution baseline: supplied by Central Brain after this task/state/hash control update.
- Required prior milestone: `Task 002 / M1 — ACCEPTED AND MERGED`.
- Read: `BOOK_OS_AUTHORITY.md`, `CORE_ONTOLOGY.md`, `PRODUCT_SPEC_v0.1.md`, `EDITORIAL_PROTOCOLS_v0.1.md`, `TECHNICAL_ARCHITECTURE_v0.1.md`, `SECURITY_AVAILABILITY_v0.1.md`, `TASK_EXECUTION_PROTOCOL_v0.1.md`, `PROJECT_STATE.md`.
- External/model credentials: none.
- External/model calls: prohibited; paid calls = 0.

## EFFICIENCY RATIONALE

Build one vertical slice on the accepted Tauri + React + Python local-core + SQLite stack. Reuse M1 AuthorityService for every authority-bearing document. Do not add a frontend framework, remote backend, provider SDK, event-sourcing system or generic form engine.

Use per-book local storage consistent with Technical Architecture:

`<BOOK_OS_DATA_DIR>/projects/<book_id>/project.sqlite`

with a small project manifest for discovery. Real manuscript content is not stored in the public software repository.

## GOAL

A native user can create a Business Nonfiction Book-from-Zero project, fill and human-approve a Book Contract, fill and human-approve an Architecture containing stable chapters, then fill and human-approve a Chapter Contract for a selected chapter, with the exact authority/revision history persisted locally.

## IN SCOPE

### A. M2 persistence

Add one migration after `0002` for only M2 project/workspace metadata required now:

- `book_projects`;
- stable `chapters`;
- a minimal working-revision pointer for editable authority documents if needed.

Do not duplicate M1 revision/decision/provenance tables.

### B. Project storage/discovery

- Tauri passes an OS application-data directory to local-core without exposing the session token to React.
- local-core stores book projects under `projects/<book_id>/` with `project.sqlite` and a small non-secret manifest.
- project list/open survives app restart.
- one project database remains independently backup/recoverable through M1 primitives.

### C. New Book

Support only first-pilot creation:

- mode: `BOOK_FROM_ZERO`;
- domain: `BUSINESS_NONFICTION`;
- working title;
- one required primary subtype;
- optional different secondary subtype;
- profile/ruleset version.

Accepted subtype list is the 10-item Business taxonomy in Product Spec.

### D. Book Contract

Typed payload with all required fields from `EDITORIAL_PROTOCOLS_v0.1.md`:

- reader;
- reader_problem;
- central_promise;
- central_thesis;
- unique_angle;
- reader_trajectory;
- explicit_exclusions;
- evidence_policy;
- voice_genre_constraints;
- readiness_criteria.

Allow durable DRAFT saves and explicit human approval. Approval must use M1 proposal/Decision/Approval history; no silent mutation.

### E. Book Architecture

Typed architecture payload sufficient for M2:

- ordered parts/chapters;
- stable chapter IDs;
- purpose / distinct contribution of chapters;
- intellectual progression;
- concept allocation;
- promise/thesis coverage;
- dependencies;
- major transitions.

Architecture cannot be approved until Book Contract is `APPROVED` or `LOCKED`. Human approval uses M1 authority history. Approved architecture materializes/updates stable chapter identities without deleting historical revisions.

### F. Chapter Contract

For an architecture chapter, typed payload with required fields:

- chapter_purpose;
- new_contribution;
- reader_prior_state;
- reader_after_state;
- required_claims;
- required_or_permitted_research;
- required_scenes_examples;
- reserved_elsewhere;
- opening_requirements;
- ending_requirements;
- transition_requirements.

Durable DRAFT save + explicit human approval through M1. Cannot approve for a chapter that is not represented by the current approved architecture.

### G. Local API + native bridge

Expose only the local typed project endpoints required for the above flow. React must not receive the bearer session token. Tauri may provide a bounded authenticated proxy restricted to loopback local-core `/api/` paths and allowed HTTP methods; it must not become an arbitrary network proxy.

### H. Desktop UI

Replace the M0 health-only screen with a minimal professional M2 surface containing:

- persistent Local Core health indicator;
- Projects list;
- New Book form;
- project dashboard/current workflow stage;
- Book Contract editor + status + Save Draft / Approve;
- Architecture editor with ordered chapter rows + status + Save Draft / Approve;
- Chapter Contract editor for a selected chapter + status + Save Draft / Approve.

No chat panel and no AI buttons in M2.

## OUT OF SCOPE

- Reader/market research automation;
- model/provider gateway or generation;
- manuscript editor/drafting;
- Research Engine / Claim Ledger;
- Book Memory/embeddings;
- Editorial Inbox;
- BookBench;
- Russia provider lane;
- Literary Master/export/audio handoff;
- cloud accounts/sync/billing;
- collaboration;
- full design system.

## REQUIRED INVARIANTS

1. Project survives app/core restart from local durable state.
2. Each project has independent `project.sqlite`.
3. Stable BookProject/chapter IDs survive title/content edits.
4. Business subtype validation is deterministic.
5. Book Contract, Architecture and Chapter Contract content changes create immutable revisions, not in-place edits.
6. Human approval produces M1 Decision + Approval and exact current authority.
7. Prior approved revision remains recoverable after replacement.
8. Architecture approval is blocked before Book Contract approval.
9. Chapter Contract approval is blocked without current approved Architecture membership.
10. React never receives the local-core bearer token.
11. Native proxy cannot address arbitrary host/path.
12. No AI/external/paid calls.

## ACCEPTANCE / EVIDENCE

1. Exact baseline recorded.
2. Fresh M2 project DB migrates through `0001→0002→0003`.
3. Existing M1 DB upgrades to M2.
4. New Book validation accepts the 10 canonical Business subtypes and rejects invalid/same-secondary values.
5. Created project can be listed/opened after constructing a new service instance (restart simulation).
6. Book Contract draft save is durable and versioned.
7. Book Contract approval creates human Decision/Approval and current `APPROVED` authority.
8. Editing an approved Book Contract preserves prior revision and uses exact-baseline proposal semantics.
9. Architecture approval before Book Contract approval fails explicitly.
10. Architecture draft supports ordered stable chapter IDs.
11. Approved Architecture creates/updates stable chapter records.
12. Reordering/renaming a chapter preserves chapter ID.
13. Chapter Contract approval for non-current-architecture chapter fails explicitly.
14. Chapter Contract draft/approval persists exact revision/Decision/Approval history.
15. Project workflow stage/dashboard updates deterministically.
16. API auth still rejects unauthenticated requests.
17. Tauri bridge is restricted to local `/api/` paths/methods and keeps token native.
18. Desktop test covers health + project creation/contract flow at component/API-boundary level with mocked Tauri invoke only.
19. Python Ruff/mypy/pytest green.
20. TypeScript lint/type/test/build green.
21. Rust/Tauri tests/check green.
22. secret/dependency scans green.
23. external/model calls = 0; paid calls = 0.
24. no private manuscript/secrets fixtures.
25. scope contains no M3+ implementation.

## REGRESSION REQUIREMENTS

M0/M1 remain green: loopback/auth/random token/sidecar lifecycle, migrations, immutable history, stale protection and backup/restore.

## RISKS / STOP CONDITIONS

Return to Central Brain rather than expanding scope if M2 would require changing Authority Protocol, replacing SQLite/local-first ownership, exposing token to React, adding provider calls/cloud infrastructure, or weakening M1 invariants.

## UNLOCKS NEXT

Central Brain acceptance of M2 unlocks M3 — Model Gateway + first controlled bounded drafting.

Do not start M3 automatically.

## BRANCH / PR

`accepted main baseline → brain/task-003-book-creation-contracts → PR → Central Brain ACCEPT → merge`

No force push; no merge before acceptance.
