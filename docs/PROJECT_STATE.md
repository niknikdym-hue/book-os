# BOOK OS — PROJECT STATE

**Status:** SMM PRODUCTION PILOT PREP — ASTRA READY / TASK 017 DELIVERY GATE  
**Version:** 2.1.0  
**Date:** 2026-09-07  
**Canonical repository:** `https://github.com/niknikdym-hue/book-os`

## Current phase

BOOK OS is now being prepared for its first representative production-book run.

The content pilot is maintained outside this repository:

- pilot series: **«Инструменты интернет-маркетинга»**;
- first production book: **«SMM продвижение»**;
- book/content source of truth: `niknikdym-hue/books-for-litres`;
- BOOK OS has no runtime dependency on that repository and must remain generic.

The external branch `brain/services-series-clean-restart-20260907` is reference evidence only. Its book content/architecture is not BOOK OS authority. A transferable observation from that project is that GPT-6 Astra at `high` reasoning has produced strong sequential long-form results; this evidence informed Task 018 but does not hard-code Astra as the only executor.

## Canonical main checkpoint

Current accepted `main` after Task 018:

- main merge: `a08d0ea6768ae33d225ca2ede83496684e3a1fd7`;
- Task 018 accepted implementation HEAD: `1b4f8a76344885b15d1cf399dc4ab74880f86895`;
- Task 018 authoritative CI: `34147087684`;
- canonical jobs: `local-core`, `desktop`, `tauri-smoke`, `macos-native-launch`, `secret-scan` — all SUCCESS;
- PR #26 review threads: 0;
- canonical schema remains Alembic `0015` because Task 018 required no migration.

## Accepted milestones / capabilities

The previously accepted chain remains authoritative:

- M0–M7 / Tasks 001–008 — accepted;
- Task 010 — Literary Master + exports — accepted;
- Task 011 — real-book pilot instrumentation — accepted;
- Task 012 — macOS launch hardening — accepted;
- Task 013 — visible/installable macOS Desktop app — accepted;
- Task 014 — Russian first-book launch workspace — accepted;
- Task 015 — Shared Content Quality Lexicon contract — accepted;
- Task 016 — superseded/absorbed by Task 014; Owner UX decision preserved;
- PR #23 — audio-native / recording-script / series authority — accepted;
- **Task 018 — GPT-6 Astra production lane — ACCEPTED AND MERGED.**

Do not return to accepted milestones without a concrete regression.

## Task 018 — accepted Astra production lane

BOOK OS now treats `gpt-6-astra` as a fully bounded OpenAI executor rather than only a routing label.

Accepted behavior:

- Astra is registered as `gpt-6-astra`;
- conservative preflight pricing is registered and auditable;
- requests above the existing 272K estimated-input threshold use the long-context pricing tier before HTTP;
- every cost-capped request remains fail-closed before Keychain read/provider HTTP when the worst-case bound exceeds the Owner cap;
- Astra defaults to reasoning `high` when Astra is intentionally used and no explicit supported effort is supplied;
- explicit `low | medium | high | xhigh | max` reasoning can be passed through Planner/Writer flows;
- actual/requested reasoning is carried into usage/provenance where available;
- `xhigh/max` remain selective high-complexity modes rather than a blanket default;
- operation-level Auto routing remains intact;
- existing HUMAN manual operation and whole-book pins remain supported;
- `/api/launch/readiness` can report Astra model/pricing/credential readiness with `external_calls=0` and `paid_calls=0`;
- tests/CI make no provider/model/paid calls.

This acceptance does **not** authorize a live Astra request. First live paid execution still requires an explicit bounded Owner financial approval.

## Model strategy

The governing rule remains:

**best executor for the editorial operation, not one model monopoly.**

Current production evidence supports a strong Astra lane:

- high-value Book Contract / Architecture work may use Astra;
- when the human deliberately pins Astra for long-form Writer work, `high` is the default reasoning profile;
- `xhigh/max` are reserved for bounded harder work such as difficult structural rework, whole-book/adversarial diagnosis or another explicitly justified operation;
- Writer, Editor, Judge and Adversarial Reviewer remain independently routable.

Provider-neutral architecture remains mandatory.

## Current pre-writing blocker — Task 017 / PR #25

The accepted 2026-09-07 series-production decision requires executable gates before the first pilot is treated as representative:

1. Series Canon asset statuses/reservations;
2. Book Uniqueness Ledger;
3. structured Book Definition Pack;
4. stronger Chapter Contract;
5. per-chapter `WRITING_ALLOWED` admission;
6. deterministic Writer rejection before model/provider access when admission is absent/stale;
7. mandatory mid-book audit;
8. independent Adversarial Review;
9. Series Closure bound to the exact Literary Master.

Task 017 / PR #25 is the only remaining system-level pre-writing blocker.

Codex has produced a locally validated implementation with:

- linear migration `0015 → 0016`;
- full backend `pytest -q` = **121 passed** after fixture reconciliation;
- targeted series-production/migration/backup tests green;
- ruff/mypy green;
- frontend lint/typecheck/tests/build green;
- provider/model/paid calls = 0;
- no manuscript generation;
- no `books-for-litres` runtime dependency.

However that implementation has not been transported into the remote PR branch because the Codex environment could not push and later hit usage limits. Therefore Task 017 is **NOT ACCEPTED** until the exact implementation is present in GitHub, canonical CI is green, and review is clean.

Do not weaken the new gates merely to preserve historical fixture assumptions.

## Current product pilot

The real product-validation path is:

`SMM final Book Definition Pack → HUMAN approval → Architecture → per-chapter admission → bounded Astra/other routed production → Chapter QA → mid-book audit → whole-book edit → Adversarial Review → Literary Master → HUMAN GO | CONDITIONAL_GO | NO_GO`

Content authority and private manuscript/research remain outside the public BOOK OS repository.

## Immediate next action

Critical path:

1. deliver/reconstruct Task 017 in GitHub from the already validated behavior;
2. run exact-head canonical CI and Central Brain review;
3. accept/merge Task 017 and advance canonical schema to `0016`;
4. complete the external SMM Book Definition Pack and obtain HUMAN approval;
5. create/approve Architecture;
6. admit chapters individually;
7. before the first live Astra request, present an explicit bounded request/token/cost slice for Owner approval;
8. begin representative production.

No new infrastructure milestone is permitted unless a concrete pilot defect proves it necessary.

## Non-negotiable invariants

- GitHub `main` is source of truth for BOOK OS system authority.
- `books-for-litres` is not a BOOK OS runtime dependency.
- Human/Owner authority cannot be auto-approved by AI.
- Accepted authority is immutable; replacements are traceable / SUPERSEDED.
- Architecture approval does not globally unlock Writing once Task 017 is accepted.
- BookBench / production BLOCKING gates cannot be averaged away.
- Real private manuscripts/evaluation corpus are not committed publicly.
- Provider-specific code cannot become book authority.
- No hidden automatic manuscript acceptance.
- Literary Master must be reproducible from exact accepted revisions.
- No paid/model execution without explicit bounded Owner approval.
- Quality target is highest professional nonfiction quality realistically achievable; technical GREEN is necessary but not sufficient.

## Change log

### 2.1.0 — 2026-09-07
- Accepted and merged Task 018 / PR #26.
- Added bounded GPT-6 Astra pricing, long-context fail-closed cost guard, reasoning control/provenance and zero-call readiness.
- Preserved operation-level routing and explicit HUMAN whole-book/operation pins.
- Recorded the SMM series/book pilot identity without introducing runtime coupling.
- Removed the obsolete abstract “Owner creative gate”: pilot title/series are already decided externally.
- Identified Task 017 delivery as the only remaining system-level pre-writing blocker.

### 2.0.0 — 2026-09-07
- Completed Task 014 stacked reconciliation.
- Accepted Task 015 and PR #23 authority.
- Closed Task 016 implementation as absorbed by Task 014.
- Activated the first real Business Nonfiction product-validation path.
