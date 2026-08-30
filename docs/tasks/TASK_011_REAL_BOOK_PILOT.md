# TASK 011 — REAL BUSINESS NONFICTION PILOT

**Status:** ACTIVE  
**Milestone:** Real-book pilot → GO/NO-GO evidence  
**Owner:** BOOK OS Central Brain / Human Owner  
**Baseline:** `ebb1ffbd8a026b2c2db00fa55f3f9863447245b8`  
**Branch:** `brain/task-011-real-book-pilot`

## WHY NOW

M0–M7 and Literary Master + exports are accepted and merged. BOOK OS now has the system capabilities required to run a real nonfiction book from initial definition through a reproducible Literary Master.

The remaining question is no longer whether the architecture compiles. It is whether the system produces a genuinely strong Business Nonfiction book with acceptable human effort, cost, factual discipline, voice preservation and editorial quality.

## PRIMARY GOAL

Run one real new Business Nonfiction book through the actual BOOK OS workflow:

`Idea → Book Definition → Research → Book Contract → Architecture → Chapter Contracts → controlled drafting → Book Memory → editorial workflows → BookBench → human decisions → Literary Master`

Then produce evidence for a HUMAN `GO | CONDITIONAL_GO | NO_GO` decision.

The system MUST NOT auto-decide GO/NO-GO.

## PRIVACY BOUNDARY

The real manuscript and research corpus are private local project data.

Public Git may contain only:

- pilot workflow/tooling;
- schemas;
- aggregate evidence structures;
- synthetic fixtures/tests;
- no real manuscript prose;
- no private source corpus;
- no private BookBench dataset text;
- no personal secrets.

No pilot feature may require publishing book content to GitHub.

## MODEL STRATEGY

OpenAI is the primary intelligence lane for this MVP/pilot.

Provider-neutral architecture remains mandatory:

- all model execution continues through `ModelGateway` / `EmbeddingGateway`;
- exact provider/model/config/prompt provenance remains recorded;
- OpenAI is not architecture authority;
- no backup provider is required for this pilot.

No paid/model call is authorized merely by this task contract. Actual provider execution requires an explicit bounded Owner-approved pilot budget before the first paid call.

## PILOT INSTRUMENTATION — MIGRATION 0010

Canonical `main` after Literary Master is Alembic `0009`. Pilot instrumentation uses `0010`, revising `0009`.

Persist local/private pilot evidence inside the book project database.

### `pilot_runs`

Minimum:
- `pilot_id`;
- `book_id`;
- pilot profile/version;
- status `ACTIVE | COMPLETED | ABORTED`;
- explicit human owner/actor;
- started/completed timestamps;
- final human decision `GO | CONDITIONAL_GO | NO_GO | NULL`;
- final human decision reason (local/private);
- immutable/append-only completion evidence once completed.

Only one ACTIVE real-book pilot per book.

### `pilot_stage_events`

Record bounded stage evidence, without duplicating manuscript text:
- stable event ID;
- pilot ID;
- stage;
- event kind;
- actor kind `HUMAN | AI | SYSTEM`;
- elapsed seconds when known;
- human minutes when known;
- provider cost when known;
- model-run count when known;
- structured outcome/status;
- local/private metadata JSON;
- timestamp.

Supported stages at minimum:
- `IDEA`;
- `BOOK_DEFINITION`;
- `RESEARCH`;
- `BOOK_CONTRACT`;
- `ARCHITECTURE`;
- `CHAPTER_CONTRACTS`;
- `DRAFTING`;
- `BOOK_MEMORY`;
- `EDITORIAL`;
- `BOOKBENCH`;
- `FINAL_REVIEW`;
- `LITERARY_MASTER`.

### `pilot_observations`

Capture what the real pilot teaches us:
- observation ID;
- pilot ID;
- stage;
- category;
- severity;
- actor kind;
- local/private description;
- optional stable artifact/revision/finding reference;
- resolved state;
- created/resolved timestamps.

Categories at minimum:
- `PRODUCT_DEFECT`;
- `WORKFLOW_FRICTION`;
- `MISSED_ERROR`;
- `BOOKBENCH_FALSE_POSITIVE`;
- `BOOKBENCH_FALSE_NEGATIVE`;
- `MODEL_QUALITY_FAILURE`;
- `VOICE_FAILURE`;
- `RESEARCH_TRACEABILITY_FAILURE`;
- `HUMAN_DECISION_REASON`;
- `OTHER`.

Severity:
- `INFO | ATTENTION | BLOCKING`.

## PILOT SERVICE

Implement a local `PilotService` that can:

1. start a pilot for an existing real book project with an explicit human actor;
2. return pilot status;
3. record stage events;
4. record/update observations without mutating book authority;
5. aggregate existing BOOK OS evidence rather than copying it:
   - model runs and known cost;
   - claims/verification distribution;
   - editorial findings/decisions;
   - BookBench snapshot/report identity and BLOCKING state;
   - Literary Master identity/hash when created;
6. produce a human-readable/JSON pilot summary;
7. expose `GO_NO_GO_EVIDENCE_READY` only when minimum evidence is complete;
8. require explicit HUMAN final decision and reason;
9. never auto-decide GO/NO-GO;
10. keep the final decision append-only once recorded.

## MINIMUM GO/NO-GO EVIDENCE

Evidence is not ready until:

- a real pilot exists and remains traceable to one book;
- the book has reached a LOCKED Literary Master;
- Literary Master exact hash/manifest identity is recorded by reference;
- all mandatory pilot stages have at least one evidence event or an explicit human `NOT_APPLICABLE` event with reason;
- provider/model execution provenance is available for all AI-created manuscript/editorial outputs used in the pilot;
- aggregate known model cost is reported; unknown cost is `UNKNOWN`, never silently zero;
- material research claims remain traceable through Claim → Evidence → Source;
- final BookBench snapshot is current and has no unresolved required BLOCKING dimension;
- unresolved pilot `BLOCKING` observations are zero;
- false positives/false negatives and missed errors have been explicitly reviewed;
- human workflow friction is recorded;
- final human literary-quality judgment is recorded separately from automated metrics.

## OPENAI PREFLIGHT

Before paid pilot drafting begins, provide a zero-call credential/config preflight:

- SecretStore can resolve the configured OpenAI credential;
- exact model/config intended for `WRITER` and `EDITOR` is explicit;
- request/token/cost bounds for the first paid slice are explicit;
- no provider call occurs during preflight;
- no secret value is returned/logged.

Credential absence is an Owner Gate only after all offline pilot readiness is complete.

## API / DESKTOP

Authenticated Local Core should expose:

- start/get pilot;
- record stage event;
- add/resolve observation;
- aggregate summary;
- GO/NO-GO evidence readiness;
- record final HUMAN decision.

Desktop should expose a minimal `Real-book Pilot` workspace:

- current stage/evidence completeness;
- elapsed human/model work evidence;
- known cost;
- open observations by severity;
- Literary Master identity when reached;
- explicit final human decision control only after evidence-ready;
- no private manuscript text copied into pilot summary views by default.

## AUTOMATED TESTS

At minimum prove:

1. fresh DB migrates `0009 → 0010`;
2. pilot requires an existing book and explicit human actor;
3. only one ACTIVE pilot per book;
4. pilot instrumentation never mutates authority revisions/status;
5. stage/event enums fail closed;
6. observations are traceable and resolution is explicit;
7. final HUMAN decision is impossible before evidence-ready;
8. AI/SYSTEM cannot record final GO/NO-GO;
9. completed final decision cannot be silently overwritten;
10. missing mandatory stages keep evidence not-ready;
11. missing Literary Master keeps evidence not-ready;
12. unresolved BLOCKING pilot observation keeps evidence not-ready;
13. aggregate provider cost is derived from existing run evidence and unknown cost is not treated as zero;
14. aggregate summary does not expose secrets;
15. zero-call OpenAI preflight reports only credential/config availability;
16. API authentication tests pass;
17. desktop pilot readiness/final-decision states are tested;
18. backup/restore advances through `0010`;
19. M0–Task010 regressions remain green;
20. normal CI provider/model/paid calls = 0.

## REAL PILOT EXECUTION RULES

Offline tooling/readiness work proceeds autonomously.

Owner input is required only for genuine creative/financial gates, including:

- selecting/confirming the real book idea and intended reader when the actual pilot begins;
- explicit approval of Book/Chapter authority states as already required by BOOK OS;
- explicit bounded paid OpenAI execution budget;
- final Literary Master human release action;
- final GO/CONDITIONAL_GO/NO_GO decision.

Do not ask the Owner for implementation details that the repository can determine.

## ACCEPTANCE

Task 011 tooling is accepted when the system can instrument a real private-local book end-to-end without leaking manuscript content and can produce fail-closed GO/NO-GO evidence readiness.

The BOOK OS MVP is declared `GO` only after the actual real-book pilot reaches Literary Master and the human Owner makes the final decision from the evidence.
