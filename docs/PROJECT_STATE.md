# BOOK OS — PROJECT STATE

**Status:** ACTIVE CHECKPOINT  
**Version:** 0.7.1  
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

No architecture redesign is required. Task 001 reached a bounded partial implementation, but mandatory M0 runtime evidence is incomplete.

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

Remote implementation branch now exists:

`codex/task-001-bootstrap`

It was created by Central Brain from the current accepted `main` checkpoint. No implementation commit or PR exists yet.

### Task 001 attempt 1

Original launch baseline:

`3834486b496b7fcb26c3bda8b9a90e3350b7954c`

Codex created local bounded work but intentionally made no commit, push or PR because mandatory acceptance evidence was incomplete.

Confirmed partial results:

- React/TypeScript desktop scaffold started;
- Python 3.12 FastAPI local-core scaffold started;
- bearer-token health endpoint implemented with unauthenticated rejection;
- SQLite bootstrap implemented with foreign-key/WAL tests;
- initial Tauri/Rust sidecar scaffold started;
- initial CI/setup documentation started;
- Python `pytest`: PASS (2 tests);
- `ruff check`: PASS;
- `mypy`: PASS;
- paid model/API calls: 0.

Unproven / blocking acceptance items:

- development Mac currently lacks Rust/Cargo;
- package install/check path was interrupted by transient npm registry DNS resolution failure;
- Tauri compile/dev launch not yet evidenced;
- TypeScript lint/type/tests not yet evidenced;
- authenticated desktop → sidecar health integration not yet evidenced end-to-end;
- sidecar lifecycle/shutdown not yet evidenced;
- full CI validation not yet evidenced;
- PR does not exist yet.

These are environment/execution blockers, not architecture blockers.

## Next permitted action

**Continue Task 001 only. Do not create Task 002.**

Codex must:

1. preserve the bounded uncommitted Task 001 work;
2. fetch `origin` and align its local Task 001 branch with remote `codex/task-001-bootstrap` without losing uncommitted work;
3. verify/install the minimum trusted macOS development prerequisites required by the accepted stack (Rust stable/Cargo and existing Apple toolchain as needed);
4. restore package-registry connectivity and install from the existing/expected lockfile without opportunistic dependency upgrades;
5. complete TypeScript/Rust/Tauri validation;
6. complete real desktop ↔ authenticated local-core health and lifecycle evidence;
7. rerun the full Task 001 acceptance matrix;
8. only when mandatory gates pass, commit/push to `codex/task-001-bootstrap` and open a PR;
9. return `PASS/PARTIAL/FAIL` evidence and stop for Central Brain acceptance.

Do not implement Model Gateway, ontology persistence, AI calls, Research, Memory or BookBench in Task 001.

## Known blockers

Current bounded blockers are development-environment/toolchain only:

- Rust/Cargo absent on Owner Mac;
- transient npm registry DNS/package connectivity failure.

No owner decision is required unless installing the standard local toolchain would require a materially different platform, paid dependency, security exception or accepted architecture change.

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
5. Inspect remote branch `codex/task-001-bootstrap` and the local uncommitted Task 001 worktree if available; no PR exists yet.
6. Continue only the Task 001 rework described under `Next permitted action` unless newer accepted authority supersedes it.
