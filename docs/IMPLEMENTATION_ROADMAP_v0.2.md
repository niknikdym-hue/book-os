# BOOK OS — IMPLEMENTATION ROADMAP v0.2

**Status:** ACCEPTED IMPLEMENTATION SEQUENCE  
**Version:** 0.2.0  
**Date:** 2026-08-29  
**Supersedes:** `docs/IMPLEMENTATION_ROADMAP_v0.1.md` for current execution sequence.

## 1. Product direction

BOOK OS is a global editorial-authoring system for high-quality nonfiction.

The MVP is evaluated on book quality, editorial control, reproducibility, authority safety and real-book workflow performance.

OpenAI is the primary intelligence lane for the current MVP/pilot. Provider-neutral architecture remains mandatory.

There is no current Russia/no-VPN/regional-runtime milestone.

## 2. Accepted completed milestones

- M0 — repository baseline and executable skeleton — ACCEPTED.
- M1 — authority & persistence engine — ACCEPTED.
- M2 — book creation, Book Contract, Architecture, Chapter Contract — ACCEPTED.
- M3 — Model Gateway + first controlled drafting — ACCEPTED.
- M4 — Research Engine & Claim Ledger — ACCEPTED.
- M5 — Book Memory — ACCEPTED.
- M6 — Editorial Workflows — ACCEPTED.
- M7 — BookBench v0.1 — ACCEPTED.

Do not return to M0–M7 without a concrete regression.

## 3. Former M8 — SUPERSEDED

The former `Russia/no-VPN provider lane` milestone is removed from the current BOOK OS program by Owner Decision `docs/decisions/2026-08-29-global-openai-first.md`.

It is historical only and does not gate any current milestone.

## 4. Current critical path

`OpenAI-first quality lane → Literary Master + exports → real Business Nonfiction pilot → GO/NO-GO`

## 5. Next milestone — Literary Master + exports

Deliver:

- final release gate;
- immutable Literary Master manifest;
- exact revision ordering;
- checksums/hashes;
- deterministic rebuild from authority state;
- human-readable manuscript export;
- DOCX/Markdown export as product need dictates;
- production handoff manifest for Audiobook Studio without merging domain authority;
- export provenance;
- no derivative export can mutate Literary Master authority.

Acceptance:

- rebuilding the same Literary Master yields identical ordered authority content and hashes;
- export is reproducible from exact revisions;
- release cannot proceed with unresolved required BLOCKING gates;
- final human authority remains explicit;
- no provider-specific implementation becomes book authority.

## 6. Real-book pilot

Use a real new Business Nonfiction book from zero.

Run:

`Idea → Book Definition → Architecture → Research → Chapter Contracts → Controlled Drafting → Editorial Workflows → BookBench → Literary Master`

Use OpenAI as the primary intelligence lane for the pilot unless a later Owner Decision changes it.

Collect:

- quality defects;
- edits proposed/accepted/rejected;
- human reasons;
- cost/time by stage;
- model/config provenance;
- BookBench scorecards;
- workflow friction;
- missed errors;
- false positives/negatives;
- whole-book coherence;
- author-voice preservation;
- research/evidence quality.

## 7. MVP GO/NO-GO

BOOK OS v0.1 passes only after the real-book pilot demonstrates that the system can produce a Literary Master meeting the product quality and authority requirements.

Final GO/NO-GO remains an Owner decision.

## 8. Future provider work

Provider competition is future optimization, not a current milestone.

A future provider may be evaluated when it offers a credible quality/cost/capability advantage.

Selection criteria:

- Writer/Editor quality;
- BookBench results;
- long-context performance;
- structured-output reliability;
- privacy/commercial suitability;
- cost/latency;
- operational availability.

No provider is selected merely for geographic availability.
