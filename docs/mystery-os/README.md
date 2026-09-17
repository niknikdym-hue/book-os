# MYSTERY OS

**Status:** INCUBATION / OWNER DESIGN DRAFT  
**Version:** 0.1.0  
**Date:** 2026-09-17  
**Repository:** `niknikdym-hue/book-os`  
**Pilot series:** `Линия 112`

## Purpose

MYSTERY OS is a reusable editorial-production system for creating high-quality mystery/crime fiction with an optional supernatural layer. It is designed as a future genre module for the wider BOOK OS publishing system, not as a one-off prompt pack for one series.

The goal is to do once, at system level, the work that should not be reinvented for every novel:

- define the genre canon and hard anti-cheat rules;
- model the solved case before prose generation;
- keep clue, suspect, timeline and reveal logic inspectable;
- make supernatural rules explicit and stable when mysticism is used;
- preserve character causality, tension, voice and series continuity;
- enforce anti-template and anti-duplication rules across a series;
- evaluate the manuscript with deterministic checks, independent model judges, blind-reader style tests and human approval;
- produce text, audio and publishing derivatives from an exact accepted Literary Master.

## Authority boundary

MYSTERY OS is deliberately introduced as an **incubating module**.

It does **not** silently change current BOOK OS authority, whose accepted product identity is nonfiction. Until the Owner separately approves promotion/integration:

- current BOOK OS nonfiction production semantics remain unchanged;
- no current Authority file is superseded by this folder;
- no runtime/database/UI migration is authorized by this draft alone;
- MYSTERY OS artifacts are design contracts for review and pilot preparation;
- any future integration must preserve BOOK OS Authority Protocol, human gates, versioning, provenance, local-first storage, Literary Master semantics, model/provider neutrality and cost controls.

## Core design principle

Mystery quality must not depend on a model improvising the answer while drafting.

The system works from a **solved private case model** toward a fair reader-facing narrative:

`commercial premise -> story definition -> solved case -> supernatural rules (if any) -> suspect/clue/timeline model -> character arcs -> scene architecture -> admitted writing -> audits -> Literary Master`

The hidden solution is authority. Draft prose is downstream.

## Project documents

1. [`MYSTERY_OS_SPEC_v0.1.md`](MYSTERY_OS_SPEC_v0.1.md) — product identity, lifecycle, roles and governing invariants.
2. [`GENRE_CANON_v0.1.md`](GENRE_CANON_v0.1.md) — detective/mystery craft rules, fair play and supernatural constraints.
3. [`ONTOLOGY_AND_CONTRACTS_v0.1.md`](ONTOLOGY_AND_CONTRACTS_v0.1.md) — first-class entities, relationships and versioned contracts.
4. [`QUALITY_GATES_v0.1.md`](QUALITY_GATES_v0.1.md) — MysteryBench dimensions, blocking defects and acceptance protocol.
5. [`SERIES_BIBLE_AND_COMMERCIAL_GATE_v0.1.md`](SERIES_BIBLE_AND_COMMERCIAL_GATE_v0.1.md) — market/premise gate, series engine and anti-duplication rules.
6. [`INTEGRATION_WITH_BOOK_OS_v0.1.md`](INTEGRATION_WITH_BOOK_OS_v0.1.md) — shared core, fiction-specific extensions and future migration path.
7. [`pilots/LINE_112_PILOT_v0.1.md`](pilots/LINE_112_PILOT_v0.1.md) — first pilot profile; series-specific rules do not become universal genre rules.
8. [`../../contracts/mystery-os/mystery_os_authority_pack.schema.json`](../../contracts/mystery-os/mystery_os_authority_pack.schema.json) — machine-readable v0.1 authority-pack contract.
9. [`../tasks/TASK_022_MYSTERY_OS_FOUNDATION.md`](../tasks/TASK_022_MYSTERY_OS_FOUNDATION.md) — bounded project/task contract.

## What is shared with BOOK OS

MYSTERY OS should reuse, not fork, mature BOOK OS primitives where semantics are genuinely shared:

- Author / Series profiles;
- Style Profile / author voice;
- Authority statuses and human approval;
- Book Memory and cross-book retrieval;
- Model Gateway and operation-level routing;
- provenance and cost ledger;
- immutable revision graph;
- Literary Master;
- audio adaptation / recording-script workflow;
- Publishing Package and platform metadata;
- local-first application/security/backup boundaries;
- general BookBench infrastructure.

Mystery-specific logic belongs in extensions, not hacks to nonfiction contracts.

## What is new

The fiction/mystery layer introduces first-class objects such as:

- `StoryDefinition`;
- `CaseSolution`;
- `MysteryQuestion`;
- `Suspect` / `Secret` / `Alibi`;
- `Clue` / `RedHerring` / `Revelation`;
- `CaseTimeline`;
- `MysticRuleSet` / `MysticEvent`;
- `CharacterArc` / `RelationshipArc`;
- `SceneContract`;
- `RevealPlan`;
- `MysteryBenchRun`;
- `ColdReaderRun`.

## Quality target

The target is not “AI can produce a mystery-shaped manuscript”. The target is a professional mystery novel whose plot remains coherent under adversarial reconstruction, whose reveal is earned, whose prose and characters are publishable, and whose series does not collapse into repeated templates.

Software GREEN is necessary and insufficient. A real-book pilot and human editorial judgment are mandatory before MYSTERY OS may be promoted into general BOOK OS production.

## First pilot

`Линия 112` is the first intended pilot because it exercises the hardest reusable requirements at once:

- contemporary setting;
- real crime/mystery engine;
- genuine supernatural layer without deus ex machina;
- recurring-series potential;
- strong audio requirements;
- high need for clue/timeline/fair-play integrity;
- commercial-series differentiation.

No plot, culprit, recurring-team design or fixed supernatural gimmick is accepted merely by naming the pilot. Those remain future human-gated decisions.