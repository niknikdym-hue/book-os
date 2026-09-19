# MYSTERY OS — AGENTS API / CODEX EDITORIAL PREPARATION LANE v0.1

**Status:** INCUBATION DRAFT  
**Date:** 2026-09-17

## 1. Purpose

MYSTERY OS should be able to launch a Codex/Agents API agent **before writing starts** when the Owner wants additional analytical power for story preparation.

This is distinct from the engineering-agent lane.

Two agent modes are therefore recognized:

1. `ENGINEERING` — proposes software/code changes for BOOK OS/MYSTERY OS.
2. `EDITORIAL_PREP` — prepares structured fiction authority candidates before Writing.

They may reuse secure runner infrastructure, but they must not share authority or permissions.

## 2. What `EDITORIAL_PREP` is for

The lane may be used to produce or stress-test proposals for:

- market/comparable synthesis from an approved source packet;
- series concept alternatives;
- first-book concept alternatives;
- recurring-character/team alternatives;
- StoryDefinition;
- series engine;
- CaseSolution;
- suspect/secret matrix;
- clue architecture;
- red-herring architecture;
- objective CaseTimeline;
- character knowledge map;
- MysticRuleSet;
- RevealPlan;
- scene architecture;
- anti-cliche audit;
- adversarial case audit;
- difference map vs prior series books;
- writing-readiness report.

It may also diagnose an already prepared authority pack and propose corrections.

## 3. What it is NOT

`EDITORIAL_PREP` is not an autonomous author and not an approval authority.

It may not:

- unlock Writing by itself;
- approve StoryDefinition;
- approve CaseSolution;
- approve recurring characters/series engine;
- approve an AntiClicheException;
- choose publication/release status;
- merge GitHub code;
- modify production application state outside the explicit import workflow;
- silently rewrite previously approved authority.

Every material output is `PROPOSED` until reviewed/accepted by the human Owner.

## 4. Invocation modes

### A. Generate candidates

Example intent:

`Prepare 4 materially different first-book concepts for series Линия 112 under the approved MYSTERY OS canon. Do not write manuscript prose.`

Expected output:
- candidates;
- differentiation matrix;
- anti-cliche risks;
- commercial risks;
- required factual research;
- recommendation evidence **without selecting a final Owner choice**.

### B. Build authority candidate

Example intent:

`For the Owner-selected concept, prepare a proposed CaseSolution + Suspect Matrix + Clue Ledger + CaseTimeline.`

Expected output must match machine-readable contracts where available.

### C. Adversarial review

Example intent:

`Try to break this CaseSolution. Find impossible timing, weak motive, unfair clueing, stronger alternative culprit, unbounded supernatural rules and cliche dependency.`

### D. Prepare writing admission

Example intent:

`Assess whether this project is ready for Scene Architecture/Writing. Return blockers only as structured findings.`

## 5. Data boundary

Editorial preparation may require unpublished/private story information. Therefore it cannot simply reuse the engineering lane's “Git snapshot only” input model.

The controller must build an explicit **Editorial Preparation Bundle** from approved local BOOK OS/MYSTERY OS data.

Allowed content may include, when selected by the Owner/workflow:

- series bible;
- StoryDefinition draft/approved version;
- CaseSolution draft/approved version;
- character cards;
- clue/timeline/mystic-rule objects;
- prior-book summaries/passports/difference maps;
- Style Profile excerpts needed for planning;
- market/source packet;
- bounded manuscript excerpts only when the task genuinely requires them.

Default exclusions:

- API keys/tokens;
- Keychain content;
- unrelated user files;
- Git credentials;
- Apple signing credentials;
- production secrets;
- full Library/BOOK_OS_DATA_DIR dumps;
- manuscripts unrelated to the requested task;
- private data not required by the task.

## 6. Private-content rule

Unpublished story content used for editorial preparation must travel only through the explicit agent input channel and must **not** be committed to the public repository.

Repository contains:
- schemas;
- task contracts;
- test fixtures using synthetic data;
- generic rule packs.

Local project storage contains:
- actual unpublished plots;
- CaseSolutions;
- manuscripts;
- private series bibles;
- real ColdReader outputs where sensitive.

## 7. Source/research model

Default agent sandbox may remain network-disabled.

For market/factual research, preferred architecture is:

`Research Broker / approved retrieval -> Source Packet -> EDITORIAL_PREP agent`

The source packet records:
- URL/source identity;
- retrieval date;
- relevant excerpt/structured facts;
- provenance;
- usage constraints.

The agent may synthesize and compare sources but must not invent external market facts.

A future bounded read-only network mode may be considered separately, but it is not required for v0.1.

## 8. Editorial Preparation Bundle

Minimum envelope:

```json
{
  "task_id": "...",
  "mode": "EDITORIAL_PREP",
  "project_id": "local-project-id",
  "series_id": "optional",
  "book_id": "optional",
  "authority_refs": [],
  "task": "...",
  "allowed_outputs": [],
  "forbidden_actions": [],
  "source_packet_refs": [],
  "private_content_scope": "MINIMUM_NECESSARY",
  "cost_cap": {},
  "reasoning_mode": "auto",
  "owner_authorized": true
}
```

The bundle must record exact authority revisions so outputs can be marked stale if inputs change.

## 9. Output contract

Preferred agent output is structured and importable.

Envelope:

```json
{
  "task_id": "...",
  "input_authority_revisions": [],
  "proposals": [],
  "findings": [],
  "assumptions": [],
  "research_gaps": [],
  "anti_cliche_findings": [],
  "blocking_issues": [],
  "suggested_next_gate": "...",
  "provenance": {}
}
```

Any prose explanation is secondary to structured objects.

## 10. Import semantics

Agent outputs are imported as proposals only.

Examples:

- generated StoryDefinition -> `DRAFT/PROPOSED`, never APPROVED;
- generated CaseSolution -> `DRAFT/PROPOSED`;
- generated clue map -> linked to exact proposed CaseSolution revision;
- agent anti-cliche finding -> finding requiring human/editorial disposition;
- agent readiness result -> diagnostic evidence, not `WRITING_ALLOWED` by itself.

Human acceptance creates the authoritative revision.

## 11. Staleness

If any material input authority changes after a prep run, dependent proposals become `STALE`.

Examples:
- Owner changes protagonist role -> recurring-team proposal may be stale;
- Owner changes culprit -> clue/timeline/reveal proposals become stale;
- MysticRuleSet changes -> supernatural clue proposals become stale;
- Series Bible changes -> concept/difference maps may be stale.

Do not silently reuse old agent output because it “looks close enough”.

## 12. Cost and model selection

The lane inherits accepted BOOK OS agent/model policy where applicable:

- model/provider is execution detail, not authority;
- Auto may choose bounded reasoning effort deterministically;
- Owner override has priority;
- every paid run requires a bounded cost authorization under active policy;
- no separate model call solely to choose reasoning effort;
- Extra High is reserved for genuinely difficult operations such as adversarial solution repair or complex cross-book series collision analysis.

A cheap planning task should not default to maximum reasoning merely because it is creative work.

## 13. Separation from production Writer

`EDITORIAL_PREP` prepares the story system.

`Writer` produces manuscript prose after gates are satisfied.

The same underlying model may technically be eligible for both roles, but roles, prompts, inputs, provenance and authority must remain distinct.

A pre-writing agent must not quietly write chapters inside a preparation task.

## 14. Separation from engineering agent

`ENGINEERING` input/output:
- committed Git snapshot;
- code/spec task;
- patch/report/tests.

`EDITORIAL_PREP` input/output:
- local editorial authority bundle;
- story-planning/review task;
- structured editorial proposals/findings.

Engineering agent cannot read private manuscripts by default. Editorial-prep agent cannot write GitHub/code by default.

## 15. Launch control in future BOOK OS UI

Future author workflow may expose an action such as:

`Усилить подготовку через агента`

Possible bounded actions:
- `Предложить варианты концепции`;
- `Проверить замысел на штампы`;
- `Собрать дело и улики`;
- `Разбить решение как критик`;
- `Проверить готовность к написанию`.

Before launch UI shows:
- task scope;
- exact private inputs that will be sent;
- model/reasoning choice;
- estimated/bounded cost;
- output type;
- statement that results require review.

No hidden agent execution.

## 16. API/runner design target

When implemented, the same local trusted controller may dispatch both agent modes through separate profiles:

```text
run_agent(mode=ENGINEERING, ...)
run_agent(mode=EDITORIAL_PREP, ...)
```

Profiles must enforce different input builders, tool permissions and output validators.

The `mode` must be fail-closed: unknown mode -> reject before API call.

## 17. Minimum acceptance before enabling real use

Before first real `EDITORIAL_PREP` call:

1. Owner approves this authority design;
2. secure input builder is implemented;
3. private content is excluded from logs/repository artifacts;
4. output JSON is schema-validated;
5. proposal-only import semantics are tested;
6. staleness propagation is tested;
7. cost gate is tested before API call;
8. zero-secret boundary is tested;
9. a synthetic mystery fixture proves the complete loop;
10. Owner explicitly authorizes the first paid/private run.

## 18. Kill switch

Disabling the agent capability or revoking its dedicated key must not break normal MYSTERY OS/BOOK OS authoring.

Agents API is an optional accelerator, not a runtime dependency.