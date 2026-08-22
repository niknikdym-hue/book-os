# BOOK OS — TASK EXECUTION PROTOCOL v0.1

**Status:** ACCEPTED EXECUTION CONTROL  
**Version:** 0.1.0  
**Date:** 2026-08-23  
**Authority:** Central Brain under `BOOKOS-DEC-0002` and explicit Owner direction  
**Normative role:** extension of `PROJECT_EXECUTION_PLAN.md` and `IMPLEMENTATION_ROADMAP_v0.1.md`

## 1. Purpose

Every implementation task must move BOOK OS toward the accepted MVP by the shortest safe path. Tasks are not work items for their own sake. A task is valid only when it has a direct line of sight to an accepted milestone, produces a testable capability or removes a concrete blocker, and is small enough to review and accept independently.

Core execution rule:

`accepted authority → justified next task → bounded implementation → objective evidence → Central Brain acceptance → accepted main → next task`

No speculative task may bypass this chain.

## 2. Critical path to BOOK OS v0.1

The implementation critical path is:

`M0 Executable Skeleton`
→ `M1 Authority & Persistence Engine`
→ `M2 Book Creation / Contracts / Architecture`
→ `M3 Model Gateway + Controlled Drafting`
→ `M4 Research Engine + Claim Ledger`
→ `M5 Book Memory`
→ `M6 Editorial Workflows`
→ `M7 BookBench`
→ `M8 Russia / No-VPN Provider Lane`
→ `M9 Literary Master / Export / Audio Handoff`
→ `M10 Real Business Book Pilot`
→ `MVP Acceptance`

Cross-cutting requirements in `PRE_IMPLEMENTATION_HARDENING_v0.1.md` are inserted into the milestone where they become necessary. They do not justify unrelated infrastructure work earlier than needed.

A task that does not advance this path or close a blocker on it requires explicit Central Brain justification before execution.

## 3. Mandatory task qualification gate

Before Codex receives a task, Central Brain must be able to answer all of the following.

### 3.1 WHY NOW

- What concrete limitation or missing capability exists now?
- Why is this the next dependency on the critical path?
- What would be blocked if the task were not done?

### 3.2 PRODUCT / SYSTEM VALUE

The task must unlock one or more concrete outcomes, for example:

- an accepted product capability becomes usable;
- a later milestone becomes technically possible;
- a required safety/quality invariant becomes enforceable;
- a measurable blocker is removed.

“Clean up”, “future-proof”, “make architecture nicer”, or “might be useful later” are not sufficient by themselves.

### 3.3 BASELINE / DEPENDENCIES

The task must identify:

- exact `origin/main` baseline HEAD;
- accepted authority/specs it implements;
- prior milestone/task that must already be accepted;
- external dependencies or credentials genuinely required.

If a prerequisite is not accepted, the task is not `READY`.

### 3.4 EFFICIENCY RATIONALE

The task must state why the proposed implementation is the smallest professional solution that satisfies current requirements.

Central Brain must prefer:

1. proven commodity technology over custom infrastructure when the component is not BOOK OS moat;
2. a local/simple implementation over distributed infrastructure until measurements require scale;
3. a narrow adapter/interface over premature general frameworks;
4. reuse of an already-proven internal pattern when it fits without coupling domain authority;
5. measured extraction of shared infrastructure only after real duplication exists.

No task may introduce infrastructure only because it is fashionable or theoretically scalable.

### 3.5 BOUNDED SCOPE

Every task must define:

- `IN SCOPE`;
- `OUT OF SCOPE`;
- allowed systems/files where useful;
- explicit non-goals;
- stop conditions.

If a task spans more than one independently acceptable milestone capability, it should normally be split.

### 3.6 ACCEPTANCE EVIDENCE

Every task must specify objective evidence before implementation begins:

- tests;
- invariants;
- build/run evidence;
- security checks;
- evals where appropriate;
- cost/latency evidence where relevant;
- exact expected user/system behavior.

Green tests alone do not prove product acceptance if the accepted behavior is wrong or missing.

### 3.7 WHAT IT UNLOCKS NEXT

Every task must name the next capability it enables.

A task is not finished merely because code exists. Its purpose is to leave the repository in a state from which the next accepted critical-path task can start safely.

## 4. Standard task header

Every new Codex task must contain, near the top:

- `MILESTONE`
- `WHY NOW`
- `PRODUCT / SYSTEM VALUE`
- `DEPENDENCIES / BASELINE`
- `EFFICIENCY RATIONALE`
- `GOAL`
- `IN SCOPE`
- `OUT OF SCOPE`
- `ACCEPTANCE / EVIDENCE`
- `RISKS / STOP CONDITIONS`
- `UNLOCKS NEXT`
- `DELIVERABLE / REPORT FORMAT`

Use `docs/tasks/TASK_TEMPLATE.md` as the default task skeleton.

## 5. Task state machine

Implementation tasks use these states:

`DRAFT`
→ `READY`
→ `IN_PROGRESS`
→ `IMPLEMENTED_AWAITING_CENTRAL_BRAIN_ACCEPTANCE`
→ `ACCEPTED`

Alternate terminal/loop states:

- `REWORK_REQUIRED`
- `BLOCKED`
- `SUPERSEDED`

Codex cannot promote its own task to `ACCEPTED`.

`ACCEPTED` requires Central Brain review of the actual diff, tests/evals, scope and architecture fit. Owner involvement is required only when a documented stop condition is triggered.

## 6. One-main-task rule

By default there is one active implementation task on the critical path.

Parallel work is allowed only when Central Brain explicitly confirms that:

- tasks are independent;
- they do not modify overlapping authority/schema surfaces in unsafe ways;
- parallelism reduces elapsed work rather than increasing merge/review risk;
- each branch remains independently reviewable.

Do not create parallel work merely to keep agents busy.

## 7. Main-branch rule

`main` contains accepted project state.

Normal implementation flow:

`main baseline → bounded branch → PR → evidence/review → Central Brain ACCEPT → merge → PROJECT_STATE update`

Direct writes to `main` by Central Brain are reserved for small authority/project-control updates where a PR adds no meaningful review value. Implementation code should normally go through a bounded branch/PR.

Force-push to `main` is prohibited.

## 8. Baseline drift rule

A task is issued against an exact `main` HEAD.

If `origin/main` changes before execution begins, Codex must compare the delta. It may continue only if the new baseline is explicitly reconciled with task scope; otherwise it returns `BASELINE_DRIFT`.

No task silently executes against an unknown baseline.

## 9. Scope-creep rule

While implementing, Codex may discover adjacent improvements. It must not include them automatically.

Classify each discovery as:

- required to satisfy current acceptance → implement within scope and report;
- defect/blocker outside scope → record and return to Central Brain;
- optional improvement → defer;
- architecture/product decision → `CENTRAL_BRAIN_DECISION_NEEDED` or Owner stop condition.

A bounded task must not become a vehicle for opportunistic refactoring.

## 10. Build-vs-buy efficiency rule

Before adding a custom subsystem, ask:

1. Is this BOOK OS-specific editorial IP?
2. Does a maintained commodity component/API solve it adequately?
3. Does using that component preserve local authority, portability and privacy requirements?
4. Is the operational burden lower than custom implementation?
5. Do provider/licensing/region constraints allow it?

Build ourselves when the capability is part of BOOK OS moat or existing technology violates a core invariant. Otherwise prefer mature commodity infrastructure.

## 11. API/model integration efficiency rule

No provider integration exists just to “support another model”.

A model/provider adapter is justified only when it serves at least one of:

- active development/benchmark lane;
- required regional lane;
- measured quality improvement for a role;
- resilience/fallback requirement;
- material cost/latency advantage without quality regression.

Live/paid calls are explicitly gated and budgeted. Unit/PR CI must not require paid model calls.

## 12. Performance and complexity rule

Optimize only against a defined workload or measured bottleneck.

Before replacing a simple implementation with a more complex one, capture:

- current workload;
- measured failure/latency/resource problem;
- target threshold;
- expected improvement;
- migration/operational cost.

Examples:

- no vector service before exact local semantic search fails the representative-book performance envelope;
- no distributed job system before local durable jobs are demonstrably insufficient;
- no shared BOOK OS/Audio Studio core before real duplicated code and stable interfaces exist.

## 13. Security and recovery are acceptance, not cleanup

A milestone cannot be accepted if its applicable security/recovery requirements are deferred as vague “later hardening”.

Apply the relevant items from:

- `SECURITY_AVAILABILITY_v0.1.md`;
- `PRE_IMPLEMENTATION_HARDENING_v0.1.md`.

Only requirements explicitly mapped to later milestones may remain deferred.

## 14. Documentation rule

Documentation is updated when it preserves recoverability, authority or operability.

Do not generate documentation for its own sake.

After accepted work, `PROJECT_STATE.md` must identify:

- exact accepted main HEAD;
- completed milestone/task;
- active blockers;
- next permitted task/action.

A successor should never have to infer the current state from chat history.

## 15. Acceptance review checklist for Central Brain

Before `ACCEPT`, Central Brain checks:

1. correct baseline;
2. task justification still valid;
3. scope respected;
4. product/architecture authority respected;
5. acceptance evidence complete;
6. applicable hardening complete;
7. no hidden paid/external dependency introduced;
8. no unnecessary complexity or duplicate infrastructure;
9. no regression to prior accepted capability;
10. repository/recovery state is truthful;
11. next capability is genuinely unlocked.

Possible verdicts:

- `ACCEPT`
- `REWORK`
- `BLOCKED`
- `OWNER_DECISION_NEEDED`

## 16. Rule for changing the plan

The roadmap is a critical path, not a sacred list of implementation details.

Central Brain may split, combine or reorder internal tasks when evidence shows a more efficient route, provided that it does not:

- change accepted product intent;
- skip required milestone gates;
- weaken Authority Protocol, quality, security or regional-access requirements;
- introduce major cost/risk without Owner decision;
- make future recovery ambiguous.

Any material roadmap change is recorded in repository authority/state with rationale.

## 17. Definition of an efficient BOOK OS task

A task is efficient when it is:

- necessary now;
- directly tied to MVP/critical path;
- minimally scoped;
- professionally implemented;
- objectively testable;
- reversible/reviewable;
- cheap enough relative to value;
- free of speculative infrastructure;
- explicit about what it unlocks next;
- recoverable from GitHub without chat context.

If those conditions are not met, the task should not be issued yet.
