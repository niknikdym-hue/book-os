# CODEX TASK 007 — EDITORIAL WORKFLOWS + DECISION INBOX

**Status:** READY  
**Milestone:** M6 — Editorial Workflows  
**Owner:** BOOK OS Central Brain

## WHY NOW

M0–M5 are accepted and merged. BOOK OS can create a real Business Nonfiction project, draft bounded manuscript units, verify factual Claims through explicit Evidence, and recover current whole-book context through Book Memory. The next critical-path capability is controlled editing: diagnoses and proposed manuscript changes must be reviewable, auditable and unable to mutate authority until a human decision accepts an exact-base proposal.

## GOAL

Implement the editorial control loop:

`exact current revision → EditorialFinding → exact-base ChangeProposal → Decision Inbox → HUMAN decision → accepted new authority or preserved prior authority`

The central acceptance invariant is:

> A finding is not an edit, a proposal is not authority, and no material manuscript change becomes current without explicit human acceptance against an unchanged exact baseline.

## BASELINE / AUTHORITY

Read current `main`, then:

- `EDITORIAL_PROTOCOLS_v0.1.md`;
- `CORE_ONTOLOGY.md`;
- `MODEL_GATEWAY_v0.1.md`;
- `BOOK_MEMORY_v0.1.md`;
- `RESEARCH_AND_CLAIMS_v0.1.md`;
- `TECHNICAL_ARCHITECTURE_v0.1.md`;
- `IMPLEMENTATION_ROADMAP_v0.1.md`;
- `TASK_EXECUTION_PROTOCOL_v0.1.md`;
- `PROJECT_STATE.md`;
- this contract.

Required prior milestone: Task 006 / M5 ACCEPTED AND MERGED.

Normal CI external/model calls = 0. Paid calls = 0.

## ARCHITECTURAL RULES

1. Reuse M1 `change_proposals`, `decisions`, `approvals`, immutable revisions and compare-and-set acceptance. Do not create a second authority system.
2. `EditorialFinding` and editorial-run records are diagnostic/workflow state, not authority.
3. Every material proposal identifies an exact current `entity_id + base_revision_id + base_revision_hash`.
4. Human acceptance uses the existing Authority Engine; AI/SYSTEM actors cannot accept/reject/waive material editorial decisions on behalf of the Owner.
5. M6 builds editorial workflow/control infrastructure and first deterministic diagnostics. It does **not** create a second provider-specific AI gateway. Future model-produced structured findings must enter through the same typed finding interface and remain proposals only.

## IN SCOPE

### A. Persistence / migration `0007`

Add only M6 workflow persistence required for:

- `editorial_runs` — bounded diagnostic run identity, role, scope, runner/version, exact input snapshot references, status and timestamps;
- `editorial_findings` — structured diagnosis with exact baseline, target and audit fields;
- finding ↔ existing M1 `change_proposals` link(s);
- optional finding state history if needed to preserve OPEN/RESOLVED/WAIVED/SUPERSEDED transitions without silent rewrite.

`EditorialFinding` minimum persisted fields:

- stable `finding_id`;
- book ID;
- role;
- category;
- target object/entity ID;
- chapter/unit ID when applicable;
- exact base revision ID/hash;
- diagnosis;
- why it matters;
- bounded evidence/diagnostic support;
- severity;
- confidence;
- expected effect / risks when present;
- actor/origin/run provenance;
- state `OPEN | RESOLVED | WAIVED | SUPERSEDED`;
- created/resolved timestamps.

Roles:

- `DEVELOPMENTAL_EDITOR`;
- `CROSS_BOOK_AUDITOR`;
- `FACT_CHECKER`;
- `LITERARY_EDITOR`;
- `STYLE_GUARDIAN`.

### B. Typed editorial finding service

Implement a single typed interface to register/list/inspect findings from all allowed editorial roles.

Rules:

- target must resolve to a real current project object/revision;
- manuscript findings must reference a stable ManuscriptUnit authority entity and exact current revision ID/hash;
- stale/non-current baseline creation is rejected;
- provider/model text, if supplied in future, is untrusted diagnostic input and never grants acceptance authority;
- finding creation cannot mutate manuscript/Contract authority.

### C. First deterministic diagnostic runs

Implement bounded local diagnostics with no external/model calls:

#### Developmental Editor — Chapter Contract coverage

For a selected/current chapter, inspect current Chapter Contract plus current ManuscriptUnits and produce findings only for clearly deterministic coverage gaps, such as:

- no current manuscript unit exists for a chapter with approved Chapter Contract;
- a required claim/contract requirement has no lexical occurrence/trace in the current chapter text under a documented conservative rule.

The diagnosis must say this is a lexical/structural signal, not a semantic truth judgment.

#### Cross-book Auditor — repetition

Across current ManuscriptUnits only, detect deterministic duplicate/near-duplicate passages using a documented local lexical similarity rule.

- ignore HISTORY/non-current revisions by default;
- record both stable locations and exact revisions in finding evidence;
- diagnosis only; never delete/merge text.

#### Fact Checker

Using the M4 Claim Ledger, create findings for material current claims requiring attention, including at least:

- `UNREVIEWED` material claims;
- `DISPUTED` material claims;
- `UNSUPPORTED` material claims;
- unresolved citation/evidence gate state when deterministically visible.

The finding must point back to the exact Claim and manuscript revision. It cannot mark a claim supported or edit the text.

### D. Literary Editor / Style Guardian workflow readiness

M6 must support `LITERARY_EDITOR` and `STYLE_GUARDIAN` findings through the same typed finding/run/proposal/Decision Inbox path.

Do not invent an automatic style-quality score or AI-prose detector here; those belong to M7 BookBench. For M6, deterministic/manual/fixture-produced findings are sufficient to prove the workflow and authority gates for these roles.

### E. Manuscript ChangeProposal from finding

For a current ManuscriptUnit finding, allow creation of one material text proposal that reuses the M1 `change_proposals` table.

Rules:

- proposal base must exactly equal the finding's current base revision ID/hash;
- proposed revision preserves the existing manuscript unit schema/metadata while changing only the requested manuscript content fields;
- proposal stores rationale linked to the finding and provenance;
- return a human-readable deterministic unified diff/preview;
- proposal creation cannot change `authority_heads`;
- stale finding/baseline cannot produce an accept-ready proposal without re-review/rebase.

No blind whole-book rewrite and no multi-unit destructive patch in this M6 slice.

### F. Decision Inbox

Implement one project-level inbox for material editorial decisions.

Each inbox item shows:

- role/category/severity/confidence;
- diagnosis + why;
- exact location and base revision/hash;
- current/stale state;
- proposed diff when a proposal exists;
- evidence/support;
- expected effect / risks;
- proposal decision history.

Human actions:

#### ACCEPT

- only `HUMAN` actor;
- call existing M1 exact-base `AuthorityService.accept_proposal`;
- new manuscript revision becomes `APPROVED` current authority;
- prior revision becomes `SUPERSEDED`;
- finding becomes `RESOLVED`;
- Decision + Approval + provenance remain recoverable.

#### REJECT

- only `HUMAN` actor;
- call/reuse M1 rejection semantics;
- current manuscript authority is unchanged;
- rejected proposal remains recoverable;
- finding remains `OPEN` so another proposal may be created, unless separately waived.

#### REQUEST REVISION

- only `HUMAN` actor;
- persist a `REQUEST_REVISION` Decision using the existing M1 `decisions` corpus;
- current proposal becomes `SUPERSEDED`/not accept-ready;
- manuscript authority is unchanged;
- finding remains `OPEN` for a new proposal.

#### WAIVE

- only `HUMAN` actor;
- persist a `WAIVE` Decision with reason;
- any open linked proposal becomes not accept-ready;
- manuscript authority is unchanged;
- finding becomes `WAIVED`.

### G. Stale proposal gate

Decision Inbox must calculate staleness from current authority, not trust cached UI state.

- if current `authority_heads` no longer equals proposal base revision ID/hash, item is visibly `STALE`;
- ACCEPT is rejected by the Authority Engine;
- no auto-rebase;
- re-review/new proposal is required.

### H. Editorial decision corpus

Expose a structured read model that can recover:

`original revision → finding/diagnosis → proposal/diff → human decision/reason → final accepted revision (if any)`.

This is project-private data in project SQLite. Do not publish user manuscript/editorial corpus into the public software repository.

### I. Minimal authenticated API + desktop UI

Expose authenticated local operations to:

- run the bounded deterministic Developmental / Cross-book / Fact diagnostics;
- create/list/inspect typed findings for all five roles;
- create a ManuscriptUnit text proposal from a finding;
- list Decision Inbox items;
- inspect deterministic diff;
- ACCEPT / REJECT / REQUEST REVISION / WAIVE;
- inspect decision corpus/history.

Desktop adds one `Editorial / Decision Inbox` workspace:

- run deterministic audits;
- filter by role/status/severity;
- diagnosis/location/base revision;
- proposed before/after or unified diff;
- visible `CURRENT | STALE` baseline;
- human action buttons;
- decision reason required for material actions;
- clear state after decision.

### J. Book Memory / Claim regression behavior

After accepted manuscript change:

- canonical authority changes through M1 only;
- M5 Book Memory sync must see the new current manuscript revision and exclude the prior one from default CURRENT retrieval;
- existing Claims tied to an older manuscript revision remain explicit/stale context; M6 must not silently rebind factual Claims to changed text.

### K. Backup/regression

Advance schema compatibility to `0007` while preserving supported older-backup restore/migrate-forward behavior.

M0–M5 regressions remain green.

## STRICT OUT OF SCOPE

- M7 BookBench scoring/rubrics/model judges;
- Author Voice Fingerprint or automatic AI-prose pathology scoring;
- automatic global rewrite / whole-book edit;
- autonomous editor agents with unrestricted tools;
- live provider-specific editorial model routing beyond the already accepted Model Gateway architecture;
- Yandex/GigaChat Russia provider lane;
- Literary Master/export/audio handoff;
- cloud/accounts/billing/sync;
- silent Claim rebinding after manuscript edit;
- accepting/waiving material decisions as AI/SYSTEM actor.

## REQUIRED ACCEPTANCE

1. Fresh DB migrates `0001→0007`; existing M5 DB upgrades to M6.
2. Finding creation requires an exact current target revision; stale baseline is rejected.
3. Finding creation never changes manuscript authority.
4. Developmental deterministic run produces a bounded structural/coverage finding on a known fixture and no false authority mutation.
5. Cross-book duplicate run finds a known duplicate across current units and ignores a historical-only duplicate.
6. Fact Checker produces findings for known material `UNREVIEWED/DISPUTED/UNSUPPORTED` claims and never changes Claim verification state.
7. Literary Editor and Style Guardian findings can traverse the same typed workflow without special authority bypass.
8. Proposal from finding reuses M1 `change_proposals`, exact base ID/hash and deterministic human-readable diff.
9. Proposal creation does not change `authority_heads`.
10. ACCEPT by HUMAN creates the new APPROVED manuscript revision, supersedes prior revision, records Decision+Approval and resolves finding.
11. AI/SYSTEM ACCEPT is rejected.
12. REJECT records human decision, leaves manuscript authority unchanged and preserves rejected proposal history.
13. REQUEST REVISION records human decision, makes prior proposal non-accept-ready, leaves finding OPEN and authority unchanged.
14. WAIVE records human decision/reason, leaves authority unchanged and marks finding WAIVED.
15. Stale proposal is visibly stale and cannot be accepted.
16. Decision corpus reconstructs original → diagnosis → proposal → decision → final accepted revision.
17. After accepted manuscript change + Book Memory sync, prior revision is absent from default CURRENT memory and new revision is present.
18. Claims tied to prior manuscript revision are not silently rebound.
19. Authenticated API boundary remains intact.
20. Desktop component test covers Finding → Proposal diff → human ACCEPT and visible resolved/current result; separate tests cover reject/revise/waive/stale states.
21. Python Ruff/mypy/pytest green.
22. TypeScript lint/type/test/build green.
23. Rust cargo test/check green.
24. secret/dependency scans green.
25. normal CI external/model calls = 0; paid calls = 0.
26. no M7+ scope.

## STOP CONDITIONS

Stop and surface a Central Brain/Owner decision rather than broadening scope if implementation would require:

- AI/SYSTEM material acceptance;
- weakening exact-base/stale protections;
- automatic Claim rebinding;
- BookBench/M7 quality scoring to make M6 work;
- mandatory paid/live editorial model calls;
- cloud state ownership;
- global destructive manuscript rewrites.

## UNLOCKS NEXT

Central Brain ACCEPT of M6 unlocks M7 — BookBench v0.1.

Do not start M7 before M6 acceptance/merge.
