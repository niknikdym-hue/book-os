# BOOK OS — PROJECT STATE

**Status:** RECONCILIATION COMPLETE — REAL BUSINESS NONFICTION PILOT READY / OWNER CREATIVE GATE  
**Version:** 2.0.0  
**Date:** 2026-09-07  
**Canonical repository:** `https://github.com/niknikdym-hue/book-os`

## Current phase

BOOK OS is a **global editorial-authoring system** for high-quality nonfiction.

All pre-pilot stacked reconciliation is complete. The current execution sequence is governed by:

- `docs/decisions/2026-08-29-global-openai-first.md`;
- `docs/decisions/2026-09-02-guided-author-workspace.md`;
- `docs/decisions/2026-09-02-audio-native-and-series.md`;
- `docs/AUDIO_NATIVE_AND_SERIES_v0.1.md` amendment version `0.2.1`;
- `docs/IMPLEMENTATION_ROADMAP_v0.2.md`;
- `docs/tasks/TASK_011_REAL_BOOK_PILOT.md`;
- the accepted Task 014 Russian first-book launch workspace.

The former Russia/no-VPN provider-lane requirement remains **SUPERSEDED** and is not a launch gate.

## Canonical main checkpoint

Latest accepted `main` checkpoint after stacked reconciliation:

- canonical `main` merge commit: `bf9787f95ae914c49b1135c1a879b093919fda2d`;
- Task 014 accepted implementation HEAD: `02ab05e90924a0f9aa7a4c1d201d1c6707bf9a17`;
- Task 014 authoritative CI: `34098133448` — all five canonical jobs SUCCESS;
- Task 015 shared Content Quality Lexicon contract merge: `afb5caba1c9791a37d901306264e019628139d7e`;
- Task 016 guided-author workspace implementation PR #22: CLOSED, NOT MERGED, because its useful behavior was already absorbed by accepted Task 014; its Owner decision was preserved in `main` by commit `fe667e877191862ca18bf25bb4ae9c074421cb5e`;
- audio/series authority PR #23 accepted HEAD: `b940a9ebe42a1a5ac13ae4165110b85af20e8e68`;
- PR #23 authoritative CI: `34106308726` — SUCCESS;
- PR #23 review threads: all resolved;
- PR #23 merge commit: `bf9787f95ae914c49b1135c1a879b093919fda2d`;
- canonical schema: Alembic `0015`.

## Accepted milestones

- M0 / Task 001 — ACCEPTED AND MERGED.
- M1 / Task 002 — ACCEPTED AND MERGED.
- M2 / Task 003 — ACCEPTED AND MERGED.
- M3 / Task 004 — ACCEPTED AND MERGED.
- M4 / Task 005 — ACCEPTED AND MERGED.
- M5 / Task 006 — ACCEPTED AND MERGED.
- M6 / Task 007 — ACCEPTED AND MERGED.
- M7 / Task 008 — BookBench v0.1 — ACCEPTED AND MERGED; PR #11; merge `5115a20512437a68da7ee7eed44e55b8ebbf0d90`.
- Task 010 — Literary Master + exports — ACCEPTED AND MERGED; accepted HEAD `51e3a97bf67b37a28a0c6c697baa94bcbec6c960`; CI `33270571416`; merge `580f0123e50fe9f05a380528da734b3c8f10155a`.
- Task 011 tooling — Real Business Nonfiction pilot instrumentation — ACCEPTED AND MERGED; accepted HEAD `74d292a621def1c729698ff16aca7a981880ed7a`; CI `33310462832`; merge `017cfe59dca02ef1c482b3560d6462f26629a693`.
- Task 012 — macOS launch hardening — ACCEPTED AND MERGED; accepted HEAD `802b955e190f6960ebcec478d0c17750bef459b9`; CI `33324568459`; merge `b9263e04144219815726b0d25ca234ae5df77ebc`.
- Task 013 — visible macOS Desktop app — ACCEPTED AND MERGED; accepted HEAD `8683f86670e9f9ac721c1815989f12972c9e3187`; merge `4ac6ee06232935fe5acacf68615332d7211aaffe`.
- Task 014 — Russian first-book launch workspace — ACCEPTED AND MERGED; accepted HEAD `02ab05e90924a0f9aa7a4c1d201d1c6707bf9a17`; CI `34098133448`; merge `73d3aab9b57604ab8c4dec8a3fec8562008157d4`.
- Task 015 — Shared Content Quality Lexicon contract — ACCEPTED AND MERGED as contract-only authority; merge `afb5caba1c9791a37d901306264e019628139d7e`. Runtime shared-store integration remains a separate future implementation decision and does not block the first pilot.
- Task 016 — Guided author workspace PR #22 — SUPERSEDED / ABSORBED by the newer Task 014 implementation. PR #22 closed without merge; the accepted Owner UX decision is preserved in `docs/decisions/2026-09-02-guided-author-workspace.md`.
- Audio-native / existing-text recording-script / series authority — ACCEPTED through PR #23; accepted HEAD `b940a9ebe42a1a5ac13ae4165110b85af20e8e68`; CI `34106308726`; merge `bf9787f95ae914c49b1135c1a879b093919fda2d`.

Do not return to accepted milestones without a concrete regression.

## Current implemented capability

BOOK OS can support the first real private Business Nonfiction pilot through:

`Idea → Book Definition → Research → Book Contract → Architecture → Chapter Contracts → controlled drafting → Book Memory → editorial workflows → BookBench → human decisions → Literary Master`

Implemented and accepted:

- local-first native macOS desktop + Python Local Core;
- durable authority state and HUMAN approval gates;
- ModelGateway / EmbeddingGateway with exact provenance;
- Research Engine + Claim/Evidence/Source traceability;
- Book Memory;
- editorial workflows;
- BookBench v0.1;
- fail-closed Literary Master and deterministic export/handoff;
- private-local pilot instrumentation and HUMAN-only GO/NO-GO evidence decision;
- normal `~/Desktop/BOOK OS.app` install/update path with packaged + installed native launch proof;
- Russian guided first-book workspace and current schema `0015`;
- bounded Planner producing DRAFT-only authority;
- in-app OpenAI Keychain setup;
- fresh explicit permission and positive cost cap for every paid Writer/Planner call;
- blind Sol↔Astra Book Contract comparison with hidden identity until human preference;
- fail-closed GPT-5.6 long-context cost guard above 272K estimated input tokens using conservative 2× input / 1.5× output pricing before HTTP;
- anti-junk / negative-first enforcement with `BANNED_TEMPLATE` vs `CONTEXT_REVIEW` semantics;
- capability-aware topic catalog, locked unsupported categories, clear current step and built-in `Как пользоваться BOOK OS`.

## Accepted contract/design authority not yet claimed as runtime implementation

### Shared Content Quality Lexicon

Task 015 establishes the interoperability contract for a shared private anti-junk lexicon between BOOK OS and Audiobook Studio.

- `BLOCK` maps to BOOK OS `BANNED_TEMPLATE` behavior.
- `WARN` maps to context review and is not a global word ban.
- Audiobook Studio literary scan is opt-in/advisory and never silently rewrites literary text.
- TTS-technical `BLOCK` may remain a fail-closed pre-provider safety gate.
- Runtime shared-store integration is **not** required for the current real-book pilot unless a concrete pilot defect proves otherwise.

### Audio-native authoring, recording scripts and series

PR #23 establishes accepted product/editorial authority, not completed runtime implementation.

Two workflows are separate:

- Workflow A: `TEXT_FIRST | AUDIO_FIRST | DUAL_TEXT_AUDIO` for a book created from zero.
- Workflow B: `SOURCE_FAITHFUL | LISTENING_ADAPTATION` for preparing textual recording material from an existing approved text book.

Non-negotiable accepted rules include:

- Workflow B prepares text for recording; it does not create audio/TTS.
- Clean UTF-8 `.txt` is the required **output format** for approved recording text of every audio path: `AUDIO_FIRST`, the audio side of `DUAL_TEXT_AUDIO`, `SOURCE_FAITHFUL`, and `LISTENING_ADAPTATION`.
- Source/import format is separate; machine metadata must not pollute the readable TXT.
- `LISTENABILITY` uses BookBench states; `BLOCKING` fails closed and `ATTENTION` requires explicit HUMAN disposition.
- Every audio release has zero unresolved material visual dependencies with disposition `BLOCKED`.
- Immutable release manifests freeze exact release-justifying audio/series authorities, evaluation snapshots/findings and HUMAN waivers.
- Series remain first-class authority-bearing objects with ordered/unordered modes, cross-volume memory and diagnostics.
- BOOK OS owns literary listenability and semantic/source fidelity; Audio Studio owns narrator/TTS execution, SSML/pronunciation rendering, synthesis/recording, mastering and audio QC.

These capabilities may be implemented later through bounded tasks when they become critical. They do not delay the first `TEXT_FIRST` Business Nonfiction pilot.

## Literary Master capability

Current implemented Literary Master:

- freezes exact current APPROVED/LOCKED authority revisions into an append-only release;
- requires a current deterministic BookBench baseline with zero unresolved BLOCKING findings;
- requires current Claim/BookBench state and HUMAN evidence for material waivers;
- deterministically rebuilds/hashes the canonical manuscript;
- produces deterministic Markdown export;
- produces a domain-separated Audiobook Studio handoff manifest;
- never auto-approves manuscript authority or releases without an explicit HUMAN actor.

When future audio/series runtime is implemented, the PR #23 release-manifest bindings are mandatory extensions rather than optional metadata.

## Model strategy

OpenAI remains the primary intelligence lane for the current MVP and real-book pilot.

Provider-neutral architecture remains mandatory:

- provider-specific behavior stays behind ModelGateway/EmbeddingGateway adapters;
- exact provider/model/config provenance is required;
- operation-level routing follows evidence, quality/risk and cost;
- OpenAI is not permanent architecture authority.

No backup provider and no Yandex/GigaChat promotion is required before the real-book pilot.

## Current critical path

`real Business Nonfiction pilot → Literary Master → HUMAN GO | CONDITIONAL_GO | NO_GO`

There is **no remaining stacked PR reconciliation gate** before the first pilot.

Do not create another infrastructure milestone unless the real pilot exposes a concrete regression that prevents quality, safety, reproducibility or required author control.

## Immediate next permitted action

Start one real new Business Nonfiction project in the accepted local BOOK OS desktop and record the private pilot against that book.

The first genuine Owner creative gate is:

- confirm/select the real book idea;
- confirm the intended reader.

After those two inputs, Central Brain may autonomously drive Book Definition, research planning, Book Contract and architecture proposals, pausing only at documented HUMAN authority gates.

Before the first paid OpenAI request, Central Brain must present a bounded execution slice with explicit request/token/cost limits and receive explicit Owner approval. Zero-call preflight remains permitted and secret-safe.

## Pilot quality evidence required

The actual pilot must measure:

- idea / reader / thesis decisions;
- research and claim traceability;
- Book/Chapter Contract quality;
- controlled model drafting with exact provenance;
- Book Memory usefulness;
- editorial findings and HUMAN decisions;
- BookBench misses / false positives;
- model cost and time by stage;
- Literary Master reproducibility;
- workflow friction and defects;
- final HUMAN literary-quality judgment.

The real manuscript, research corpus and private evaluation content remain local/private and are never committed to the public repository.

## Historical / superseded lanes

The former `M8 — Russia/no-VPN provider lane` / Task 009 / PR #12 remains **SUPERSEDED**.

- historical PR #12 final HEAD: `bb29e8a80cafeea1dd141910cae192fd73479ed1`;
- historical CI: `33252854938` SUCCESS;
- state: CLOSED, NOT MERGED;
- disposition: historical/salvage evidence only.

No regional-provider availability blocks the current pilot.

## Non-negotiable invariants

- GitHub `main` is source of truth for BOOK OS system authority.
- Chat is not authority.
- Human/Owner authority cannot be auto-approved by AI.
- Accepted authority is immutable; replacements are traceable / SUPERSEDED.
- BookBench BLOCKING gates cannot be averaged away.
- Real private manuscripts/evaluation corpus are not committed publicly.
- Provider-specific code cannot become book authority.
- No hidden automatic manuscript acceptance.
- Literary Master must be reproducible from exact accepted revisions.
- Paid/model calls require explicit bounded Owner approval before execution.

## Change log

### 2.0.0 — 2026-09-07

- Completed stacked reconciliation after Task 014.
- Accepted and merged Task 015 shared Content Quality Lexicon contract; runtime integration remains separate.
- Closed Task 016 PR #22 without merge because accepted Task 014 already contains the guided-author capability; preserved its Owner decision in `main`.
- Accepted and merged PR #23 audio-native / recording-script / series authority after exact-head CI success and resolution of all review findings.
- Recorded universal UTF-8 TXT recording-text output, exact BookBench LISTENABILITY semantics, zero unresolved `BLOCKED` visual dependencies for audio release, and immutable release-manifest bindings.
- Removed #21/#22/#23 reconciliation from the critical path.
- Activated the first real Business Nonfiction pilot as the only current product-validation path before HUMAN GO/CONDITIONAL_GO/NO_GO.

### 1.9.0 — 2026-09-07

- Accepted Task 013 and Task 014.
- Advanced canonical schema to `0015`.
- Recorded GPT-5.6 long-context fail-closed cost guard, installed Desktop proof, blind Sol↔Astra comparison, anti-junk/CONTEXT_REVIEW, Planner DRAFT/HUMAN gates and Keychain/paid-call protections.
- Opened bounded stacked reconciliation before the real pilot.

### 1.8.0 — 2026-08-31

- Accepted Task 011 pilot tooling and Task 012 macOS launch hardening.
- Activated the real Business Nonfiction pilot as the remaining product GO/NO-GO evidence path.

### 1.7.0 — 2026-08-29

- Accepted Task 010 Literary Master + exports.
- Adopted OpenAI-first quality path with provider-neutral architecture.

### 1.6.0 — 2026-08-29

- Reaffirmed BOOK OS as a global system.
- Superseded former Russia/no-VPN M8 / Task 009 as a launch gate.
