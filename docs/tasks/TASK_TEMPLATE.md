# CODEX TASK XXX — <SHORT NAME>

**Status:** DRAFT  
**Milestone:** Mx — <milestone name>  
**Owner:** BOOK OS Central Brain  
**Execution role:** Codex

## WHY NOW

State the concrete missing capability/blocker and why this is the next dependency on the accepted critical path.

## PRODUCT / SYSTEM VALUE

State what usable capability, enforceable invariant, or later milestone this task unlocks.

## DEPENDENCIES / BASELINE

- Canonical repository: `https://github.com/niknikdym-hue/book-os`
- Exact expected `origin/main` HEAD: `<sha>`
- Required accepted prior task/milestone: `<id/status>`
- Authority/specs to read: `<files>`
- Required external dependencies/credentials: `<none or explicit list>`

If baseline or prerequisites differ, return `BASELINE_DRIFT` / `BLOCKED` before implementation.

## EFFICIENCY RATIONALE

Explain why this is the smallest professional implementation that satisfies current requirements. Note which larger/more complex alternatives are deliberately deferred and why.

## GOAL

One concise implementation outcome.

## IN SCOPE

- ...

## OUT OF SCOPE

- ...

## REQUIRED BEHAVIOR / INVARIANTS

- ...

## APPLICABLE HARDENING

List the exact requirements from `SECURITY_AVAILABILITY_v0.1.md` and `PRE_IMPLEMENTATION_HARDENING_v0.1.md` that become mandatory in this task.

## ACCEPTANCE / EVIDENCE

Before implementation begins, define objective proof:

1. ...
2. ...

Include tests/build/evals/security/cost/latency evidence as appropriate.

## REGRESSION REQUIREMENTS

- Previously accepted capabilities that must remain green.
- Tests/checks that prove no regression.

## RISKS / STOP CONDITIONS

Return to Central Brain instead of inventing a solution if:

- ...

Use `CENTRAL_BRAIN_DECISION_NEEDED` or the documented Owner stop condition where applicable.

## UNLOCKS NEXT

Name the exact next capability/milestone that becomes safe to start after Central Brain accepts this task.

## BRANCH / PR

Default:

`main baseline → codex/<task-name> → PR → Central Brain acceptance → merge`

No force push. Codex does not merge or self-accept unless the task explicitly says otherwise.

## PROJECT STATE

Codex may update `PROJECT_STATE.md` to factual state:

`IMPLEMENTED_AWAITING_CENTRAL_BRAIN_ACCEPTANCE`

Central Brain updates the accepted checkpoint after review/merge.

## DELIVERABLE / REPORT FORMAT

Return:

- baseline HEAD;
- branch/final HEAD;
- PR;
- commits/files changed;
- exact validation commands/results;
- acceptance criteria PASS/PARTIAL/FAIL;
- applicable hardening evidence;
- external/paid calls;
- architecture deviations;
- known limitations/blockers;
- confirmation of clean git status;
- next safe action.

Do not begin the next task automatically.
