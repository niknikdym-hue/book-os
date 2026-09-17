# MYSTERY OS — INTEGRATION WITH BOOK OS v0.2

**Status:** INCUBATION DRAFT  
**Date:** 2026-09-18

## 1. Principle

MYSTERY OS is designed as a future fiction genre module of the wider BOOK OS publishing system, not a parallel product that duplicates platform infrastructure.

Integration must happen only after human acceptance of MYSTERY OS authority and bounded implementation evidence.

## 2. Shared platform core

Reuse BOOK OS primitives where semantics are genuinely shared:

- Author / Series hierarchy;
- StyleProfile / author voice;
- authority statuses and immutable revision history;
- human approval gates;
- Research Source/Evidence infrastructure;
- Book Memory / retrieval / cross-book similarity;
- Model Gateway and operation-level routing;
- cost/provenance ledger;
- BookBench infrastructure;
- Literary Master;
- audio adaptation / recording-script path;
- publishing/export infrastructure;
- local-first storage/security/backup;
- Agents API engineering lane after its own acceptance.

Do not fork these primitives merely because fiction has additional semantics.

## 3. Fiction-specific extensions

MYSTERY OS adds genre-specific authority such as:

- StoryDefinition;
- NarrativeContract;
- ReaderKnowledgeState;
- CaseSolution;
- MysteryQuestion;
- Suspect/Secret/Alibi;
- Clue/RedHerring/EvidenceChain;
- CaseTimeline/NarrativeTimeline;
- CharacterKnowledgeState;
- FictionResearchLedger / FictionalizationDecision;
- MysticRuleSet / MysticEvent;
- CharacterArc / RelationshipArc;
- RevealPlan;
- SceneContract;
- RepresentativeFictionSample;
- AntiClicheFinding / AntiClicheException;
- ProfessionalFictionBenchmarkRun;
- MysteryBenchRun / ColdReaderRun;
- EditorialMachineGateState.

These should integrate by extension/composition, not by abusing nonfiction Claim/Chapter fields.

## 4. Editorial Machine state

Future BOOK OS integration should expose one genre-neutral production shell with genre-specific gate packs.

For MYSTERY OS, advancement is governed by `EditorialMachineGateState`.

Required behavior:

- gate state is persisted;
- gate inputs are revision-bound;
- material upstream change marks dependent gates `STALE`;
- `WRITING_ALLOWED` is scoped to exact scenes/chapters and authority revisions;
- missing/stale/blocking gate state fails closed before provider/model access;
- completed model/API execution never self-converts a gate to PASS;
- human-required decisions remain explicit.

This mirrors and extends the chapter-admission philosophy already developed in BOOK OS nonfiction.

## 5. Shared research, separate semantics

Real-world fiction research should reuse BOOK OS Source/Evidence infrastructure.

But fiction must distinguish:

- real-world evidence supporting realism;
- in-world fictional EvidenceChain supporting a case solution.

They are different ontologies even when both use the word evidence.

A FictionResearchItem may reference real sources/evidence and then link to CaseSolution/Clue/Timeline/Scene authority.

## 6. Shared StyleProfile, separate NarrativeContract

StyleProfile remains the shared expression/voice primitive.

NarrativeContract is fiction-specific epistemic authority controlling:
- POV;
- tense/person;
- narrator reliability;
- knowledge access;
- fair withholding;
- psychic distance;
- documentary/dream/vision rules.

Do not overload StyleProfile with mystery fairness semantics.

## 7. BookBench extension

General BookBench infrastructure should be extended with MysteryBench dimensions rather than replaced.

Shared evaluation plumbing may handle:
- exact revision identity;
- findings/severity;
- evaluator provenance;
- human disposition;
- rerun/supersession;
- cost tracking.

Mystery-specific evaluators include:
- case reconstruction;
- fair-play audit;
- narrative-integrity audit;
- clue lifecycle;
- timeline/knowledge audit;
- supernatural-rule audit;
- anti-cliche/series collision;
- ColdReader;
- Professional Fiction Benchmark.

## 8. Professional Fiction Benchmark boundary

Benchmark infrastructure may later become a reusable fiction capability for other genres.

It must remain rights-safe:
- no public copyrighted benchmark corpus;
- no named-living-author imitation objective;
- no substantial protected text in repository/eval artifacts;
- derived metrics and high-level craft comparisons only where appropriate.

Benchmark output is diagnostic evidence, not autonomous literary authority.

## 9. Model routing integration

Reuse operation-level routing.

MYSTERY OS adds operation categories such as:
- premise/series architecture;
- NarrativeContract design;
- CaseSolution;
- clue/reveal architecture;
- realism dependency diagnosis;
- scene drafting;
- midpoint diagnosis;
- ColdReader;
- adversarial reconstruction;
- professional benchmark diagnosis;
- literary edit.

Each role may route to different executors based on measured quality/risk/cost.

No model monopoly.

## 10. Agents API integration

Reuse the accepted BOOK OS Agents API engineering lane for `ENGINEERING` work.

A separate `EDITORIAL_PREP` operation family may use the same safe orchestration principles while keeping:
- private content minimum necessary;
- no secrets;
- bounded spend;
- explicit Owner launch;
- structured outputs;
- outputs `PROPOSED` only;
- no GitHub write from editorial-prep job;
- no self-approval;
- no automatic Writing unlock.

Agent use remains optional.

## 11. UI integration direction

Do not expose ontology complexity directly to the author.

Future author-facing flow should remain simple, for example:

`Замысел -> Конструкция -> Написание -> Редактура -> Проверка -> Выпуск`

Under the surface, fiction-specific gate states control what can run.

Advanced/spoiler views may expose CaseSolution, clue/timeline maps and benchmark findings intentionally.

## 12. Literary Master integration

One shared LiteraryMaster concept should bind genre-specific accepted authority.

For mystery it should reference exact accepted revisions of at least:
- StoryDefinition;
- NarrativeContract;
- CaseSolution;
- character/relationship authority;
- FictionResearchLedger snapshot;
- ClueLedger/EvidenceChains;
- CaseTimeline;
- MysticRuleSet when used;
- StyleProfile;
- manuscript;
- final MysteryBench;
- Professional Fiction Benchmark;
- Series Closure where applicable;
- human release approval.

Derived outputs remain downstream.

## 13. Migration principle

Do not implement MYSTERY OS against an obsolete branch snapshot.

After Task 022 is accepted, every implementation slice must:
- start/rebase from the then-current accepted BOOK OS `main`;
- inspect current Task 021 and Agents API accepted state;
- reuse compatible primitives;
- avoid duplicating already implemented author/series/audio/export/cost systems;
- add migrations only where fiction-specific persisted semantics require them;
- preserve backward compatibility for existing nonfiction books.

## 14. Genre-module future

The long-term platform should permit additional fiction genre packs to share the core while supplying their own authority/eval layers.

MYSTERY OS should therefore prove a pattern:

`BOOK OS shared publishing core + genre authority pack + genre gates + genre evals`

not:

`BOOK OS nonfiction app + mystery hacks`.

## 15. Promotion gate

MYSTERY OS may be promoted from incubation into the wider BOOK OS product only after:

- Task 022 authority is human accepted;
- bounded implementation slices are technically GREEN;
- a synthetic full-cycle fixture proves orchestration/gate semantics;
- representative prose path works;
- a real private `Линия 112` pilot demonstrates professional-quality potential;
- Professional Fiction Benchmark + human editorial review support the quality target;
- existing nonfiction behavior is not regressed;
- Owner explicitly approves product integration.

## 16. Principle

The editorial intelligence is genre-specific. The publishing platform should be shared.