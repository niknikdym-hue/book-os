# MYSTERY OS — CODEX / AGENTS API EXECUTION CONTRACT v0.1

**Status:** INCUBATION DRAFT  
**Date:** 2026-09-17

## 1. Purpose

MYSTERY OS must be implementable through the existing BOOK OS engineering-agent lane when that lane is available and authorized.

This document defines how a Codex/Agents API engineering executor may work on MYSTERY OS without gaining authority over editorial canon, literary acceptance, repository merge, production manuscripts or release.

The intended executor is the same isolated engineering lane being developed for BOOK OS under the dedicated Agents API development work. MYSTERY OS does not create a second agent infrastructure unless a future concrete defect proves one is needed.

## 2. Reuse, do not fork

When the BOOK OS Agents API lane is accepted, MYSTERY OS tasks should reuse its:

- dedicated development OpenAI Platform project/key;
- explicit committed Git snapshot input;
- OpenAI-hosted sandbox;
- network-disabled-by-default policy;
- no-Keychain/no-manuscript/no-production-secret boundary;
- patch/report artifact output;
- Central Brain review/application step;
- exact-head CI verification;
- no-agent-merge/no-agent-release rule;
- bounded cost/reasoning policy.

MYSTERY OS must not create an easier bypass around those controls.

## 3. Availability rule

The agent lane is a **capability**, not an implicit authorization.

Before every MYSTERY OS engineering run, the controller must resolve:

1. Is the BOOK OS Agents API lane currently accepted/available?
2. Is the destination branch explicitly allowed?
3. Is the requested task bounded enough for one run?
4. Does the task require manuscript/private unpublished data? If yes, default answer is STOP unless a separately reviewed privacy design authorizes a safe input path.
5. Is a paid run authorized and bounded by Owner cost controls?

If any required condition is false, create a task packet but do not run the agent.

## 4. What the agent MAY do

Subject to task scope, the engineering agent may:

- implement approved MYSTERY OS data models and migrations;
- add deterministic validators and quality gates;
- implement clue/timeline/knowledge-state graph logic;
- implement MysteryBench infrastructure;
- add anti-cliche rule registries and scanners;
- implement Series Bible / Book Passport / difference-map machinery;
- extend Book Memory indexing for fiction entities;
- add API endpoints and Local Core orchestration;
- implement author-facing UI for already approved product behavior;
- add tests, fixtures, migrations and documentation required by the task;
- diagnose failing CI or integration defects;
- produce bounded refactors required by an approved implementation contract;
- prepare patch/report artifacts for Central Brain review.

## 5. What the agent MAY NOT decide

The engineering agent cannot redefine or self-approve:

- genre canon;
- fair-play standard;
- anti-cliche policy;
- what literary quality means;
- series commercial direction;
- StoryDefinition/CaseSolution for an unpublished book;
- culprit, motive, twist or recurring characters as final authority;
- whether a manuscript is publishable;
- human acceptance boundaries;
- whether a blocked cliche should receive an exception;
- Literary Master release;
- cost/risk trade-offs reserved to Owner;
- merge/deploy/install/release decisions.

If implementation reveals an authority gap, the agent reports it as `AUTHORITY_GAP` and stops rather than inventing policy.

## 6. Standard task packet

Every Codex/Agents API implementation request for MYSTERY OS should be stored as a bounded repository task with this minimum header:

```text
TASK_ID:
TITLE:
SOURCE_OF_TRUTH_REPO: niknikdym-hue/book-os
BASE_SHA:
DESTINATION_BRANCH:
AUTHORITY_FILES:
SCOPE_IN:
SCOPE_OUT:
REQUIRED_BEHAVIOR:
FAIL_CLOSED_RULES:
TEST_REQUIREMENTS:
MIGRATION_RULES:
PRIVATE_DATA_ALLOWED: NO (default)
PROVIDER_CALLS_ALLOWED: NO (default)
PAID_CALLS_ALLOWED: NO (default)
MERGE_ALLOWED: NO
INSTALL_DEPLOY_RELEASE_ALLOWED: NO
OWNER_GATES:
ACCEPTANCE_EVIDENCE:
```

The packet must point to exact authority files rather than copying a simplified paraphrase that may drift.

## 7. Recommended task slicing

Do not ask one agent run to “implement MYSTERY OS”.

Suggested future slices after authority approval:

### MYS-01 — schema/core entities
Implement fiction authority entities and revision/staleness semantics only.

### MYS-02 — deterministic case validators
Timeline, knowledge-state, clue lifecycle, rule consistency.

### MYS-03 — writing admission
SceneContract + fail-closed `WRITING_ALLOWED` integration.

### MYS-04 — MysteryBench
Findings/severity/adversarial reconstruction harness and ColdReader protocol plumbing.

### MYS-05 — series fiction brain
Book Passport, consumable assets, difference/collision map.

### MYS-06 — anti-cliche layer
Machine-readable registry, findings, exception workflow, series collision detection.

### MYS-07 — author UX
Genre-specific author flow using approved backend semantics.

### MYS-08 — pilot instrumentation
`Линия 112` dry-run / real-book evidence capture with no hard-coded series logic in generic modules.

Each slice must be independently reviewable and must not silently implement later slices.

## 8. Reasoning/model policy

MYSTERY OS engineering should inherit the active BOOK OS Agents API lane model/reasoning policy rather than hard-code a second policy.

Current design expectation from that lane is:

- default executor: `gpt-5.6-sol`;
- default reasoning selection: Auto through deterministic local policy;
- Owner may explicitly select Medium / High / Extra High;
- no extra model call solely to select reasoning effort;
- Extra High requires a concrete difficult engineering reason rather than precautionary use.

If the governing BOOK OS engineering-lane policy changes later, MYSTERY OS inherits the newer accepted policy.

## 9. Snapshot and authority rule

Agent input must be based on an explicit committed snapshot.

For a MYSTERY OS task, the snapshot should include:

- current accepted/main platform authority needed by task;
- approved MYSTERY OS authority files;
- exact implementation baseline;
- task contract;
- relevant tests/fixtures.

Do not feed chat history as authority.

## 10. Output contract

Expected agent outputs are proposals, for example:

- `report.md`;
- patch/diff artifact;
- tests/logs;
- migration note;
- identified authority gaps;
- proposed commit message;
- risk/rollback note.

An agent session marked complete is not acceptance evidence by itself.

## 11. Central Brain review

Before any patch is applied, Central Brain checks:

- task stayed inside scope;
- no authority was weakened;
- no blocked cliche/fair-play rule was silently removed to make tests pass;
- schema represents fiction semantics rather than stuffing data into nonfiction fields;
- no manuscript/secrets were committed;
- tests measure the promised behavior;
- migration/staleness behavior is correct;
- change remains compatible with current BOOK OS critical path.

## 12. GitHub write boundary

Default MYSTERY OS agent mode remains proposal-only.

If a future accepted BOOK OS agent lane gains bounded write capability, MYSTERY OS may inherit only the same reviewed restrictions. The agent still may not:

- write directly to `main`;
- self-merge;
- mutate another active agent's PR without explicit instruction;
- change repository secrets;
- release/deploy/install;
- change Owner-approved authority files except as a proposal requiring human review.

## 13. Editorial AI vs engineering agent

Keep these lanes distinct.

### Engineering Codex/Agents API lane
Changes software/spec implementation and returns patches.

### Production editorial Model Gateway
Researches, plans, writes, edits and evaluates books under authoring authority/cost gates.

The engineering agent must not become a hidden production writer, and the production Writer must not gain repository engineering authority.

## 14. Pilot use

For `Линия 112`, the agent may later be used to implement generic MYSTERY OS functionality or pilot instrumentation.

It must not hard-code:

- `Линия 112` title;
- its future characters;
- culprit patterns;
- specific clues;
- fixed supernatural gimmicks;
- story-specific logic

into reusable MYSTERY OS modules.

Series-specific data belongs in project/series authority, not application code.

## 15. Kill switch and safety inheritance

MYSTERY OS inherits the engineering lane's kill-switch concept: disabling/revoking the dedicated development lane must stop agent execution without affecting production book-writing credentials.

No MYSTERY OS feature may make the engineering agent a runtime dependency for normal authoring.