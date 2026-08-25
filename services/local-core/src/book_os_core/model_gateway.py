from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol
import json

import httpx
from pydantic import BaseModel, Field, ValidationError

from .prompts import PromptTemplate
from .secrets import SecretStore


class ModelProviderError(RuntimeError):
    pass


class ModelOutputError(RuntimeError):
    pass


class ModelBudgetError(RuntimeError):
    pass


class AuthorityInputRef(BaseModel):
    revision_id: str
    revision_hash: str
    entity_type: str


class SectionDraftOutput(BaseModel):
    text: str = Field(min_length=1)
    notes: list[str] = Field(default_factory=list)


class ModelTaskRequest(BaseModel):
    task_id: str
    task_type: Literal["SECTION_DRAFT"]
    role: Literal["WRITER"]
    provider: str
    model: str
    prompt_id: str
    prompt_version: str
    prompt_hash: str
    section_objective: str = Field(min_length=1, max_length=4000)
    authority_inputs: list[AuthorityInputRef] = Field(min_length=1)
    authoritative_context: dict[str, Any]
    untrusted_context: list[str] = Field(default_factory=list)
    max_output_tokens: int = Field(default=3500, ge=100, le=12000)
    max_cost_usd: float | None = Field(default=None, ge=0)


@dataclass(frozen=True)
class ModelAdapterResult:
    provider_run_id: str | None
    output: dict[str, Any]
    usage: dict[str, Any]


class ModelAdapter(Protocol):
    provider_name: str

    def generate(self, request: ModelTaskRequest, prompt: PromptTemplate) -> ModelAdapterResult:
        ...


class ModelGateway:
    def __init__(self, adapters: dict[str, ModelAdapter]):
        self._adapters = dict(adapters)

    def generate(self, request: ModelTaskRequest, prompt: PromptTemplate) -> ModelAdapterResult:
        try:
            adapter = self._adapters[request.provider]
        except KeyError as exc:
            raise ModelProviderError(f"provider is not configured: {request.provider}") from exc
        return adapter.generate(request, prompt)


class DeterministicFakeAdapter:
    provider_name = "fake"

    def __init__(
        self,
        *,
        mode: Literal["success", "malformed", "provider_error", "budget_error"] = "success",
    ) -> None:
        self.mode = mode
        self.last_request: ModelTaskRequest | None = None

    def generate(self, request: ModelTaskRequest, prompt: PromptTemplate) -> ModelAdapterResult:
        self.last_request = request
        if self.mode == "provider_error":
            raise ModelProviderError("deterministic provider failure")
        if self.mode == "budget_error":
            raise ModelBudgetError("deterministic budget guard failure")
        if self.mode == "malformed":
            return ModelAdapterResult(
                provider_run_id="fake-malformed",
                output={"notes": ["missing required text"]},
                usage={"input_tokens": 10, "output_tokens": 2},
            )
        return ModelAdapterResult(
            provider_run_id="fake-success",
            output={
                "text": f"Draft for: {request.section_objective}",
                "notes": ["deterministic fake adapter"],
            },
            usage={"input_tokens": 100, "output_tokens": 40},
        )


class OpenAIResponsesAdapter:
    provider_name = "openai"

    def __init__(
        self,
        secret_store: SecretStore,
        *,
        client: httpx.Client | None = None,
        endpoint: str = "https://api.openai.com/v1/responses",
        timeout_seconds: float = 90.0,
    ) -> None:
        self._secret_store = secret_store
        self._client = client or httpx.Client(timeout=timeout_seconds)
        self._endpoint = endpoint
        self._timeout_seconds = timeout_seconds

    @staticmethod
    def output_schema() -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {"type": "string", "minLength": 1},
                "notes": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["text", "notes"],
            "additionalProperties": False,
        }

    def _body(self, request: ModelTaskRequest, prompt: PromptTemplate) -> dict[str, Any]:
        user_payload = {
            "task_type": request.task_type,
            "section_objective": request.section_objective,
            "authority_inputs": [item.model_dump(mode="json") for item in request.authority_inputs],
            "authoritative_context": request.authoritative_context,
            "untrusted_context": request.untrusted_context,
        }
        return {
            "model": request.model,
            "store": False,
            "input": [
                {
                    "role": "developer",
                    "content": [{"type": "input_text", "text": prompt.developer_text}],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": json.dumps(user_payload, ensure_ascii=False, sort_keys=True),
                        }
                    ],
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "section_draft",
                    "strict": True,
                    "schema": self.output_schema(),
                }
            },
            "max_output_tokens": request.max_output_tokens,
        }

    @staticmethod
    def _output_text(payload: dict[str, Any]) -> str:
        direct = payload.get("output_text")
        if isinstance(direct, str) and direct:
            return direct
        for output in payload.get("output", []):
            if not isinstance(output, dict):
                continue
            for content in output.get("content", []):
                if isinstance(content, dict) and content.get("type") == "output_text":
                    text_value = content.get("text")
                    if isinstance(text_value, str) and text_value:
                        return text_value
        raise ModelOutputError("OpenAI response contains no output_text")

    def generate(self, request: ModelTaskRequest, prompt: PromptTemplate) -> ModelAdapterResult:
        api_key = self._secret_store.get_secret("openai_api_key")
        response = self._client.post(
            self._endpoint,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=self._body(request, prompt),
            timeout=self._timeout_seconds,
        )
        if response.status_code >= 400:
            raise ModelProviderError(f"OpenAI HTTP {response.status_code}")
        payload = response.json()
        if not isinstance(payload, dict):
            raise ModelOutputError("OpenAI response JSON must be an object")
        output_text = self._output_text(payload)
        try:
            parsed = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise ModelOutputError("OpenAI structured output is not JSON") from exc
        if not isinstance(parsed, dict):
            raise ModelOutputError("OpenAI structured output must be an object")
        try:
            validated = SectionDraftOutput.model_validate(parsed)
        except ValidationError as exc:
            raise ModelOutputError("OpenAI structured output failed schema validation") from exc
        usage = payload.get("usage")
        return ModelAdapterResult(
            provider_run_id=str(payload["id"]) if payload.get("id") is not None else None,
            output=validated.model_dump(mode="json"),
            usage=usage if isinstance(usage, dict) else {},
        )
