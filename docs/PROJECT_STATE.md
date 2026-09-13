# BOOK OS — PROJECT STATE

**Status:** AUTO BOOK COMPLETE CYCLE — IMPLEMENTED AWAITING REVIEW
**Version:** 3.0.0-candidate
**Date:** 2026-09-13
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
- Series Studio supports new series, external import and continuation of a saved BOOK OS series,
  with Series Bible, Book Passports, immutable sources, explicit rights, difference maps and
  fail-closed writing/finalization gates;
- the Owner-authorized «Секреты продвижения услуг» preset preserves four fixed titles/order and
  four planned directions without starting manuscript generation.

Candidate schema head: Alembic `0022`. Migration `0021` contains durable Auto Book runtime;
migration `0022` contains the series workspace/read model and decisions.

## Acceptance boundary

This implementation is not `ACCEPTED` until the exact published head has green canonical CI and a
fresh review. Technical GREEN does not establish literary quality. A separate Owner-authorized,
hard-budgeted blind quality trial is still required before claiming that Auto Book matches the
quality of the supplied «Как продавать услуги» references.

No paid/model request was authorized or executed while preparing this candidate. No installed
Desktop application is replaced by this task.

## Next safe action

Publish the bounded candidate PR, run canonical CI and review, fix defects on the same branch, then
present the separate quality-trial budget for Owner authorization. Do not merge or run a paid
quality trial without the required decision.

## Non-negotiable invariants

- GitHub `main` is the accepted system source of truth.
- Owner/HUMAN authority cannot be silently replaced by a model.
- A stale or missing Series Bible, Book Passport, difference map, evidence link or exact snapshot
  fails closed.
- A blocking quality finding cannot be averaged away or exported as a ready Literary Master.
- Imported originals are immutable until the author explicitly deletes the source.
- Import does not grant permission to imitate, rewrite or publish a third party's text.
- Auto may select an executor, but may not bypass authority, quality, budget or provenance gates.
- No blind retry is allowed after an unknown provider outcome.
- Starting one series book never starts writing another planned book.
- Private manuscripts, secrets and evaluation corpora are not committed.
