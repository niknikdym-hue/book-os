# BOOK OS — PROJECT STATE

**Status:** ACTIVE CHECKPOINT  
**Version:** 0.5.0  
**Date:** 2026-08-23  
**Canonical repository:** `https://github.com/niknikdym-hue/book-os`

## Current phase

**PRE-IMPLEMENTATION AUDIT COMPLETE → IMPLEMENTATION MILESTONE 0 READY**

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
- Implementation sequence: `IMPLEMENTATION_ROADMAP_v0.1.md`
- Cross-cutting hardening: `PRE_IMPLEMENTATION_HARDENING_v0.1.md`

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

**State:** READY TO EXECUTE.

## Next permitted action

Codex Task 001 only:

- create Tauri + React desktop skeleton;
- create Python/FastAPI local-core sidecar;
- authenticated loopback health integration;
- SQLite migration skeleton;
- CI/non-paid tests;
- dependency lockfiles/minimal security scanning consistent with Task 001.

Do not implement Model Gateway, ontology persistence, AI calls, Research, Memory or BookBench in Task 001.

## Known blockers

None.

Operational rule: a design file becomes repository authority only after it is committed to canonical GitHub `main`. Chat-generated material alone is not authority.

## Stop conditions

Escalate to Owner before changing product intent, human authority, regional-access requirement, public/private data boundary, major recurring cost, quality floor, or BOOK OS/Audio Studio authority boundary.

## Recovery rule

If the chat disappears:

1. Open repository `main`.
2. Read README recovery order and `DESIGN_INDEX.md`.
3. Read this file.
4. Inspect active task/PR and exact HEAD.
5. Continue only the `Next permitted action` unless newer accepted authority supersedes it.
