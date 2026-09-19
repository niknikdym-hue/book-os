# MYS-11 — PRODUCTION ROUTING / EDITORIAL_PREP / FICTION GATEWAY / PRE-WRITING DRY RUN

**Status:** IMPLEMENTATION / STACKED DRAFT  
**Date:** 2026-09-19  
**Repository:** `niknikdym-hue/book-os`  
**Base:** MYS-10 exact GREEN head `ef52aab55e35d3ecb79be38bdb2a25eaaa19f024`  
**Branch:** `codex/mys-11-production-routing-dry-run-20260919`

## Purpose

Close the final gap between a technically valid editorial machine and actual controlled fiction writing.

MYS-11 answers four questions:

1. which operation should remain local;
2. which operation should use the standard Writer;
3. which high-blast-radius operation may justify Astra / EDITORIAL_PREP agent;
4. whether an exact WritingAdmissionToken can actually reach the existing BOOK OS ModelGateway without bypassing authority, budget or provider controls.

## Reuse boundary

MYS-11 reuses:

- shared BOOK OS `RoutingChoice`;
- shared provider adapters;
- shared ModelGateway;
- shared prompt registry;
- existing OpenAI/Yandex cost guards;
- MYS-05 WritingAdmissionToken;
- MYS-06 Writer qualification;
- MYS-09 Series Brain;
- MYS-10 Anti-Cliche gate.

It does **not** create a second model gateway or a second provider registry.

## Execution classes

### A_LOCAL

Examples:

- schema validation;
- CaseTimeline deterministic validation;
- exact series collisions.

Rules:

- no provider call;
- no agent;
- no provider spend.

### B_STANDARD

Examples:

- REPRESENTATIVE_SAMPLE_DRAFT;
- SCENE_DRAFT;
- ROUTINE_SCENE_REVISION;
- CONTINUITY_EXTRACTION.

Default OpenAI Auto routes:

- representative sample -> `gpt-5.6-sol`;
- scene draft -> `gpt-5.6-sol`;
- routine scene revision -> `gpt-5.6-sol`;
- continuity extraction -> `gpt-5.6-terra`.

These operations do not depend on Agents API being enabled.

### C_PREMIUM

Examples:

- SERIES_ARCHITECTURE;
- CASE_SOLUTION_ARCHITECTURE;
- CLUE_REVEAL_ARCHITECTURE;
- ANTI_CLICHE_STRESS_TEST;
- SERIES_SEMANTIC_COLLISION;
- WRITING_READINESS_AUDIT;
- WHOLE_BOOK_DEVELOPMENTAL.

Default OpenAI Auto route:

- `gpt-6-astra`.

Premium routing is selective. It is not the default prose Writer.

## Exact Owner and cost authorization

Provider execution requires structured immutable authorization artifacts.

### Owner execution authorization

Binds:

- authorization ref;
- exact operation ID;
- exact operation kind;
- provider-execution permission;
- EDITORIAL_PREP-agent permission;
- private-content permission;
- current state.

A string that looks like an Owner approval is insufficient.

### Cost authorization

Binds:

- authorization ref;
- exact operation ID;
- currency;
- maximum USD amount;
- current state.

The requested operation cap must fit both:

- global route policy cap;
- exact cost authorization cap.

Route fingerprint includes authorization artifact content, not only IDs.

## EDITORIAL_PREP agent

Agents API remains optional.

Normal admitted fiction writing must work with:

- agent lane unavailable;
- agent capability disabled.

EDITORIAL_PREP may be used only when:

- operation minimum class is C_PREMIUM;
- operation is explicitly allowlisted;
- provider execution is explicitly requested;
- agent lane is available;
- agent capability/kill-switch is enabled;
- exact Owner authorization permits agent use;
- exact cost authorization exists;
- private-content permission exists when private content is included;
- exact EditorialPrepBundle passes.

## EditorialPrepBundle

The bundle is fail-closed and binds:

- task ID;
- project/series/book;
- exact current authority refs;
- bounded task;
- output allowlist;
- forbidden actions;
- source packet refs;
- private-content scope;
- reasoning mode;
- output schema ref;
- proposal-only status;
- network mode;
- secret-material flag.

Required forbidden actions include:

- UNLOCK_WRITING;
- APPROVE_STORY_AUTHORITY;
- APPROVE_ANTI_CLICHE_EXCEPTION;
- WRITE_MANUSCRIPT_PROSE;
- REPOSITORY_WRITE;
- MERGE_DEPLOY_RELEASE.

Agent output is proposal-only.

Agent cannot write manuscript prose or repository state.

## Network/source boundary

Modes:

- DISABLED;
- SOURCE_PACKET_ONLY.

SOURCE_PACKET_ONLY requires explicit source packet refs.

No arbitrary web/network scope is granted by the editorial-prep bundle.

Secrets/credentials are forbidden in the bundle.

## Existing shared Auto routing

MYS-11 extends the existing BOOK OS model-routing registry rather than creating fiction-only routing infrastructure.

This preserves the general principle:

> strongest executor per operation, premium only where quality gain materially justifies cost.

## Fiction ModelGateway task types

The existing shared ModelGateway now accepts strict structured task types:

- REPRESENTATIVE_SAMPLE_DRAFT;
- SCENE_DRAFT;
- ROUTINE_SCENE_REVISION;
- CONTINUITY_EXTRACTION.

## Fiction Writer output

Scene tasks return one of:

### DRAFT

Requires:

- non-empty scene prose;
- no architecture blocker fields.

### ARCHITECTURE_BLOCKER

Requires:

- no manuscript prose;
- blocker code;
- blocker detail.

Writer prompt explicitly forbids silently inventing:

- clue;
- culprit fact;
- supernatural rule;
- timeline fact;
- relationship turn;
- research fact;
- authority change.

If authority is insufficient, Writer must stop with ARCHITECTURE_BLOCKER.

## Admission-bound gateway

`execute_fiction_gateway_task()` requires exact:

- book ID;
- scene ID;
- SceneContract revision;
- production mode;
- authority revision set;
- ProductionRouteResult;
- Owner authorization ref;
- cost authorization ref;
- unexpired WritingAdmissionToken.

A mismatch blocks before ModelGateway/provider execution.

REPRESENTATIVE_SAMPLE_DRAFT requires REPRESENТATIVE_SAMPLE admission.

SCENE_DRAFT requires MASS_DRAFT admission.

Continuity extraction and routine revision still require an admitted exact scene.

## Provider adapters

Both shared OpenAI and Yandex structured-output adapters know the fiction schemas.

No hidden prose-only unstructured provider path is added.

## Synthetic pre-writing dry run

The final MYS-11 acceptance fixture must prove:

1. accepted story/narrative/case authority exists;
2. SceneContract reaches REVIEWED;
3. case/narrative/research gates are clear;
4. Series Brain is qualified;
5. Anti-Cliche is qualified;
6. standard Writer route is qualified;
7. REPRESENTATIVE_SAMPLE obtains WritingAdmissionToken;
8. token reaches fake shared ModelGateway and returns schema-valid fiction DRAFT;
9. MASS_DRAFT remains blocked before MYS-06 sample + Writer qualification;
10. after exact MYS-06 qualification, MASS_DRAFT admits;
11. admitted MASS_DRAFT reaches fake shared ModelGateway;
12. Agents API remains disabled throughout normal writing path.

No real provider call is made in the dry run.

## Machine contracts

MYS-11 adds/hardens:

- `contracts/mystery-os/production_route_request.schema.json`;
- `contracts/mystery-os/editorial_prep_agent.schema.json`;
- `contracts/mystery-os/fiction_gateway_task.schema.json`;
- `contracts/mystery-os/fiction_scene_output.schema.json`;
- `contracts/mystery-os/fiction_continuity_output.schema.json`.

## Deliberately OUT

- no real provider call;
- no real EDITORIAL_PREP dispatch;
- no actual `Линия 112` manuscript prose;
- no merge authorization;
- no release.

## Acceptance

MYS-11 is technically GREEN only when:

- Class A cannot call provider/agent;
- standard Writer path works with Agents API disabled;
- high-blast-radius operations cannot be routed below premium class;
- exact Owner/cost authorization artifacts are enforced;
- route hash changes with authorization changes;
- agent cannot be enabled for a normal scene even by permissive policy mistake;
- agent bundle cannot contain secrets;
- agent cannot write manuscript/repository;
- agent forbidden-action set is complete;
- source-packet network mode is bounded;
- fiction task/output schemas work through shared ModelGateway/provider adapters;
- expired/mismatched admission blocks before provider;
- malformed fiction structured output fails;
- ARCHITECTURE_BLOCKER cannot contain hidden prose;
- synthetic representative-sample and MASS_DRAFT dry runs reach fake ModelGateway only at the correct gates;
- all inherited MYS-01..10 tests remain GREEN;
- Ruff, strict mypy, full pytest, Desktop/Tauri/native/secret scan pass;
- real provider/model/paid calls = 0.

Only after this acceptance and the subsequent Fiction UI integration slice may the Owner be told that the system is ready to launch the real manuscript workflow.
