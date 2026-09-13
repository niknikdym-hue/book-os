# BOOK OS — TASK 021 — AUTO BOOK COMPLETE CYCLE AND SERIES STUDIO

**State:** IMPLEMENTED_AWAITING_CENTRAL_BRAIN_ACCEPTANCE
**Milestone:** product workflow consolidation after accepted PR #37
**Baseline:** `origin/main` at `19ab44ba30036936f843e9b13f2a0f7c8f7b1204`
**Date:** 2026-09-13

## Why now

The repository contained strong authority, research, memory, editorial, BookBench, Literary Master,
provider and series primitives, but the author still had to operate them as separate technical
panels. Auto Book stopped before the complete research/editorial/correction/export cycle, and
Series Studio did not yet provide a persistent multi-book workspace.

## Goal

An author describes a nonfiction book, chooses **Автоматически**, selects required files and starts
one durable workflow. BOOK OS researches, plans, writes, checks, edits, independently critiques,
corrects and exports the selected book without turning the UI into a routing console. For a series,
the same workflow must preserve Series Bible and Book Passport boundaries and fail closed on stale
or material cross-book overlap.

## In scope

- operation/complexity/risk/cost-aware model routing with exact provenance;
- durable Local Core orchestration, budget reservations, idempotency and recovery;
- research and attachment context, chapter and whole-book checks, mid-book audit;
- independent exact-snapshot critique and at most two bounded correction passes;
- structured selected outputs and visual/audio equivalents;
- new/external/existing series scenarios, 3–5 concepts, explicit book/file binding and rights;
- persistent Series Bible, Book Passports, imported sources, similarity findings and Owner decisions;
- hard series gates before WRITING and finalization;
- Owner-specific «Секреты продвижения услуг» preset stored only as a series profile;
- deterministic fixtures, migrations, backup compatibility, UI and regression checks.

## Out of scope

- rewriting the supplied private «Как продавать услуги» manuscript;
- provider training/fine-tuning or imitation of third-party text;
- paid quality generation without a separate bounded Owner approval;
- automatic publication, audiobook synthesis, cover generation, merge or replacement of the
  installed macOS application;
- a second research, quality, memory, authority or model-gateway architecture.

## Acceptance evidence

1. Auto is the default and manual modes remain available.
2. The desktop observes a Local Core worker and restores progress after restart.
3. Every stage has durable input/output evidence; unknown paid outcomes are not blindly repeated.
4. Model/effort choice is operation-aware and recorded, not Astra High for every operation.
5. Unregistered or stale material claims, blocking editorial findings and independent-critique
   findings prevent the master until corrected and rechecked.
6. Selected exports preserve native tables/PNG visuals and their meaning in audio adaptations.
7. Series Studio has three paths, persistent books/order/status, explicit rights and immutable input.
8. Current approved Series Bible, Book Passports and difference map are mandatory for writing/final.
9. Corrupt/partial imports and blocking overlap cannot produce PASS.
10. Full Python/Desktop/Rust/security CI passes at the exact published head with model/paid calls = 0.

Literary quality acceptance additionally requires the separate blinded plan in
`docs/benchmarks/AUTO_BOOK_QUALITY_TRIAL_PLAN_2026-09-13.md`.

## Stop conditions

- no merge by Codex;
- no live paid/model call without explicit Owner authorization of the exact plan and hard cap;
- do not commit manuscripts, secrets or locally stored project data;
- do not report literary quality from deterministic tests alone.

## Unlocks next

Owner review of the actual author workflow and a small budgeted real-quality comparison. Only its
results may justify routing-floor changes or acceptance of the complete Auto Book experience.
