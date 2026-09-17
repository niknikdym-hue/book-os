# TASK 022 — MYSTERY OS FOUNDATION

**Status:** PROPOSED / OWNER REVIEW REQUIRED  
**Date:** 2026-09-18  
**Repository:** `niknikdym-hue/book-os`  
**Base at branch creation:** `19ab44ba30036936f843e9b13f2a0f7c8f7b1204`  
**Branch:** `brain/task-022-mystery-os-foundation-20260917`

## 1. Owner intent

Create MYSTERY OS as a deeply specified, reusable mystery/crime-fiction **editorial machine** with enough rigor that it can later be integrated into the wider BOOK OS publishing platform.

First intended pilot: series **«Линия 112»**.

Owner requirements captured in this task:

- build the writing system once and reuse it across books;
- mystery/detective logic must be explicitly modeled and checked;
- supernatural rules must be controlled rather than improvised;
- cheap overused cliches, stock twists, template characters and AI-prose patterns must be identified and blocked/flagged;
- narrative POV and withholding must not cheat the reader;
- real-world procedures/facts that support case logic must be researched and versioned;
- series books must remain materially unique;
- commercial viability must be checked before full manuscript investment;
- target quality is professional international commercial fiction, not merely acceptable self-publishing/Samizdat output;
- quality must be checked against an external professional-fiction benchmark, not only internal rules;
- expensive frontier intelligence should be used selectively on high-impact/global operations rather than on every page;
- a representative prose sample must prove Writer/voice quality before mass drafting;
- project must be designed for later BOOK OS integration rather than as a separate throwaway tool;
- the existing BOOK OS Agents API/Codex capability must be reusable when needed;
- Agents API/Codex must be usable not only for software implementation but, after a separate safe implementation, for **bounded pre-writing editorial preparation**;
- no current nonfiction authority/runtime may be silently broken or replaced.

## 2. Scope of Task 022

### IN

- MYSTERY OS product/editorial specification;
- canonical Editorial Machine gate map;
- genre canon and fair-play rules;
- supernatural-rule discipline;
- narrative/POV/reader-knowledge contract;
- fiction research and real-world realism discipline;
- anti-cliche / anti-template policy;
- professional fiction quality standard;
- external Professional Fiction Benchmark protocol;
- representative-fiction-sample gate;
- selective premium-intelligence / cost-aware routing policy;
- fiction-specific ontology and contracts;
- MysteryBench quality gates;
- series/commercial governance;
- future BOOK OS integration boundary;
- first pilot profile for «Линия 112»;
- machine-readable authority/narrative/research/benchmark/gate-state schemas;
- optional Codex/Agents API engineering execution contract;
- optional Codex/Agents API editorial-preparation contract;
- secure separation between engineering and editorial-prep agent modes;
- future implementation roadmap/slices.

### OUT

- no database migration;
- no Local Core implementation;
- no Desktop UI change;
- no paid model/API call;
- no real manuscript generation;
- no real private unpublished plot committed to repository;
- no application install/replacement;
- no deployment/release;
- no merge to main without Owner approval;
- no change to accepted BOOK OS nonfiction product identity in current main;
- no self-approval by Codex/agent.

## 3. Required design invariants

### 3.1 Solution-before-prose
Systematic mystery drafting requires an accepted solved case model. Writer cannot invent the culprit/decisive mechanism ad hoc while drafting.

### 3.2 Truth separation
The system separates objective story truth, character knowledge, investigator hypotheses, reader-visible evidence, narrator knowledge and narrative presentation.

### 3.3 Fair play
Decisive solution facts/rules cannot appear only in the final explanation unless the selected genre profile explicitly rejects fair-play expectations and reader promise reflects that choice.

### 3.4 Supernatural discipline
If supernatural causality is material, powers/limits/triggers/reliability are versioned authority. No late new power may solve the case.

### 3.5 Anti-cliche enforcement
Cheap cliches are not merely “style suggestions”. A registry distinguishes blocked-by-default devices, high-risk tropes, style pathologies and series collisions. Blocked devices require an explicit human-approved exception.

### 3.6 Series uniqueness
Same case structure with changed names/location/profession is a failure.

### 3.7 Professional quality target
“Complete”, “readable”, “genre-correct”, “technically coherent” or “good enough for self-publishing” are not sufficient acceptance criteria. The manuscript target is professionally conceived, edited and authored commercial fiction capable of comparison with established-publisher genre work.

### 3.8 Human authority
Human Owner approves material story/series authority and final release. AI proposes and critiques.

### 3.9 No hidden integration shortcut
Fiction semantics must not be stuffed into nonfiction fields just to avoid proper future schema design.

### 3.10 Agent optionality
Agents API/Codex may accelerate engineering and pre-writing preparation, but normal authoring must not depend on an external agent runtime.

### 3.11 Selective premium intelligence
The strongest/most expensive executor is reserved for operations where a wrong decision has high downstream blast radius or where measured quality gain is material. Most ordinary scene drafting may use a cheaper proven Writer under strong authority/QA. Deterministic checks should not spend model tokens.

### 3.12 No silent quality downgrade
Cost controls optimize the route to the quality target; they do not redefine the target downward. If budget prevents a quality-critical operation, the trade-off must be surfaced to the Owner.

### 3.13 Narrative honesty
A mystery may misdirect but may not preserve a twist by silently censoring conscious POV knowledge, changing narrator rules or using unearned unreliability. NarrativeContract is first-class authority.

### 3.14 Research realism
Plot-critical real-world facts/procedures are linked to story authority through a FictionResearchLedger. Unresolved R3/R4 dependencies block affected Writing. Model assertions are not evidence.

### 3.15 External professional benchmark
Internal MysteryBench cannot certify world-class/professional quality by itself. Representative and whole-book candidates must be evaluated against curated professional-fiction craft benchmarks without copying protected expression or named-author voice.

### 3.16 Representative-sample-first
Do not scale an unproven prose mode to a full manuscript. A bounded representative sample must pass material voice, POV, scene, dialogue, anti-cliche and benchmark checks before mass drafting.

### 3.17 Fail-closed editorial state
Future runtime must represent gate state explicitly. `WRITING_ALLOWED` is scoped, version-bound and false when required authority/evaluations are missing, stale or blocking. A completed model call never implies gate PASS.

## 4. Deliverables in this branch

Required project pack:

- `docs/mystery-os/README.md`;
- `docs/mystery-os/MYSTERY_OS_SPEC_v0.1.md`;
- `docs/mystery-os/EDITORIAL_MACHINE_GATE_MAP_v0.1.md`;
- `docs/mystery-os/GENRE_CANON_v0.1.md`;
- `docs/mystery-os/ANTI_CLICHE_AND_TEMPLATE_POLICY_v0.1.md`;
- `docs/mystery-os/WORLD_CLASS_FICTION_STANDARD_v0.1.md`;
- `docs/mystery-os/NARRATIVE_CONTRACT_v0.1.md`;
- `docs/mystery-os/FICTION_RESEARCH_AND_REALISM_v0.1.md`;
- `docs/mystery-os/PROFESSIONAL_FICTION_BENCHMARK_v0.1.md`;
- `docs/mystery-os/QUALITY_ROUTING_v0.1.md`;
- `docs/mystery-os/ONTOLOGY_AND_CONTRACTS_v0.1.md`;
- `docs/mystery-os/QUALITY_GATES_v0.1.md`;
- `docs/mystery-os/SERIES_BIBLE_AND_COMMERCIAL_GATE_v0.1.md`;
- `docs/mystery-os/INTEGRATION_WITH_BOOK_OS_v0.1.md`;
- `docs/mystery-os/CODEX_AGENT_EXECUTION_v0.1.md`;
- `docs/mystery-os/AGENTS_API_EDITORIAL_PREP_v0.1.md`;
- `docs/mystery-os/MYSTERY_OS_PROJECT_STATE.md`;
- `docs/mystery-os/pilots/LINE_112_PILOT_v0.1.md`;
- `contracts/mystery-os/mystery_os_authority_pack.schema.json`;
- `contracts/mystery-os/narrative_contract.schema.json`;
- `contracts/mystery-os/fiction_research_ledger.schema.json`;
- `contracts/mystery-os/professional_fiction_benchmark.schema.json`;
- `contracts/mystery-os/editorial_machine_gate.schema.json`;
- `contracts/mystery-os/editorial_prep_agent.schema.json`.

## 5. Quality-routing requirement

MYSTERY OS inherits BOOK OS operation-level routing: no single model owns the whole book.

### Deterministic/local first
Use software rather than model calls for schema, staleness, exact timeline conflicts, authority binding, clue lifecycle completeness, exact repetitions and other provable properties.

### Standard editorial lane
Use the least expensive proven Writer/Editor without material quality loss for bounded scene drafting, routine revisions, structured memory extraction and low-risk local edits.

### Premium/global lane
Use the strongest proven frontier/Astra-class executor or bounded editorial-prep agent where additional reasoning can materially improve high-blast-radius decisions, including:

- series positioning/engine;
- concept selection;
- StoryDefinition;
- NarrativeContract for complex POV/unreliability;
- CaseSolution;
- clue/reveal architecture;
- difficult MysticRuleSet;
- ending architecture;
- long character/relationship arcs;
- anti-cliche adversarial analysis;
- plot-critical realism dependency discovery;
- representative-sample diagnosis;
- midpoint structural diagnosis;
- whole-book developmental diagnosis;
- adversarial reconstruction;
- professional benchmark diagnosis;
- final literary/readiness review.

Routing must be justified by quality/risk/cost evidence and recorded in provenance. Premium is not a default for every creative operation.

## 6. Agents API / Codex requirement

### Engineering mode

Reuse the existing BOOK OS Agents API engineering lane when accepted/available.

Purpose:
- code;
- migrations;
- tests;
- validators;
- MysteryBench implementation;
- UI implementation;
- diagnostics.

Output remains proposal patch/report under the active safety policy.

### Editorial-preparation mode

Future implementation must allow an explicitly launched `EDITORIAL_PREP` job for pre-writing work such as:

- concept candidates;
- series-engine candidates;
- StoryDefinition;
- NarrativeContract candidates/audits;
- CaseSolution;
- suspect/clue/timeline architecture;
- realism dependency discovery/contradiction audit;
- MysticRuleSet;
- anti-cliche/adversarial audits;
- professional benchmark diagnosis;
- writing-readiness preparation.

Requirements:

- explicit Owner/user launch;
- exact input bundle shown/recorded;
- minimum-necessary private content;
- no secrets;
- bounded cost before API call;
- output schema validation;
- all outputs imported as `PROPOSED`;
- material input changes mark proposals stale;
- agent cannot self-grant `WRITING_ALLOWED`;
- agent cannot write GitHub in editorial-prep mode;
- agent cannot become a hidden manuscript writer in a prep task.

## 7. Future implementation slices after Owner acceptance

No runtime implementation is authorized by Task 022 itself. If approved, use bounded follow-on tasks:

1. `MYS-01` — core fiction authority/revisions/staleness + StoryDefinition/CaseSolution;
2. `MYS-02` — deterministic case/timeline/knowledge/clue validators;
3. `MYS-03` — NarrativeContract / ReaderKnowledge / narrative-fairness validators;
4. `MYS-04` — FictionResearchLedger / realism dependencies / research staleness;
5. `MYS-05` — EditorialMachineGateState + SceneContract + `WRITING_ALLOWED` admission;
6. `MYS-06` — representative-sample workflow + StyleProfile/Writer qualification;
7. `MYS-07` — MysteryBench + ColdReader/adversarial harness;
8. `MYS-08` — Professional Fiction Benchmark harness/eval contracts;
9. `MYS-09` — fiction Series Brain / Book Passport / collisions;
10. `MYS-10` — anti-cliche registry/scanners/exception workflow;
11. `MYS-11` — quality-routing/model-operation extension + eval hooks;
12. `MYS-12` — author UX;
13. `MYS-13` — Agents API `EDITORIAL_PREP` runner/import path;
14. `MYS-14` — synthetic full-cycle fixture;
15. `MYS-15` — «Линия 112» real pilot under separate paid/private Owner gate.

Implementation should reuse compatible Task 021/BOOK OS primitives after reconciliation with the then-current accepted `main`; do not fork equivalent platform infrastructure.

## 8. First pilot rule

No Book 1 mass drafting should be treated as a representative MYSTERY OS pilot until at least:

- MYSTERY OS authority is human accepted;
- StoryDefinition is accepted;
- NarrativeContract is accepted;
- CaseSolution is accepted;
- case timeline/clue architecture is coherent;
- plot-critical realism dependencies are resolved/bounded;
- supernatural rules (if used) are bounded;
- anti-cliche gate passes;
- series engine is accepted;
- quality routing for high-impact preparation is resolved;
- representative fiction sample passes material professional-quality checks;
- writing admission path exists for the chosen production mode.

## 9. Acceptance criteria for Task 022

Task 022 design can be accepted when Owner agrees that:

- the system captures the real professional work of mystery construction rather than a generic beat sheet;
- quality target is explicitly professional/publisher-level rather than Samizdat-level completion;
- blocked cliches/templates are explicit enough to prevent default model shortcuts;
- narrative fairness prevents POV-based cheating;
- factual realism is traceable and can block broken procedural/case assumptions;
- fiction ontology is separable from nonfiction ontology but integrable at platform level;
- quality gates can become executable tests/evaluations;
- external benchmark prevents MYSTERY OS from grading only its own homework;
- representative-sample gate prevents scaling mediocre prose;
- explicit machine gate state can fail closed before paid/model execution;
- series/commercial rules protect against repeated formula books;
- routing spends premium intelligence where marginal quality is most valuable rather than on every page;
- «Линия 112» can be piloted without hard-coding its story into generic software;
- both engineering and pre-writing agent use are explicitly designed and safely bounded;
- current BOOK OS authority remains intact until separate integration approval.

## 10. Stop gate

After this documentation/contract pack is created and reviewed in Draft PR:

**STOP.**

Do not implement migrations, UI, runtime agent calls, paid editorial calls, manuscript generation or merge until the Owner gives the next explicit instruction.