from __future__ import annotations

from typing import Any
import json

import httpx
from pydantic import BaseModel, ValidationError

from .model_gateway import (
    BookArchitectureProposalOutput,
    BookBenchJudgeOutput,
    BookBenchPairwiseOutput,
    BookContractProposalOutput,
    ChapterContractProposalOutput,
    ModelAdapterResult,
    ModelBudgetError,
    ModelOutputError,
    ModelProviderError,
    ModelTaskRequest,
    OpenAIResponsesAdapter,
    SectionDraftOutput,
)
from .prompts import PromptTemplate
from .secrets import SecretStore


class BookOSOpenAIResponsesAdapter(OpenAIResponsesAdapter):
    """OpenAI adapter with the current BOOK OS model/price registry."""

    provider_name = "openai"
    _PRICING_SOURCE_DATE = "2026-09-06"
    _PRICING_USD_PER_MILLION = {
        "gpt-6-astra": (10.0, 50.0),
        "gpt-5.6-sol": (4.0, 20.0),
        "gpt-5.6": (4.0, 20.0),
        "gpt-5.6-terra": (2.0, 12.0),
        "gpt-5.6-luna": (0.2, 1.2),
    }


class YandexChatCompletionsAdapter:
    """Yandex AI Studio adapter through its OpenAI-compatible Chat Completions API."""

    provider_name = "yandex"
    _PRICING_SOURCE_DATE = "2026-09-06"
    # Current synchronous prices converted from USD / 1K tokens to USD / 1M tokens.
    _PRICING_USD_PER_MILLION: dict[str, tuple[float, float]] = {
        "aliceai-llm": (4.09836, 9.836064),
        "aliceai-llm-flash": (0.819672, 1.639344),
        "yandexgpt-5.1": (6.557376, 6.557376),
        "yandexgpt-5-pro": (9.836064, 9.836064),
        "yandexgpt-5-lite": (1.639344, 1.639344),
    }
    _INPUT_TOKEN_OVERHEAD = 4096

    def __init__(
        self,
        secret_store: SecretStore,
        *,
        client: httpx.Client | None = None,
        endpoint: str = "https://ai.api.cloud.yandex.net/v1/chat/completions",
        timeout_seconds: float = 90.0,
    ) -> None:
        self._secret_store = secret_store
        self._client = client or httpx.Client(timeout=timeout_seconds)
        self._endpoint = endpoint
        self._timeout_seconds = timeout_seconds

    @staticmethod
    def _output_type(task_type: str) -> type[BaseModel]:
        if task_type == "BOOK_CONTRACT_PROPOSAL":
            return BookContractProposalOutput
        if task_type == "ARCHITECTURE_PROPOSAL":
            return BookArchitectureProposalOutput
        if task_type == "CHAPTER_CONTRACT_PROPOSAL":
            return ChapterContractProposalOutput
        if task_type == "BOOKBENCH_JUDGE":
            return BookBenchJudgeOutput
        if task_type == "BOOKBENCH_PAIRWISE":
            return BookBenchPairwiseOutput
        return SectionDraftOutput

    @classmethod
    def _model_key(cls, model: str) -> str:
        if model.startswith("gpt://"):
            remainder = model[len("gpt://") :]
            parts = remainder.split("/", 1)
            if len(parts) != 2 or not parts[1]:
                raise ModelProviderError("invalid Yandex model URI")
            return parts[1].removesuffix("/latest")
        return model.strip().removesuffix("/latest")

    @classmethod
    def _pricing(cls, model: str) -> tuple[float, float]:
        key = cls._model_key(model)
        try:
            return cls._PRICING_USD_PER_MILLION[key]
        except KeyError as exc:
            raise ModelBudgetError(
                f"cost cap cannot be enforced for unpriced Yandex model: {model}"
            ) from exc

    def _resolved_model_uri(self, model: str, folder_id: str) -> str:
        if model.startswith("gpt://"):
            return model
        key = self._model_key(model)
        if key not in self._PRICING_USD_PER_MILLION:
            raise ModelProviderError(f"unsupported Yandex model: {model}")
        return f"gpt://{folder_id}/{key}"

    def _body(
        self,
        request: ModelTaskRequest,
        prompt: PromptTemplate,
        resolved_model_uri: str,
    ) -> dict[str, Any]:
        user_payload = {
            "task_type": request.task_type,
            "section_objective": request.section_objective,
            "authority_inputs": [item.model_dump(mode="json") for item in request.authority_inputs],
            "authoritative_context": request.authoritative_context,
            "untrusted_context": request.untrusted_context,
            "task_payload": request.task_payload,
        }
        schema = OpenAIResponsesAdapter.output_schema(request.task_type)
        return {
            "model": resolved_model_uri,
            "messages": [
                {"role": "system", "content": prompt.developer_text},
                {
                    "role": "user",
                    "content": json.dumps(user_payload, ensure_ascii=False, sort_keys=True),
                },
            ],
            "max_tokens": request.max_output_tokens,
            "temperature": 0.2,
            "stream": False,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": request.task_type.casefold(),
                    "strict": True,
                    "schema": schema,
                },
            },
        }

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
        preflight_upper_bound_usd = (
            input_token_upper_bound * input_price + request.max_output_tokens * output_price
        ) / 1_000_000
        if preflight_upper_bound_usd > request.max_cost_usd:
            raise ModelBudgetError(
                "worst-case Yandex request cost "
                f"${preflight_upper_bound_usd:.6f} exceeds cap ${request.max_cost_usd:.6f}"
            )
        return {
            "max_cost_usd": request.max_cost_usd,
            "preflight_upper_bound_usd": round(preflight_upper_bound_usd, 6),
            "input_token_upper_bound": input_token_upper_bound,
            "max_output_tokens": request.max_output_tokens,
            "input_usd_per_million": input_price,
            "output_usd_per_million": output_price,
            "pricing_source_date": cls._PRICING_SOURCE_DATE,
        }

    @staticmethod
    def _choice_content(payload: dict[str, Any]) -> str:
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ModelOutputError("Yandex response contains no choices")
        first = choices[0]
        if not isinstance(first, dict):
            raise ModelOutputError("Yandex response choice is invalid")
        message = first.get("message")
        if not isinstance(message, dict):
            raise ModelOutputError("Yandex response contains no message")
        content = message.get("content")
        if not isinstance(content, str) or not content:
            raise ModelOutputError("Yandex response contains no message content")
        return content

    @classmethod
    def _usage_with_cost_guard(
        cls,
        usage: object,
        guard: dict[str, Any] | None,
        resolved_model_uri: str,
    ) -> dict[str, Any]:
        raw = dict(usage) if isinstance(usage, dict) else {}
        input_tokens = raw.get("prompt_tokens")
        output_tokens = raw.get("completion_tokens")
        result: dict[str, Any] = {
            **raw,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "resolved_model_uri": resolved_model_uri,
        }
        if guard is None:
            return result
        audited = dict(guard)
        if (
            isinstance(input_tokens, (int, float))
            and not isinstance(input_tokens, bool)
            and isinstance(output_tokens, (int, float))
            and not isinstance(output_tokens, bool)
        ):
            estimated = (
                float(input_tokens) * float(guard["input_usd_per_million"])
                + float(output_tokens) * float(guard["output_usd_per_million"])
            ) / 1_000_000
            audited["estimated_actual_cost_usd"] = round(estimated, 6)
        result["cost_guard"] = audited
        return result

    def generate(self, request: ModelTaskRequest, prompt: PromptTemplate) -> ModelAdapterResult:
        api_key = self._secret_store.get_secret("yandex_ai_studio_api_key")
        folder_id = self._secret_store.get_secret("yandex_folder_id")
        resolved_model_uri = self._resolved_model_uri(request.model, folder_id)
        body = self._body(request, prompt, resolved_model_uri)
        guard = self._budget_guard(request, body)
        response = self._client.post(
            self._endpoint,
            headers={
                "Authorization": f"Api-Key {api_key}",
                "OpenAI-Project": folder_id,
                "Content-Type": "application/json",
            },
            json=body,
            timeout=self._timeout_seconds,
        )
        if response.status_code >= 400:
            raise ModelProviderError(f"Yandex AI Studio HTTP {response.status_code}")
        payload = response.json()
        if not isinstance(payload, dict):
            raise ModelOutputError("Yandex response JSON must be an object")
        try:
            parsed = json.loads(self._choice_content(payload))
        except json.JSONDecodeError as exc:
            raise ModelOutputError("Yandex structured output is not JSON") from exc
        if not isinstance(parsed, dict):
            raise ModelOutputError("Yandex structured output must be an object")
        try:
            validated = self._output_type(request.task_type).model_validate(parsed)
        except ValidationError as exc:
            raise ModelOutputError("Yandex structured output failed schema validation") from exc
        usage = self._usage_with_cost_guard(payload.get("usage"), guard, resolved_model_uri)
        return ModelAdapterResult(
            provider_run_id=str(payload["id"]) if payload.get("id") is not None else None,
            output=validated.model_dump(mode="json"),
            usage=usage,
        )
