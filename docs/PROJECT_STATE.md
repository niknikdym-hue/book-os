# BOOK OS — PROJECT STATE

**Status:** ACTIVE CHECKPOINT  
**Version:** 0.8.0  
**Date:** 2026-08-24  
**Canonical repository:** `https://github.com/niknikdym-hue/book-os`

## Current phase

**IMPLEMENTATION MILESTONE 0 — TASK 001 ACCEPTED / READY FOR MERGE**

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

## Task 001 acceptance

Task contract:

`docs/tasks/CODEX_TASK_001_BOOTSTRAP.md`

PR:

`#3 — Task 001 — executable local-first skeleton`

Implementation branch:

`codex/task-001-bootstrap`

Accepted implementation commit:

`f4217dab4ff1d97e0cda14b3aacc87e1b61886cf` — `Fix native sidecar launch and shutdown`

Accepted baseline `main` for Task 001:

`c404996e3713a4e51d9f7f04e0ad2e010f1b7f31`

### Repository-side evidence

GitHub Actions run:

`32738392596` — `SUCCESS`

All required jobs passed:

- `local-core` — success;
- `desktop` — success;
- `tauri-smoke` — success;
- `secret-scan` — success.

Round 5B changed only the bounded M0 surface required for the final defects:

- deterministic relative `BOOK_OS_PYTHON` resolution against `apps/desktop`;
- absolute `BOOK_OS_PYTHON` passthrough;
- synchronous/idempotent sidecar cleanup on native exit;
- focused Rust path-resolution tests;
- README clarification and matching design-hash update.

External/model API calls: `0`.  
Paid API calls: `0`.

### Owner-Mac native evidence

Owner re-verified the accepted implementation commit on the development Mac using the README repo-relative launch command.

Criterion 8 — **PASS**:

- native BOOK OS window displayed `Local Core healthy`.

Criterion 9 — **PASS**:

- after normal window close, `pgrep -fl 'book_os_core' || true` returned no process;
- after a second launch and `Cmd-Q`, the same process check again returned no process.

The previously observed reproducibility and delayed-shutdown defects are therefore closed on the accepted implementation.

## Central Brain verdict

**TASK 001 / M0 — ACCEPTED**

The executable local-first foundation is accepted:

- native Tauri + React/TypeScript desktop shell;
- Python 3.12 local core;
- authenticated loopback health boundary with random per-launch token/port;
- SQLite/Alembic bootstrap with foreign-key/WAL coverage;
- reproducible local setup;
- green Python/TypeScript/Rust/secret-scan CI;
- deterministic sidecar shutdown;
- no paid/model API dependency.

No architecture redesign or Owner decision is required.

## Next permitted action

1. Merge PR #3 to `main` through the accepted review path.
2. Verify the resulting canonical `main` HEAD and CI.
3. Only after that merge, issue the next bounded implementation task for **M1 — Authority & Persistence Engine** from `IMPLEMENTATION_ROADMAP_v0.1.md`.

Do not start M1 against the pre-merge Task 001 branch.

## M1 capability to unlock after merge

M1 is the next accepted roadmap milestone and will implement only the bounded authority-bearing persistence foundation:

- core ontology persistence;
- immutable Revision;
- Authority statuses;
- Decision / Approval / Provenance;
- ChangeProposal with stale-baseline protection;
- transactions/invariants;
- backup/export primitive.

M1 must have its own exact-baseline task contract and acceptance evidence.

## Operational rule

A design/task/implementation result becomes canonical repository authority only after it is committed to `main` through the accepted review path.

Task 001 is accepted by Central Brain, but until PR #3 is merged, `main` still contains the pre-M0 implementation baseline.

## Stop conditions

Escalate to Owner before changing product intent, human authority, regional-access requirement, public/private data boundary, major recurring cost, quality floor, or BOOK OS/Audio Studio authority boundary.

## Recovery rule

If the chat disappears:

1. Open repository `main`.
2. Read README recovery order and `DESIGN_INDEX.md`.
3. Read this file.
4. Read `TASK_EXECUTION_PROTOCOL_v0.1.md`.
5. Verify whether PR #3 has been merged.
6. If PR #3 is merged and `main` contains the accepted Task 001 implementation, continue with the bounded M1 task only.
7. If PR #3 is not merged, do not start M1; complete the Task 001 merge path first.
