# BOOK OS — MODEL GATEWAY v0.1

**Status:** ACCEPTED FOR V0.1 IMPLEMENTATION  
**Version:** 0.1.0  
**Date:** 2026-08-22

## 1. Purpose

BOOK OS routes **tasks**, not brands. A model/provider is an execution resource selected by capability, BookBench results, region, privacy, cost and availability.

No model name is architectural authority.

## 2. Gateway inputs

A `ModelTaskRequest` must include at minimum:

- task/role: e.g. `ARCHITECT`, `DRAFT_SECTION`, `DEV_EDIT`, `FACT_ANALYZE`, `STYLE_JUDGE`;
- exact authority/context references;
- required output schema;
- language;
- quality tier;
- region/provider-policy context;
- privacy/data-sensitivity class;
- maximum budget/cost policy;
- latency class;
- allowed tools;
- idempotency key;
- prompt-template version/hash.

## 3. Provider adapter interface

Every provider adapter must normalize:

- structured text generation;
- streaming when supported;
- tool/function calling capability metadata;
- max context/output limits;
- usage/token/cost accounting;
- retryable vs terminal errors;
- request/response IDs;
- data-retention/logging controls when exposed;
- model/version identity;
- provider-specific safety/refusal outcomes.

Provider-specific SDK objects must not leak into core domain logic.

## 4. Capability matrix

Gateway maintains versioned metadata per model/configuration:

- provider;
- model ID/version;
- supported regions/legal path;
- context/output limits;
- structured-output reliability;
- tool support;
- multilingual/Russian quality;
- BookBench role scores;
- latency percentiles;
- input/output cost;
- privacy/data handling flags;
- current availability/health;
- allowed BOOK OS roles.

## 5. Routing order

A request is routed by hard constraints first, then quality/cost preference:

1. regional/legal availability;
2. privacy/data-policy compatibility;
3. required capability/schema/tool support;
4. minimum BookBench score for task role;
5. user/project quality tier;
6. cost/latency optimization;
7. health/fallback policy.

A cheaper model is not selected when it falls below the role's quality floor.

## 6. Initial provider plan

### Owner development lane

- OpenAI adapter first, because an OpenAI API credential/path on the Owner's Mac has already been proven in another local project.
- Use current Responses API / structured outputs via the official SDK, behind our adapter.
- This is a development/benchmark lane, not a guarantee for Russian end-user runtime.

### Russia product lane

Implement and benchmark at least:

- Yandex Cloud AI Studio text generation + embeddings capabilities;
- GigaChat generation + embeddings capabilities.

The product may use one or both depending on BOOK OS eval results and commercial/provider terms.

### International benchmark/optional lanes

- Anthropic Claude API;
- Google Gemini API;
- future frontier/open-weight providers that pass internal evals.

These remain optional until their value is demonstrated on BOOK OS datasets.

## 7. Russia/no-VPN invariant

For a user in Russia:

- BOOK OS must not require VPN;
- BOOK OS must not require a personal ChatGPT/Claude/Gemini subscription;
- BOOK OS must not require the user to bring an OpenAI/other foreign API key;
- BOOK OS does not circumvent provider geographic/contractual restrictions;
- unsupported providers are excluded by routing policy;
- at least one compliant provider/self-hosted path must pass the minimum BOOK OS quality bar before the product is declared Russia-ready.

As of 2026-08-22, OpenAI's official API-supported-country page states that access/offering access outside listed countries may lead to suspension, and Russia is not on that list. Therefore OpenAI cannot be the mandatory Russian runtime path.

## 8. Prompt/template registry

Prompts are versioned product assets, not anonymous strings embedded throughout code.

Each template has:

- stable template ID;
- semantic version/hash;
- role;
- required input schema;
- required output schema;
- allowed tools;
- evaluation dataset/run references;
- change history.

A prompt/model change that affects critical role behavior must be re-evaluated before production promotion.

## 9. Structured outputs

Core workflows should prefer schema-constrained structured output for findings, claims, contracts, routing and proposals. Free prose is permitted for manuscript drafting/literary output, but surrounding metadata remains structured.

Validation uses local typed schemas; invalid output is not silently accepted.

## 10. Retries, idempotency and failures

- side-effect-free inference calls may retry transient failures with bounded exponential backoff;
- each task has an idempotency key and persisted run record;
- retry never creates two accepted proposals;
- provider outage may trigger a configured fallback only if fallback meets all hard constraints;
- provider switch is logged in provenance;
- a structured failure is better than silently degrading quality below threshold.

## 11. Cost control

Every call records:

- estimated/actual input-output usage;
- provider/model;
- task type;
- project/book;
- latency;
- cost where calculable.

Budgets exist at task, project and provider levels. Paid/expensive evaluation runs require explicit execution flags in development and should not be triggered by ordinary UI refreshes.

## 12. Evaluation-driven model assignment

Model roles are promoted through BOOK OS datasets:

`representative tasks → model outputs → deterministic checks + blind pairwise/rubric judging + human labels → role scorecard`.

Public leaderboards are discovery signals only. Internal performance on actual editorial tasks is authority.

## 13. Current official API facts validated 2026-08-22

- OpenAI Responses API supports model responses, structured output/tooling and usage accounting: `https://developers.openai.com/api/reference/`
- Anthropic exposes a Messages API and model/rate-limit/region documentation: `https://platform.claude.com/docs/`
- Gemini currently exposes the Interactions API and stable `v1` core API path: `https://ai.google.dev/gemini-api/docs`
- Yandex Cloud AI Studio exposes REST/gRPC text generation and embeddings APIs: `https://yandex.cloud/en/docs/overview/api`
- GigaChat exposes generation/model/embedding REST APIs at `https://api.giga.chat`: `https://developers.sber.ru/docs/ru/gigachat/api/main`
- OpenAI supported countries policy: `https://help.openai.com/en/articles/5347006-openai-api-supported-countries-and-territories`
