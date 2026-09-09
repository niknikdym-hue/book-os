# TASK 019 — OPENAI EXECUTOR + WORK-LEVEL UI

**Status:** IN IMPLEMENTATION  
**Milestone:** Desktop execution controls  
**Owner:** BOOK OS Central Brain  
**Date:** 2026-09-09

## Goal

Expose the accepted OpenAI executor/work-level product contract in the real book workspace without changing BOOK OS authority, stages or quality gates.

## Owner contract

User-facing OpenAI execution must support:

- model executor selection through the existing routing UI, including GPT-6 Astra;
- mandatory per-operation work-level selection:
  - Medium → `medium`;
  - High → `high`;
  - Extra High → `xhigh`;
- fail-closed behavior before provider execution when a desktop OpenAI operation has no selected level;
- one-operation semantics: clear the pending work level after an execution attempt;
- exact effort transport into the existing `reasoning_effort` / Responses API path;
- existing provenance of the selected/actual effort;
- no silent downgrade.

## In scope

1. Present provider `openai` as **OpenAI**.
2. Advertise the three accepted user-facing work levels from the provider registry.
3. Add a visible work-level selector inside the open-book workspace.
4. Centralize desktop enforcement so Planner and Writer cannot bypass the selector through separate panels.
5. Preserve the existing OpenAI adapter transport: `reasoning: { effort: ... }`.
6. Add deterministic no-provider tests for registry and desktop request injection/reset.
7. Record the owner decision in `docs/decisions/`.

## Out of scope

- no paid/model call;
- no secret changes;
- no schema migration;
- no change to model cost caps;
- no change to authority or approval gates;
- no change to Auto routing choices;
- no removal of backend/internal `low`/`max` compatibility;
- no Yandex work-level product contract in this task.

## Acceptance

1. Open book workspace visibly offers Medium / High / Extra High.
2. OpenAI provider registry returns `work_levels=[medium, high, xhigh]` and user-facing label `OpenAI`.
3. GPT-6 Astra remains selectable through the existing registered model lane.
4. Desktop OpenAI execution with no pending work level is blocked before Tauri/backend invocation.
5. Extra High is sent as `reasoning_effort=xhigh`.
6. The pending level is cleared after one OpenAI execution attempt.
7. Non-OpenAI provider calls are not subjected to the OpenAI selector.
8. Existing backend request path continues to emit the chosen effort into the OpenAI Responses request and provenance.
9. Frontend tests/typecheck/lint/build green; backend pytest/ruff/mypy green; canonical CI green.
10. Provider/model/paid calls in implementation/tests/CI = 0.

## Merge gate

Do not self-accept or merge until exact-head canonical CI is green and Central Brain review finds no governance regression.
