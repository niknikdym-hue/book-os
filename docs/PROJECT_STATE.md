# BOOK OS — PROJECT STATE

**Status:** ACTIVE CHECKPOINT  
**Version:** 0.7.3  
**Date:** 2026-08-23  
**Canonical repository:** `https://github.com/niknikdym-hue/book-os`

## Current phase

**IMPLEMENTATION MILESTONE 0 — TASK 001 REWORK REQUIRED**

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

## Pre-implementation verdict

`GO_FOR_IMPLEMENTATION` remains valid.

No architecture redesign is required. Task 001 has a bounded partial implementation, but mandatory M0 runtime evidence is incomplete.

## Task-governance rule

Every implementation task must pass `TASK_EXECUTION_PROTOCOL_v0.1.md`.

Mandatory line of sight:

`accepted milestone dependency → WHY NOW → product/system value → smallest professional implementation → objective acceptance evidence → capability unlocked next`.

Only one critical-path implementation task is active by default.

## Active product baseline

- First user: Owner.
- First pilot: real Business Nonfiction book from zero.
- Two modes architecturally supported: Book from Zero + Existing Manuscript/Materials.
- Local-first desktop.
- Human final authority.
- Model/provider agnostic.
- Russia-ready requirement: no VPN, no personal foreign AI subscription/API key, compliant provider routing.
- BOOK OS and Audio Studio are separate products linked by immutable production handoff.

## Active implementation task

`docs/tasks/CODEX_TASK_001_BOOTSTRAP.md`

**State:** `REWORK_REQUIRED — CONTINUE SAME TASK`.

Remote implementation branch:

`codex/task-001-bootstrap`

### Task 001 attempt 1

Original launch baseline:

`3834486b496b7fcb26c3bda8b9a90e3350b7954c`

Confirmed partial results:

- React/TypeScript desktop scaffold started;
- Python 3.12 FastAPI local-core scaffold started;
- bearer-token health endpoint implemented with unauthenticated rejection;
- SQLite bootstrap implemented with foreign-key/WAL tests;
- initial Tauri/Rust sidecar scaffold started;
- initial CI/setup documentation started;
- Python `pytest`: PASS (2 tests);
- `ruff check`: PASS;
- `mypy`: previously PASS before subsequent annotation edit;
- TypeScript checks: PASS in second attempt;
- Rust stable/Cargo installed successfully;
- paid model/API calls: 0.

### Task 001 attempt 2

Remaining blocker was a required Tauri raster application icon. Central Brain classified it as a technical M0 packaging asset, not an Owner/product decision.

Central Brain created an original neutral temporary PNG placeholder for the remote implementation branch:

`apps/desktop/src-tauri/icons/icon.png`

Placeholder blob SHA:

`e342bb265b32f09d4e7dee61f60f33c0be48a66a`

Branch commit:

`fbbd0d6de0465a9883eb80effabf5ada7010790b`

This placeholder is not final BOOK OS branding and exists only to unblock M0 compilation. It contains no third-party asset.

Unproven / blocking acceptance items that Codex must still complete:

- rerun mypy after final Python edit;
- `cargo check` / Tauri compile after syncing the icon commit;
- real native desktop launch;
- real desktop → sidecar authenticated health integration;
- sidecar shutdown/orphan-process lifecycle evidence;
- full final secret scan;
- full fresh/reproducible setup evidence;
- final commit/push of implementation and PR.

These are environment/execution completion items, not architecture blockers.

## Next permitted action

**Continue Task 001 only. Do not create Task 002.**

Codex must:

1. preserve its bounded uncommitted Task 001 work;
2. fetch `origin` and reconcile the remote `codex/task-001-bootstrap` icon commit without losing local work;
3. rerun the complete Task 001 acceptance matrix;
4. fix only defects required for Task 001 acceptance;
5. when all mandatory M0 gates pass, commit/push implementation to `codex/task-001-bootstrap` and open/return a PR;
6. stop for Central Brain acceptance.

Do not implement Model Gateway, ontology persistence, AI calls, Research, Memory or BookBench in Task 001.

## Known blockers

No known architecture or Owner blocker.

Current task can proceed after Codex syncs the remote placeholder icon and completes validation.

## Operational rule

A design/task/implementation result becomes repository authority only after it is committed to canonical GitHub `main` through the accepted review path. Chat-only and uncommitted local work are not authority.

## Stop conditions

Escalate to Owner before changing product intent, human authority, regional-access requirement, public/private data boundary, major recurring cost, quality floor, or BOOK OS/Audio Studio authority boundary.

Central Brain may change internal task slicing/order only when it provides a more efficient critical path without skipping accepted milestone gates or weakening hardening/quality requirements.

## Recovery rule

If the chat disappears:

1. Open repository `main`.
2. Read README recovery order and `DESIGN_INDEX.md`.
3. Read this file.
4. Read `TASK_EXECUTION_PROTOCOL_v0.1.md`.
5. Inspect remote branch `codex/task-001-bootstrap` and any local uncommitted Task 001 worktree.
6. Continue only the Task 001 rework described under `Next permitted action` unless newer accepted authority supersedes it.
