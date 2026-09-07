# BOOK OS — PROJECT STATE

**Status:** TASK 014 ACCEPTED — STACKED DECISIONS RECONCILIATION / REAL BOOK PILOT  
**Version:** 1.9.0  
**Date:** 2026-09-07  
**Canonical repository:** `https://github.com/niknikdym-hue/book-os`

## Current phase

BOOK OS is a **global editorial-authoring system** for high-quality nonfiction.

The current execution sequence is governed by:

- `docs/decisions/2026-08-29-global-openai-first.md`;
- `docs/IMPLEMENTATION_ROADMAP_v0.2.md`;
- `docs/tasks/TASK_011_REAL_BOOK_PILOT.md`;
- the accepted Task 014 launch workspace now merged into `main`.

The former Russia/no-VPN provider-lane requirement is SUPERSEDED and removed from the current program. PR #12 is historical/salvage evidence only and must not be resumed as a launch gate.

## Canonical main checkpoint

Latest accepted `main` checkpoint after Task 014 acceptance:

- merge commit: `73d3aab9b57604ab8c4dec8a3fec8562008157d4`;
- Task 014 accepted implementation HEAD: `02ab05e90924a0f9aa7a4c1d201d1c6707bf9a17`;
- authoritative Task 014 CI: `34098133448` — `local-core`, `desktop`, `tauri-smoke`, `macos-native-launch`, and `secret-scan` all SUCCESS;
- review threads: 0 unresolved;
- canonical schema: Alembic `0015`.

## Accepted milestones

- M0 / Task 001 — ACCEPTED AND MERGED.
- M1 / Task 002 — ACCEPTED AND MERGED.
- M2 / Task 003 — ACCEPTED AND MERGED.
- M3 / Task 004 — ACCEPTED AND MERGED.
- M4 / Task 005 — ACCEPTED AND MERGED.
- M5 / Task 006 — ACCEPTED AND MERGED.
- M6 / Task 007 — ACCEPTED AND MERGED.
- M7 / Task 008 — BookBench v0.1 — ACCEPTED AND MERGED; PR #11; merge commit `5115a20512437a68da7ee7eed44e55b8ebbf0d90`.
- Task 010 — Literary Master + exports — ACCEPTED AND MERGED; accepted HEAD `51e3a97bf67b37a28a0c6c697baa94bcbec6c960`; authoritative CI `33270571416`; merge PR #14 commit `580f0123e50fe9f05a380528da734b3c8f10155a`.
- **Task 011 tooling — Real Business Nonfiction pilot instrumentation — ACCEPTED AND MERGED:** accepted HEAD `74d292a621def1c729698ff16aca7a981880ed7a`; authoritative CI `33310462832`; draft PR #15 closed without merge solely because of the known ready-for-review connector bug; exact accepted transfer PR #16 merged unchanged; merge commit `017cfe59dca02ef1c482b3560d6462f26629a693`.
- **Task 012 — macOS launch hardening — ACCEPTED AND MERGED:** accepted HEAD `802b955e190f6960ebcec478d0c17750bef459b9`; authoritative CI `33324568459`; desktop/local-core/Tauri/secret-scan all PASS; two review blockers fixed and resolved; PR #17 merge commit `b9263e04144219815726b0d25ca234ae5df77ebc`.
- **Task 013 — visible macOS Desktop app — ACCEPTED AND MERGED:** accepted HEAD `8683f86670e9f9ac721c1815989f12972c9e3187`; PR #19 merge commit `4ac6ee06232935fe5acacf68615332d7211aaffe`.
- **Task 014 — Russian first-book launch workspace — ACCEPTED AND MERGED:** accepted HEAD `02ab05e90924a0f9aa7a4c1d201d1c6707bf9a17`; authoritative CI `34098133448`; all five canonical jobs SUCCESS; zero unresolved review threads; merge commit `73d3aab9b57604ab8c4dec8a3fec8562008157d4`.

Do not return to accepted milestones without a concrete regression.

## Current accepted capability

BOOK OS can now support the first real private Business Nonfiction pilot through:

`Idea → Book Definition → Research → Book Contract → Architecture → Chapter Contracts → controlled drafting → Book Memory → editorial workflows → BookBench → human decisions → Literary Master`

The system now has:

- local-first native desktop + Python Local Core;
- durable authority state and human approval gates;
- ModelGateway / EmbeddingGateway with exact provenance;
- Research Engine + Claim/Evidence/Source traceability;
- Book Memory;
- editorial workflows;
- BookBench v0.1;
- fail-closed Literary Master and deterministic export/handoff;
- private-local pilot stage/event/observation instrumentation;
- fail-closed HUMAN-only GO/NO-GO evidence readiness/final decision;
- hardened macOS startup and owned Local Core lifecycle;
- a normal install/update path for `~/Desktop/BOOK OS.app` plus CI proof for both packaged and installed app frontend mount and healthy Local Core;
- Russian first-book launch workspace with guided author flow and current Alembic schema `0015`;
- bounded Planner with DRAFT-only generated authority and HUMAN approval gates;
- in-app OpenAI Keychain setup and fresh explicit paid-call permission with positive per-request cost caps;
- blind Sol↔Astra Book Contract comparison with hidden model identity until human preference is recorded;
- fail-closed GPT-5.6 long-context pricing guard: requests above the 272K estimated-input threshold use conservative 2× input / 1.5× output pricing before HTTP, with deterministic zero-HTTP over-cap regression coverage;
- anti-junk/negative-first enforcement, including context-review distinctions, without weakening human authority.

## Literary Master capability

BOOK OS has a fail-closed final release capability that:

- freezes exact current APPROVED/LOCKED authority revisions into an append-only Literary Master;
- requires a complete current deterministic BookBench baseline with zero BLOCKING findings;
- requires current BookBench registry and Claim state;
- requires HUMAN evidence for material editorial waivers;
- deterministically rebuilds and hashes the canonical manuscript;
- produces deterministic Markdown export;
- produces a domain-separated Audiobook Studio handoff manifest;
- never auto-approves manuscript authority or creates a Literary Master without an explicit human release actor.

## Task 011 acceptance boundary

Task 011 **tooling** is accepted. This does **not** mean BOOK OS product GO has been declared.

The remaining product validation is the actual private real-book pilot. Evidence is not complete until one real book reaches LOCKED Literary Master and the human Owner records `GO | CONDITIONAL_GO | NO_GO` from the resulting evidence.

The real manuscript, research corpus and private evaluation content remain local/private and are never committed to the public repository.

## Model strategy

OpenAI is the primary intelligence lane for the current MVP and real-book pilot.

Provider-neutral architecture remains mandatory:

- provider-specific behavior stays behind ModelGateway/EmbeddingGateway adapters;
- exact provider/model/config provenance remains required;
- OpenAI is not permanent architecture authority;
- future competitors may be benchmarked when they offer credible quality/cost/capability value.

No backup provider is required before the real-book pilot.

No Yandex/GigaChat live promotion is required. No regional provider lane blocks the pilot.

## Current critical path

`reconcile open stacked authority/UX work against accepted Task 014 main → real Business Nonfiction pilot → Literary Master → HUMAN GO/CONDITIONAL_GO/NO_GO`

The open stacked PRs #21, #22 and #23 are not accepted merely because Task 014 is merged. They must be rebased/normalized against current `main` and reviewed independently. This reconciliation is not a new infrastructure milestone and must not weaken the real-book pilot priority.

## Immediate next permitted action

Reconcile the open stacked PRs #21, #22 and #23 against accepted `main` without importing stale Task 014 assumptions, then proceed to one real new Business Nonfiction project in the accepted local BOOK OS desktop and record the private pilot against that book.

For the actual pilot, the genuine Owner input gate remains creative:

- confirm/select the real book idea;
- confirm the intended reader.

After those two inputs, Central Brain may autonomously drive Book Definition, research planning, Book Contract and architecture proposals, pausing only at the documented HUMAN authority gates.

Before the first paid OpenAI request, Central Brain must present a bounded writer/editor execution slice with explicit request/token/cost limits and receive explicit Owner approval. Preflight itself remains zero-call and secret-safe.

## Pilot quality evidence required

The actual pilot must measure more than code-path completion:

- idea/reader/thesis decisions;
- research and claim traceability;
- Book/Chapter Contract quality;
- controlled OpenAI drafting with exact provenance;
- Book Memory usefulness;
- editorial findings and human decisions;
- BookBench misses/false positives;
- known/unknown model cost and time by stage;
- Literary Master reproducibility;
- workflow friction and defects;
- final human literary-quality judgment.

## Historical transfer notes

Task 010 was developed and accepted in draft PR #13. The connected GitHub ready-for-review GraphQL action failed on a platform schema error, so accepted exact HEAD `51e3a97...` was transferred unchanged to non-draft PR #14 solely to complete the merge.

Task 011 used the same validated transfer pattern after the same connector bug: draft PR #15 was closed without merge and exact accepted HEAD `74d292a...` was transferred unchanged to PR #16 and merged.

Task 014 final delivery used a Central Brain Git-object transport because Codex repeatedly produced the correct narrow four-file fix locally but lacked an authenticated GitHub push path. The transported blobs exactly matched the Codex-reviewed target blobs before the atomic branch commit.

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

## Non-negotiable invariants

- GitHub `main` is source of truth for BOOK OS system authority;
- chat is not authority;
- human/Owner authority cannot be auto-approved by AI;
- accepted authority is immutable and replacements are traceable/SUPERSEDED;
- BookBench BLOCKING gates cannot be averaged away;
- real private manuscripts/evaluation corpus are not committed publicly;
- provider-specific code cannot become book authority;
- no hidden automatic manuscript acceptance;
- Literary Master must be reproducible from exact accepted revisions;
- paid/model calls require an explicit bounded pilot budget before execution.

## Change log

### 1.9.0 — 2026-09-07
- Recorded Task 013 visible macOS Desktop app as ACCEPTED AND MERGED; accepted HEAD `8683f86670e9f9ac721c1815989f12972c9e3187`, merge `4ac6ee06232935fe5acacf68615332d7211aaffe`.
- Recorded Task 014 Russian first-book launch workspace as ACCEPTED AND MERGED; accepted HEAD `02ab05e90924a0f9aa7a4c1d201d1c6707bf9a17`, authoritative CI `34098133448`, merge `73d3aab9b57604ab8c4dec8a3fec8562008157d4`.
- Advanced canonical schema checkpoint to `0015`.
- Recorded the fail-closed GPT-5.6 >272K cost tier guard and deterministic pre-HTTP over-cap regression.
- Restored and proved both packaged and installed Desktop-app launch/readiness behavior.
- Preserved blind Sol↔Astra comparison, anti-junk/CONTEXT_REVIEW, Planner DRAFT/HUMAN gates, Keychain and paid-call protections.
- Set the next repository action to bounded reconciliation of open stacked PRs #21/#22/#23 before the real-book pilot proceeds.

### 1.8.0 — 2026-08-31
- Recorded Task 011 pilot tooling as ACCEPTED AND MERGED via exact accepted transfer PR #16; accepted HEAD `74d292a621def1c729698ff16aca7a981880ed7a`, CI `33310462832`, merge `017cfe59dca02ef1c482b3560d6462f26629a693`.
- Advanced canonical schema to `0010`.
- Recorded Task 012 macOS launch hardening as ACCEPTED AND MERGED; accepted HEAD `802b955e190f6960ebcec478d0c17750bef459b9`, CI `33324568459`, merge `b9263e04144219815726b0d25ca234ae5df77ebc`.
- Clarified that Task 011 tooling acceptance is not BOOK OS product GO.
- Set the immediate next permitted action to the first actual private Business Nonfiction pilot.
- Explicitly prohibited resuming former M8/PR #12 as a launch gate.

### 1.7.0 — 2026-08-29
- ACCEPTED and merged Task 010 / Literary Master + exports.
- Recorded exact acceptance HEAD `51e3a97bf67b37a28a0c6c697baa94bcbec6c960` and CI `33270571416`.
- Advanced canonical schema to `0009`.
- Activated the real Business Nonfiction pilot as the remaining pre-GO/NO-GO milestone.
- Preserved OpenAI-first MVP/pilot strategy and provider-neutral architecture.

### 1.6.0 — 2026-08-29
- Reaffirmed BOOK OS as a global system.
- Removed the Russia/no-VPN/regional-runtime task from the current product program.
- Superseded former M8 / Task 009 as a launch gate.
- Closed PR #12 without merge; retained it only as historical/salvage evidence.
- Adopted `IMPLEMENTATION_ROADMAP_v0.2.md`.
- Set OpenAI as primary MVP/pilot intelligence lane while preserving provider-neutral architecture.
- New critical path: OpenAI-first quality → Literary Master → real-book pilot → GO/NO-GO.
