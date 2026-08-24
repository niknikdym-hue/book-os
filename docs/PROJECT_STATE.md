# BOOK OS — PROJECT STATE

**Status:** ACTIVE CHECKPOINT  
**Version:** 0.9.0  
**Date:** 2026-08-24  
**Canonical repository:** `https://github.com/niknikdym-hue/book-os`

## Current phase

**IMPLEMENTATION MILESTONE 1 — TASK 002 READY**

## Latest accepted design authority

- Product/Authority baseline: `BOOK_OS_AUTHORITY.md`
- Execution roles/plan: `PROJECT_EXECUTION_PLAN.md`
- Core Ontology: `CORE_ONTOLOGY.md` v0.2.0 — accepted
- Product spec: `PRODUCT_SPEC_v0.1.md`
- Editorial contracts/roles/acceptance: `EDITORIAL_PROTOCOLS_v0.1.md`
- Research/Claim Ledger: `RESEARCH_AND_CLAIMS_v0.1.md`
- Model Gateway: `MODEL_GATEWAY_v0.1.md`
- Book Memory: `BOOK_MEMORY_v0.1.md`
- BookBench: `BOOKBENCH_v0.1.md`
- Technical Architecture: `TECHNICAL_ARCHITECTURE_v0.1.md`
- Security/availability: `SECURITY_AVAILABILITY_v0.1.md`
- Audio handoff: `AUDIO_HANDOFF_v0.1.md`
- Implementation critical path: `IMPLEMENTATION_ROADMAP_v0.1.md`
- Cross-cutting hardening: `PRE_IMPLEMENTATION_HARDENING_v0.1.md`
- Task necessity/efficiency/acceptance control: `TASK_EXECUTION_PROTOCOL_v0.1.md`
- Standard implementation task skeleton: `tasks/TASK_TEMPLATE.md`

The complete recovery map is `DESIGN_INDEX.md`.

## Completed milestone

### Task 001 / M0 — ACCEPTED AND MERGED

Merged PR:

`#3 — Task 001 — executable local-first skeleton`

Accepted implementation commit:

`f4217dab4ff1d97e0cda14b3aacc87e1b61886cf`

Final accepted Task 001 branch checkpoint:

`d6d5b3d5b9630c15c3d4e99cc4894cec94260ef4`

Canonical M0 merge commit on `main`:

`b2bbe3dd208e15cbca0420e90c1b4adadab7acda`

Task 001 acceptance evidence:

- implementation CI run `32738392596` — success;
- final acceptance/state CI run `32748228147` — all jobs success;
- Owner-Mac native gate 8 PASS — `Local Core healthy`;
- Owner-Mac native gate 9 PASS — no `book_os_core` process after normal close or Cmd-Q;
- external/model API calls = 0;
- paid API calls = 0.

M0 provides the accepted executable local-first foundation:

- Tauri 2 + React/TypeScript desktop;
- Python 3.12 local core;
- authenticated loopback sidecar with random per-launch port/token;
- SQLite + Alembic bootstrap;
- deterministic sidecar launch/shutdown;
- non-paid CI and secret scanning;
- reproducible Owner-Mac setup.

## Active implementation task

`docs/tasks/CODEX_TASK_002_AUTHORITY_PERSISTENCE.md`

**State:** `READY`

Milestone:

`M1 — Authority & Persistence Engine`

Planned implementation branch:

`codex/task-002-authority-persistence`

The exact execution baseline SHA is the current canonical `origin/main` supplied by Central Brain at launch after this state/hash control update is complete. Codex must verify that exact SHA before implementation and return `BASELINE_DRIFT` if it differs.

## WHY THIS IS NEXT

M2 cannot safely persist Book Contracts, Chapter Contracts, manuscript authority, or future editorial decisions until BOOK OS can enforce and recover:

- stable entity identity;
- immutable revision snapshots;
- Authority Protocol statuses;
- exact-baseline ChangeProposal;
- stale-write rejection;
- transactional Decision / Approval;
- append-only Provenance;
- deterministic revision hashes;
- verified local backup/restore.

Task 002 implements only this M1 kernel.

## Next permitted action

1. Synchronize `docs/DESIGN_FILE_HASHES.sha256` for this state and Task 002 contract.
2. Create `codex/task-002-authority-persistence` from the resulting exact `main` HEAD.
3. Launch `CODEX_TASK_002_AUTHORITY_PERSISTENCE.md` in Codex Cloud Tasks against that exact branch/baseline.
4. After the first implementation commit is published, Central Brain opens one PR to `main`.
5. Review only Task 002 acceptance evidence; do not begin M2 until Central Brain ACCEPT and merge.

## Known blockers

No architecture blocker.

No Owner decision is required for Task 002 under the accepted M1 authority and execution protocol.

GitHub `@codex` execution has previously been unreliable; manual Codex Cloud start/publication may still be required. This is an execution-channel constraint, not a product/architecture blocker.

## Task 002 scope guard

Do not implement M2/M3+ capabilities in M1:

- no New Book / Book Contract UI;
- no manuscript editor;
- no Model Gateway/provider calls;
- no Research/Claim Ledger;
- no Book Memory/embeddings;
- no BookBench;
- no Russia provider lane;
- no Literary Master;
- no Audio Studio implementation;
- no cloud/accounts/billing;
- no distributed infrastructure.

## Operational rule

`main` contains accepted project state.

Normal implementation flow:

`accepted main baseline → bounded branch → implementation/evidence → PR → Central Brain ACCEPT → merge → PROJECT_STATE update`

Central Brain may make small authority/project-control updates directly to `main` when a separate PR adds no meaningful review value. Implementation code still goes through a bounded branch/PR.

## Stop conditions

Escalate to Owner before changing product intent, human authority, regional-access requirement, public/private data boundary, major recurring cost, quality floor, or BOOK OS/Audio Studio authority boundary.

## Recovery rule

If the chat disappears:

1. Open repository `main`.
2. Read README recovery order and `DESIGN_INDEX.md`.
3. Read this file.
4. Read `TASK_EXECUTION_PROTOCOL_v0.1.md`.
5. Read `docs/tasks/CODEX_TASK_002_AUTHORITY_PERSISTENCE.md`.
6. Inspect `origin/main` and `codex/task-002-authority-persistence`.
7. Continue only Task 002 until Central Brain acceptance/merge; do not start M2 automatically.
