# CODEX TASK 009 — RUSSIA / NO-VPN PROVIDER LANE

**Status:** READY
**Milestone:** M8 — Russia/no-VPN provider lane
**Owner:** BOOK OS Central Brain
**Baseline:** start only from the exact canonical `main` HEAD recorded when this task is activated.

## WHY NOW

M0–M7 are accepted and merged. BOOK OS now has authority/persistence, book creation, controlled drafting, Research/Claim Ledger, Book Memory, editorial workflows and BookBench v0.1. The next launch-critical milestone is to prove that the core product can run for a user in Russia without VPN, without a personal foreign AI subscription/key, and without lowering the editorial quality floor.

M8 must create a provider-neutral regional routing lane and evaluate real region-compliant provider configurations before any Russia-ready claim.

## GOAL

Implement:

`region/legal policy → versioned capability matrix → provider adapter → bounded task execution → BookBench role evaluation → explicit promotion/fallback`

At M8 completion, at least one **commercially and regionally permitted** Russian runtime route must meet the defined BOOK OS role-quality gate for the core launch tasks.

If no candidate passes, return a product-quality blocker. Do not weaken the bar.

## BINDING AUTHORITY

Read current `main`, then:

- `docs/BOOK_OS_AUTHORITY.md`;
- `docs/PRODUCT_SPEC_v0.1.md`;
- `docs/TECHNICAL_ARCHITECTURE_v0.1.md`;
- `docs/MODEL_GATEWAY_v0.1.md`;
- `docs/SECURITY_AVAILABILITY_v0.1.md`;
- `docs/BOOKBENCH_v0.1.md`;
- `docs/BOOK_MEMORY_v0.1.md`;
- `docs/IMPLEMENTATION_ROADMAP_v0.1.md`;
- `docs/TASK_EXECUTION_PROTOCOL_v0.1.md`;
- `docs/PROJECT_STATE.md`;
- this task.

Required prior milestone: Task 008 / M7 ACCEPTED AND MERGED.

## CURRENT OFFICIAL PROVIDER FACTS — VERIFIED 2026-08-27

Treat these as dated capability/policy inputs, not eternal constants. Store source URLs + verification date in the capability matrix.

### Yandex Cloud / AI Studio

- Yandex Cloud currently exposes a Russia region.
- AI Studio exposes text-generation and embeddings REST/gRPC APIs.
- Text generation supports structured JSON object / JSON Schema output.
- API keys can be scoped to AI Studio/text-generation execution; IAM bearer tokens are also supported.
- Current documented API examples use AI Studio endpoints under `https://ai.api.cloud.yandex.net/` and model URIs such as `gpt://<folder_id>/yandexgpt/latest`.
- Never infer model quality from provider marketing; discover/store exact returned model/version identity.

Official sources:
- `https://yandex.cloud/en/docs/overview/concepts/region`
- `https://yandex.cloud/en/docs/overview/api`
- `https://yandex.cloud/en/docs/iam/concepts/authorization/api-key`
- `https://yandex.cloud/en/docs/iam/api-ref/authentication`
- `https://yandex.cloud/en/docs/serverless-integrations/operations/workflows/constructor/foundationmodelscall`

### GigaChat API

- Since 2026-07-17 the target API host is `https://api.giga.chat`.
- Authorization key is exchanged for a bearer access token; documented token lifetime is 30 minutes.
- Scopes include `GIGACHAT_API_PERS`, `GIGACHAT_API_B2B`, `GIGACHAT_API_CORP`; commercial BOOK OS runtime must use an appropriate paid/commercial path, not personal freemium.
- GigaChat supports strict JSON-schema structured output.
- `GigaChat-2-Pro` and `GigaChat-2-Max` are current commercial candidates; `GigaChat-3-Ultra` is currently restricted to physical-person freemium and must NOT be marked commercial-production-eligible for BOOK OS.
- Freemium output is documented as personal/non-commercial; commercial use requires a paid arrangement.
- Production TLS verification must remain enabled. Documentation examples that disable certificate verification are not permission for BOOK OS to ship `verify=False`; use system trust or an explicitly configured trusted CA bundle.

Official sources:
- `https://developers.sber.ru/docs/ru/gigachat/api/reference/rest/gigachat-api`
- `https://developers.sber.ru/docs/ru/gigachat/guides/structured-output`
- `https://developers.sber.ru/docs/ru/gigachat/guides/selecting-a-model`
- `https://developers.sber.ru/docs/ru/gigachat/tariffs/legal-tariffs`
- `https://developers.sber.ru/docs/ru/gigachat/tariffs/commercial`
- `https://developers.sber.ru/docs/ru/gigachat/api/reference/rest/get-models`

### OpenAI

Russia is absent from the current official supported-country list. OpenAI remains an Owner development/international benchmark lane only and is **not eligible** as the mandatory `RU` runtime route.

Official source:
- `https://help.openai.com/en/articles/5347006-openai-api-supported-countries-and-territories`

## NON-NEGOTIABLE RULES

1. No VPN/circumvention.
2. A Russian user does not supply a personal foreign-provider subscription/key.
3. Region/legal policy is a hard gate before quality/cost optimization.
4. No provider/model is architecture authority.
5. Provider-specific SDK/HTTP response types do not leak into core domain logic.
6. Secrets stay behind `SecretStore`; no provider credentials reach React, Git, SQLite authority content or logs.
7. No raw real manuscript/eval corpus in the public repository.
8. Normal CI external/provider/model calls = `0`; normal CI paid calls = `0`.
9. Live provider execution is **manual/promotional evidence only**, guarded by an explicit execution flag and credentials; ordinary UI/tests never trigger it.
10. A provider outage or refusal becomes a structured unavailable/fallback state; the product never tells a Russian user to “turn on VPN”.
11. Fallback may run only when it satisfies region/legal/privacy/capability **and the applicable quality gate**.
12. Never lower the Writer/Editor quality gate merely to make M8 green.
13. Provider/model/config changes invalidate promotion evidence until re-evaluated.
14. Human authority remains unchanged; provider output can only create the same bounded DRAFT/proposal/diagnostic states accepted in M3–M7.

## IN SCOPE

### A. Migration `0009` / regional provider evidence persistence

Use the next unused schema revision after the accepted M7 database.

Persist only non-secret provider/runtime evidence needed for M8:

#### `provider_capabilities`
Minimum:
- stable entry ID;
- provider;
- model/config identity;
- capability-matrix version/hash;
- region (`RU`, etc.);
- regional/legal eligibility state;
- commercial eligibility state;
- supported BOOK OS roles;
- generation/structured-output/embedding/tool capabilities;
- context/output limits when known;
- data/privacy flags;
- auth mode metadata without secret values;
- TLS policy metadata;
- source URLs + `verified_at`;
- availability/health;
- cost metadata when known;
- current/superseded status.

#### `provider_probe_runs`
Minimum:
- exact provider/model/config;
- matrix version/hash;
- probe type (`MOCK | LIVE`);
- region;
- request capability;
- latency/usage/cost metadata;
- normalized success/refusal/unavailable/error category;
- external request/response IDs when safe;
- timestamp;
- **no credential or manuscript content**.

#### `provider_role_promotions`
Minimum:
- provider/model/config identity;
- region;
- BOOK OS role;
- exact immutable BookBench dataset snapshot/version/hash;
- exact BookBench scorecard/eval references;
- role-quality decision `PROMOTED | REJECTED | EXPIRED`;
- decision reason;
- independence evidence;
- capability matrix version/hash;
- human/Central-Brain promotion actor metadata;
- created/superseded timestamps.

Promotion is derived routing evidence, never manuscript authority.

### B. Versioned provider capability matrix

Implement a provider-neutral matrix/service that can:

- load versioned seed policy facts with source + verification date;
- overlay live-discovered model/version/health data;
- retain historical matrix versions;
- answer “is this provider/model/config eligible for region + role + privacy + capability?” with structured reasons;
- never silently treat an unknown policy/legal/commercial state as allowed.

Seed at minimum:
- Yandex AI Studio as `RU` region candidate;
- GigaChat paid/commercial scopes as `RU` candidate;
- OpenAI as not eligible for mandatory `RU` runtime;
- GigaChat-3-Ultra as not commercial-production eligible under current verified terms.

### C. Region/provider policy engine

Add an explicit policy object to routing.

For `region=RU`:
1. region/legal/commercial eligibility;
2. privacy/data-policy;
3. required capability/schema;
4. role-quality promotion state;
5. health/fallback;
6. then cost/latency preference.

Return normalized reasons such as:
- `REGION_NOT_SUPPORTED`;
- `COMMERCIAL_PATH_NOT_VERIFIED`;
- `QUALITY_NOT_PROMOTED`;
- `CREDENTIAL_MISSING`;
- `PROVIDER_UNAVAILABLE`;
- `CAPABILITY_MISSING`;
- `TLS_TRUST_NOT_READY`.

No VPN suggestion exists.

### D. Yandex AI Studio generation adapter

Integrate through the existing M3 `ModelGateway`; do not create a parallel gateway.

Requirements:
- bounded typed BOOK OS requests;
- exact provider/model/config provenance;
- strict structured-output path compatible with existing schemas;
- plain literary text output when task contract permits prose;
- usage/latency/provider request IDs normalized;
- structured refusals/errors;
- SecretStore credential lookup;
- support service API key and/or IAM-token strategy without exposing either to UI;
- no provider request body/credential logging by default;
- mocked `httpx.MockTransport` tests in normal CI;
- no live call in normal CI.

Model URI/config is explicit and versioned; `latest` may be a configured discovery alias but the returned/executed model identity must be stored.

### E. GigaChat generation adapter

Integrate through the same `ModelGateway`.

Requirements:
- `https://api.giga.chat` target;
- authorization-key → access-token exchange;
- bounded in-memory access-token cache honoring expiry;
- commercial scope configurable (`B2B`/`CORP`), no personal freemium default for product runtime;
- strict JSON Schema structured-output path;
- exact returned model/version identity;
- usage/latency/request identity where available;
- normalize blacklist/refusal, auth, rate-limit, provider and malformed-output failures;
- production TLS verification stays enabled; support an explicit trusted CA bundle path/config where required, never hard-code `verify=False`;
- mocked token + generation HTTP tests;
- no live call in normal CI.

### F. Russia-compliant embeddings adapters

Boundedly extend the existing M5 `EmbeddingGateway`; do not add a vector database.

Implement mocked/provider adapters for:
- Yandex AI Studio embeddings;
- GigaChat embeddings.

Persist/use exact provider/model/version/config/dimension identity so M5/M7 stale-config protections continue to work.

No live embedding call in normal CI.

### G. Routing + fallback integration

Generalize accepted M3 routing without regressing current OpenAI development adapter.

Add:
- explicit region context;
- provider policy/capability check;
- promoted-role requirement for production `RU`;
- deterministic fallback ordering;
- structured fallback provenance;
- no fallback to ineligible/unpromoted provider;
- no fallback after an authority-changing action (existing authority rules still apply).

### H. BookBench role-quality promotion

Reuse M7 BookBench; do not invent a second eval system.

For M8 define role-specific release profiles, not a universal score.

At minimum evaluate critical launch roles:
- `WRITER` / controlled drafting;
- `EDITOR` / bounded editorial diagnosis/proposal support;
- `EVALUATOR` where used as release-grade judge evidence.

A configuration is not production-promotable for a role when:
- any required critical dimension is `BLOCKING`;
- structured output is malformed on required structured tasks;
- authority/privacy/injection fixture fails;
- region/legal/commercial state is not positively verified;
- release-grade judge evidence is `SAME_CONFIG` or `UNKNOWN` where independence is required.

Required critical dimensions include as applicable:
- `BOOK_CONTRACT_FULFILLMENT`;
- `CHAPTER_CONTRACT_FULFILLMENT`;
- `SPECIFICITY_GENERICNESS`;
- `EVIDENCE_UNSUPPORTED_CLAIMS`;
- `AUTHOR_VOICE`;
- `AI_PROSE_PATHOLOGY`;
- `CONTRADICTION_INCONSISTENCY`;
- `CROSS_BOOK_COHERENCE`.

ATTENTION may remain visible for human review; BLOCKING cannot be averaged away.

### I. Manual live probe / promotion runner

Implement a bounded CLI/service operation for live M8 evidence.

Hard gate:
- live execution only when an explicit flag such as `BOOK_OS_ALLOW_LIVE_PROVIDER=1` is present;
- credential must be available from SecretStore/environment injection;
- command prints estimated/request limits before execution when calculable;
- ordinary tests/UI do not enable the flag;
- real manuscript text is not required: use a private/local or synthetic evaluation corpus as appropriate;
- public repo keeps synthetic fixtures only.

The runner:
1. discovers/probes provider/model;
2. executes bounded representative role cases;
3. records exact provider/model/version/config/usage/cost;
4. runs BookBench/role scorecards;
5. emits promotion evidence;
6. **does not self-promote**. Central Brain decides `PROMOTED` only after inspecting evidence.

### J. Fallback/unavailable API + desktop UX

Authenticated local API exposes:
- capability matrix by region;
- route decision/reasons;
- provider health/probe evidence (secret-safe);
- promoted role routes;
- structured unavailable/fallback state.

Desktop adds a minimal `Provider Lane / Availability` view:
- current product region;
- eligible providers/models/roles;
- promotion state;
- health/last verified timestamp;
- exact reason when unavailable;
- no secret values;
- no “use VPN” guidance;
- no button that silently performs paid/live eval.

### K. Backup/regression

Advance backup/schema compatibility through the new M8 migration.

Preserve M0–M7 regressions:
- authority;
- projects/contracts;
- drafting;
- Research/Claim Ledger;
- Book Memory;
- editorial workflows;
- BookBench;
- desktop/Tauri/auth;
- secret scan.

## STRICT OUT OF SCOPE

- weakening BookBench quality gates;
- automatically declaring Russia-ready because an API responds;
- hiding provider terms/commercial uncertainty;
- OpenAI as a Russian mandatory runtime or geo-circumvention;
- VPN/proxy circumvention;
- cloud accounts/billing/product subscription system;
- BOOK OS-owned multi-tenant provider brokerage launch;
- M9 Literary Master/export/audio implementation;
- M10 real-book pilot;
- auto-approval of manuscript/editorial authority;
- real private manuscript/eval data in public Git;
- live paid provider calls in normal CI;
- disabling TLS verification in production.

## TWO-STAGE ACCEPTANCE

### Stage A — IMPLEMENTATION ACCEPTANCE

Required before any live provider promotion:

1. fresh/M7 DB upgrades through the M8 migration;
2. versioned capability matrix persists exact source/verification/model/config identity;
3. `RU` policy excludes region/commercial unknown/ineligible routes by default;
4. OpenAI is not eligible as mandatory `RU` runtime;
5. Yandex generation adapter passes mocked success/structured-output/auth/error/provenance tests;
6. GigaChat mocked token-exchange/cache/strict-JSON/refusal/rate-limit/provenance tests pass;
7. production GigaChat path never uses `verify=False`;
8. Yandex/GigaChat embeddings adapters pass mocked exact-config tests and M5/M7 config gates remain intact;
9. production `RU` route requires role promotion, not merely provider health;
10. fallback never chooses ineligible/unpromoted route;
11. no quality gate is averaged/lowered;
12. live runner is explicit-flag gated and cannot run from ordinary UI/test path;
13. authenticated availability API + desktop unavailable/fallback view work;
14. backup/restore through M8 schema passes;
15. Python Ruff/mypy/pytest green;
16. TypeScript lint/type/test/build/audit green;
17. Rust cargo test/check green;
18. secret scan green;
19. normal CI external/provider/model calls = 0; paid calls = 0;
20. no M9+ scope.

Passing Stage A does **not** make M8 accepted and does **not** authorize a Russia-ready claim.

### Stage B — LIVE PROMOTION ACCEPTANCE

M8 is ACCEPTED only when:

21. at least one `RU` generation route is live-probed through a permitted commercial/provider path with exact model/config evidence;
22. required structured-output and bounded task cases execute successfully;
23. the candidate is evaluated on the exact immutable M8 evaluation dataset through BookBench;
24. at least `WRITER` and required `EDITOR` launch roles meet their role-specific critical-dimension gates with zero required `BLOCKING` dimensions/severe authority/privacy failures;
25. any release-grade judge evidence used for promotion satisfies the M7 independence rule;
26. exact usage/latency/cost and provider/model/version are recorded;
27. Central Brain explicitly records `PROMOTED` for the approved region/role/config;
28. a simulated provider outage demonstrates fallback to another already-promoted compliant route, or structured `PROVIDER_UNAVAILABLE` if no second promoted route exists;
29. the desktop/API shows the resulting promoted/unavailable state without secrets or VPN guidance;
30. full authoritative GitHub CI remains green after promotion evidence/state code changes.

If credentials, commercial access or a small live-eval budget are unavailable, stop after Stage A with `BLOCKED_LIVE_PROMOTION`; do not pretend M8 is complete.

## DELIVERY CONTRACT — CRITICAL

Codex completion text is **not delivery evidence**.

A task is considered implemented only when:
- code is physically present on the existing GitHub M8 branch;
- the PR HEAD changes to the published implementation commit;
- the changed-file scope is inspectable in GitHub;
- authoritative GitHub CI runs against that exact HEAD.

If the execution environment cannot publish to GitHub, report `BLOCKED_PUBLICATION`; do not claim PASS/complete. Do not create another PR or another M8 task to hide a publication failure.

## REPORT FORMAT

Return:
- exact baseline SHA;
- exact published HEAD SHA;
- PR number;
- changed-file summary;
- Stage A acceptance mapping 1–20;
- exact local and GitHub CI evidence;
- external/live/paid call counts;
- blockers for Stage B, if any;
- no self-ACCEPT. Central Brain owns milestone acceptance/promotion.

## UNLOCKS NEXT

Only Central Brain ACCEPT + merge of full M8 (Stage A + Stage B) unlocks M9 — Literary Master + exports.
