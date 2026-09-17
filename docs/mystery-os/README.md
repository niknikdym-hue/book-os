# MYSTERY OS

**Status:** INCUBATION / OWNER DESIGN DRAFT  
**Version:** 0.2.0  
**Date:** 2026-09-18  
**Repository:** `niknikdym-hue/book-os`  
**Pilot series:** `Линия 112`

## Purpose

MYSTERY OS is a reusable editorial-production system for creating high-quality mystery/crime fiction with an optional supernatural layer. It is designed as a future genre module for the wider BOOK OS publishing system, not as a one-off prompt pack for one series.

The goal is to do once, at system level, the work that should not be reinvented for every novel:

- define the genre canon and hard anti-cheat rules;
- model the solved case before prose generation;
- keep clue, suspect, timeline and reveal logic inspectable;
- make supernatural rules explicit and stable when mysticism is used;
- control narrative POV, reader knowledge and fair withholding;
- verify real-world procedures/facts that materially support case logic;
- preserve character causality, tension, voice and series continuity;
- block cheap cliches, stock twists, template characters and machine-prose shortcuts;
- enforce anti-template and anti-duplication rules across a series;
- target professional international commercial-fiction quality rather than merely complete/acceptable self-publishing output;
- benchmark output against professional-fiction craft standards rather than grading only against internal rules;
- spend premium model/agent budget selectively on high-impact global decisions rather than every page;
- evaluate manuscripts with deterministic checks, independent model judges, cold-reader style tests and human approval;
- optionally use Agents API/Codex for engineering and bounded pre-writing preparation;
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

`commercial premise -> StoryDefinition -> NarrativeContract -> CaseSolution -> FictionResearchLedger -> MysticRuleSet (if any) -> suspects/clues/timeline/knowledge -> character arcs -> scene architecture -> representative sample -> admitted writing -> midpoint/whole-book audits -> Professional Fiction Benchmark -> Literary Master`

The hidden solution is authority. Draft prose is downstream.

## Project documents

1. [`MYSTERY_OS_SPEC_v0.1.md`](MYSTERY_OS_SPEC_v0.1.md) — product identity, lifecycle, roles and governing invariants.
2. [`EDITORIAL_MACHINE_GATE_MAP_v0.1.md`](EDITORIAL_MACHINE_GATE_MAP_v0.1.md) — single fail-closed route from idea to Literary Master and execution/routing map.
3. [`GENRE_CANON_v0.1.md`](GENRE_CANON_v0.1.md) — detective/mystery craft rules, fair play and supernatural constraints.
4. [`ANTI_CLICHE_AND_TEMPLATE_POLICY_v0.1.md`](ANTI_CLICHE_AND_TEMPLATE_POLICY_v0.1.md) — blocked cliches, risky tropes, AI-template pathologies and exception protocol.
5. [`WORLD_CLASS_FICTION_STANDARD_v0.1.md`](WORLD_CLASS_FICTION_STANDARD_v0.1.md) — professional/publisher-level fiction quality target and observable standards.
6. [`NARRATIVE_CONTRACT_v0.1.md`](NARRATIVE_CONTRACT_v0.1.md) — POV, narrator reliability, reader knowledge and fair-withholding authority.
7. [`FICTION_RESEARCH_AND_REALISM_v0.1.md`](FICTION_RESEARCH_AND_REALISM_v0.1.md) — factual/procedural realism, research risk and intentional fictionalization rules.
8. [`PROFESSIONAL_FICTION_BENCHMARK_v0.1.md`](PROFESSIONAL_FICTION_BENCHMARK_v0.1.md) — external craft benchmark protocol and representative-sample gate.
9. [`QUALITY_ROUTING_v0.1.md`](QUALITY_ROUTING_v0.1.md) — selective premium intelligence, Astra/agent/standard-writer/deterministic routing and cost rules.
10. [`ONTOLOGY_AND_CONTRACTS_v0.1.md`](ONTOLOGY_AND_CONTRACTS_v0.1.md) — first-class fiction entities, relationships and versioned contracts.
11. [`QUALITY_GATES_v0.1.md`](QUALITY_GATES_v0.1.md) — MysteryBench dimensions, blocking defects and acceptance protocol.
12. [`SERIES_BIBLE_AND_COMMERCIAL_GATE_v0.1.md`](SERIES_BIBLE_AND_COMMERCIAL_GATE_v0.1.md) — market/premise gate, series engine and anti-duplication rules.
13. [`INTEGRATION_WITH_BOOK_OS_v0.1.md`](INTEGRATION_WITH_BOOK_OS_v0.1.md) — shared platform core, fiction extensions and future migration path.
14. [`CODEX_AGENT_EXECUTION_v0.1.md`](CODEX_AGENT_EXECUTION_v0.1.md) — reuse of the BOOK OS Agents API engineering lane for implementation work.
15. [`AGENTS_API_EDITORIAL_PREP_v0.1.md`](AGENTS_API_EDITORIAL_PREP_v0.1.md) — optional Codex/Agents API lane for bounded pre-writing preparation.
16. [`pilots/LINE_112_PILOT_v0.1.md`](pilots/LINE_112_PILOT_v0.1.md) — first pilot profile; series-specific decisions do not become universal genre rules.
17. [`../../contracts/mystery-os/mystery_os_authority_pack.schema.json`](../../contracts/mystery-os/mystery_os_authority_pack.schema.json) — machine-readable v0.1 mystery authority pack.
18. [`../../contracts/mystery-os/narrative_contract.schema.json`](../../contracts/mystery-os/narrative_contract.schema.json) — machine-readable NarrativeContract.
19. [`../../contracts/mystery-os/fiction_research_ledger.schema.json`](../../contracts/mystery-os/fiction_research_ledger.schema.json) — machine-readable factual realism ledger.
20. [`../../contracts/mystery-os/professional_fiction_benchmark.schema.json`](../../contracts/mystery-os/professional_fiction_benchmark.schema.json) — machine-readable benchmark run/findings contract.
21. [`../../contracts/mystery-os/editorial_prep_agent.schema.json`](../../contracts/mystery-os/editorial_prep_agent.schema.json) — machine-readable editorial-prep agent request contract.
22. [`../tasks/TASK_022_MYSTERY_OS_FOUNDATION.md`](../tasks/TASK_022_MYSTERY_OS_FOUNDATION.md) — bounded project/task contract and stop gate.

## What is shared with BOOK OS

MYSTERY OS should reuse, not fork, mature BOOK OS primitives where semantics are genuinely shared:

- Author / Series profiles;
- Style Profile / author voice;
- Authority statuses and human approval;
- Research Source/Evidence infrastructure for real-world facts;
- Book Memory and cross-book retrieval;
- Model Gateway and operation-level routing;
- provenance and cost ledger;
- immutable revision graph;
- Literary Master;
- audio adaptation / recording-script workflow;
- Publishing Package and platform metadata;
- local-first application/security/backup boundaries;
- general BookBench infrastructure;
- accepted Agents API engineering infrastructure, when available.

Mystery-specific logic belongs in extensions, not hacks to nonfiction contracts.

## What is new

The fiction/mystery layer introduces first-class objects such as:

- `StoryDefinition`;
- `NarrativeContract` / `ReaderKnowledgeState`;
- `CaseSolution`;
- `MysteryQuestion`;
- `Suspect` / `Secret` / `Alibi`;
- `Clue` / `RedHerring` / `EvidenceChain`;
- `CaseTimeline` / `NarrativeTimeline`;
- `CharacterKnowledgeState`;
- `FictionResearchItem` / `FictionalizationDecision`;
- `MysticRuleSet` / `MysticEvent`;
- `CharacterArc` / `RelationshipArc`;
- `SceneContract`;
- `RevealPlan`;
- `AntiClicheFinding` / `AntiClicheException`;
- `RepresentativeFictionSample`;
- `ProfessionalFictionBenchmarkRun`;
- `MysteryBenchRun`;
- `ColdReaderRun`.

## Editorial machine

The canonical gate map is:

`IDEA -> MARKET -> SERIES POSITION -> STORY DEFINITION -> NARRATIVE CONTRACT -> CASE SOLUTION -> REALISM PLAN -> MYSTIC RULES -> CHARACTERS -> SUSPECT/CLUE/TIMELINE -> SCENE ARCHITECTURE -> REPRESENTATIVE SAMPLE -> WRITING -> MIDBOOK -> DEVELOPMENTAL REBUILD -> WHOLE-BOOK AUDITS -> PROFESSIONAL BENCHMARK -> LITERARY MASTER -> DERIVATIVES`

A provider response does not advance state by itself. Required authority must be fresh and required gates must pass.

## Quality routing

MYSTERY OS does **not** use the most expensive model for every page.

The intended hierarchy is:

- **deterministic/local checks** for properties software can prove;
- **standard Writer/Editor** for most bounded scene drafting and routine local revisions once architecture and representative sample are strong;
- **premium frontier/Astra-class execution** for high-impact global decisions and long-context diagnosis;
- **Agents API/Codex editorial preparation** for bounded multi-step planning/adversarial work when that mode is explicitly launched and cost-justified.

Examples of premium/global operations include concept/series engine, CaseSolution, narrative/reveal architecture, difficult character arcs, midpoint structural diagnosis, adversarial case reconstruction, professional benchmark diagnosis and final whole-book developmental/literary review.

Cost optimizes the route to the quality target. It does not silently lower the target.

## Agents API / Codex modes

MYSTERY OS is designed to support two separate optional agent modes:

### `ENGINEERING`

For software/spec implementation:
- code;
- migrations;
- validators;
- tests;
- MysteryBench implementation;
- UI/integration work.

It reuses the secure BOOK OS development-agent lane and returns proposal patches/reports for Central Brain review.

### `EDITORIAL_PREP`

For book preparation before Writing:
- concept alternatives;
- StoryDefinition;
- NarrativeContract candidates/audits;
- CaseSolution;
- suspects/secrets;
- clues/red herrings;
- timeline;
- realism dependency discovery;
- MysticRuleSet;
- RevealPlan;
- anti-cliche/adversarial audits;
- professional benchmark diagnosis;
- writing-readiness preparation.

Outputs are always `PROPOSED`; they cannot self-unlock Writing or self-approve literary authority.

Agents API is an optional accelerator, not a runtime dependency.

## Quality target

The target is not “AI can produce a mystery-shaped manuscript” and not “good enough for Samizdat”. The target is a professional commercial mystery novel whose plot survives adversarial reconstruction, whose reveal is earned, whose characters and prose have identity, whose real-world mechanics are credible, whose narrative does not cheat, and whose series does not collapse into repeated templates.

Software GREEN is necessary and insufficient. Internal MysteryBench GREEN is also insufficient by itself: a professional benchmark and human literary judgment are mandatory before MYSTERY OS may be treated as quality-complete.

## First pilot

`Линия 112` is the first intended pilot because it exercises demanding reusable requirements at once:

- contemporary setting;
- real crime/mystery engine;
- genuine supernatural layer without deus ex machina;
- emergency-service/procedural realism risk;
- recurring-series potential;
- strong audio requirements;
- high need for clue/timeline/fair-play integrity;
- narrative-information control;
- commercial-series differentiation;
- strong anti-cliche pressure.

No plot, culprit, recurring-team design, literal 112 mechanism or fixed supernatural gimmick is accepted merely by naming the pilot. Those remain future human-gated decisions.