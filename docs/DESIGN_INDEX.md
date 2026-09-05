# BOOK OS — DESIGN / RECOVERY INDEX v0.3

**Status:** CURRENT RECOVERY AUTHORITY  
**Date:** 2026-09-06  
**Canonical repository:** `https://github.com/niknikdym-hue/book-os`

## Purpose

This file is the recovery map for BOOK OS. A successor must be able to recover the current product authority and execution state without chat history.

## Recovery order

Read in this order:

1. `BOOK_OS_AUTHORITY.md` — non-negotiable product/authority decisions and explicit supersessions.
2. `PROJECT_STATE.md` — exact accepted checkpoint, canonical schema and next permitted action.
3. `decisions/2026-08-29-global-openai-first.md` — current provider/program decision; former Russia/no-VPN M8 is SUPERSEDED.
4. `decisions/2026-09-06-operation-level-model-routing.md` — Owner decision: no single-model monopoly; route the best executor per editorial operation using task-specific evidence, quality/risk and cost.
5. `IMPLEMENTATION_ROADMAP_v0.2.md` — current execution roadmap.
6. `tasks/TASK_011_REAL_BOOK_PILOT.md` — current real-book pilot contract and GO/NO-GO evidence rules.
7. `CORE_ONTOLOGY.md` — first-class entities and invariants.
8. `PRODUCT_SPEC_v0.1.md` — product scope, user experience and MVP success.
9. `EDITORIAL_PROTOCOLS_v0.1.md` — Book/Chapter Contracts, agent roles and human acceptance.
10. `RESEARCH_AND_CLAIMS_v0.1.md` — Research Engine, Claim Ledger and evidence policy.
11. `MODEL_GATEWAY_v0.1.md` — provider-neutral execution gateway. Interpret any old regional wording through the superseding 2026-08-29 decision and operation-level routing through the 2026-09-06 Owner decision.
12. `BOOK_MEMORY_v0.1.md` — whole-book memory and retrieval.
13. `BOOKBENCH_v0.1.md` — quality/eval system and AI-prose pathology detection.
14. `TECHNICAL_ARCHITECTURE_v0.1.md` — local-first technical architecture and stack.
15. `SECURITY_AVAILABILITY_v0.1.md` — security/privacy/backup baseline. Any former Russia-specific launch gate is historical unless reaffirmed by newer authority.
16. `AUDIO_HANDOFF_v0.1.md` — immutable integration boundary with Audio Studio.
17. `PRE_IMPLEMENTATION_HARDENING_v0.1.md` — security, rights, supply-chain, recovery, performance and release hardening.
18. `TASK_EXECUTION_PROTOCOL_v0.1.md` — task necessity, efficiency, scope, evidence and acceptance rules.
19. `tasks/` — bounded task history/current contracts.
20. Recent accepted PRs, exact HEADs, CI runs, review threads and `main`.

Chat history is optional working context. It is never authority.

## Current accepted implementation checkpoint

Current accepted implementation includes:

- M0–M7 / Tasks 001–008;
- Task 010 — Literary Master + exports;
- Task 011 tooling — real Business Nonfiction pilot instrumentation;
- Task 012 — macOS launch hardening.

Canonical schema: Alembic `0010`.

The exact current `main` SHA and acceptance evidence live only in `PROJECT_STATE.md`; do not copy an old SHA from a historical task and treat it as current.

## Current critical path

`real Business Nonfiction pilot → Literary Master → HUMAN GO | CONDITIONAL_GO | NO_GO`

No additional infrastructure milestone is required before the first complete book unless the real pilot reveals a concrete regression.

## Superseded program lane

The former `M8 — Russia/no-VPN provider lane` / Task 009 / PR #12 is **SUPERSEDED** and not part of the current program.

Do not:

- request Yandex/GigaChat credentials as a prerequisite to the current pilot;
- resume Stage B live provider promotion;
- block the real-book pilot on regional-provider availability;
- merge PR #12 as a current milestone.

The historical work remains available as salvage evidence only.

## Mapping to the baseline design questions

| Requirement | Authority/spec |
|---|---|
| Product goal / first user | `BOOK_OS_AUTHORITY.md`, `PRODUCT_SPEC_v0.1.md` |
| End-to-end workflow | `BOOK_OS_AUTHORITY.md`, `EDITORIAL_PROTOCOLS_v0.1.md` |
| Book State / Authority Graph | `BOOK_OS_AUTHORITY.md`, `CORE_ONTOLOGY.md` |
| Entities / relationships | `CORE_ONTOLOGY.md` |
| Book Contract / Chapter Contract | `EDITORIAL_PROTOCOLS_v0.1.md` |
| Claim Ledger / research evidence | `RESEARCH_AND_CLAIMS_v0.1.md` |
| Editorial agents / human acceptance | `EDITORIAL_PROTOCOLS_v0.1.md` |
| Model Gateway / current provider strategy / operation-level routing | `MODEL_GATEWAY_v0.1.md`, `decisions/2026-08-29-global-openai-first.md`, `decisions/2026-09-06-operation-level-model-routing.md` |
| Book Memory | `BOOK_MEMORY_v0.1.md` |
| BookBench | `BOOKBENCH_v0.1.md` |
| Versioning / provenance | `CORE_ONTOLOGY.md`, `TECHNICAL_ARCHITECTURE_v0.1.md` |
| Technology stack / build-vs-buy | `TECHNICAL_ARCHITECTURE_v0.1.md`, `BOOK_OS_AUTHORITY.md` |
| Security / privacy / recovery | `SECURITY_AVAILABILITY_v0.1.md`, newer explicit decisions |
| Literary Master / downstream audio | `BOOK_OS_AUTHORITY.md`, `AUDIO_HANDOFF_v0.1.md` |
| Current MVP/pilot acceptance | `PROJECT_STATE.md`, `TASK_011_REAL_BOOK_PILOT.md` |
| Task necessity / bounded delivery | `TASK_EXECUTION_PROTOCOL_v0.1.md` |

## Baseline rule

Implementation may refine internal code structure but may not change accepted product behavior, Authority Protocol, evidence semantics, Literary Master semantics, human-acceptance boundaries, mandatory hardening requirements or task-execution control rules without an explicit decision record.

When older baseline documents conflict with a newer explicit Owner decision, the newer decision is authoritative and the older requirement is SUPERSEDED rather than silently rewritten.
