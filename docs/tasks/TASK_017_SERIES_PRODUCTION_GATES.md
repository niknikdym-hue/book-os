# CODEX TASK 017 — EXECUTABLE SERIES PRODUCTION GATES

**Status:** READY  
**Milestone:** Real-book production readiness — pre-writing gate  
**Owner:** BOOK OS Central Brain  
**Execution role:** Codex

## WHY NOW

The first production pilot is fixed: series «Инструменты интернет-маркетинга», first production book «SMM продвижение». Current `main` already has Author/Series/Style profiles, target length, pilot instrumentation, Research, BookBench, Writer/Editor, Literary Master and Task 014 workspace. But the accepted 2026-09-07 Owner decision requires stronger series-production controls before a representative real pilot may enter long-form Writing.

This is the only launch-critical runtime blocker before Book Definition/Architecture can safely admit chapters to Writing.

## PRODUCT / SYSTEM VALUE

Make series-book production fail-closed against semantic overlap, weak definition, global writing unlock, padding, and deferred structural defects. Convert accepted editorial authority into executable product behavior for the first real series pilot.

## DEPENDENCIES / BASELINE

- Canonical repository: `https://github.com/niknikdym-hue/book-os`
- Exact expected `origin/main` HEAD: `c6504fb70cc65abef9753e2be03da0b610bd8451`
- Required accepted state: Tasks 001–016 disposition recorded; PR #23 reconciled/merged; canonical schema `0015`
- Mandatory authority:
  - `docs/BOOK_OS_AUTHORITY.md`
  - `docs/PROJECT_STATE.md`
  - `docs/TASK_EXECUTION_PROTOCOL_v0.1.md`
  - `docs/decisions/2026-09-06-author-series-length-style-publishing-controls.md`
  - `docs/decisions/2026-09-07-series-production-and-chapter-admission.md`
  - `docs/tasks/TASK_011_REAL_BOOK_PILOT.md`
- External dependencies/credentials: none
- Provider/model/paid calls: 0

If baseline differs materially, return `BASELINE_DRIFT` before implementation.

## EFFICIENCY RATIONALE

Implement only the minimum executable slice explicitly required by accepted authority for a representative series pilot. Do not build audio runtime, publishing taxonomy, shared lexicon runtime, cloud sync, or provider expansion. Reuse current authority, planning, research, drafting, BookBench, pilot and desktop patterns.

## GOAL

Implement executable series-production gates so a series book can progress from Definition to chapter-specific Writing admission without semantic reuse, weak evidence, padding, or silent bypass.

## IN SCOPE

1. Living Series Canon / Exclusion Registry with accepted asset statuses at minimum:
   `PLANNED | RESERVED | USED_DRAFT | USED_ACCEPTED | CROSS_REFERENCE_ONLY | LEGACY_PROTECTED | RELEASED`.
2. Book Uniqueness Ledger bound to book/Architecture/chapter identities.
3. Structured Book Definition Pack sufficient for:
   - reader/problem;
   - promise/thesis/mechanism;
   - `NOT THIS BOOK`;
   - series/future-book boundaries;
   - benchmark/substitute map;
   - original-contribution hypothesis;
   - research/evidence functions;
   - practical-value map;
   - target-market/Russia application;
   - freshness risk;
   - overlap proof;
   - AI-substitution result.
4. Stronger Chapter Contract fields from accepted 2026-09-07 authority.
5. Per-chapter `WRITING_ALLOWED = NO | YES` admission state with fail-closed Writer enforcement.
6. Chapter admission evidence/checks for current approved Definition/Architecture/Chapter Contract, uniqueness, evidence readiness, boundaries/reservations, domain quality gates, anti-junk/provenance, and unresolved merge/delete conditions.
7. Mid-book audit checkpoint at 40–60% planned manuscript progress, fail-closed for structural blockers.
8. Independent Adversarial Review checkpoint before Literary Master; it creates evidence/findings and never approves.
9. Series Closure mechanics sufficient to promote actually used accepted assets and preserve/release reservations based on exact accepted Literary Master evidence.
10. Desktop/API surface sufficient to show why Writing is blocked and which gate remains open.
11. Backup/restore/migration coverage for the new state.

## REQUIRED BEHAVIOR / INVARIANTS

- Architecture approval MUST NOT globally enable Writing.
- Writer MUST fail closed for any chapter without `WRITING_ALLOWED=YES`.
- AI cannot approve Definition, Architecture, Chapter admission, Series Closure, Literary Master, or waivers.
- `USED_ACCEPTED` cannot silently return to free inventory.
- Accepted Literary Master remains final exclusion evidence; registry is navigation/planning, not replacement for semantic comparison.
- A different example/statistic/channel does not make the same mechanism unique.
- Practical map must support `problem → decision → action → artifact/output → observable check`.
- AI-substitution failure is REWORK, not prose-polish permission.
- Target length remains a density/planning constraint. **NO PADDING / NO WATER:** no runtime path may justify generation merely to hit a character target; missing volume must correspond to a new substantive function.
- Book-specific content/archetypes/platform choices are private project data, not hard-coded BOOK OS product rules.
- No runtime dependency on `books-for-litres`.
- Current schema `0015` must advance by one linear Alembic revision only.
- Normal CI makes zero provider/model/paid calls.

## OUT OF SCOPE

- Writing the SMM manuscript or its Book Definition content.
- Hard-coding Russian SMM platforms or business archetypes.
- Audio-native runtime implementation.
- Publishing Package/taxonomy runtime expansion.
- Shared anti-junk lexicon runtime integration.
- New providers or cloud infrastructure.
- Paid OpenAI/Yandex calls.

## ACCEPTANCE / EVIDENCE

At minimum prove:

1. fresh DB and upgrade path migrate `0015 → 0016` and backup/restore remains valid;
2. Series Canon assets persist all required statuses with provenance and valid transitions;
3. `USED_ACCEPTED` is immutable/fail-closed except explicit superseding authority path;
4. Book Uniqueness Ledger binds exact book/architecture/chapter identities;
5. Definition Pack persists all required sections and cannot be treated as approved by AI/SYSTEM;
6. Architecture approval alone leaves every chapter `WRITING_ALLOWED=NO`;
7. Writer returns a deterministic gate failure before model HTTP when chapter is not admitted;
8. admission requires current approved Definition + Architecture + Chapter Contract and all mandatory checks;
9. stale/replaced authority invalidates prior admission;
10. uniqueness/overlap BLOCKING evidence prevents admission;
11. research/evidence not-ready prevents admission when claims require support;
12. practical-value and target-market/freshness required gates fail closed;
13. AI-substitution/deletion/merge blocker prevents admission;
14. anti-junk/provenance blocker prevents admission;
15. admitted chapter can use existing Writer path without weakening paid-call permission/cost caps;
16. mid-book checkpoint appears when progress enters 40–60% and structural BLOCKING prevents unrestricted continuation;
17. adversarial review is independent evidence, cannot approve, and unresolved BLOCKING prevents Literary Master release readiness;
18. Series Closure promotes only assets proven used in exact accepted master and releases unused reservations only with evidence;
19. Desktop shows chapter admission state and human-readable blockers;
20. no real manuscript/proprietary corpus/secrets enter public repo;
21. full backend/frontend/native/secret-scan regression remains green;
22. provider/model/paid requests in CI = 0.

## REGRESSION REQUIREMENTS

Preserve:
- schema history through `0015`;
- Task 014 guided workspace;
- Planner DRAFT/HUMAN gates;
- blind Sol↔Astra comparison;
- GPT-5.6 >272K fail-closed cost guard;
- anti-junk `BANNED_TEMPLATE` / `CONTEXT_REVIEW` semantics;
- Keychain and fresh per-request paid permission;
- Pilot instrumentation;
- Literary Master fail-closed HUMAN release;
- installed `~/Desktop/BOOK OS.app` launch/update behavior.

## RISKS / STOP CONDITIONS

Return `CENTRAL_BRAIN_DECISION_NEEDED` instead of inventing semantics if:
- current data model cannot represent exact authority binding without a destructive migration;
- a proposed status transition conflicts with Authority Protocol;
- Writer cannot be gated pre-HTTP without weakening accepted ModelGateway behavior;
- implementation would require hard-coding the pilot series/book or importing content from `books-for-litres`.

## UNLOCKS NEXT

After Central Brain accepts Task 017, the real «SMM продвижение» pilot may proceed through approved Book Definition Pack → Architecture → chapter-by-chapter admission → controlled Writing.

## BRANCH / PR

Use existing task branch:
`brain/task-017-series-production-gates`

Commit implementation to this same branch and update the same PR. No force push. Codex does not merge or self-accept.

## PROJECT STATE

Codex may set factual task state to `IMPLEMENTED_AWAITING_CENTRAL_BRAIN_ACCEPTANCE`. Central Brain alone records acceptance after exact-head review/CI.

## DELIVERABLE / REPORT FORMAT

Return:
- baseline HEAD;
- final remote HEAD;
- commits/files changed;
- migration id;
- validation commands/results;
- acceptance matrix PASS/PARTIAL/FAIL;
- exact pre-HTTP Writer gate evidence;
- backup/restore evidence;
- full CI evidence;
- external/model/paid calls (must be 0);
- architecture deviations/known blockers;
- clean git status;
- next safe action.

Do not begin SMM manuscript generation or any paid model execution.
