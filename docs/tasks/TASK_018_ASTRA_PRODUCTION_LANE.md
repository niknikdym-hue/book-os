# TASK 018 — GPT-6 ASTRA PRODUCTION LANE

**Status:** READY  
**Milestone:** Real-book pilot preflight  
**Owner:** BOOK OS Central Brain  
**Execution role:** Codex

## WHY NOW

The first production pilot book is being prepared and the Owner reports materially stronger book-quality results from GPT-6 Astra in a separate clean-restart series project. BOOK OS already registers `gpt-6-astra` and Auto-routes Book Contract / Architecture to it, but the OpenAI cost guard does not yet register Astra pricing, so a fail-closed paid call with mandatory `max_cost_usd` is not production-ready.

This task closes only the Astra execution lane. It does not authorize a paid call.

## BASELINE

- Repository: `niknikdym-hue/book-os`
- Exact baseline main: `c6504fb70cc65abef9753e2be03da0b610bd8451`
- Branch: `brain/task-018-astra-production-lane`
- Current OpenAI endpoint: Responses API.
- Astra is already present in `model_routing.PROVIDERS`; preserve that behavior.

## CURRENT OFFICIAL OPENAI FACTS TO ENCODE

Verified 2026-09-07 from official OpenAI API docs:

- model id: `gpt-6-astra`;
- Responses API supported;
- input price: USD 10 / 1M tokens;
- cached input: USD 1 / 1M tokens (do not use cached-input assumptions in the conservative preflight cap unless the current guard explicitly proves cache applicability);
- output price: USD 50 / 1M tokens;
- prompts above 272K input tokens: 2x input/cache and 1.5x output for the full request;
- context window 1.05M; max output 128K;
- reasoning efforts supported: `low | medium | high | xhigh | max`; `none` is not supported.

Pricing/source date must be explicit and auditable.

## GOAL

Make GPT-6 Astra a safe, fully bounded BOOK OS OpenAI production executor for high-value book operations while preserving explicit Owner cost approval and zero-call preflight.

## IN SCOPE

1. Add `gpt-6-astra` to OpenAI conservative pricing/cost-cap logic.
2. Reuse the existing >272K long-context multipliers and prove they apply to Astra.
3. Add deterministic zero-HTTP tests for:
   - normal Astra request under cap;
   - Astra request over cap rejects before HTTP;
   - >272K Astra request uses long-context price tier and rejects before HTTP when over cap;
   - unknown/unpriced OpenAI model remains fail-closed when a cost cap is required.
4. Add an explicit operation-level Astra reasoning policy for high-value professional book work without creating a model monopoly. Minimum desired initial policy:
   - `BOOK_CONTRACT_PROPOSAL`: Astra, reasoning `high` or stronger;
   - `ARCHITECTURE_PROPOSAL`: Astra, reasoning `high` or stronger;
   - `SECTION_DRAFT`: keep current Auto model routing globally, but when the human manually selects/pins Astra, default the Astra reasoning profile to `high` unless the human explicitly chooses another supported effort;
   - `xhigh` / `max`: available for bounded exceptional operations such as difficult architecture rework, adversarial review, whole-book diagnosis or another explicitly justified high-complexity operation; they are not the default for every chapter;
   - evaluation/adversarial/editorial operations must remain separately routable and must not be silently forced to Astra.
5. Preserve the existing manual operation pin and whole-book pin. The first real production pilot is expected to use a HUMAN whole-book Astra pin after this task is accepted, but this must remain an explicit project setting, not hard-coded product behavior.
6. If the current request schema has no reasoning field, add the smallest auditable field/policy necessary so the OpenAI Responses request actually carries the selected reasoning effort. Persist/return enough provenance to know which effort was used.
7. Zero-call preflight must be able to report that `gpt-6-astra` is registered/configured and whether the OpenAI credential is available, without revealing the secret and without calling OpenAI.
8. Preserve existing fresh explicit paid permission and positive per-request `max_cost_usd` behavior.

## OUT OF SCOPE

- No paid/model/provider calls in implementation or CI.
- No SMM manuscript generation.
- No hard-coded book or series content.
- No runtime dependency on `books-for-litres` or any external project branch.
- No provider expansion beyond existing architecture.
- No change making Astra the only Writer/Editor/Judge.
- No secret value in GitHub, logs, tests or comments.

## EVIDENCE FROM THE SEPARATE CLEAN-RESTART BOOK PROJECT

The separate branch `brain/services-series-clean-restart-20260907` is reference evidence only, not BOOK OS authority and not a runtime dependency.

Useful transferable evidence as of 2026-09-07:

- Astra `High` was used successfully for sequential long-form chapter work and was explicitly preferred for continued drafting;
- `xhigh` / `Max` were reserved for targeted harder operations rather than used continuously;
- chapter production paired long-form drafting with separate research/source records and a practical specification, reinforcing the existing BOOK OS chapter-admission/evidence approach.

BOOK OS absorbs only the generic lesson: `Astra High` is a credible default reasoning profile when Astra is intentionally chosen for long-form professional prose, while stronger efforts should be used selectively and recorded as provenance.

## QUALITY / ROUTING PRINCIPLE

Astra is preferred where current evidence says it materially improves complex book-quality work, but BOOK OS keeps operation-level routing. The governing rule remains: **best executor for the editorial operation**, not one model for the whole system unless the human explicitly uses the existing whole-book manual pin.

## ACCEPTANCE

1. Official Astra pricing is encoded with source date and conservative fail-closed behavior.
2. Astra >272K pricing tier is tested before HTTP.
3. Astra reasoning effort is actually emitted in the Responses API body and covered by deterministic tests.
4. Manual operation/book Astra pins remain valid and auditable.
5. Auto Book Contract/Architecture Astra routing remains green.
6. Manual whole-book Astra pin yields Astra `high` for long-form drafting unless the human explicitly selects another supported effort.
7. Existing Sol/Terra/Luna cost guards remain green.
8. Zero-call credential/config preflight is secret-safe.
9. Full backend tests green; ruff/mypy green; frontend tests/typecheck/lint green where touched; cargo/CI canonical jobs green.
10. Provider/model/paid calls in tests/CI = 0.
11. No weakening of Task 014/017 fail-closed gates, authority, anti-junk, Keychain, Literary Master or pilot evidence.

## DELIVERABLE

Push implementation to this same branch/PR. Do not merge or self-accept. If push is unavailable, return `NOT_PUSHED` plus a complete directly-applicable diff in GitHub-visible comments, split if needed, with exact final HEAD and SHA-256.

The first real paid Astra request is a separate Owner financial gate after this task is accepted.