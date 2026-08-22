# BOOK OS — DESIGN BASELINE INDEX v0.1

**Status:** ACCEPTED FOR V0.1 IMPLEMENTATION  
**Date:** 2026-08-23  
**Canonical repository:** `https://github.com/niknikdym-hue/book-os`

## Purpose

This file is the map of the implementation-ready design baseline. It exists so a successor can recover BOOK OS without chat history.

## Recovery order

A new Central Brain or implementation lead must read, in order:

1. `BOOK_OS_AUTHORITY.md` — non-negotiable product/authority decisions.
2. `PROJECT_EXECUTION_PLAN.md` — roles, operating model, delivery sequence.
3. `PROJECT_STATE.md` — exact current checkpoint and next permitted action.
4. `CORE_ONTOLOGY.md` — first-class entities and invariants.
5. `PRODUCT_SPEC_v0.1.md` — product scope, user experience and MVP success.
6. `EDITORIAL_PROTOCOLS_v0.1.md` — Book/Chapter Contracts, agent roles and human acceptance.
7. `RESEARCH_AND_CLAIMS_v0.1.md` — Research Engine, Claim Ledger, evidence policy.
8. `MODEL_GATEWAY_v0.1.md` — provider independence, routing, regional policy, cost/quality gates.
9. `BOOK_MEMORY_v0.1.md` — whole-book memory and retrieval.
10. `BOOKBENCH_v0.1.md` — quality/eval system and AI-prose pathology detection.
11. `TECHNICAL_ARCHITECTURE_v0.1.md` — local-first technical architecture and stack.
12. `SECURITY_AVAILABILITY_v0.1.md` — secrets, privacy, backups, no-VPN/regional requirements.
13. `AUDIO_HANDOFF_v0.1.md` — immutable integration boundary with Audio Studio.
14. `IMPLEMENTATION_ROADMAP_v0.1.md` — milestones, acceptance gates, Codex sequencing.
15. `PRE_IMPLEMENTATION_HARDENING_v0.1.md` — mandatory security, rights, supply-chain, recovery, performance and release hardening mapped to milestones.
16. `tasks/` — active and historical bounded implementation tasks.
17. Recent commits, open PRs, tests and eval evidence.

Chat history is optional context. It is never authority.

## Mapping to the original v0.1 design questions

| Requirement | Authority/spec |
|---|---|
| 1. Product goal | `PRODUCT_SPEC_v0.1.md` |
| 2. First user | `BOOK_OS_AUTHORITY.md`, `PRODUCT_SPEC_v0.1.md` |
| 3. End-to-end workflow | `PRODUCT_SPEC_v0.1.md`, `EDITORIAL_PROTOCOLS_v0.1.md` |
| 4. Book State / Authority Graph | `BOOK_OS_AUTHORITY.md`, `CORE_ONTOLOGY.md` |
| 5. Entities / relationships | `CORE_ONTOLOGY.md` |
| 6. Book Contract | `EDITORIAL_PROTOCOLS_v0.1.md` |
| 7. Chapter Contract | `EDITORIAL_PROTOCOLS_v0.1.md` |
| 8. Claim Ledger | `RESEARCH_AND_CLAIMS_v0.1.md` |
| 9. Editorial agents | `EDITORIAL_PROTOCOLS_v0.1.md` |
| 10. Model Gateway | `MODEL_GATEWAY_v0.1.md` |
| 11. Book Memory | `BOOK_MEMORY_v0.1.md` |
| 12. BookBench v0.1 | `BOOKBENCH_v0.1.md` |
| 13. Human acceptance | `EDITORIAL_PROTOCOLS_v0.1.md` |
| 14. Versioning / provenance | `CORE_ONTOLOGY.md`, `TECHNICAL_ARCHITECTURE_v0.1.md` |
| 15. Technology stack | `TECHNICAL_ARCHITECTURE_v0.1.md` |
| 16. Build ourselves | `TECHNICAL_ARCHITECTURE_v0.1.md` |
| 17. Buy/use through APIs | `MODEL_GATEWAY_v0.1.md`, `RESEARCH_AND_CLAIMS_v0.1.md` |
| 18. MVP | `PRODUCT_SPEC_v0.1.md`, `IMPLEMENTATION_ROADMAP_v0.1.md` |
| 19. MVP success | `PRODUCT_SPEC_v0.1.md` |
| 20. Further phases | `IMPLEMENTATION_ROADMAP_v0.1.md` |
| Cross-cutting implementation hardening | `PRE_IMPLEMENTATION_HARDENING_v0.1.md` |

## Baseline rule

Implementation may refine internal code structure but may not change accepted product behavior, Authority Protocol, evidence semantics, regional access requirements, Literary Master semantics, human-acceptance boundaries, or mandatory hardening requirements without an explicit decision record.
