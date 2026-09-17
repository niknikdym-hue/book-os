# MYSTERY OS — PROJECT STATE

**Status:** EDITORIAL MACHINE FOUNDATION COMPLETE FOR DRAFT REVIEW  
**Version:** 0.2.0  
**Date:** 2026-09-18  
**Repository:** `niknikdym-hue/book-os`  
**Branch:** `brain/task-022-mystery-os-foundation-20260917`  
**Base SHA:** `19ab44ba30036936f843e9b13f2a0f7c8f7b1204`

## Current phase

MYSTERY OS exists as a proposed reusable mystery/crime-fiction editorial machine designed for later integration into BOOK OS.

No runtime implementation is authorized yet.

The design pack now covers:

- canonical end-to-end Editorial Machine gate map;
- explicit machine-readable gate state / scoped `WRITING_ALLOWED` contract;
- mystery/fair-play genre canon;
- narrative/POV/reader-knowledge fairness contract;
- fiction research / real-world realism / fictionalization discipline;
- supernatural causal discipline;
- anti-cliche / anti-template policy;
- professional publisher-level fiction quality target;
- external Professional Fiction Benchmark protocol;
- representative-fiction-sample gate before mass drafting;
- selective premium-intelligence routing;
- fiction ontology and authority contracts;
- MysteryBench and ColdReader/adversarial quality gates;
- series/commercial governance and anti-duplication;
- future BOOK OS integration boundary;
- Codex/Agents API engineering mode;
- Codex/Agents API `EDITORIAL_PREP` mode for bounded pre-writing preparation;
- machine-readable authority, narrative, research, benchmark, gate-state and agent-request schemas;
- first pilot profile for `Линия 112`.

## Owner decisions captured during design

- Project name: `MYSTERY OS`.
- First intended pilot series: `Линия 112`.
- Build an editorial machine first; do not improvise each book from chat/prompt instructions.
- Do not build the series around stale archival/gothic defaults.
- Cheap/overused cliches and templates must be explicitly detected and blocked/flagged.
- Build the system once and apply it repeatedly to books/series.
- Design for eventual inclusion in the wider BOOK OS publishing system.
- Existing BOOK OS Agents API/Codex capability should be reusable when useful.
- Agent use should include optional pre-writing preparation, not only software implementation.
- Premium/global reasoning should be used selectively on high-impact decisions; it is too expensive and unnecessary to use the strongest lane for every page.
- Target quality is professionally published commercial fiction, not merely acceptable Samizdat/self-publishing completion.
- Internal quality checks alone are insufficient; professional-fiction benchmarking is required.
- Do not mass-draft until a representative prose sample proves the selected narrative/voice/Writer path is strong enough.

## Editorial Machine route

`IDEA -> MARKET -> SERIES POSITION -> STORY DEFINITION -> NARRATIVE CONTRACT -> CASE SOLUTION -> REALISM PLAN -> MYSTIC RULES -> CHARACTERS -> SUSPECT/CLUE/TIMELINE -> SCENE ARCHITECTURE -> REPRESENTATIVE SAMPLE -> WRITING -> MIDBOOK -> DEVELOPMENTAL REBUILD -> WHOLE-BOOK AUDITS -> PROFESSIONAL BENCHMARK -> LITERARY MASTER -> DERIVATIVES`

Advancement is based on fresh authority + gate PASS, not on model completion.

Future runtime is explicitly expected to persist gate state as `NOT_STARTED | DRAFT | BLOCKED | PASS | STALE | HUMAN_REVIEW_REQUIRED` and keep `WRITING_ALLOWED=false` outside an exact admitted scope.

## Current quality-routing hypothesis

`deterministic/local checks -> standard bounded Writer/Editor -> premium frontier/Astra-class global reasoning where materially justified -> independent evaluation -> human approval`

Agents API/Codex may optionally provide bounded multi-step `EDITORIAL_PREP` for concept, narrative architecture, CaseSolution, clue/timeline/mystic architecture, realism dependencies, benchmark diagnosis and adversarial audits.

No model or provider is permanent architectural authority.

## Current pilot state — «Линия 112»

Accepted:
- title/brand `Линия 112`;
- contemporary mystical mystery/detective/thriller direction;
- commercial priority;
- professional quality target;
- MYSTERY OS editorial-machine process before manuscript writing.

Not accepted yet:
- protagonists;
- literal meaning of `112` in the series engine;
- first-book concept;
- NarrativeContract for Book 1;
- culprit/motive/mechanism;
- recurring supernatural device;
- romance line;
- exact subgenre profile;
- number of planned volumes.

## Design completeness result

The foundation now has explicit protection against five common false-success modes:

1. **technically coherent but narratively dishonest mystery** — controlled by NarrativeContract/reader-knowledge gates;
2. **plausible-sounding but factually impossible contemporary case** — controlled by FictionResearchLedger/realism gates;
3. **internally GREEN but mediocre/self-publishing-level prose** — controlled by Representative Sample + Professional Fiction Benchmark;
4. **high-quality architecture diluted by unnecessary premium spend** — controlled by operation-level Quality Routing;
5. **model completion mistaken for editorial readiness** — controlled by machine-readable fail-closed gate state and scoped `WRITING_ALLOWED`.

## Stop gate

Task 022 remains documentation/contracts only.

Until a new explicit Owner instruction:

- do not add database migrations;
- do not modify Desktop UI;
- do not implement runtime `EDITORIAL_PREP` calls;
- do not perform paid model/agent calls;
- do not generate the actual `Линия 112` manuscript;
- do not install/replace/deploy the app;
- do not merge Task 022.

## Next decision after Draft review

Owner may choose one of:

1. revise/strengthen MYSTERY OS authority pack;
2. accept the foundation and authorize bounded implementation slices (`MYS-01...MYS-15`);
3. authorize only a no-runtime/private concept-preparation pilot after defining the safe execution path;
4. hold the module without implementation.

## Recovery order

To recover MYSTERY OS without chat history, read:

1. `README.md`;
2. `MYSTERY_OS_PROJECT_STATE.md`;
3. `EDITORIAL_MACHINE_GATE_MAP_v0.1.md`;
4. `WORLD_CLASS_FICTION_STANDARD_v0.1.md`;
5. `MYSTERY_OS_SPEC_v0.1.md`;
6. `GENRE_CANON_v0.1.md`;
7. `NARRATIVE_CONTRACT_v0.1.md`;
8. `FICTION_RESEARCH_AND_REALISM_v0.1.md`;
9. `ANTI_CLICHE_AND_TEMPLATE_POLICY_v0.1.md`;
10. `PROFESSIONAL_FICTION_BENCHMARK_v0.1.md`;
11. `QUALITY_ROUTING_v0.1.md`;
12. `ONTOLOGY_AND_CONTRACTS_v0.1.md`;
13. `QUALITY_GATES_v0.1.md`;
14. `SERIES_BIBLE_AND_COMMERCIAL_GATE_v0.1.md`;
15. `AGENTS_API_EDITORIAL_PREP_v0.1.md`;
16. `CODEX_AGENT_EXECUTION_v0.1.md`;
17. `INTEGRATION_WITH_BOOK_OS_v0.1.md`;
18. `pilots/LINE_112_PILOT_v0.1.md`;
19. `../tasks/TASK_022_MYSTERY_OS_FOUNDATION.md`.

Current BOOK OS main remains the authority for the existing nonfiction product until a future integration decision is explicitly accepted.