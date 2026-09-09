# BOOK OS — OWNER DECISION: OPENAI MODEL + WORK-LEVEL SELECTOR

**Status:** ACCEPTED / OWNER DECISION  
**Version:** 1.0  
**Date:** 2026-09-09  
**Scope:** Desktop book workspace, Model Gateway, provenance

## Decision

BOOK OS must let the human choose the model executor and the work level used for OpenAI book operations without changing the governing BOOK OS system.

The governing distinction is:

> **The model is an executor. BOOK OS remains the authority/governance system.**

Changing the selected OpenAI model or its work level must not alter Book/Series authority, workflow stages, quality gates, editorial rules, anti-junk rules, human approval requirements or Literary Master release criteria.

## Provider and model presentation

The user-facing provider name is **OpenAI**.

The OpenAI model registry includes, among other registered executors, **GPT-6 Astra** (`gpt-6-astra`). Existing operation-level Auto routing and explicit HUMAN manual model selection remain valid.

A human may manually select a model for one operation or use the existing whole-book model pin. A whole-book model pin pins the executor model; it does not silently pin a reasoning/work level forever.

## Mandatory user-facing work levels

For the desktop OpenAI execution lane, BOOK OS exposes exactly these work levels:

| User label | OpenAI API reasoning effort |
| --- | --- |
| Medium | `medium` |
| High | `high` |
| Extra High | `xhigh` |

`low` and `max` remain provider/API capabilities where already supported internally, but they are **not** part of this user-facing BOOK OS work-level selector. Adding or removing a user-facing level requires a new traceable owner decision.

## Per-operation semantics

The work level is an explicit decision for the **next OpenAI operation**, not a permanent property of the book.

Required desktop behavior:

1. before an OpenAI execution, the human selects Medium, High or Extra High;
2. BOOK OS sends the mapped `reasoning.effort` in the exact model request;
3. the selected/actual effort is retained in run usage/provenance where the existing execution lane provides it;
4. after the execution attempt, the pending work-level selection is cleared;
5. a later material OpenAI operation therefore requires an explicit level again;
6. if no level is selected, desktop must fail closed before backend/provider execution;
7. BOOK OS must never silently downgrade or substitute the selected level.

This per-operation rule applies even when a model is manually pinned for the whole book.

## Auto routing

Auto routing remains an executor-selection mechanism at the editorial-operation level. It does not remove the explicit work-level decision for a desktop OpenAI call.

As of 2026-09-09, the registered current OpenAI production model family used by BOOK OS supports `medium`, `high` and `xhigh`, so the three-level product contract is compatible with both GPT-6 Astra and the registered GPT-5.6 Sol/Terra/Luna lanes.

## Official OpenAI facts verified 2026-09-09

Official model documentation confirms:

- GPT-6 Astra API model id: `gpt-6-astra`;
- Responses API support;
- Astra reasoning efforts include `low | medium | high | xhigh | max`;
- GPT-5.6 Sol/Terra/Luna expose `medium | high | xhigh` among their supported reasoning efforts.

Sources:

- `https://developers.openai.com/api/docs/models/gpt-6-astra`
- `https://developers.openai.com/api/docs/models`
- `https://developers.openai.com/api/docs/models/gpt-5.6-sol`
- `https://developers.openai.com/api/docs/models/gpt-5.6-terra`

Provider facts are dated evidence, not BOOK OS authority. If provider capabilities change, BOOK OS must fail closed or update this contract through a traceable decision; it must not silently reinterpret the labels.

## Governance invariants

Model/work-level selection may affect execution quality, latency and cost. It may not:

- approve or lock authority;
- skip a stage or quality gate;
- weaken Chapter/Series admission;
- change Style/Author/Series authority;
- auto-accept manuscript output;
- bypass cost authorization;
- alter human decision rights;
- change Literary Master release criteria.

## Supersession

This decision does **not** supersede the 2026-09-06 operation-level model-routing decision or Task 018 Astra production-lane authority. It narrows and makes explicit the desktop product contract for human OpenAI work-level selection.

Any prior UI assumption that an OpenAI execution may silently rely on a default reasoning effort is superseded for the desktop book workspace. Backend/internal compatibility defaults may remain for non-desktop flows, tests or controlled automation where separately authorized.

## Change log

- **1.0 — 2026-09-09:** Owner required OpenAI model selection with mandatory per-operation Medium / High / Extra High work levels; mapped Extra High to API `xhigh`; preserved BOOK OS governance invariants and operation-level routing.
