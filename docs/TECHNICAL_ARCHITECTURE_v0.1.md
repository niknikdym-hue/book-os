# BOOK OS — TECHNICAL ARCHITECTURE v0.1

**Status:** ACCEPTED FOR V0.1 IMPLEMENTATION  
**Version:** 0.1.0  
**Date:** 2026-08-22

## 1. Architecture objective

Build a local-first, recoverable, single-user v0.1 that can evolve into a professional product without making one vendor/cloud/chat the owner of the book state.

## 2. Chosen v0.1 architecture

```text
┌──────────────────────────────────────────────────────────────┐
│ BOOK OS Desktop — Tauri 2 + React/TypeScript                │
│  UI / navigation / diff review / project controls           │
└───────────────────────┬──────────────────────────────────────┘
                        │ local authenticated IPC/HTTP
┌───────────────────────▼──────────────────────────────────────┐
│ BOOK OS Local Core — Python 3.12 sidecar                    │
│  FastAPI + Pydantic + domain services                       │
│  Authority / Contracts / Claims / Memory / BookBench        │
│  Model Gateway / Research Gateway / durable jobs            │
└───────────────┬───────────────────────┬──────────────────────┘
                │                       │
       ┌────────▼────────┐      ┌───────▼─────────────────┐
       │ Local state      │      │ External adapters       │
       │ SQLite + FTS5    │      │ LLMs / research APIs    │
       │ assets/indexes   │      │ region/policy routed    │
       └─────────────────┘      └─────────────────────────┘
```

A future BOOK OS service/backend may broker provider access, billing/sync and region-compliant remote inference, but it is **not required to own the manuscript state in v0.1**.

## 3. Desktop shell — Tauri 2

### Choice

`Tauri 2 + React + TypeScript`.

### Responsibilities

- native desktop window and file dialogs;
- application lifecycle;
- spawn/monitor local core sidecar;
- secure OS integration/secrets adapter;
- signed updates later;
- local IPC/session security;
- user interface.

### Why

Tauri 2 is cross-platform, supports a web frontend with Rust native shell, and officially supports bundling external binaries such as Python API servers as sidecars. It also has signed updater and secret-store ecosystem support.

Do not place editorial business logic in React components.

## 4. Local editorial core — Python 3.12

### Choice

Python sidecar using:

- FastAPI for typed local service and streaming endpoints;
- Pydantic v2 for schema validation/JSON schemas;
- SQLAlchemy 2 + Alembic for persistence/migrations;
- `httpx` for provider/research HTTP adapters;
- NumPy for first-book exact semantic similarity;
- pytest for core tests.

### Why Python

The editorial/research/eval ecosystem and provider SDK support are strongest and fastest to iterate in Python. Tauri officially supports bundling Python sidecars, so end users do not install Python separately.

Python is not an architectural authority: the domain schemas/interfaces must remain portable.

## 5. Desktop ↔ local core transport

v0.1:

- sidecar binds only `127.0.0.1` to an OS-assigned/random high port;
- Tauri creates a random per-session bearer secret and passes it to the sidecar through process environment/stdin;
- all local API calls require the session secret;
- sidecar prints/returns ready/port only to parent;
- no `0.0.0.0` bind;
- streaming via SSE or WebSocket where needed;
- shutdown tied to desktop parent lifecycle.

Future hardening may use Unix domain sockets/named pipes, but it is not required for v0.1.

## 6. Canonical local persistence

### SQLite is canonical book-state database

Use SQLite with:

- foreign keys enabled;
- WAL journaling;
- explicit migrations;
- transactions around authority transitions;
- FTS5 for lexical search;
- JSON fields only where structure is genuinely flexible, not as a substitute for schema.

Canonical entities/revisions/decisions/provenance are stored in SQLite.

### File asset store

Large/imported artifacts live under a project-controlled assets directory and are referenced by content hash + metadata.

### Derived indexes

FTS and semantic indexes are rebuildable derived data. They never become authority.

## 7. Project storage layout

Conceptual per-book layout:

```text
<BOOK_PROJECT_DIR>/
├── project.sqlite
├── assets/
├── indexes/
├── exports/
├── backups/
└── project-manifest.json
```

The app may place this under the OS application data directory by default while allowing explicit project export/backup.

The public `book-os` GitHub repository is **software/project-development authority**, not storage for real private manuscripts.

## 8. Semantic index choice

v0.1 canonical choice:

- embedding vectors stored with revision/model metadata;
- exact local cosine similarity using NumPy at first-book scale;
- `SemanticIndex` interface isolates the implementation.

Why not a vector service now:

- a single book is small enough for exact search;
- less operational complexity;
- no remote dependency;
- reproducible and easy to test.

If scale benchmarks later require ANN, consider embedded LanceDB OSS or another mature local engine. Do not make currently-alpha `sqlite-vec` a required v0.1 dependency.

## 9. Durable local workflow/jobs

Do **not** add Redis/Celery/Temporal in v0.1.

Implement a small durable job subsystem in SQLite with:

- job ID/type;
- payload/schema version;
- idempotency key;
- state: queued/running/succeeded/failed/cancelled;
- attempts;
- lease/heartbeat;
- created/started/completed timestamps;
- result/error reference;
- provider run IDs/cost.

Reason: single-user desktop requires crash recovery and idempotency, not distributed cluster orchestration. If a future backend needs distributed workflows, keep job/service boundaries compatible with Temporal or another durable orchestrator.

## 10. Domain modules

Recommended initial modules:

```text
core/
  domain/
    books/
    authority/
    contracts/
    manuscript/
    research/
    claims/
    editorial/
    memory/
    bookbench/
    release/
  gateways/
    models/
    research/
    secrets/
  application/
    workflows/
    commands/
    queries/
  infrastructure/
    db/
    files/
    telemetry/
```

Keep provider SDKs in adapters, not domain modules.

## 11. API/schema discipline

- Pydantic schemas define local API contracts and model structured-output validation.
- Critical domain IDs use UUIDv7/ULID-style sortable unique IDs (implementation may choose one consistently).
- Timestamps UTC internally.
- Authority transitions are transactional.
- Content revisions include SHA-256 hashes.
- Stale proposal detection compares base revision ID/hash.
- No business rule is enforced only in UI.

## 12. Model Gateway implementation

Adapters implement a normalized interface. Initial development order:

1. `OpenAIAdapter` — benchmark/dev lane using Owner's existing Mac credential path.
2. `YandexAIStudioAdapter` — Russian compliant candidate.
3. `GigaChatAdapter` — Russian compliant candidate.
4. Anthropic/Gemini adapters only when benchmark coverage justifies implementation.

Provider keys are loaded through SecretStore, never committed.

## 13. Research Gateway implementation

Initial adapters:

- `OpenAlexAdapter`;
- `CrossrefAdapter`;
- `SemanticScholarAdapter`;
- `WebSearchAdapter` abstraction;
- `DirectWebSourceFetcher` with caching/provenance;
- `LocalFileSourceAdapter`.

## 14. Secrets

Define a `SecretStore` interface.

Initial macOS adapter should use OS Keychain and may reuse the existing Owner credential naming only through explicit configuration; do not copy secret values into project files.

Cross-platform future:

- macOS Keychain;
- Windows Credential Manager;
- Linux Secret Service/Keyring;
- optional Tauri Stronghold fallback.

Secrets must not pass to the React frontend unless strictly unavoidable.

## 15. Observability

### Local baseline

- structured JSON logs with correlation IDs;
- task/job/model/research run IDs;
- latency/error/cost counters;
- OpenTelemetry-compatible spans around workflows/provider calls.

### LLM observability

Langfuse or similar can be used in development/self-hosted mode for traces/eval experimentation, but it is **not authority** and manuscript content must not be exported by default.

## 16. Testing stack

- Python: pytest + property/invariant tests for authority/versioning.
- TypeScript: Vitest + React Testing Library.
- UI E2E: Playwright against packaged/dev desktop where practical.
- Rust/Tauri: cargo tests for native helpers/security/process lifecycle.
- Migrations: upgrade/downgrade/fixture tests.
- Model adapters: mocked contract tests + explicitly gated live smoke tests.
- Research adapters: recorded fixtures/contract tests; no fragile live-web dependency in unit CI.
- BookBench: versioned eval datasets and regression reports.

## 17. CI/CD

GitHub Actions:

- lint/type/unit tests on each PR;
- no paid API required for normal PR checks;
- live provider/eval workflows are manual/protected with budgets and secrets;
- build artifacts for macOS first;
- later signed/notarized macOS release and Tauri signed updater.

Public repo rules: never expose API keys, private manuscripts or proprietary user/editorial decision datasets.

## 18. Build vs buy

### Build ourselves — BOOK OS moat/domain

- ontology;
- Authority Protocol;
- Book/Chapter Contracts;
- Claim/Evidence semantics;
- editorial workflows;
- Author Voice Fingerprint;
- AI-prose pathology checks;
- cross-book editor;
- BookBench definitions/datasets;
- human acceptance;
- editorial decision corpus;
- Literary Master semantics.

### Use commodity technology/APIs

- frontier models;
- embeddings;
- academic metadata APIs;
- web search;
- SQLite;
- Tauri;
- FastAPI/Pydantic/SQLAlchemy;
- OpenTelemetry;
- optional eval/observability tooling;
- GitHub Actions;
- OS secret stores.

## 19. Future cloud/service layer

Add only when needed for end-user distribution:

- BOOK OS account/auth;
- provider brokerage so users do not need vendor subscriptions/keys;
- region-compliant routing;
- usage/billing;
- encrypted sync/backups;
- remote compute/open-weight inference;
- organization/collaboration later.

The cloud service must not make the local Literary Master inaccessible if the service is unavailable.

## 20. Current official technology validation — 2026-08-22

- Tauri 2: cross-platform desktop, external sidecars, signed updater: `https://v2.tauri.app/`
- Tauri sidecars: `https://v2.tauri.app/develop/sidecar/`
- SQLite FTS5: `https://sqlite.org/fts5.html`
- FastAPI: `https://fastapi.tiangolo.com/`
- Pydantic: `https://docs.pydantic.dev/latest/`
- LanceDB OSS embedded retrieval option: `https://docs.lancedb.com/`
- sqlite-vec current alpha status: `https://alexgarcia.xyz/sqlite-vec/`
- OpenTelemetry: `https://opentelemetry.io/docs/`
- Langfuse open-source observability/evals option: `https://langfuse.com/docs`

## 21. Architecture rejection list

Do not introduce without a measured need:

- Kubernetes;
- microservices for local v0.1;
- Redis;
- distributed message brokers;
- remote mandatory vector DB;
- generic agent framework controlling authority;
- one vendor's proprietary conversation/memory store as book state;
- automatic cloud manuscript storage by default;
- direct provider calls from React UI.
