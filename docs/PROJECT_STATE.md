# BOOK OS — PROJECT STATE

**Status:** AUTO BOOK COMPLETE CYCLE — IMPLEMENTED AWAITING EXACT-HEAD REVIEW
**Version:** 3.1.0-candidate
**Date:** 2026-09-14
**Canonical repository:** `https://github.com/niknikdym-hue/book-os`

## Canonical baseline

- accepted `origin/main`: `19ab44ba30036936f843e9b13f2a0f7c8f7b1204` (PR #37 merged);
- implementation branch: `codex/auto-book-complete-cycle-20260913`;
- this branch is a review candidate, not accepted authority;
- private manuscripts and provider credentials remain outside Git.

GitHub `main` remains the system source of truth. Chat history is not required to reconstruct the
product or its authority.

## Candidate capability

The current review candidate extends the existing BOOK OS modules instead of adding a parallel
product layer:

- one author-facing Auto Book launch with Auto as the default, explicit attachments, selected
  outputs, visual policy, hard request/cost limits and natural-language change requests;
- Local Core owns execution, leases, durable stage/operation checkpoints, restart recovery,
  idempotency and unknown-paid-outcome handling; the desktop is an observer/controller;
- deterministic operation-aware model routing uses Sol for eligible routine work and Astra at the
  measured level required by complexity/risk; manual modes remain available;
- explicit research, architecture, chapter planning/writing/review, mid-book audit, whole-book edit,
  fact/evidence gate, literary edit, visuals, independent critique, bounded correction and master
  export stages;
- structured Literary Master outputs include native tables, programmatic PNG visuals, captions,
  alt/audio equivalents, bibliography and independent format QA;
- selected DOCX/LitRes/PDF/EPUB/audio/TXT/pronunciation/extras/publisher outputs are generated
  independently and become stale when their exact master changes;
- audio outputs require a separately versioned exact-source AudioScript, source/semantic and
  listenability checks, explicit HUMAN approval, one clean UTF-8 recording TXT and an immutable
  Audiobook Studio handoff; AUDIO_FIRST/DUAL constraints propagate upstream and existing-text audio
  adaptation remains a separate workflow;
- Series Studio supports new series, external import and continuation of a saved BOOK OS series,
  including 3–5 proposed concepts for a new series, Series Bible, Book Passports, immutable sources,
  explicit rights, semantic/structural difference maps, Topic Ownership, overlap disposition and
  fail-closed writing/finalization gates;
- the Owner-authorized «Секреты продвижения услуг» preset preserves its fixed existing titles/order
  and planned directions without starting manuscript generation;
- Author Experience v2 exposes the author workflow as `Главная / Серии / Книги / Библиотека /
  Настройки` and seven book stages without making technical routing controls the primary surface;
- durable book and series cost views distinguish confirmed, reserved, unknown and forecast cost.

## Candidate schema

Candidate schema head: Alembic `0028`.

- `0021` — durable Auto Book runtime;
- `0022` — series workspace/read model and Owner decisions;
- `0023` — AudioScript authority, source/script-bound QA, pronunciation and production handoff;
- `0024` — explicit series-book origin semantics;
- `0025` — nonfiction bibliography default;
- `0026` — safe correction of historical series-origin inference;
- `0027` — Auto Book recovery/paid-operation truth and final-acceptance support;
- `0028` — completed series-governance records required by the current candidate.

Schema and backup compatibility are tested through the current head. A stale lower migration number
must not be used as candidate-state evidence.

## Acceptance boundary

This implementation is not `ACCEPTED` until the exact published head has green canonical CI and a
fresh Central Brain review. Technical GREEN does not establish literary quality. A separate
Owner-authorized, hard-budgeted quality trial may be run later only if the Owner requests it after
reviewing the actual application.

Deterministic implementation/CI work must make zero production provider/model/TTS calls and zero
paid calls. Private manuscripts, API keys and credentials must not be committed.

The current Owner gate is to finish exact-head free verification first. Only after all assignments
from the 2026-09-13/14 work package are verified may a checked macOS build be used for the Owner's
hands-on application review. That review does not itself authorize merge or production release.

## Known bounded limitations — do not overclaim

- scanned PDFs whose text cannot be extracted remain PARTIAL/fail-closed; arbitrary OCR is not
  claimed;
- DOCX/PDF/EPUB QA is structural/reopen/reference QA, not pixel-level platform certification;
- LitRes output must keep platform-acceptance claims false until actual platform acceptance exists;
- the current audio ATTENTION surface does not prove per-location human review when multiple hidden
  findings share an aggregate code; this is a bounded P2 UX/audit limitation;
- deterministic fixtures prove workflow and safety invariants, not final literary quality.

These limitations do not authorize weakening quality gates and do not by themselves block a private
Owner review of the application.

## Next safe action

1. Finish the current exact-head deterministic regression fix without weakening Series Duplication.
2. Run canonical free CI on that exact head and perform a fresh Central Brain review.
3. Keep PR Draft and unmerged.
4. If the work package is fully verified, prepare the exact checked macOS application build for
   Owner hands-on review, preserving rollback and user data.
5. Stop after Owner review setup and wait for the Owner's next instruction.

No paid literary-quality run, merge, deploy, notarization or production release is authorized by
this state document.

## Non-negotiable invariants

- GitHub `main` is the accepted system source of truth.
- Owner/HUMAN authority cannot be silently replaced by a model.
- A stale or missing Series Bible, Book Passport, difference map, evidence link or exact snapshot
  fails closed.
- A blocking quality finding cannot be averaged away or exported as a ready Literary Master.
- Imported originals are immutable until the author explicitly deletes the source.
- Import does not grant permission to imitate, rewrite or publish a third party's text.
- Auto may select an executor, but may not bypass authority, quality, budget or provenance gates.
- Extra High is not a routine default; escalation requires a concrete recorded reason.
- No blind retry is allowed after an unknown provider outcome.
- Starting one series book never starts writing another planned book.
- Private manuscripts, secrets and evaluation corpora are not committed.
