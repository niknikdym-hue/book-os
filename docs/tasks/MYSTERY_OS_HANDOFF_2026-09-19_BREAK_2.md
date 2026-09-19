# MYSTERY OS — HANDOFF / SAFE BREAKPOINT 2026-09-19 #2

**Status:** SAFE BREAKPOINT  
**Repository:** `niknikdym-hue/book-os`  
**Owner decision:** continue building MYSTERY OS inside BOOK OS; do not write the real manuscript yet.  
**Do not merge without Owner authorization.**  
**Real provider/model/paid calls in MYS-07..MYS-12 preparation described here:** 0.

---

## 1. Product decision now LOCKED for implementation

The real fiction workflow will live in **BOOK OS**, not as a separate app and not as a chat-only workflow.

Operating model:

- **BOOK OS** = source of truth + editorial/production machine;
- **Chat** = Central Brain / decision console;
- **Writer / Astra / Agents API** = bounded executors for specific operations.

BOOK OS must receive a separate top-level **Fiction / MYSTERY OS** workspace.

Do **not** force fiction into the existing nonfiction-only `BUSINESS_NONFICTION` project path.

The fiction workspace must be a real persisted/local workspace, not a decorative tab.

For the real series:

- series project: **«Линия 112»**;
- each book is its own production unit;
- series-level authority/Series Brain remains shared;
- each book moves through pre-writing -> representative sample -> qualification -> MASS_DRAFT -> whole-book QA.

The Owner agreed to this design.

---

## 2. Technical GREEN stack completed in this phase

### MYS-07 — MysteryBench / ColdReader / Adversarial Reconstruction

Draft PR: **#52**  
Head:

`cdf30088ff791661700c48e26b50d44b2af53ac6`

Status: **technically GREEN**, Draft, unmerged.

Implemented:

- MIDBOOK / FINAL MysteryBench policies;
- exact manuscript/authority binding;
- ColdReader checkpoints;
- CaseSolution/spoiler isolation;
- blind adversarial reconstruction before CaseSolution reveal;
- structured `VerifiedEvaluationArtifact`;
- exact evaluator/snapshot/class/rubric/purpose provenance;
- current designated CaseSolution binding;
- no averaging-away of BLOCKING gaps.

### MYS-08 — Professional Fiction Benchmark

Draft PR: **#53**  
Head:

`ff1d7692f9b26e03dee162fdb464c2f7cf325258`

Status: **technically GREEN**, Draft, unmerged.

Implemented:

- rights-safe/versioned FictionBenchmarkSet;
- market/subgenre/language match;
- author/corpus diversity;
- publication-span/freshness rules;
- lawful text-access provenance;
- no protected corpus storage / no mimicry requests;
- exact professional dimension evidence;
- no universal 1–10 score;
- readiness bands that cannot hide BLOCKING/MAJOR gaps;
- MYS-06 benchmark bridge.

### MYS-09 — Series Brain / Book Passport / Collision Gate

Draft PR: **#54**  
Head:

`2985ad3742a8aba0a28c5cd4b4bd29fcf06e36ea`

Status: **technically GREEN**, Draft, unmerged.

Final verification included **312 passed tests** plus all standard smoke checks.

Implemented:

- Book Passport;
- stable series identity + historical Series Profile revisions;
- exact + semantic collision checks;
- mandatory semantic collision core;
- independent Series Editor evidence;
- Series Context ref vs Series Brain ref;
- full historical asset ledger;
- one-use / recurring / reserved / claimed asset semantics;
- no retroactive one-use -> recurring reclassification;
- standalone case + late-entry rules;
- Series Brain integrated into MYS-05 `WRITING_ALLOWED`.

### MYS-10 — Executable Anti-Cliche / Exception Registry

Draft PR: **#55**  
Head:

`ef52aab55e35d3ecb79be38bdb2a25eaaa19f024`

Status: **technically GREEN**, Draft, unmerged.

Implemented:

- 50+ machine-coded mystery/supernatural/style/series rules;
- blocked-by-default vs high-risk vs style pathology vs series collision;
- exact finding refs;
- exact exception scope;
- verified HUMAN ACCEPT authority;
- REWORK/REJECT remain blocking;
- Series Brain binding for series exceptions;
- SERIES_COLLISION cannot be waived by AntiClicheException;
- qualified MYS-10 result required by MYS-05;
- fake/manual anti-cliche ref no longer unlocks Writing.

Important catalog entries include explicit blocks for:

- inherited old mansion / house-as-evil gateway;
- dusty archive / letters / diaries as primary explanation;
- bookcase secret room;
- convenient camera/network/phone failure;
- late decisive forensic fact;
- amnesia hiding POV knowledge;
- psychiatric diagnosis as universal explanation;
- chosen-by-bloodline;
- convenient psychic;
- repeated dead-person calls/messages as fixed formula;
- confession instead of proof;
- villain exposition monologue;
- generic supernatural shorthand;
- AI/template prose pathologies.

### MYS-11 — Production Routing / Agents / Fiction Gateway / Dry Run

Draft PR: **#57**  
Head:

`12480e4480dab766878774922408af334d1cada9`

Status: **technically GREEN**, Draft, unmerged.

CI run: `35458772758` / run #1746.

PASS:

- Ruff format;
- Ruff check;
- strict mypy;
- full pytest;
- Desktop lint/typecheck/tests/build/audit;
- Tauri cargo test/check;
- secret scan;
- native self-contained macOS build/launch;
- synthetic representative-sample dry run;
- synthetic MASS_DRAFT dry run;
- deterministic fake shared ModelGateway execution.

Workflow overall remains red only because Apple distribution signing credentials are unavailable. This is an external release gate, not a MYS-11 logic failure.

Provider/model/paid calls: 0.

---

## 3. MYS-11 final architecture now fixed

### Execution classes

`A_LOCAL`
- deterministic/local only;
- no provider;
- no agent;
- no spend.

`B_STANDARD`
- REPRESENTATIVE_SAMPLE_DRAFT;
- SCENE_DRAFT;
- ROUTINE_SCENE_REVISION;
- CONTINUITY_EXTRACTION.

Shared OpenAI Auto routing now includes:

- representative sample -> `gpt-5.6-sol`;
- scene draft -> `gpt-5.6-sol`;
- routine scene revision -> `gpt-5.6-sol`;
- continuity extraction -> `gpt-5.6-terra`.

`C_PREMIUM`
- SERIES_ARCHITECTURE;
- CASE_SOLUTION_ARCHITECTURE;
- CLUE_REVEAL_ARCHITECTURE;
- ANTI_CLICHE_STRESS_TEST;
- SERIES_SEMANTIC_COLLISION;
- WRITING_READINESS_AUDIT;
- WHOLE_BOOK_DEVELOPMENTAL.

Shared OpenAI Auto route:
- `gpt-6-astra`.

Premium reasoning is therefore selective, not used for every prose scene.

### EDITORIAL_PREP / Agents API

Agents API is **optional**.

Normal fiction writing remains operational when:

- agent lane unavailable;
- agent capability disabled.

Agent dispatch requires exact:

- C_PREMIUM operation;
- operation allowlist;
- owner authorization artifact;
- cost authorization artifact;
- explicit private-content permission when needed;
- exact authority refs;
- EditorialPrepBundle;
- kill-switch/capability enabled;
- source-packet-only network mode when external evidence is needed.

Agent bundle forbids:

- UNLOCK_WRITING;
- APPROVE_STORY_AUTHORITY;
- APPROVE_ANTI_CLICHE_EXCEPTION;
- WRITE_MANUSCRIPT_PROSE;
- REPOSITORY_WRITE;
- MERGE_DEPLOY_RELEASE.

Agent output is proposal-only.

### Exact authorization artifacts

Owner and cost authorization are structured immutable artifacts bound to exact operation IDs/kinds.

A string like `owner-auth:anything` is insufficient.

Route fingerprint includes authorization artifact content.

### Fiction ModelGateway

The shared BOOK OS ModelGateway now accepts strict task types:

- REPRESENTATIVE_SAMPLE_DRAFT;
- SCENE_DRAFT;
- ROUTINE_SCENE_REVISION;
- CONTINUITY_EXTRACTION.

Strict scene result:

- `DRAFT`; or
- `ARCHITECTURE_BLOCKER`.

ARCHITECTURE_BLOCKER cannot contain hidden manuscript prose.

Writer prompts explicitly forbid silently inventing:

- clues;
- culprit facts;
- supernatural rules;
- timeline facts;
- relationship turns;
- research facts;
- authority changes.

If required authority is missing, Writer stops.

### Admission-bound fiction gateway

`WritingAdmissionToken -> ProductionRouteResult -> FictionGatewayExecutionRequest -> shared ModelGateway`

Exact checks include:

- book;
- scene;
- SceneContract revision;
- production mode;
- full authority revision set including SceneContract;
- production route;
- owner authorization;
- cost authorization;
- provider/model;
- token expiry.

Synthetic dry run reached the shared ModelGateway via `DeterministicFakeAdapter`, with no external provider call.

---

## 4. Current MYS-12 branch

Branch:

`brain/mys-12-fiction-workspace-ui-20260919`

Current exact head at break:

`12480e4480dab766878774922408af334d1cada9`

This is exactly the MYS-11 GREEN head.

**No MYS-12 implementation commit has been made yet.**

The branch is the safe starting point for the Fiction workspace.

Do not call MYS-12 started/implemented beyond design/read-only inspection.

---

## 5. MYS-12 design decision already made

The current `/api/projects` and nonfiction project model are intentionally `BUSINESS_NONFICTION`-specific.

Do **not** smuggle fiction through those fields.

MYS-12 should add a separate fiction workspace boundary while reusing:

- common BOOK OS desktop shell/navigation;
- common ModelGateway;
- common authority/gates;
- common persistence primitives where appropriate;
- common cost/routing infrastructure.

### Required top-level UX

Add a clear top-level navigation destination:

**Fiction / MYSTERY OS**

Do not bury it inside nonfiction authoring.

### Required first workspace

Series project:

**Линия 112**

The workspace should expose at minimum:

- series overview;
- books list;
- current book;
- pre-writing gate status;
- Book Passport / Series Brain status;
- StoryDefinition status;
- NarrativeContract status;
- CaseSolution status;
- CaseTimeline / clue / research readiness;
- Anti-Cliche status;
- Representative Sample status;
- Writer Qualification status;
- Professional Benchmark status;
- production route status;
- current allowed mode:
  - NOT_READY;
  - REPRESENTATIVE_SAMPLE_ALLOWED;
  - MASS_DRAFT_ALLOWED.

### Book workflow

Each fiction book should progress through:

1. Book Definition / premise;
2. Book Passport;
3. StoryDefinition;
4. NarrativeContract;
5. CaseSolution;
6. Timeline / Clues / Research;
7. Series Brain;
8. Anti-Cliche;
9. representative-sample admission;
10. sample generation;
11. MYS-06 qualification;
12. professional benchmark;
13. MASS_DRAFT;
14. whole-book / final review.

### Storage/API requirement

The workspace must be real and persisted/local.

Do not build a visual-only fake page.

Prefer a dedicated fiction workspace API/storage model rather than widening nonfiction `book_projects` prematurely.

---

## 6. Exact next implementation sequence after break

1. Re-verify:
   - PR #57 head == `12480e4480dab766878774922408af334d1cada9`;
   - MYS-12 branch starts at the same exact head.

2. Read current Desktop navigation/store/API implementation:
   - `apps/desktop/src/App.tsx`;
   - `apps/desktop/src/BookSidebar.tsx`;
   - `apps/desktop/src/SeriesStudio.tsx`;
   - `apps/desktop/src/api.ts`;
   - `apps/desktop/src/types.ts`;
   - relevant local-core app/project persistence.

3. Implement minimal real fiction workspace backend:
   - series list/create/fetch;
   - book list/create/fetch;
   - stored fiction workspace state;
   - computed pre-writing status projection.

4. Implement top-level Desktop Fiction/MYSTERY OS navigation.

5. Add series workspace UI for `Линия 112` structure.

6. Add tests:
   - navigation;
   - persistence;
   - no nonfiction regression;
   - gate-status rendering;
   - current book switching;
   - REPRESENTATIVE_SAMPLE vs MASS_DRAFT status.

7. Full CI.

8. Only after MYS-12 technical GREEN:
   - perform one final synthetic workspace -> gate -> fake ModelGateway integration test;
   - then issue the Owner signal:
     **«Готовы запускать работу над рукописью „Линия 112“».**

Do not issue that signal before MYS-12 is GREEN.

---

## 7. Real manuscript status

**NOT STARTED.**

No real `Линия 112` prose has been generated.

No real CaseSolution/StoryDefinition/Book Passport has been created yet.

No real paid Astra/Agents work has been run.

When ready, the first real workflow will be created inside BOOK OS Fiction workspace, not as a chat-only manuscript.

---

## 8. Merge / release state

PRs #52, #53, #54, #55, #57 are Draft and unmerged.

No merge is authorized.

No release is authorized.

Apple signing remains an unrelated external release credential gate.

---

## 9. Restart instruction

At restart, the first message can simply be:

**«Продолжаем MYSTERY OS с MYS-12 Fiction workspace»**

Then:

- verify exact heads;
- resume from section 6;
- do not redesign MYS-01..11;
- do not start real manuscript until MYS-12 is GREEN and the explicit readiness signal is sent.
