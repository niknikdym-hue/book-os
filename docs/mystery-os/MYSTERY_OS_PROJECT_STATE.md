# MYSTERY OS — PROJECT STATE

**Status:** FOUNDATION DESIGN COMPLETE FOR DRAFT REVIEW  
**Version:** 0.1.0  
**Date:** 2026-09-17  
**Repository:** `niknikdym-hue/book-os`  
**Branch:** `brain/task-022-mystery-os-foundation-20260917`  
**Base SHA:** `19ab44ba30036936f843e9b13f2a0f7c8f7b1204`

## Current phase

MYSTERY OS exists as a proposed reusable mystery/crime-fiction editorial module designed for later integration into BOOK OS.

No runtime implementation is authorized yet.

The design pack now covers:

- mystery/fair-play genre canon;
- supernatural causal discipline;
- anti-cliche / anti-template policy;
- professional publisher-level fiction quality target;
- selective premium-intelligence routing;
- fiction ontology and authority contracts;
- MysteryBench and ColdReader/adversarial quality gates;
- series/commercial governance and anti-duplication;
- future BOOK OS integration boundary;
- Codex/Agents API engineering mode;
- Codex/Agents API `EDITORIAL_PREP` mode for bounded pre-writing preparation;
- machine-readable authority and agent-request schemas;
- first pilot profile for `Линия 112`.

## Owner decisions captured during design

- Project name: `MYSTERY OS`.
- First intended pilot series: `Линия 112`.
- Do not build the series around stale archival/gothic defaults.
- Cheap/overused cliches and templates must be explicitly detected and blocked/flagged.
- Build the system once and apply it repeatedly to books/series.
- Design for eventual inclusion in the wider BOOK OS publishing system.
- Existing BOOK OS Agents API/Codex capability should be reusable when useful.
- Agent use should include optional pre-writing preparation, not only software implementation.
- Premium/global reasoning should be used selectively on high-impact decisions; it is too expensive and unnecessary to use the strongest lane for every page.
- Target quality is professionally published commercial fiction, not merely acceptable Samizdat/self-publishing completion.

## Current quality-routing hypothesis

`deterministic/local checks -> standard bounded Writer/Editor -> premium frontier/Astra-class global reasoning where materially justified -> human approval`

Agents API/Codex may optionally provide bounded multi-step `EDITORIAL_PREP` for concept, CaseSolution, clue/timeline/mystic architecture and adversarial audits.

No model or provider is permanent architectural authority.

## Current pilot state — «Линия 112»

Accepted:
- title/brand `Линия 112`;
- contemporary mystical mystery/detective/thriller direction;
- commercial priority;
- professional quality target;
- MYSTERY OS process before manuscript writing.

Not accepted yet:
- protagonists;
- literal meaning of `112` in the series engine;
- first-book concept;
- culprit/motive/mechanism;
- recurring supernatural device;
- romance line;
- exact subgenre profile;
- number of planned volumes.

## Stop gate

Task 022 is documentation/contracts only.

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
2. accept the foundation and authorize bounded implementation slices (`MYS-01...`);
3. authorize only a no-code `Линия 112` concept/CaseSolution pilot using the approved preparation process;
4. hold the module without implementation.

## Recovery order

To recover MYSTERY OS without chat history, read:

1. `README.md`;
2. `MYSTERY_OS_PROJECT_STATE.md`;
3. `WORLD_CLASS_FICTION_STANDARD_v0.1.md`;
4. `MYSTERY_OS_SPEC_v0.1.md`;
5. `GENRE_CANON_v0.1.md`;
6. `ANTI_CLICHE_AND_TEMPLATE_POLICY_v0.1.md`;
7. `QUALITY_ROUTING_v0.1.md`;
8. `ONTOLOGY_AND_CONTRACTS_v0.1.md`;
9. `QUALITY_GATES_v0.1.md`;
10. `SERIES_BIBLE_AND_COMMERCIAL_GATE_v0.1.md`;
11. `AGENTS_API_EDITORIAL_PREP_v0.1.md`;
12. `CODEX_AGENT_EXECUTION_v0.1.md`;
13. `INTEGRATION_WITH_BOOK_OS_v0.1.md`;
14. `pilots/LINE_112_PILOT_v0.1.md`;
15. `../tasks/TASK_022_MYSTERY_OS_FOUNDATION.md`.

Current BOOK OS main remains the authority for the existing nonfiction product until a future integration decision is explicitly accepted.