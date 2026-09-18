# MYS-05 — EDITORIAL MACHINE GATE / SCENECONTRACT / WRITING_ALLOWED

**Status:** IMPLEMENTATION / STACKED DRAFT  
**Date:** 2026-09-18  
**Repository:** `niknikdym-hue/book-os`  
**Base:** `codex/mys-04-fiction-research-20260918` @ `e50f82fc37c7673873bb31773d7090b04ade0551`  
**Branch:** `codex/mys-05-writing-admission-20260918`

## Purpose

Compose the already-implemented MYSTERY OS authority and deterministic validation layers into one fail-closed, **scene-scoped writing admission**.

MYS-05 is the first runtime slice that answers:

> May this exact SceneContract revision be handed to a Writer/provider now?

It does not write prose.

It emits a deterministic `WritingAdmissionToken` only when the current snapshot passes.

## Inputs composed by MYS-05

- MYS-01 exact authority/revision/dependency/staleness;
- MYS-02 CaseIntegrityResult;
- MYS-03 NarrativeValidationResult / reader-knowledge state, including proof that the exact scene was evaluated;
- MYS-04 ResearchLedgerResult, including per-research external evidence snapshot refs and recheck deadlines;
- current SceneContract;
- external anti-cliche evaluation evidence until MYS-10 owns it;
- representative-sample / Writer qualification evidence where required by production mode;
- execution-route / execution / cost authorization when provider access is requested.

## SceneContract

The scene is a writing-admission unit, not global story authority.

Minimum executable fields include:

- `scene_id`;
- viewpoint;
- time ref;
- location ref;
- purpose;
- entering state;
- exiting state;
- knowledge-state ref;
- at least one state-change code;
- tension source;
- mystery/clue/reveal operations where applicable;
- factual/research dependencies;
- continuity constraints;
- prohibited disclosure;
- anti-cliche warnings;
- audio/listenability notes where applicable.

A scene with no state change is not admitted merely because it is fluent prose.

## Scene review vs human approval

Global high-blast-radius authority remains HUMAN-approved through MYS-01:

- StoryDefinition;
- NarrativeContract;
- CaseSolution;
- accepted research conclusions;
- other accepted book-level authority.

A SceneContract may receive writing admission at `REVIEWED` without requiring the Owner to click APPROVE for every scene.

This does **not** weaken authority because admission is bound to:

- the exact SceneContract revision/hash;
- the exact effective upstream revision IDs;
- a deterministic dependency fingerprint;
- exact evaluation refs;
- the earliest relevant research recheck deadline.

If any of these change — or the research deadline is reached — the previous admission token is no longer current.

## Required authority

Every SceneContract must have exact dependencies on at least:

- StoryDefinition;
- NarrativeContract;
- CaseSolution.

Policy may require additional book authority.

SceneContract-required research IDs are converted to exact `FICTION_RESEARCH_ITEM` authority dependencies.

Every actual dependency — not only the minimum list — must point to a current effective accepted revision.

## Working vs effective authority

A newer upstream DRAFT does not invalidate writing based on the currently accepted upstream revision.

Once that new upstream revision becomes effective/accepted, a SceneContract still bound to the old revision fails with a stale dependency.

This preserves the MYS-01 rule that proposals do not silently replace accepted authority.

## Gate composition

MYS-05 currently creates these deterministic records:

1. `SCENE_CONTRACT`
2. `AUTHORITY_FRESHNESS`
3. `CASE_INTEGRITY`
4. `NARRATIVE_FAIRNESS`
5. `REALISM_RESEARCH`
6. `ANTI_CLICHE_EXTERNAL`
7. `SAMPLE_WRITER_QUALIFICATION`
8. `EXECUTION_AUTHORIZATION`

Any blocking finding prevents `WRITING_ALLOWED`.

## Anti-cliche fail-closed boundary

Even before MYS-10 exists, MYS-05 requires an `anti_cliche_evaluation_ref`.

No unresolved BLOCKED-BY-DEFAULT code may remain.

MYS-10 will later become the standard producer of this evidence; MYS-05 does not implement its scanner.

## Representative sample vs mass drafting

### REPRESENTATIVE_SAMPLE

May be admitted before Writer qualification because the sample itself is used by MYS-06 to qualify the prose mode/Writer.

All other current gates still apply, including authority, case, narrative, research and anti-cliche evidence.

### MASS_DRAFT

Requires:

- representative sample qualified;
- exact sample evaluation ref;
- Writer qualified;
- exact Writer qualification ref.

Therefore MYS-05 cannot accidentally scale an unqualified prose mode to a whole manuscript before MYS-06 evidence exists.

## Provider / cost safety

When provider execution is requested, admission also requires:

- execution route ref;
- execution authorization ref;
- cost authorization ref.

If provider execution is not requested, deterministic/local planning may evaluate admission without these refs.

MYS-05 does not call a provider.

## Narrative scope

A clean NarrativeValidationResult is not sufficient unless it contains a ReaderKnowledge checkpoint for the exact SceneContract scene_id.

This prevents a validation result for another scene, an empty evaluation, or a stale partial run from being reused as if the current scene had passed POV/reader-fairness checks.

## Research interaction

Research blocks admission when:

- an explicitly required research item is invalid;
- any research authority actually bound to the SceneContract is invalid;
- accepted authority consumed by the scene is marked affected by external research invalidation;
- the scene authority itself is marked affected;
- a relevant research evaluation snapshot is missing;
- a relevant research recheck deadline has been reached.

Research snapshot refs are kept per research authority entity. An unrelated research update elsewhere in the book does not invalidate this scene token, while a non-blocking evidence/access-state change for research actually used by this scene does.

The token records the earliest relevant `not_after_epoch`, so cached-green research cannot keep a writing authorization alive past its recheck deadline.

This catches expiry or superseded/changed evidence even when story text itself did not change.

## Version-bound admission token

A successful result contains:

- deterministic admission ID;
- book ID;
- scene ID;
- production mode;
- exact SceneContract revision ref;
- dependency fingerprint;
- authority revision refs;
- evaluation refs;
- earliest relevant `not_after_epoch`.

`verify_writing_admission_token()` re-runs the full gate immediately before Writer/provider access using the current deterministic clock.

The old token is invalid if:

- current gate becomes BLOCKED;
- SceneContract changes;
- an accepted upstream revision changes;
- dependencies change after review;
- a non-blocking narrative or relevant-research evaluation snapshot changes;
- a research recheck deadline is reached;
- qualification/execution evidence changes.

This closes the gap where a scene could be approved once and executed later against different authority.

## Machine-readable contracts

MYS-05 adds:

- `contracts/mystery-os/scene_contract.schema.json`;
- `contracts/mystery-os/writing_admission_token.schema.json`.

These are integration contracts for the future publishing system; they do not imply DB/API/UI implementation in this slice.

## Deliberately OUT

MYS-05 does not implement:

- MYS-06 representative sample generation/qualification;
- MYS-07 MysteryBench;
- MYS-10 anti-cliche scanner/exception registry;
- MYS-11 actual model routing;
- MYS-13 Agents API runner;
- DB/Alembic/API/Desktop;
- prose generation;
- real `Линия 112` content;
- merge/release.

It only consumes explicit refs from future layers so the gate stays fail-closed until those layers provide them.

## Acceptance evidence

MYS-05 is technically GREEN only when:

- clean reviewed SceneContract can receive representative-sample admission without human per-scene approval;
- missing/stale exact dependencies block;
- unaccepted upstream DRAFT does not displace accepted authority;
- acceptance of a new upstream invalidates old admission;
- case/narrative/research blockers block;
- narrative evaluation must cover the exact scene;
- relevant research evidence snapshot changes invalidate old tokens;
- cached-green research cannot outlive its recheck deadline;
- anti-cliche evaluation evidence is mandatory;
- MASS_DRAFT fails without MYS-06 sample/Writer qualification evidence;
- provider access fails without route/execution/cost authorization;
- dependency/evaluation changes invalidate prior token;
- full inherited test suite remains green;
- Ruff/mypy/pytest + Desktop/Tauri/native/secret scan pass;
- zero provider/model/paid calls;
- Central Brain reviews exact diff.

Technical GREEN does not authorize merge or manuscript Writing.
