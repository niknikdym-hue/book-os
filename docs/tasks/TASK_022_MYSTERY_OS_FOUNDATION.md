# TASK 022 — MYSTERY OS FOUNDATION

**Status:** PROPOSED / OWNER REVIEW REQUIRED  
**Date:** 2026-09-17  
**Repository:** `niknikdym-hue/book-os`  
**Base at branch creation:** `19ab44ba30036936f843e9b13f2a0f7c8f7b1204`  
**Branch:** `brain/task-022-mystery-os-foundation-20260917`

## 1. Owner intent

Create MYSTERY OS as a deeply specified, reusable mystery/crime-fiction production system with enough rigor that it can later be integrated into the wider BOOK OS publishing platform.

First intended pilot: series **«Линия 112»**.

Owner requirements captured in this task:

- build the writing system once and reuse it across books;
- mystery/detective logic must be explicitly modeled and checked;
- supernatural rules must be controlled rather than improvised;
- cheap overused cliches, stock twists, template characters and AI-prose patterns must be identified and blocked/flagged;
- series books must remain materially unique;
- commercial viability must be checked before full manuscript investment;
- target quality is professional international commercial fiction, not merely acceptable self-publishing/Samizdat output;
- expensive frontier intelligence should be used selectively on high-impact/global operations rather than on every page;
- project must be designed for later BOOK OS integration rather than as a separate throwaway tool;
- the existing BOOK OS Agents API/Codex capability must be reusable when needed;
- Agents API/Codex must be usable not only for software implementation but, after a separate safe implementation, for **bounded pre-writing editorial preparation**;
- no current nonfiction authority/runtime may be silently broken or replaced.

## 2. Scope of Task 022

### IN

- MYSTERY OS product/editorial specification;
- genre canon and fair-play rules;
- supernatural-rule discipline;
- anti-cliche / anti-template policy;
- professional fiction quality standard;
- selective premium-intelligence / cost-aware routing policy;
- fiction-specific ontology and contracts;
- MysteryBench quality gates;
- series/commercial governance;
- future BOOK OS integration boundary;
- first pilot profile for «Линия 112»;
- machine-readable authority schema;
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
The system separates objective story truth, character knowledge, investigator hypotheses, reader-visible evidence and narrative order.

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

## 4. Deliverables in this branch

Required project pack:

- `docs/mystery-os/README.md`;
- `docs/mystery-os/MYSTERY_OS_SPEC_v0.1.md`;
- `docs/mystery-os/GENRE_CANON_v0.1.md`;
- `docs/mystery-os/ANTI_CLICHE_AND_TEMPLATE_POLICY_v0.1.md`;
- `docs/mystery-os/WORLD_CLASS_FICTION_STANDARD_v0.1.md`;
- `docs/mystery-os/QUALITY_ROUTING_v0.1.md`;
- `docs/mystery-os/ONTOLOGY_AND_CONTRACTS_v0.1.md`;
- `docs/mystery-os/QUALITY_GATES_v0.1.md`;
- `docs/mystery-os/SERIES_BIBLE_AND_COMMERCIAL_GATE_v0.1.md`;
- `docs/mystery-os/INTEGRATION_WITH_BOOK_OS_v0.1.md`;
- `docs/mystery-os/CODEX_AGENT_EXECUTION_v0.1.md`;
- `docs/mystery-os/AGENTS_API_EDITORIAL_PREP_v0.1.md`;
- `docs/mystery-os/pilots/LINE_112_PILOT_v0.1.md`;
- `contracts/mystery-os/mystery_os_authority_pack.schema.json`;
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
- CaseSolution;
- clue/reveal architecture;
- difficult MysticRuleSet;
- ending architecture;
- long character/relationship arcs;
- anti-cliche adversarial analysis;
- midpoint structural diagnosis;
- whole-book developmental diagnosis;
- adversarial reconstruction;
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
- CaseSolution;
- suspect/clue/timeline architecture;
- MysticRuleSet;
- anti-cliche/adversarial audits;
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

No implementation is authorized by Task 022 itself. If approved, use bounded follow-on tasks:

1. `MYS-01` — core fiction entities/revisions/staleness;
2. `MYS-02` — deterministic case/timeline/knowledge/clue validators;
3. `MYS-03` — SceneContract + writing admission;
4. `MYS-04` — MysteryBench + ColdReader/adversarial harness;
5. `MYS-05` — fiction Series Brain / Book Passport / collisions;
6. `MYS-06` — anti-cliche registry/scanners/exception workflow;
7. `MYS-07` — quality-routing/model-operation extension + eval hooks;
8. `MYS-08` — author UX;
9. `MYS-09` — Agents API `EDITORIAL_PREP` runner/import path;
10. `MYS-10` — synthetic full-cycle fixture;
11. `MYS-11` — «Линия 112» real pilot under separate paid/private Owner gate.

## 8. First pilot rule

No Book 1 prose should be treated as a representative MYSTERY OS pilot until at least:

- MYSTERY OS authority is human accepted;
- StoryDefinition is accepted;
- CaseSolution is accepted;
- case timeline/clue architecture is coherent;
- supernatural rules (if used) are bounded;
- anti-cliche gate passes;
- series engine is accepted;
- quality routing for high-impact preparation is resolved;
- writing admission path exists for the chosen production mode.

## 9. Acceptance criteria for Task 022

Task 022 design can be accepted when Owner agrees that:

- the system captures the real professional work of mystery construction rather than a generic beat sheet;
- quality target is explicitly professional/publisher-level rather than Samizdat-level completion;
- blocked cliches/templates are explicit enough to prevent default model shortcuts;
- fiction ontology is separable from nonfiction ontology but integrable at platform level;
- quality gates can become executable tests/evaluations;
- series/commercial rules protect against repeated formula books;
- the routing design spends premium intelligence where marginal quality is most valuable rather than on every page;
- «Линия 112» can be piloted without hard-coding its story into generic software;
- both engineering and pre-writing agent use are explicitly designed and safely bounded;
- current BOOK OS authority remains intact until separate integration approval.

## 10. Stop gate

After this documentation/contract pack is created and reviewed in Draft PR:

**STOP.**

Do not implement migrations, UI, runtime agent calls, paid editorial calls, manuscript generation or merge until the Owner gives the next explicit instruction.