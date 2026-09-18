# MYS-02 — DETERMINISTIC CASE INTEGRITY VALIDATORS

**Status:** IMPLEMENTATION / STACKED DRAFT  
**Date:** 2026-09-18  
**Repository:** `niknikdym-hue/book-os`  
**Base:** `codex/mys-01-fiction-authority-20260918` @ `2360ad5cb1f1c8dc4f185027f845d91c7df2dbf5`  
**Branch:** `codex/mys-02-case-integrity-20260918`

## Purpose

Implement the deterministic validators that prove structural facts about a mystery case before any model is asked to judge literary quality.

MYS-02 answers only questions software can answer from explicit structured authority. It does not guess missing travel times, forensic facts, motives, reader psychology or supernatural rules.

## IN

- normalized case-event time model using integer seconds on an internal case clock;
- separate reader-order fields for clue exposure/payoff so nonlinear narrative is not confused with case chronology;
- duplicate event/clue identifier detection;
- invalid event interval detection;
- actor double-location overlap detection;
- explicit minimum travel-time feasibility checks;
- fail-closed missing travel-rule findings when a move cannot otherwise be proven feasible;
- character knowledge acquisition/use ordering;
- clue origin/exposure/payoff reference validation;
- clue reader-order lifecycle validation;
- accepted temporal/supernatural-rule references for intentional pre-origin exposure;
- fair-play check for decisive clue exposure;
- decisive-clue payoff requirement;
- clue dependency existence and cycle checks;
- deterministic findings with stable codes, severity and object references;
- unit tests.

## OUT

- no database/Alembic migration;
- no API/Desktop changes;
- no LLM/model/Agents API calls;
- no real-world travel or forensic research inside the validator;
- no literary quality score;
- no probability-based suspicion model;
- no private `Линия 112` story data;
- no merge authorization.

## Design invariants

1. **No guessed physics.** Travel feasibility consumes explicit `TravelRule` authority. Missing rule is a finding, not an invitation to invent a duration.
2. **Case clock is machine time.** Events use `start_second/end_second`; prose labels such as “late evening” are separate presentation data.
3. **Case time != reader order.** Physical causality uses case seconds. Reader-facing clue exposure/payoff uses explicit `exposure_order/payoff_order`. Flashbacks, prologues and nonlinear narration therefore do not create false timeline findings.
4. **Unknown is not valid.** If movement between different locations requires a duration and no accepted rule exists, feasibility is unresolved and blocks deterministic PASS.
5. **Knowledge is causal.** A character may use a fact only if it is initial knowledge or was acquired at/before the use event.
6. **Clues have lifecycle.** A material clue has a cause/origin, reader exposure where required, explicit reader order, dependencies and payoff/recontextualization.
7. **Temporal exceptions are authority.** A clue may be exposed before its objective origin only through an explicitly accepted temporal/mystic rule reference; arbitrary strings cannot bypass causality.
8. **Fair play is profile-aware.** In `REQUIRED` mode, a decisive clue without reader exposure is BLOCKING; in `EXPECTED` mode it is MAJOR; `RELAXED` does not make broken references/order valid.
9. **No opaque score.** Output is a list of exact findings; any BLOCKING finding prevents case-integrity PASS.
10. **Real-world facts remain research authority.** MYS-02 consumes explicit durations/rules but does not replace Fiction Research & Realism.

## Finding code families

### Timeline
- `CASE.EVENT.EMPTY_ID`
- `CASE.EVENT.DUPLICATE_ID`
- `CASE.EVENT.INVALID_INTERVAL`
- `CASE.ACTOR.DOUBLE_LOCATION`
- `CASE.TRAVEL.RULE_INVALID`
- `CASE.TRAVEL.RULE_CONFLICT`
- `CASE.TRAVEL.RULE_MISSING`
- `CASE.TRAVEL.IMPOSSIBLE`

### Knowledge
- `CASE.KNOWLEDGE.EVENT_MISSING`
- `CASE.KNOWLEDGE.TIME_OUTSIDE_EVENT`
- `CASE.KNOWLEDGE.USED_BEFORE_ACQUIRED`

### Clues
- `CASE.CLUE.EMPTY_ID`
- `CASE.CLUE.DUPLICATE_ID`
- `CASE.CLUE.ORIGIN_MISSING`
- `CASE.CLUE.EXPOSURE_MISSING_EVENT`
- `CASE.CLUE.PAYOFF_MISSING_EVENT`
- `CASE.CLUE.EXPOSURE_EVENT_REQUIRED`
- `CASE.CLUE.EXPOSURE_ORDER_MISSING`
- `CASE.CLUE.PAYOFF_EVENT_REQUIRED`
- `CASE.CLUE.PAYOFF_ORDER_MISSING`
- `CASE.CLUE.EXPOSED_BEFORE_ORIGIN`
- `CASE.CLUE.PAYOFF_BEFORE_EXPOSURE`
- `CASE.CLUE.TEMPORAL_RULE_UNKNOWN`
- `CASE.CLUE.DECISIVE_NOT_EXPOSED`
- `CASE.CLUE.DECISIVE_NO_PAYOFF`
- `CASE.CLUE.DEPENDENCY_MISSING`
- `CASE.CLUE.DEPENDENCY_CYCLE`

## Acceptance evidence

Before MYS-02 is technically GREEN:

- targeted validator tests pass;
- existing local-core suite remains green;
- `ruff format --diff .` passes;
- `ruff check .` passes;
- strict `mypy src` passes;
- zero provider/model calls;
- Central Brain diff review.

MYS-02 technical GREEN does not approve Task 022, MYS-01, or any manuscript.
