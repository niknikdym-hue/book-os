# MYS-09 — SERIES BRAIN / BOOK PASSPORT / COLLISION GATE

**Status:** IMPLEMENTATION / STACKED DRAFT  
**Date:** 2026-09-19  
**Repository:** `niknikdym-hue/book-os`  
**Base:** `codex/mys-08-professional-fiction-benchmark-20260919` @ `ff1d7692f9b26e03dee162fdb464c2f7cf325258`  
**Branch:** `codex/mys-09-series-brain-book-passport-20260919`

## Purpose

Prevent a successful mystery series from becoming a visible formula.

MYS-09 separates:

- recurring **series promises** that readers should recognize;
- book-specific **variables** that must materially change;
- **consumable assets** that lose value after use;
- **reserved assets** held for future books;
- lexical/exact collisions;
- semantic collisions hidden behind renamed professions, locations or surface details.

It does not generate series ideas or run a semantic model itself.

## Book Passport

Every accepted/planned volume has a `MysteryBookPassport` recording at least:

- premise signature;
- primary case type;
- victim/target profile;
- culprit relationship;
- motive family;
- mechanism;
- concealment;
- suspect architecture;
- clue architecture;
- red-herring pattern;
- supernatural device;
- setting type;
- protagonist jeopardy;
- emotional conflict;
- recurring relationship movement;
- midpoint reversal;
- final reveal;
- climax staging;
- ending state;
- opening/body-discovery/interview patterns;
- case-solution architecture;
- prose/scene-pattern risk;
- assets consumed;
- assets reserved;
- explicit claims on prior reservations.

The passport is content-hashed.

## Series Profile evolution

A series bible can evolve after each volume.

Therefore:

- the **current** Book Passport must bind to the exact current Series Profile revision;
- historical accepted passports retain their historical Series Profile ref;
- all passports must share the same stable `series_profile_id`.

Updating the Series Bible for book 4 does not rewrite book 1's accepted history.

Acceptance-time recurring-asset policy is stored with each accepted historical passport so later Series Bible changes cannot retroactively reinterpret whether a previous use was a one-use asset or an allowed signature.

## Exact collision layer

Deterministic/local checks handle literal identity cheaply.

Policy distinguishes:

- `exact_blocking_dimensions`;
- `exact_attention_dimensions`.

Examples of blocking exact repeats may include:

- mechanism;
- supernatural device;
- suspect architecture;
- final reveal;
- climax staging;
- relationship movement;
- CaseSolution architecture.

Exact-attention patterns such as repeated opening/interview cadence are diagnostics by themselves and may remain non-blocking until semantic/fatigue evidence makes them material.

A hard composite rule blocks:

> same culprit relationship + same motive family.

This rule is independent of superficial renaming.

## Semantic collision core

Exact checks are not enough.

MYS-09 requires semantic comparison against **every accepted prior Book Passport** across the minimum core:

- premise;
- case type;
- culprit relationship;
- motive family;
- mechanism;
- concealment;
- suspect architecture;
- clue architecture;
- supernatural device;
- midpoint reversal;
- protagonist jeopardy;
- emotional conflict;
- relationship movement;
- final reveal;
- climax staging;
- setting type;
- CaseSolution architecture;
- prose/scene-pattern risk.

The policy may add dimensions; it may not remove this core.

Exact and semantic dimensions are intentionally allowed to overlap.

This is required because:

- exact comparison catches identical codes/structures cheaply;
- semantic comparison catches the same idea with changed labels.

Only `exact_blocking` and `exact_attention` are mutually exclusive.

## Semantic evidence

For every:

`current book × prior book × required semantic dimension`

MYS-09 requires `SeriesSemanticCollisionEvidence`.

States:

- `CLEAR`;
- `ATTENTION`;
- `MATERIAL_COLLISION`.

Every row binds to a shared immutable `VerifiedEvaluationArtifact`.

Artifact purpose must be exactly:

`SERIES_COLLISION:<current_book_id>:<prior_book_id>:<dimension>`

and must match:

- current Series Context snapshot;
- evaluator identity/class;
- rubric;
- SUCCEEDED;
- current=true.

A single bounded Series Editor / Agents API operation may produce many registered dimension artifacts. MYS-09 does **not** require one provider call per dimension.

## Independence

Series semantic evidence is high-stakes editorial evidence.

When independence is required:

- independence state must be `INDEPENDENT`;
- evaluator identity may not equal Writer executor identity.

Writer identity is part of Series Context hash, so changing the Writer configuration invalidates previous independence-bound semantic evidence.

## Series Context vs Series Brain ref

Two refs are deliberately separate.

### `series-context:<hash>`

Stable input snapshot for semantic evaluation:

- current Series Profile;
- current Book Passport;
- all accepted prior Book Passport refs/hashes;
- acceptance-time recurring-asset policies;
- collision policy;
- Writer executor identity.

### `series-brain:<hash>`

Final gate snapshot:

- exact Series Context ref;
- semantic evidence rows.

Thus semantic evidence can be evaluated against a stable context without a cyclic hash, while any rerun/change in semantic evidence still changes the final Series Brain ref.

## Asset ledger

MYS-09 replays the complete accepted historical asset ledger in book-number order.

It validates:

- one-use assets are not consumed twice;
- recurring signature assets may recur;
- future reservations exist before they are claimed;
- a reservation claim is consumed in the claiming book;
- reserved assets are not consumed without claim;
- consumed assets cannot later be reserved;
- reservations cannot be duplicated;
- recurring signatures cannot be reserved as one-use future assets.

The historical ledger itself is revalidated on every run.

A corrupt imported history blocks a new volume rather than becoming accepted fact.

## Reservation semantics

A prior book may reserve an asset for later.

A later book consumes it by recording both:

- the code in `assets_consumed`;
- the same code in `reservation_claim_codes`.

This creates a visible handoff rather than silently stealing a planned future reveal.

## Standalone series rule

Default mystery-series policy:

- each volume resolves its primary case;
- later volumes provide a bounded late-entry orientation;
- recurring relationship/series arcs may continue.

A Series Profile may explicitly select `strongly_serialized=true` to relax those two default gates.

## Human attention disposition

`MATERIAL_COLLISION` is blocking.

`ATTENTION` may proceed only when policy permits and a required human disposition ref is verified.

A model-generated string cannot impersonate that human decision.

## Writing admission integration

MYS-09 is not a report-only feature.

MYS-05 `WritingGatePolicy` gains `series_book`.

For series books:

- `series_uniqueness_qualified` must be true;
- exact `series_brain_ref` must exist.

`readiness_with_series_uniqueness()` is the standard bridge.

If Series Brain fails, manual stale readiness flags are cleared.

The exact Series Brain ref becomes part of the WritingAdmissionToken evaluation provenance.

Standalone books are unchanged.

## Machine contracts

MYS-09 adds:

- `contracts/mystery-os/mystery_book_passport.schema.json`;
- `contracts/mystery-os/series_semantic_collision.schema.json`;
- `contracts/mystery-os/series_brain_run.schema.json`.

## Cost/model boundary

This implementation performs **zero provider/model calls**.

Future semantic collision execution is a strong candidate for a bounded Series Editor / Agents API operation because it compares one new passport against many prior passports in one coordinated run.

Exact comparisons and asset-ledger checks remain local/deterministic.

## Deliberately OUT

- no semantic model execution;
- no real `Линия 112` Book Passport yet;
- no real prior-book corpus;
- no title/cover collision search;
- no reader-feedback fatigue ingestion;
- no database migration;
- no merge authorization.

## Acceptance evidence

MYS-09 is technically GREEN only when tests prove:

- clean new volume passes all prior passports;
- historical Series Profile revisions remain valid history;
- current passport must use exact current profile;
- malformed historical profile refs block;
- prior book numbers truly precede current;
- exact blocking reuse blocks;
- exact attention remains diagnostic;
- same culprit relationship + motive blocks;
- recurring assets may recur;
- one-use assets cannot recur;
- reservation claims are explicit and ordered;
- corrupt prior asset history blocks;
- semantic evidence exists for every prior/core-dimension pair;
- semantic core cannot be disabled;
- semantic material collision blocks despite lexical difference;
- semantic ATTENTION requires verified human disposition;
- semantic evaluator cannot be Writer;
- semantic artifact provenance is exact;
- Series Brain ref changes when semantic evidence changes;
- policy/profile/current passport changes invalidate old evidence;
- standalone case/orientation rules work;
- strongly serialized exception works;
- Book 1 with no priors requires no semantic rows;
- Series Brain is required by MYS-05 before series writing admission;
- inherited MYS-01..08 tests remain GREEN;
- Ruff, strict mypy, full pytest, Desktop/Tauri/native/secret scan pass;
- provider/model/paid calls = 0.

Technical GREEN does not authorize merge or real manuscript writing.
