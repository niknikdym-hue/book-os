# BOOK OS — PROJECT STATE

**Status:** ACTIVE CHECKPOINT  
**Version:** 1.0.0  
**Date:** 2026-08-25  
**Canonical repository:** `https://github.com/niknikdym-hue/book-os`

## Current phase

**IMPLEMENTATION MILESTONE 2 — TASK 003 READY**

## Accepted authority

- Product/Authority baseline: `BOOK_OS_AUTHORITY.md`
- Product spec: `PRODUCT_SPEC_v0.1.md`
- Core Ontology: `CORE_ONTOLOGY.md` v0.2.0
- Editorial contracts/gates: `EDITORIAL_PROTOCOLS_v0.1.md`
- Technical Architecture: `TECHNICAL_ARCHITECTURE_v0.1.md`
- Security/availability: `SECURITY_AVAILABILITY_v0.1.md`
- Implementation roadmap: `IMPLEMENTATION_ROADMAP_v0.1.md`
- Execution control: `TASK_EXECUTION_PROTOCOL_v0.1.md`
- Complete recovery map: `DESIGN_INDEX.md`

## Completed milestones

### M0 / Task 001 — ACCEPTED AND MERGED

- PR `#3 — Task 001 — executable local-first skeleton`
- canonical M0 merge: `b2bbe3dd208e15cbca0420e90c1b4adadab7acda`
- native Owner-Mac `Local Core healthy`: PASS
- sidecar cleanup after normal close and Cmd-Q: PASS

M0 provides the accepted Tauri + React desktop, Python local-core, authenticated loopback boundary, SQLite/Alembic bootstrap and non-paid CI baseline.

### M1 / Task 002 — ACCEPTED AND MERGED

- contract: `docs/tasks/CODEX_TASK_002_AUTHORITY_PERSISTENCE.md`
- PR: `#5 — Task 002 — Authority & Persistence Engine`
- accepted implementation HEAD: `e6f749b8797def444d9c92036c713eef43198f92`
- canonical M1 merge: `c2cf2e88c81797ff3f67873b1d406ecc7f806e84`
- final strict CI run: `32878002451` — SUCCESS
  - `local-core` — success (`ruff format --check`, `ruff check`, mypy, 15 pytest tests)
  - `desktop` — success
  - `tauri-smoke` — success
  - `secret-scan` — success
- external/model calls: `0`; paid calls: `0`

M1 now enforces/recoverably stores:

- stable sortable authority identities;
- immutable revision snapshots;
- deterministic canonical JSON + SHA-256 hashes;
- Authority Protocol status history;
- exact revision-id/hash ChangeProposal baselines;
- transactional stale-baseline compare-and-set;
- human Decision / Approval;
- append-only Provenance + input revision links;
- rollback on injected authority-transition failure;
- WAL-safe SQLite backup/restore with manifest/checksum/integrity/schema checks;
- tampered/newer-schema restore rejection and no-silent-downgrade policy.

Synthetic M1 evidence used 100 entities / 2000 revisions / 1900 accepted proposals-decisions-approvals without external/paid calls.

## Active implementation task

`docs/tasks/CODEX_TASK_003_BOOK_CREATION_CONTRACTS.md`

**State:** `READY`

Milestone:

`M2 — Book Creation / Book Contract / Architecture / Chapter Contract`

Planned implementation branch:

`brain/task-003-book-creation-contracts`

## WHY THIS IS NEXT

M1 made authority safe but the product still cannot create a real book project. M2 is the shortest critical-path slice that converts the runtime/authority kernel into a usable authoring product surface.

After M2, the Owner must be able to complete this native local-first path without AI/chat state:

`Projects → New Business Book → Book Contract approval → Architecture approval → Chapter → Chapter Contract approval`.

## Task 003 scope guard

M2 implements only structured local project creation/contracts and their minimal desktop/API surfaces.

Do not implement yet:

- model/provider gateway or generation;
- manuscript drafting/editor;
- Research Engine / Claim Ledger;
- Book Memory/embeddings;
- Editorial Inbox;
- BookBench;
- Russia provider lane;
- Literary Master/export/audio handoff;
- cloud accounts/sync/billing.

## Next permitted action

1. Synchronize `docs/DESIGN_FILE_HASHES.sha256` after this state + Task 003 contract.
2. Create `brain/task-003-book-creation-contracts` from the resulting exact `main` HEAD.
3. Implement only `docs/tasks/CODEX_TASK_003_BOOK_CREATION_CONTRACTS.md`.
4. Open one PR to `main`, run objective M2 acceptance, rework only concrete blockers.
5. Central Brain ACCEPT + merge M2 before starting M3.

## Known blockers

No architecture or Owner decision blocker for M2.

## Operational rule

`main` is accepted project-development authority. Implementation code uses bounded branches/PRs. Central Brain may make small project-control updates directly to `main` when a separate PR adds no review value.

## Recovery rule

If the chat disappears:

1. Open repository `main`.
2. Read README recovery order and `DESIGN_INDEX.md`.
3. Read this file and `TASK_EXECUTION_PROTOCOL_v0.1.md`.
4. Read `docs/tasks/CODEX_TASK_003_BOOK_CREATION_CONTRACTS.md`.
5. Inspect `origin/main` and `brain/task-003-book-creation-contracts`.
6. Continue only M2 until Central Brain ACCEPT/merge; do not start M3 automatically.
