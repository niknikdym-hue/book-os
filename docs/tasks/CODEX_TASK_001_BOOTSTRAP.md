# CODEX TASK 001 — MATERIALIZE DESIGN BASELINE + EXECUTABLE SKELETON

**Status:** READY TO EXECUTE AFTER DESIGN FILES ARE AVAILABLE TO CODEX  
**Owner:** BOOK OS Central Brain  
**Execution role:** Codex

## GOAL

Turn the accepted BOOK OS v0.1 design baseline into a clean, reproducible repository baseline and the smallest executable local-first desktop skeleton. Do not implement editorial features yet.

## AUTHORITY / BASELINE

1. Start from current `origin/main` of `https://github.com/niknikdym-hue/book-os`.
2. Read `README.md`, `docs/BOOK_OS_AUTHORITY.md`, `docs/PROJECT_EXECUTION_PLAN.md`, `docs/PROJECT_STATE.md`, `docs/DESIGN_INDEX.md` and all v0.1 specs before changing code.
3. If any accepted specs are not yet in `main`, first add the supplied design-baseline files without silently changing their product meaning.
4. Report exact starting HEAD.

## IN SCOPE

### A. Repository normalization

Create/normalize this high-level structure:

```text
book-os/
├── README.md
├── docs/
│   ├── ...accepted authority/specs...
│   ├── decisions/
│   └── tasks/
├── apps/
│   └── desktop/
├── services/
│   └── local-core/
├── .github/workflows/
└── tooling/config files as minimally required
```

### B. Desktop skeleton

- Tauri 2.
- React + TypeScript frontend.
- One simple BOOK OS window showing application name and Local Core health status.
- No design flourish beyond a clean minimal professional shell.

### C. Python local core skeleton

- Python 3.12 target.
- FastAPI.
- Pydantic v2.
- health/version endpoint.
- bind only to `127.0.0.1`, random/OS-assigned port.
- require a per-launch random bearer/session token supplied by parent process.
- no external network call.

### D. Sidecar lifecycle

- Tauri launches local core as sidecar in development/build-compatible structure.
- obtains ready/port status.
- desktop calls authenticated health endpoint.
- shuts sidecar down with application lifecycle.
- document dev strategy for packaging Python sidecar; actual full production packaging may be a follow-up if cross-arch tooling makes it too large for Task 001.

### E. Persistence skeleton

- SQLite dependency/migration framework in local core.
- migration `0001` may create only a minimal metadata/schema-version table unless ontology persistence is required for bootstrap.
- enable foreign keys and choose/document WAL setup.
- no production ontology schema yet (Task 002).

### F. CI / quality

Add GitHub Actions for relevant non-paid checks:

- Python formatting/lint/type checks as chosen by repo;
- Python unit tests;
- TypeScript lint/type/unit checks;
- Rust/Tauri compile/check where feasible on CI;
- no paid model/API calls.

Prefer simple maintained tooling. Do not introduce a large monorepo framework unless required.

## OUT OF SCOPE

- Model Gateway provider implementations.
- OpenAI/Yandex/GigaChat API calls.
- real Book/Chapter/Claim persistence.
- BookBench.
- Research Engine.
- vector/semantic search.
- authentication/accounts/cloud backend.
- billing.
- Audio Studio integration implementation.
- UI polish beyond skeleton.
- Docker/Kubernetes/Redis/Temporal.

## REQUIRED BEHAVIOR / INVARIANTS

- No secret in repo/log/test fixture.
- No service binds to public network interface.
- No chat/session memory used as application state.
- No provider SDK added yet.
- Keep dependencies minimal and pinned/locked through standard lockfiles.
- Repository remains runnable from fresh clone with documented prerequisites.

## TESTS / ACCEPTANCE

Must demonstrate:

1. `origin/main` baseline HEAD recorded.
2. Desktop dev launch succeeds on the development Mac.
3. Local core starts only on loopback.
4. Unauthenticated local health request is rejected; request with session token succeeds.
5. Desktop displays successful authenticated Local Core health.
6. Python tests pass.
7. TS type/lint/tests pass.
8. Rust/Tauri check/build smoke passes as applicable.
9. No paid/external API request occurs.
10. `git status` clean at delivered HEAD.

## DELIVERABLE / REPORT FORMAT

Return:

- starting HEAD;
- final HEAD;
- branch/PR URL if used;
- changed files grouped by purpose;
- exact validation commands and results;
- sidecar/port/auth implementation summary;
- known limitations;
- confirmation that no external/paid API call occurred;
- any architecture ambiguity as `OWNER/CENTRAL_BRAIN_DECISION_NEEDED` rather than inventing a solution.

Do not begin Task 002.
