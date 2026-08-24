# CODEX TASK 002 — AUTHORITY & PERSISTENCE ENGINE

**Status:** READY  
**Milestone:** M1 — Authority & Persistence Engine  
**Owner:** BOOK OS Central Brain  
**Execution role:** Codex

## DESTINATION / EXECUTION ROUTING

Before doing any work, verify the Codex header:

1. Interface: **Codex Cloud Tasks** for execution.
2. Repository: **`niknikdym-hue/book-os`**.
3. Branch: **`codex/task-002-authority-persistence`** — **NOT `main`**.
4. PR: Central Brain will open one PR to `main` after the first implementation commit is published to this branch. Do not create duplicate branches or PRs.
5. The exact execution baseline SHA is supplied by Central Brain in the launch instruction after this task contract is committed. `git fetch origin` and verify both `origin/main` and the selected branch start at that SHA before implementation.
6. If the Codex header shows another repository/branch, or the baseline differs, stop with `BASELINE_DRIFT`.

If shell `git push` lacks GitHub credentials, do not recreate the work in another task. Use the Codex Cloud publication/apply-to-GitHub action to publish the completed result to `codex/task-002-authority-persistence`. If the UI cannot publish to that branch, return the exact publication limitation.

## WHY NOW

Task 001 / M0 is accepted and merged. BOOK OS now has a reproducible native desktop, authenticated local-core process boundary, SQLite/Alembic bootstrap, green CI, and deterministic sidecar lifecycle.

The next accepted critical-path dependency is M1. M2 Book Creation / Contracts cannot safely persist Book Contracts, Chapter Contracts, manuscript authority, or future editorial decisions until BOOK OS has a tested authority-bearing persistence layer with immutable revisions, exact proposal baselines, transactional human decisions, provenance, and recoverable backup/restore.

## PRODUCT / SYSTEM VALUE

After acceptance, BOOK OS will be able to persist and recover authority history without chat memory or mutable “latest text” state.

M1 must make these invariants executable:

- stable entity identity is separate from immutable revision content;
- approved/locked authority is never edited in place;
- every material proposal targets an exact base revision ID/hash;
- stale proposals cannot overwrite newer authority;
- accepted proposals create new authority while preserving prior history;
- rejected proposals leave authority unchanged;
- Decision, Approval, and Provenance remain recoverable append-only history;
- authority transitions are atomic;
- local backup/restore reproduces the exact authority state.

This is the minimum safe foundation required before M2 creates real books/contracts.

## DEPENDENCIES / BASELINE

Canonical repository:

`https://github.com/niknikdym-hue/book-os`

Document-creation baseline after accepted M0 merge:

`b2bbe3dd208e15cbca0420e90c1b4adadab7acda`

**Execution baseline:** use the exact `origin/main` SHA supplied by Central Brain in the launch instruction after this control document and project state are committed. If the branch/main SHA does not match that launch SHA, return `BASELINE_DRIFT`.

Required accepted prior milestone:

`Task 001 / M0 — ACCEPTED AND MERGED`

Read before changing code:

- `docs/BOOK_OS_AUTHORITY.md`
- `docs/CORE_ONTOLOGY.md`
- `docs/TECHNICAL_ARCHITECTURE_v0.1.md`
- `docs/SECURITY_AVAILABILITY_v0.1.md`
- `docs/PRE_IMPLEMENTATION_HARDENING_v0.1.md`
- `docs/IMPLEMENTATION_ROADMAP_v0.1.md`
- `docs/TASK_EXECUTION_PROTOCOL_v0.1.md`
- `docs/PROJECT_STATE.md`
- `services/local-core/alembic/versions/0001_m0_bootstrap.py`
- current `services/local-core` source/tests/config

Required external credentials: **none**.

External/model API calls: **prohibited**.

Paid API calls: **0**.

## EFFICIENCY RATIONALE

Implement only the authority/persistence kernel in the existing Python local core using the already accepted SQLite + SQLAlchemy 2 + Alembic stack.

Use the smallest normalized model that can enforce M1 invariants:

- stable authority-bearing entity identity;
- immutable revision snapshots;
- transactional current-authority reference;
- ChangeProposal;
- append-only Decision / Approval / Provenance history;
- backup/restore primitive.

Do **not** create 22 ontology tables merely because the ontology has 22 logical entities. `CORE_ONTOLOGY.md` explicitly does not require that.

Domain-specific Book/Chapter/Claim/Manuscript schemas belong to later milestones. M1 may use a versioned revision payload envelope for future typed domain payloads, but arbitrary unvalidated JSON/EAV storage must not replace domain schemas. No event-sourcing platform, CQRS framework, remote database, Redis, job system, vector database, generic repository framework, or provider SDK is justified here.

## GOAL

Implement a local, transactional, recoverable Authority & Persistence Engine that enforces immutable revision history, exact-baseline proposals, human decision/approval provenance, stale-write protection, and verified SQLite backup/restore.

## IN SCOPE

### A. M1 persistence migration

Add one Alembic migration after M0 bootstrap, normally:

`0002_m1_authority_persistence.py`

Create only the normalized tables/indexes/constraints required for:

- stable authority-bearing entity identity;
- immutable revision snapshots and parent lineage;
- current authority reference/head;
- authority status history or equivalent explicit status representation;
- ChangeProposal;
- Decision;
- Approval;
- ProvenanceRecord;
- provenance input revision links where required.

Preserve foreign keys and WAL behavior.

Do not add Book/Chapter/Claim/Source/Memory/BookBench production tables yet unless one is strictly required to enforce an M1 invariant; if so, stop and justify why before expanding scope.

### B. Stable IDs and timestamps

Use one consistent sortable unique-ID strategy compatible with the accepted architecture (`UUIDv7` or `ULID` style) for new critical domain IDs.

- UTC timestamps internally.
- IDs remain stable across revision changes and backup/restore.
- If a small maintained dependency is needed, pin it and update lockfiles.
- Do not implement a large custom identity framework.

### C. Immutable revision envelope

Persist each revision as an immutable snapshot containing at minimum:

- revision ID;
- stable entity ID/type;
- parent revision(s) as needed;
- schema name/version for the typed payload;
- canonical serialized content/content reference;
- deterministic SHA-256 content hash;
- created timestamp;
- provenance reference.

Define one deterministic UTF-8 canonicalization rule and test at least:

- mapping/key-order independence;
- Unicode content stability;
- identical normalized payload -> identical hash;
- changed content -> changed hash.

Revision content must never be updated in place. If status is represented separately from immutable content, expose the effective Authority Protocol status cleanly through the domain service.

Authority statuses:

`DRAFT | PROPOSED | REVIEWED | APPROVED | LOCKED | SUPERSEDED`

### D. Authority transition service

Implement a small domain/application service that can:

- register/create a stable authority entity;
- create an immutable revision;
- identify/read current authority;
- create a ChangeProposal against an exact base revision ID **and** hash;
- record human/formally permitted decisions;
- accept a valid proposal transactionally;
- reject a proposal without changing authority;
- lock approved authority where applicable;
- retrieve revision/decision/approval/provenance history.

No business rule may exist only in UI. M1 does not require new desktop UI.

### E. Stale-baseline protection

Proposal acceptance must perform an atomic compare-and-set or equivalent transactional check against the current authority revision.

If current authority no longer equals the proposal’s exact base revision ID/hash:

- return an explicit stale-baseline domain error;
- do not create a new authority head;
- do not supersede current authority;
- do not partially write Approval/Decision state.

A pre-check outside the transaction alone is insufficient.

### F. Human decision / approval history

Persist append-only history sufficient to answer:

- what proposal/subject was decided;
- who/what actor made the decision;
- `ACCEPT | REJECT | REQUEST_REVISION | WAIVE`;
- reason;
- timestamp;
- which exact revision became authority;
- which prior authority revision it replaced;
- which checks/gates were recorded.

Important/material authority must not be auto-approved by an AI/system actor. M1 tests may use explicit deterministic human test actors.

### G. Provenance

Persist append-only provenance fields as applicable:

- origin: `HUMAN_WRITTEN | AI_ASSISTED | AI_GENERATED | IMPORTED | SYSTEM_DERIVED`;
- actor;
- task ID;
- input revision IDs;
- provider/model/version fields nullable for future use;
- timestamp;
- transformation metadata only when required.

Secrets/API keys must never enter provenance.

No provider SDK or live model call is part of M1.

### H. Transaction / failure behavior

Authority acceptance must be atomic.

Add tests proving that an injected persistence/write failure during the acceptance transaction leaves:

- current authority unchanged;
- no partial supersede;
- no orphan Approval;
- no misleading accepted proposal state.

Use deterministic fault injection/mocking rather than OS-destructive disk manipulation in normal CI.

### I. Backup / restore primitive

Implement the minimum M1 local backup/recovery primitive for canonical SQLite state.

Required behavior:

- create a consistent SQLite backup while WAL may be active using a safe SQLite backup/checkpoint approach, not an unsafe raw copy assumption;
- emit a small manifest containing schema/Alembic revision, backup format version, database SHA-256, created timestamp, and application/schema metadata needed for restore validation;
- restore into a fresh destination;
- verify manifest/checksum before accepting restore;
- run/verify SQLite integrity and schema compatibility;
- restore exact authority/revision/proposal/decision/approval/provenance history;
- refuse a backup whose schema is newer than the supported application schema with an explicit error;
- document the v0.1 downgrade policy: no silent automatic downgrade.

Full assets bundling, encryption, cloud sync, export UI, and Literary Master release packaging are out of scope.

### J. M1 performance baseline

Run one non-paid synthetic local measurement after implementation using a realistic M1 authority-history workload.

At minimum report:

- workload size (entities/revisions/proposals/decisions);
- database size;
- current-authority lookup timing;
- proposal acceptance timing;
- backup time;
- restore time.

Use thousands of revision/history rows so the result is meaningful, but do not add optimization or a benchmark framework unless a measured problem appears. This measurement is evidence, not a product performance promise.

## OUT OF SCOPE

Do not implement:

- M2 New Book UI or project dashboard;
- full BookProject / BookProfile / BookContract / BookArchitecture / Chapter / ChapterContract product flows;
- manuscript editor or ManuscriptUnit hierarchy;
- Claim / Source / Evidence tables;
- Model Gateway or any provider adapter;
- OpenAI/Yandex/GigaChat/Anthropic/Gemini SDK/calls;
- Research Engine;
- Book Memory / FTS product search / embeddings;
- durable model/research job subsystem unless strictly required by M1 (it should not be);
- Editorial Findings workflow;
- BookBench;
- Russia provider routing;
- Literary Master;
- Audio Studio integration;
- accounts/cloud/billing/sync;
- Docker/Redis/Celery/Temporal/Kubernetes;
- desktop UI polish;
- speculative generic agent/event-sourcing framework.

## REQUIRED BEHAVIOR / INVARIANTS

1. Stable entity identity survives revision changes.
2. Revision content is immutable after creation.
3. `APPROVED`/`LOCKED` authority is never mutated in place.
4. Every material ChangeProposal stores exact base revision ID and hash.
5. Proposal acceptance is transactional and stale-safe.
6. Accepted proposal creates new authority; prior approved authority is preserved and may become `SUPERSEDED`.
7. Rejected proposal leaves authority unchanged.
8. Decision history is not rewritten.
9. Approval points to exact prior/new authority revisions.
10. Provenance is append-only and secret-free.
11. Deterministic revision hash is reproducible.
12. Backup/restore reproduces exact authority state and history.
13. Corrupt/tampered backup is rejected.
14. Newer unsupported schema is rejected explicitly.
15. M0 loopback/auth/lifecycle/CI behavior remains unchanged.

## APPLICABLE HARDENING

From accepted security/hardening authority, M1 must include:

- transactional authority transitions;
- SHA-256 revision integrity;
- stale proposal detection;
- database integrity checks on backup/restore;
- backup while WAL is active;
- restore to a fresh installation/path;
- corrupted/incomplete backup detection;
- explicit schema downgrade policy;
- write-failure/crash-equivalent rollback behavior for authority transitions;
- export/restore must not lose provenance/history;
- local-first privacy: no real manuscript/editorial data in public fixtures;
- no secrets in database provenance/tests/logs;
- a synthetic M1 performance/size baseline, without premature optimization.

## ACCEPTANCE / EVIDENCE

Report every item `PASS`, `PARTIAL`, or `FAIL` with concrete evidence.

1. Exact execution `origin/main` baseline recorded and matches Central Brain launch SHA.
2. New M1 migration upgrades a fresh database successfully.
3. Migration upgrades an M0 bootstrap database successfully.
4. Foreign keys remain enabled and WAL behavior remains valid.
5. Stable sortable IDs are generated consistently for M1 entities.
6. Revision snapshots are immutable and parent/history references remain recoverable.
7. Canonical serialization/hash tests pass, including key-order and Unicode cases.
8. Valid authority status handling passes; invalid transition/operation attempts fail explicitly.
9. Approved/locked authority cannot be mutated in place.
10. ChangeProposal records exact base revision ID + hash.
11. Valid proposal acceptance atomically produces new current authority and Approval/history.
12. Prior authority remains recoverable and is not deleted.
13. Rejected proposal leaves current authority unchanged.
14. Stale proposal acceptance is rejected and leaves all authority state unchanged.
15. Decision records actor/decision/reason/timestamp and remain append-only.
16. Approval records exact approved/prior revisions and gate metadata.
17. Provenance records origin/actor/task/input revisions and remain append-only; no secrets.
18. Injected write failure during acceptance rolls back the whole authority transition.
19. WAL-safe backup succeeds and produces manifest + checksum.
20. Restore to fresh destination reproduces exact authority/revision/proposal/decision/approval/provenance state.
21. Tampered/corrupt backup checksum is detected before restore acceptance.
22. Unsupported newer-schema backup fails explicitly; downgrade policy is documented.
23. Synthetic M1 performance baseline is reported without introducing speculative infrastructure.
24. All Python formatting/lint/type/unit/migration tests pass.
25. Existing desktop/Tauri/secret-scan CI remains green.
26. External/model calls = 0; paid calls = 0.
27. No real manuscript/private editorial data or secrets added.
28. `git diff --check` passes and final worktree is clean.
29. Scope contains no M2/M3+ implementation.
30. Final branch is published to `codex/task-002-authority-persistence`.

## REGRESSION REQUIREMENTS

Task 001 / M0 remains accepted and must not regress:

- native desktop/local-core architecture unchanged;
- local core remains loopback-only and authenticated;
- random per-launch token/port behavior unchanged;
- sidecar lifecycle/shutdown unchanged;
- current M0 CI jobs stay green;
- existing M0 migration history remains intact; do not rewrite `0001_m0_bootstrap.py`;
- public repo remains free of secrets/private manuscript data.

Normal PR CI must remain non-paid and provider-independent.

## RISKS / STOP CONDITIONS

Return `CENTRAL_BRAIN_DECISION_NEEDED` rather than inventing a new architecture if implementation would require:

- changing the accepted Authority Protocol or statuses;
- allowing AI/system self-approval of material authority;
- changing local-first state ownership;
- replacing SQLite;
- adding cloud state, accounts, provider SDKs, or external services;
- creating a generic event-sourcing/CQRS framework;
- creating all ontology domain tables prematurely;
- weakening stale-baseline, transaction, history, integrity, or backup requirements;
- storing secrets/private manuscript data;
- significant new recurring cost;
- a schema decision that materially constrains M2+ in a way not implied by accepted ontology.

Adjacent optional improvements are deferred. Fix only defects required for M1 acceptance.

## UNLOCKS NEXT

Central Brain acceptance of Task 002 unlocks:

**M2 — Book Creation / Book Contract / Architecture / Chapter Contract**

M2 can then build real BookProject/Business profile creation and authority-bearing contracts on the tested revision/decision/persistence foundation.

Do not start M2 automatically.

## BRANCH / PR

Implementation branch:

`codex/task-002-authority-persistence`

Flow:

`accepted main baseline → codex/task-002-authority-persistence → implementation/evidence → one PR to main → Central Brain review → merge only after ACCEPT`

No force push.

Codex does not merge or self-accept.

If Codex Cloud cannot push from shell, use the Cloud publication/apply action for this exact branch. Do not create a duplicate branch/task solely because shell credentials are unavailable.

## PROJECT STATE

During implementation, Codex may update `docs/PROJECT_STATE.md` only to factual state:

`IMPLEMENTED_AWAITING_CENTRAL_BRAIN_ACCEPTANCE`

It must not mark M1 accepted.

If updating a hashed authority file, update `docs/DESIGN_FILE_HASHES.sha256` consistently.

## DELIVERABLE / REPORT FORMAT

Return one report containing:

- exact launch baseline `origin/main` SHA;
- implementation branch and final HEAD;
- commit(s) and files changed grouped by purpose;
- migration/schema summary;
- authority/revision/proposal/decision/approval/provenance behavior;
- deterministic hash rule;
- transaction/stale-baseline evidence;
- backup/restore format and disaster-test evidence;
- synthetic performance baseline;
- exact validation commands/results;
- 30-row acceptance matrix with `PASS/PARTIAL/FAIL`;
- new GitHub Actions run ID and all job conclusions;
- dependency/lockfile changes;
- external/model calls and paid calls;
- architecture deviations;
- known limitations/blockers;
- clean git status confirmation;
- publication status;
- next safe action.

Final implementation status must be:

`IMPLEMENTED_AWAITING_CENTRAL_BRAIN_ACCEPTANCE`

Stop there. Do not merge. Do not start M2.
