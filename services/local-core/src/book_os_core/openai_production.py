from __future__ import annotations

import hashlib
import json
from typing import Any

from .model_gateway import ModelTaskRequest
from .prompts import PromptTemplate
from .provider_adapters import BookOSOpenAIResponsesAdapter


class OpenAIProductionResponsesAdapter(BookOSOpenAIResponsesAdapter):
    """BOOK OS production OpenAI lane with stable prompt caching and cache-aware cost audit."""

    _PRICING_SOURCE_DATE = "2026-09-09"
    _PROMPT_CACHE_TTL = "30m"
    _CACHED_INPUT_MULTIPLIER = 0.10
    _CACHE_WRITE_MULTIPLIER = 1.25

    @classmethod
    def _prompt_cache_key(cls, request: ModelTaskRequest) -> str:
        authority_identity = sorted(
            (
                item.entity_type,
                item.revision_hash,
            )
            for item in request.authority_inputs
        )
        material = json.dumps(
            {
                "model": request.model,
                "prompt_hash": request.prompt_hash,
                "authority": authority_identity,
            },
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest = hashlib.sha256(material).hexdigest()[:48]
        return f"book-os:{digest}"

    def _body(self, request: ModelTaskRequest, prompt: PromptTemplate) -> dict[str, Any]:
        body = super()._body(request, prompt)
        body["prompt_cache_key"] = self._prompt_cache_key(request)
        body["prompt_cache_options"] = {"ttl": self._PROMPT_CACHE_TTL}
        return body

    @classmethod
    def _budget_guard(
        cls,
        request: ModelTaskRequest,
        body: dict[str, Any],
    ) -> dict[str, Any] | None:
        if request.max_cost_usd is None:
            return None
        input_price, output_price = cls._pricing(request.model)
        serialized = json.dumps(
            body, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        input_token_upper_bound = len(serialized) + cls._INPUT_TOKEN_OVERHEAD
        long_context_pricing = input_token_upper_bound > cls._LONG_CONTEXT_INPUT_TOKEN_THRESHOLD
        context_multiplier = (
            cls._LONG_CONTEXT_INPUT_PRICE_MULTIPLIER if long_context_pricing else 1.0
        )
        output_multiplier = (
            cls._LONG_CONTEXT_OUTPUT_PRICE_MULTIPLIER if long_context_pricing else 1.0
        )

        uncached_input_price = input_price * context_multiplier
        cached_input_price = input_price * cls._CACHED_INPUT_MULTIPLIER * context_multiplier
        cache_write_price = input_price * cls._CACHE_WRITE_MULTIPLIER * context_multiplier
        effective_output_price = output_price * output_multiplier

        # A cache miss may write the eligible prefix. Cache writes cost more than ordinary
        # uncached input, so use the cache-write rate for the preflight upper bound.
        preflight_upper_bound_usd = (
            input_token_upper_bound * cache_write_price
            + request.max_output_tokens * effective_output_price
        ) / 1_000_000
        if preflight_upper_bound_usd > request.max_cost_usd:
            raise cls._budget_error(
                preflight_upper_bound_usd=preflight_upper_bound_usd,
                max_cost_usd=request.max_cost_usd,
            )

        reasoning = body.get("reasoning")
        return {
            "max_cost_usd": request.max_cost_usd,
            "preflight_upper_bound_usd": round(preflight_upper_bound_usd, 6),
            "input_token_upper_bound": input_token_upper_bound,
            "max_output_tokens": request.max_output_tokens,
            "input_usd_per_million": uncached_input_price,
            "cached_input_usd_per_million": cached_input_price,
            "cache_write_usd_per_million": cache_write_price,
            "output_usd_per_million": effective_output_price,
            "long_context_pricing": long_context_pricing,
            "long_context_input_token_threshold": cls._LONG_CONTEXT_INPUT_TOKEN_THRESHOLD,
            "reasoning_effort": (reasoning.get("effort") if isinstance(reasoning, dict) else None),
            "prompt_cache_key": body.get("prompt_cache_key"),
            "prompt_cache_ttl": cls._PROMPT_CACHE_TTL,
            "pricing_source_date": cls._PRICING_SOURCE_DATE,
        }

    @staticmethod
    def _budget_error(*, preflight_upper_bound_usd: float, max_cost_usd: float) -> Exception:
        from .model_gateway import ModelBudgetError

        return ModelBudgetError(
            "worst-case OpenAI request cost "
            f"${preflight_upper_bound_usd:.6f} exceeds cap ${max_cost_usd:.6f}"
        )

    @classmethod
    def _usage_with_cost_guard(
        cls,
        usage: object,
        guard: dict[str, Any] | None,
    ) -> dict[str, Any]:
        result = dict(usage) if isinstance(usage, dict) else {}
        if guard is None:
            return result

        audited = dict(guard)
        input_tokens = result.get("input_tokens")
        output_tokens = result.get("output_tokens")
        details = result.get("input_tokens_details")
        cached_tokens = details.get("cached_tokens", 0) if isinstance(details, dict) else 0
        cache_write_tokens = (
            details.get("cache_write_tokens", 0) if isinstance(details, dict) else 0
        )

        numeric_input = isinstance(input_tokens, (int, float)) and not isinstance(
            input_tokens, bool
        )
        numeric_output = isinstance(output_tokens, (int, float)) and not isinstance(
            output_tokens, bool
        )
        numeric_cached = isinstance(cached_tokens, (int, float)) and not isinstance(
            cached_tokens, bool
        )
        numeric_write = isinstance(cache_write_tokens, (int, float)) and not isinstance(
            cache_write_tokens, bool
        )

        if numeric_input and numeric_output:
            input_count = max(0.0, float(input_tokens))
            output_count = max(0.0, float(output_tokens))
            if numeric_cached and numeric_write:
                assert isinstance(cached_tokens, (int, float)) and not isinstance(
                    cached_tokens, bool
                )
                assert isinstance(cache_write_tokens, (int, float)) and not isinstance(
                    cache_write_tokens, bool
                )
                cached_count = max(0.0, float(cached_tokens))
                write_count = max(0.0, float(cache_write_tokens))
                uncached_count = max(0.0, input_count - cached_count - write_count)
            else:
                cached_count = 0.0
                write_count = input_count
                uncached_count = 0.0

            estimated = (
                uncached_count * float(guard["input_usd_per_million"])
                + cached_count * float(guard["cached_input_usd_per_million"])
                + write_count * float(guard["cache_write_usd_per_million"])
                + output_count * float(guard["output_usd_per_million"])
            ) / 1_000_000
            audited["estimated_actual_cost_usd"] = round(estimated, 6)
            audited["uncached_input_tokens"] = int(uncached_count)
            audited["cached_input_tokens"] = int(cached_count)
            audited["cache_write_tokens"] = int(write_count)

        result["cost_guard"] = audited
        return result
