# BOOK OS — OWNER DECISION: OPENAI WEB RESEARCH + PROMPT CACHE

**Status:** ACCEPTED / OWNER DECISION  
**Version:** 1.1  
**Date:** 2026-09-09  
**Scope:** Research Engine, production OpenAI execution lane

## Decision

BOOK OS may use current OpenAI platform capabilities only when they materially strengthen the existing product architecture. This decision admits two capabilities now:

1. bounded OpenAI Web Search as an additional source-discovery adapter for the Research Engine;
2. prompt caching for repeated stable OpenAI book context.

Function calling, MCP, Skills, image generation and other platform capabilities are not admitted by this decision merely because they exist.

## Web research contract

OpenAI Web Search is a discovery layer only. It must not bypass the existing BOOK OS chain:

`Research Question → Source Discovery → Source Import/Inspection → Claim → Evidence → Human/Fact-check Decision`.

The adapter may import source identities/URLs returned by the hosted web-search tool. Model prose, summaries or citations that merely look plausible are not Evidence and cannot mark a claim verified.

The production search is intentionally bounded:

- one hosted web-search call per explicit research action;
- current Responses API `web_search` tool, not the legacy `web_search_preview` integration;
- low search context;
- cost-sensitive GPT-5.6 Luna discovery model rather than GPT-6 Astra;
- small output budget;
- no autonomous research loop;
- no authority writes or approvals.

GPT-6 Astra remains available for high-value authoring/editorial reasoning; using Astra for simple source discovery would waste cost without improving the governance model.

## Prompt-cache contract

Production OpenAI book operations use provider prompt caching to reduce repeated-input cost for stable BOOK OS context.

The cache key is derived from non-secret identities only:

- model id;
- canonical prompt hash;
- exact authority revision hashes/types.

It must not contain manuscript text, API secrets or personal identifiers.

For production book operations, BOOK OS places an explicit cache breakpoint after the stable authority payload and before the changing section objective/untrusted/task payload. The cache therefore targets the reusable authority prefix rather than merely routing requests with a stable cache key.

Changing an authority revision changes the cache identity. Prompt caching never changes authority semantics, approval rights, quality gates or model-output acceptance.

Cost preflight must remain conservative: because a cache miss may incur cache-write pricing, the upper bound uses the cache-write rate rather than assuming a cache hit. Usage/provenance retains the provider's cached/cache-write token details when available.

## Official provider facts verified 2026-09-09

OpenAI documentation currently confirms:

- GPT-6 Astra supports Responses API web search and prompt caching;
- GPT-5.6 Luna supports Responses API web search and reasoning effort `none`;
- Responses supports the current `web_search` tool, source inclusion through `web_search_call.action.sources`, `max_tool_calls`, `prompt_cache_key`, explicit `prompt_cache_breakpoint`, and `prompt_cache_options`;
- current prompt-cache TTL option is `30m`;
- cache writes are billed at 1.25x uncached input token rate and cached input at 0.1x for GPT-5.6 and later;
- web search is billed per web run plus applicable search-content/model tokens.

Provider facts are dated evidence and may require a later implementation update if OpenAI changes the contract.

## Governance invariants

Neither web search nor prompt caching may:

- write or approve Book/Series authority;
- skip stages or quality gates;
- convert discovered URLs into verified Evidence without inspection;
- silently change the selected executor/work level;
- create unbounded autonomous paid loops;
- expose secrets in requests, cache keys, logs or provenance.

## Change log

- **1.1 — 2026-09-09:** moved the new integration from legacy `web_search_preview` to current `web_search` and required an explicit reusable authority cache boundary before dynamic task content.
- **1.0 — 2026-09-09:** admitted bounded OpenAI web discovery and production prompt caching as concrete technical strengthening; explicitly deferred unrelated platform features.
