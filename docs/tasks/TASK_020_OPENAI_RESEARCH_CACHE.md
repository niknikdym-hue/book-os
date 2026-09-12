# TASK 020 — OPENAI WEB RESEARCH + PROMPT CACHE

**Status:** IN IMPLEMENTATION  
**Milestone:** Production technical strengthening  
**Owner:** BOOK OS Central Brain  
**Date:** 2026-09-10

## Goal

Add only the OpenAI platform capabilities already accepted for the launch path that close current BOOK OS gaps or materially improve production economics without weakening governance.

## In scope

1. Bounded OpenAI web-source discovery in the native Research Engine.
2. Source-only normalization into `ResearchCandidate`; model prose is ignored for Evidence purposes.
3. Default native research enrichment of the existing OpenAlex/Crossref/Semantic Scholar search.
4. Production OpenAI prompt caching keyed by model + prompt hash + exact authority revision identity, with an explicit reusable authority breakpoint before dynamic task content.
5. Cache-aware conservative preflight cost guard and usage audit.
6. Deterministic tests with mocked HTTP; provider/model paid calls in tests/CI = 0.

## Explicitly out of scope

- Function calling/tool side effects;
- MCP;
- OpenAI Skills;
- File Search replacement for Book Memory;
- image/audio generation;
- autonomous research loops;
- any authority or approval changes.

## Web research bounds

- model: `gpt-5.6-luna`;
- hosted tool: current Responses API `web_search`;
- search context: low;
- maximum hosted tool calls per research action: 1;
- maximum model output: 128 tokens;
- model reasoning: none;
- returned BOOK OS objects: source identities/URLs only.

## Prompt-cache contract

- production native OpenAI adapter only;
- `prompt_cache_options.mode = explicit`;
- `prompt_cache_options.ttl = 30m`;
- explicit cache breakpoint after stable authority payload and before changing section objective/untrusted/task payload;
- cache key contains hashes/identities only, never manuscript text or secrets;
- exact authority revision change changes cache identity;
- cost preflight assumes cache-write rate on input, not a best-case cache hit;
- cached/cache-write token counts remain visible in usage when provider returns them.

## Acceptance

1. Native app composes the production OpenAI adapter and web research gateway.
2. Existing explicit narrow research-provider selection remains narrow.
3. Existing default scholarly research is enriched with web discovery.
4. Duplicate web URLs are normalized/deduplicated.
5. Model-generated prose is never imported as a source/evidence excerpt.
6. Prompt-cache key and authority prefix are stable across different section objectives when prompt + authority identity/context are unchanged.
7. Dynamic section/task content remains outside the reusable authority cache boundary.
8. Prompt-cache key changes when authority revision identity changes.
9. Cache-aware cost audit distinguishes uncached, cached and cache-write input tokens.
10. No secret appears in request body/cache key.
11. Canonical exact-head CI is green before merge.

## Merge gate

Draft PR only until exact-head CI is green and Central Brain review confirms no research-governance or cost-guard regression.
