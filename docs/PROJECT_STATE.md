# BOOK OS — PROJECT STATE

**Status:** GLOBAL / OPENAI-FIRST QUALITY PATH ACTIVE  
**Version:** 1.6.0  
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

Do not return to M0–M7 without a concrete regression.

## Superseded former M8

The former `M8 — Russia/no-VPN provider lane` is no longer a current milestone.

Owner Decision on 2026-08-29 removed the Russia/no-VPN/regional-runtime task entirely from the current BOOK OS product program.

Former PR #12:

- final historical HEAD: `bb29e8a80cafeea1dd141910cae192fd73479ed1`;
- final CI: `33252854938` SUCCESS;
- state: CLOSED, NOT MERGED;
- disposition: historical/salvage evidence only.

No Yandex/GigaChat live promotion is required.
No regional provider availability blocks Literary Master, the real-book pilot, or GO/NO-GO.

## Model strategy

OpenAI is the primary intelligence lane for the current MVP and real-book pilot.

Provider-neutral architecture remains mandatory:

- provider-specific behavior stays behind ModelGateway/EmbeddingGateway adapters;
- exact provider/model/config provenance remains required;
- OpenAI is not permanent architecture authority;
- future competitors may be benchmarked when they offer credible quality/cost/capability value.

No backup provider is required before the real-book pilot.

## Current critical path

`OpenAI-first quality path → Literary Master + exports → real Business Nonfiction pilot → GO/NO-GO`

## Immediate next objective

Build and accept the Literary Master/export capability on top of accepted M0–M7, using the OpenAI-first quality lane for the MVP.

Then immediately run the real Business Nonfiction pilot from Idea to Literary Master and make the final GO/NO-GO decision from actual quality evidence.

## Non-negotiable invariants

- GitHub is source of truth;
- human/Owner authority cannot be auto-approved by AI;
- accepted authority is immutable and replacements are traceable/SUPERSEDED;
- BookBench BLOCKING gates cannot be averaged away;
- real private manuscripts/evaluation corpus are not committed publicly;
- provider-specific code cannot become book authority;
- no hidden automatic manuscript acceptance;
- Literary Master must be reproducible from exact accepted revisions.

## Change log

### 1.6.0 — 2026-08-29
- Reaffirmed BOOK OS as a global system.
- Removed the Russia/no-VPN/regional-runtime task from the current product program.
- Superseded former M8 / Task 009 as a launch gate.
- Closed PR #12 without merge; retained it only as historical/salvage evidence.
- Adopted `IMPLEMENTATION_ROADMAP_v0.2.md`.
- Set OpenAI as primary MVP/pilot intelligence lane while preserving provider-neutral architecture.
- New critical path: OpenAI-first quality → Literary Master → real-book pilot → GO/NO-GO.
