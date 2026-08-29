# BOOK OS — PROJECT STATE

**Status:** REAL BUSINESS NONFICTION PILOT ACTIVE  
**Version:** 1.7.0  
**Date:** 2026-08-29  
**Canonical repository:** `https://github.com/niknikdym-hue/book-os`

## Current phase

BOOK OS is a **global editorial-authoring system** for high-quality nonfiction.

The current execution sequence is governed by:

- `docs/decisions/2026-08-29-global-openai-first.md`;
- `docs/IMPLEMENTATION_ROADMAP_v0.2.md`.

The former Russia/no-VPN provider-lane requirement is SUPERSEDED and removed from the current program.

## Accepted milestones

- M0 / Task 001 — ACCEPTED AND MERGED.
- M1 / Task 002 — ACCEPTED AND MERGED.
- M2 / Task 003 — ACCEPTED AND MERGED.
- M3 / Task 004 — ACCEPTED AND MERGED.
- M4 / Task 005 — ACCEPTED AND MERGED.
- M5 / Task 006 — ACCEPTED AND MERGED.
- M6 / Task 007 — ACCEPTED AND MERGED.
- M7 / Task 008 — BookBench v0.1 — ACCEPTED AND MERGED; PR #11; merge commit `5115a20512437a68da7ee7eed44e55b8ebbf0d90`.
- **Task 010 — Literary Master + exports — ACCEPTED AND MERGED:** accepted HEAD `51e3a97bf67b37a28a0c6c697baa94bcbec6c960`; authoritative CI `33270571416`; Python 82/82; desktop 11/11 + build/audit; Rust cargo test/check; secret scan all PASS; merge PR #14 commit `580f0123e50fe9f05a380528da734b3c8f10155a`.

Do not return to accepted milestones without a concrete regression.

## Literary Master capability now accepted

BOOK OS now has a fail-closed final release capability that:

- freezes exact current APPROVED/LOCKED authority revisions into an append-only Literary Master;
- requires a complete current deterministic M7 BookBench baseline with zero BLOCKING findings;
- requires current BookBench registry and Claim state;
- requires HUMAN evidence for material editorial waivers;
- deterministically rebuilds and hashes the canonical manuscript;
- produces deterministic Markdown export;
- produces a domain-separated Audiobook Studio handoff manifest;
- never auto-approves manuscript authority or creates a Literary Master without an explicit human release actor.

Canonical schema is now Alembic `0009`.

## Historical PR transfer note

Task 010 was developed and accepted in draft PR #13. The connected GitHub GraphQL `markPullRequestReadyForReview` action failed on a platform schema error, so accepted exact HEAD `51e3a97...` was transferred unchanged to non-draft PR #14 solely to complete the merge. No code/evidence changed during the transfer.

## Superseded former M8

The former `M8 — Russia/no-VPN provider lane` is no longer a current milestone.

Owner Decision on 2026-08-29 removed the Russia/no-VPN/regional-runtime task entirely from the current BOOK OS product program.

Former PR #12:

- final historical HEAD: `bb29e8a80cafeea1dd141910cae192fd73479ed1`;
- final CI: `33252854938` SUCCESS;
- state: CLOSED, NOT MERGED;
- disposition: historical/salvage evidence only.

No Yandex/GigaChat live promotion is required.
No regional provider availability blocks the real-book pilot or GO/NO-GO.

## Model strategy

OpenAI is the primary intelligence lane for the current MVP and real-book pilot.

Provider-neutral architecture remains mandatory:

- provider-specific behavior stays behind ModelGateway/EmbeddingGateway adapters;
- exact provider/model/config provenance remains required;
- OpenAI is not permanent architecture authority;
- future competitors may be benchmarked when they offer credible quality/cost/capability value.

No backup provider is required before the real-book pilot.

## Current critical path

`real Business Nonfiction pilot → GO/NO-GO`

## Immediate next objective

Run one real new Business Nonfiction book through the actual system from Idea to Literary Master.

Public Git contains only pilot tooling/contracts/aggregate evidence schemas and synthetic tests. The real book manuscript, private research corpus and private evaluation content remain in the Owner's local project data and are never committed publicly.

The pilot must measure actual workflow quality rather than merely prove code paths:

- idea/reader/thesis decisions;
- research and claim traceability;
- Book/Chapter Contract quality;
- controlled OpenAI drafting with exact provenance;
- Book Memory usefulness;
- editorial findings and human decisions;
- BookBench misses/false positives;
- cost/time by stage;
- Literary Master reproducibility;
- workflow friction and defects;
- final human quality judgment.

## Non-negotiable invariants

- GitHub is source of truth for BOOK OS system authority;
- human/Owner authority cannot be auto-approved by AI;
- accepted authority is immutable and replacements are traceable/SUPERSEDED;
- BookBench BLOCKING gates cannot be averaged away;
- real private manuscripts/evaluation corpus are not committed publicly;
- provider-specific code cannot become book authority;
- no hidden automatic manuscript acceptance;
- Literary Master must be reproducible from exact accepted revisions;
- paid/model calls require an explicit bounded pilot budget before execution.

## Change log

### 1.7.0 — 2026-08-29
- ACCEPTED and merged Task 010 / Literary Master + exports.
- Recorded exact acceptance HEAD `51e3a97bf67b37a28a0c6c697baa94bcbec6c960` and CI `33270571416`.
- Advanced canonical schema to `0009`.
- Activated the real Business Nonfiction pilot as the only remaining pre-GO/NO-GO milestone.
- Preserved OpenAI-first MVP/pilot strategy and provider-neutral architecture.

### 1.6.0 — 2026-08-29
- Reaffirmed BOOK OS as a global system.
- Removed the Russia/no-VPN/regional-runtime task from the current product program.
- Superseded former M8 / Task 009 as a launch gate.
- Closed PR #12 without merge; retained it only as historical/salvage evidence.
- Adopted `IMPLEMENTATION_ROADMAP_v0.2.md`.
- Set OpenAI as primary MVP/pilot intelligence lane while preserving provider-neutral architecture.
- New critical path: OpenAI-first quality → Literary Master → real-book pilot → GO/NO-GO.
