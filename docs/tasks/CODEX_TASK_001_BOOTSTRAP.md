# CODEX TASK 001 — EXECUTABLE LOCAL-FIRST SKELETON

**Status:** READY AFTER TASK-GOVERNANCE BASELINE IS MERGED  
**Milestone:** M0 — Repository Baseline and Executable Skeleton  
**Owner:** BOOK OS Central Brain  
**Execution role:** Codex

## WHY NOW

BOOK OS has an accepted implementation-ready design but no executable product runtime yet. Every later capability — Authority Engine, Contracts, Model Gateway, Research, Book Memory and BookBench — depends on a reproducible desktop/local-core/persistence/test foundation.

This is therefore the first implementation dependency on the critical path. Starting editorial or AI features before this foundation would create throwaway integration code, unclear security boundaries and untestable state ownership.

## PRODUCT / SYSTEM VALUE

Task 001 does not deliver editorial features. It establishes the smallest real BOOK OS application that can safely host them.

After acceptance, BOOK OS will have:

- a native desktop process;
- a local editorial-core process boundary;
- authenticated loopback communication;
- a canonical local persistence/migration foundation;
- reproducible quality/CI checks;
- an explicit base on which M1 Authority & Persistence can be implemented without re-platforming.

## DEPENDENCIES / BASELINE

Repository:

`https://github.com/niknikdym-hue/book-os`

Before changing code:

1. `fetch origin`;
2. record exact current `origin/main` HEAD supplied/confirmed by Central Brain at task issuance;
3. if the launch instruction's expected HEAD does not equal current `origin/main`, return `BASELINE_DRIFT` before implementation;
4. read the recovery/design baseline in `README.md` and `docs/DESIGN_INDEX.md`;
5. read at minimum:
   - `docs/BOOK_OS_AUTHORITY.md`;
   - `docs/PROJECT_EXECUTION_PLAN.md`;
   - `docs/PROJECT_STATE.md`;
   - `docs/TASK_EXECUTION_PROTOCOL_v0.1.md`;
   - `docs/TECHNICAL_ARCHITECTURE_v0.1.md`;
   - `docs/SECURITY_AVAILABILITY_v0.1.md`;
   - `docs/PRE_IMPLEMENTATION_HARDENING_v0.1.md`;
   - `docs/IMPLEMENTATION_ROADMAP_v0.1.md`.

Prerequisite milestone: accepted v0.1 design baseline / pre-implementation audit.

Required external credentials: none.

Paid/external model APIs: prohibited.

## EFFICIENCY RATIONALE

Use the smallest professional foundation already accepted by Technical Architecture:

- Tauri 2 + React/TypeScript instead of a heavier Electron/cloud-first shell;
- one Python 3.12 FastAPI sidecar because the editorial/research/eval ecosystem will live in Python;
- SQLite + Alembic rather than a remote database;
- authenticated loopback HTTP for v0.1 rather than prematurely building sockets/IPC abstractions;
- ordinary package lockfiles and lightweight CI rather than a large monorepo/build platform;
- no Docker, Redis, distributed orchestration, vector database, agent framework or provider SDK.

The task intentionally defers production ontology persistence and editorial features so the foundation remains reviewable and reversible.

## GOAL

Turn the accepted BOOK OS design baseline into the smallest clean, reproducible, executable local-first desktop skeleton on which M1 can safely implement authority-bearing state.

## IN SCOPE

### A. Repository/runtime structure

Create/normalize the implementation structure only as required:

```text
book-os/
├── README.md
├── docs/
├── apps/
│   └── desktop/
├── services/
│   └── local-core/
├── .github/workflows/
└── minimal tooling/config files
```

Do not add empty future-domain directories merely to mirror a diagram.

### B. Desktop skeleton

- Tauri 2;
- React + TypeScript;
- one clean minimal BOOK OS window;
- visible Local Core health state;
- no design-system/framework expansion beyond what is required for the shell.

### C. Python local core

- Python 3.12 target;
- FastAPI;
- Pydantic v2;
- health/version endpoint;
- bind only to `127.0.0.1`;
- OS-assigned/random high port;
- per-launch unguessable bearer/session token supplied by the parent process;
- no external network call.

### D. Sidecar lifecycle

- Tauri launches/monitors local core in a development/build-compatible sidecar structure;
- obtains readiness/port without exposing a fixed public service;
- desktop calls the authenticated health endpoint;
- sidecar lifecycle is tied to desktop lifecycle;
- document the chosen packaging path if full production bundling is deliberately deferred from M0.

### E. Persistence bootstrap

- SQLite dependency;
- SQLAlchemy 2 + Alembic migration framework;
- migration `0001` creates only bootstrap/schema metadata required for M0;
- foreign keys enabled;
- WAL choice documented and exercised;
- no production ontology schema yet.

### F. CI / quality baseline

Add maintained, minimal, non-paid checks for:

- Python format/lint/type/unit tests;
- TypeScript lint/type/unit tests;
- Rust/Tauri compile/check/build smoke where feasible;
- dependency lockfiles;
- minimal secret/dependency security scanning appropriate to M0;
- no live model/API calls.

## OUT OF SCOPE

- Model Gateway/provider implementations;
- OpenAI/Yandex/GigaChat/Anthropic/Gemini calls or SDKs;
- real Book/Chapter/Claim/Revision persistence;
- Authority Engine business logic;
- BookBench;
- Research Engine;
- Book Memory/vector/semantic search;
- user accounts/auth/cloud backend;
- billing/provider brokerage;
- Audio Studio integration implementation;
- signed/notarized production releases/updater;
- full backup/export subsystem;
- UI polish/design system beyond the minimal shell;
- Docker/Kubernetes/Redis/Celery/Temporal;
- generic agent framework;
- speculative shared core with Audio Studio.

## REQUIRED BEHAVIOR / INVARIANTS

- no secret in repository/log/test fixture;
- no service binds to a public network interface;
- random per-launch local authentication secret is not hard-coded;
- no chat/session transcript is application state;
- no provider SDK is added;
- dependencies use normal ecosystem lockfiles/pinning;
- fresh clone prerequisites are documented;
- failures are explicit; desktop must not falsely show Local Core healthy;
- implementation code respects the local-first boundary in accepted architecture.

## APPLICABLE HARDENING FOR M0

From `SECURITY_AVAILABILITY_v0.1.md` and `PRE_IMPLEMENTATION_HARDENING_v0.1.md`, M0 must include only the hardening that is due now:

- loopback-only sidecar boundary;
- authenticated local requests;
- no arbitrary shell/network execution endpoint;
- secrets excluded from source/logs/fixtures;
- dependency lockfiles/pinning;
- minimal dependency/secret scanning;
- deterministic migration bootstrap;
- clear fresh-clone/recovery instructions;
- explicit process shutdown/lifecycle behavior.

Prompt-injection, SSRF research-fetch controls, rights ledger, provider brokerage, release signing/SBOM, full backup disaster tests and other later-milestone requirements remain mandatory at their mapped milestone and must not inflate Task 001.

## ACCEPTANCE / EVIDENCE

Task 001 must demonstrate all of the following:

1. exact starting `origin/main` HEAD recorded;
2. desktop dev launch succeeds on Owner's development Mac;
3. Tauri launches the local-core sidecar;
4. local core listens only on loopback;
5. port is random/OS-assigned rather than a public fixed listener;
6. unauthenticated health request is rejected;
7. authenticated request with the per-launch token succeeds;
8. desktop displays successful authenticated Local Core health;
9. local-core shutdown follows application lifecycle or has an explicit tested cleanup mechanism;
10. fresh SQLite database/migration bootstrap succeeds;
11. SQLite foreign keys are enabled;
12. WAL behavior is documented/tested as selected;
13. Python tests pass;
14. Python format/lint/type checks pass;
15. TypeScript lint/type/tests pass;
16. Rust/Tauri check/build smoke passes as applicable;
17. lockfiles exist for used ecosystems;
18. M0 secret/dependency checks are clean or have explicitly justified non-blocking findings;
19. no external/model network call occurred;
20. paid API calls = 0;
21. repository can be set up from a fresh clone using documented prerequisites;
22. delivered branch has clean `git status`.

For each criterion report `PASS`, `PARTIAL` or `FAIL` with evidence. Do not convert a missing criterion into prose optimism.

## REGRESSION REQUIREMENTS

Because this is M0, regression scope is primarily repository authority and documentation:

- accepted authority/spec files remain intact;
- no private manuscript or credentials enter public Git;
- recovery order remains valid;
- normal non-paid CI does not depend on external AI providers.

## RISKS / STOP CONDITIONS

Stop and return to Central Brain if implementation would require:

- changing accepted desktop/local-core architecture;
- binding outside loopback;
- introducing cloud state ownership;
- adding a provider/model dependency;
- adding major infrastructure outside M0;
- weakening security to make sidecar integration work;
- committing secrets/private manuscript data;
- significant unplanned recurring cost;
- broad refactoring unrelated to M0.

Return `CENTRAL_BRAIN_DECISION_NEEDED` rather than inventing a new architecture.

## UNLOCKS NEXT

Central Brain acceptance of Task 001 unlocks:

**M1 — Authority & Persistence Engine**

Specifically, M1 can then implement ontology persistence, immutable revisions, authority transitions, proposals, decisions/approvals/provenance and backup/restore primitives on a tested runtime/database foundation.

Do not start M1 automatically.

## BRANCH / PR

Default branch:

`codex/task-001-bootstrap`

Flow:

`accepted main baseline → bounded branch → PR to main → Central Brain review → merge only after ACCEPT`

No force push. Codex does not merge or self-accept Task 001.

## PROJECT STATE

After implementation, Codex may update `docs/PROJECT_STATE.md` only to factual state:

`IMPLEMENTED_AWAITING_CENTRAL_BRAIN_ACCEPTANCE`

It must not mark M0 accepted.

## DELIVERABLE / REPORT FORMAT

Return one report containing:

- baseline main HEAD;
- branch;
- final branch HEAD;
- PR URL;
- commits and files changed grouped by purpose;
- implementation summary for desktop/local core/sidecar/auth/SQLite/CI;
- exact validation commands/results;
- acceptance criteria table with PASS/PARTIAL/FAIL;
- applicable M0 hardening evidence;
- fresh-clone/setup evidence;
- secret/dependency scan result;
- external requests and paid API calls;
- architecture deviations;
- known limitations/blockers;
- clean git status confirmation;
- next safe action.

Do not begin Task 002/M1.
