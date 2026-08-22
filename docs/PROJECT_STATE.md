# BOOK OS — PROJECT STATE

**Status:** ACTIVE CHECKPOINT  
**Version:** 0.6.0  
**Date:** 2026-08-23  
**Canonical repository:** `https://github.com/niknikdym-hue/book-os`

## Current phase

**PRE-IMPLEMENTATION AUDIT + TASK GOVERNANCE COMPLETE → IMPLEMENTATION MILESTONE 0 READY**

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

## Pre-implementation audit verdict

`GO_FOR_IMPLEMENTATION`.

No architecture redesign is required before Milestone 0. The final audit added mandatory milestone-mapped hardening for:

- prompt injection / untrusted retrieved content;
- SSRF/network fetch and hostile file-import boundaries;
- source reuse rights/permissions;
- software supply-chain/SBOM/dependency security;
- signed/notarized update trust before external distribution;
- migration/backup disaster tests;
- measured performance/scale envelope;
- durable authoring UX/crash recovery;
- accessibility/localization baseline;
- commercial/legal provider-brokerage launch gate;
- data lifecycle/purge semantics;
- Literary Master release reproducibility.

These requirements are authority through `PRE_IMPLEMENTATION_HARDENING_v0.1.md`; most are intentionally scheduled after M0 and must not inflate Task 001.

## Task-governance verdict

Every implementation task must now pass the qualification gate in `TASK_EXECUTION_PROTOCOL_v0.1.md` before Codex receives it.

Mandatory line of sight:

`accepted milestone dependency → WHY NOW → product/system value → smallest professional implementation → objective acceptance evidence → capability unlocked next`.

Tasks that are speculative, not on the MVP critical path, unjustified by a blocker/measurement, or broader than an independently acceptable capability must not be issued.

By default only one critical-path implementation task is active. Parallel tasks require explicit Central Brain independence/safety justification.

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

**State:** READY TO EXECUTE after this task-governance baseline is accepted in `main` and Central Brain locks the exact launch HEAD.

Task 001 now explicitly records:

- why it is the first dependency;
- what product/runtime capability it creates;
- why its architecture is the smallest sufficient professional option;
- bounded scope/non-goals;
- M0 hardening due now vs later;
- measurable acceptance evidence;
- the exact next milestone it unlocks.

## Next permitted action

Codex Task 001 only:

- create Tauri + React desktop skeleton;
- create Python/FastAPI local-core sidecar;
- authenticated loopback health integration;
- SQLite migration skeleton;
- CI/non-paid tests;
- dependency lockfiles/minimal M0 security scanning.

Do not implement Model Gateway, ontology persistence, AI calls, Research, Memory or BookBench in Task 001.

## Known blockers

None.

Operational rule: a design/task file becomes repository authority only after it is committed to canonical GitHub `main`. Chat-generated material alone is not authority.

## Stop conditions

Escalate to Owner before changing product intent, human authority, regional-access requirement, public/private data boundary, major recurring cost, quality floor, or BOOK OS/Audio Studio authority boundary.

Central Brain may change internal task slicing/order only when it provides a more efficient critical path without skipping accepted milestone gates or weakening hardening/quality requirements.

## Recovery rule

If the chat disappears:

1. Open repository `main`.
2. Read README recovery order and `DESIGN_INDEX.md`.
3. Read this file.
4. Read `TASK_EXECUTION_PROTOCOL_v0.1.md`.
5. Inspect active task/PR and exact HEAD.
6. Continue only the `Next permitted action` unless newer accepted authority supersedes it.
