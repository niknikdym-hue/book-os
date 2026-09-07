# BOOK OS — OWNER DECISION: OPERATION-LEVEL MODEL ROUTING

**Status:** ACCEPTED / OWNER DECISION  
**Version:** 1.0  
**Date:** 2026-09-06  
**Scope:** Model Gateway, BookBench, real-book production workflow

## Decision

BOOK OS does **not** choose one globally “best model” and then assign that model to an entire book by default.

The governing principle is:

> **Не “лучшая модель”, а лучший исполнитель для конкретной редакционной операции.**

In English: **not “the best model”, but the best executor for the specific editorial operation.**

This decision is a normative extension of `BOOK_OS_AUTHORITY.md` §9 `Model principle` and is consistent with the permanent highest-professional-quality rule in §1A.

## Required behavior

`Model Gateway` must route work at the level of a bounded editorial operation or role, not at the level of “one model owns the whole book”.

Examples of distinct operations include, without limitation:

- Book Contract synthesis and critique;
- whole-book architecture;
- chapter-contract planning;
- bounded drafting;
- developmental editing;
- line/literary editing;
- research synthesis;
- claim/evidence review;
- long-context whole-book diagnosis;
- repetition/contradiction analysis;
- author-voice work;
- pairwise judging and BookBench evaluation;
- final high-level review.

The best executor may differ between these operations.

## Routing criteria

Model/provider assignment must be justified by the needs of the specific operation and may consider:

1. measured output quality on BOOK OS evals and real-book evidence;
2. task-specific reasoning/writing/editing strength;
3. context requirements and long-context reliability;
4. factual/evidence risk;
5. independence requirements for writer/judge/editor roles;
6. privacy, safety and contractual constraints;
7. latency and availability;
8. cost and marginal quality gained per unit of cost.

Cost is a routing factor, but it may not silently lower the professional-quality target. A more expensive model is justified where the expected quality/risk improvement is material. A cheaper model should be preferred where bounded evaluation shows no material quality loss for the operation.

## No model monopoly

No model, including a current flagship model, receives permanent architectural priority or automatic ownership of all stages of a book.

A model may be preferred for one operation and rejected for another. New models must be eligible for bounded evaluation without requiring a rewrite of BOOK OS architecture.

The current OpenAI-first MVP decision remains in force as a provider/program decision; it does not imply single-model routing inside the OpenAI lane.

## Comparative and blind evaluation

Where the quality difference is material or uncertain, BOOK OS should support controlled comparative evaluation, including blind A/B or pairwise tests where appropriate.

A valid comparison should, where practical:

- use the same underlying authority/context and equivalent task constraints;
- hide model identity from the human evaluator until the preference decision is recorded;
- preserve exact model, prompt, input, output, cost and provenance after reveal;
- avoid allowing one candidate to see or imitate another candidate’s result unless the task explicitly requires comparative editing;
- use human editorial judgment together with BookBench evidence rather than brand reputation.

Blind comparison is an evaluation tool, not a requirement to duplicate every production step across multiple models.

## Production consequence

BOOK OS should spend expensive-model budget selectively on operations where additional capability is likely to improve the book materially, while using other proven models for operations where they are equally good or more efficient.

Therefore a production book may legitimately use several models across its lifecycle, with every material model assignment recorded in provenance.

## Human authority

Model routing never replaces human authority. AI models may propose, draft, diagnose, edit and evaluate, but material authority gates and Literary Master release remain human decisions under the Authority Protocol.

## Supersession

This decision does **not** supersede the architecture-level model/provider-agnostic rule or the 2026-08-29 OpenAI-first MVP decision. It makes the routing granularity explicit: **operation-level, evidence-driven, quality-first and cost-aware.**

Any older implementation assumption that one preferred model should automatically handle the entire book is superseded by this decision.

## Change log

- **1.0 — 2026-09-06:** Owner accepted operation-level model routing: “не ‘лучшая модель’, а лучший исполнитель для конкретной редакционной операции”; added blind comparative evaluation and no-model-monopoly consequences.
