from __future__ import annotations

import json

import httpx
import pytest

from book_os_core.model_gateway import ModelBudgetError, ModelTaskRequest
from book_os_core.provider_adapters import (
    BookOSOpenAIResponsesAdapter,
    YandexChatCompletionsAdapter,
)
from book_os_core.prompts import SECTION_DRAFT_V1
from book_os_core.secrets import DictSecretStore


def request(provider: str, model: str, *, max_cost_usd: float = 0.50) -> ModelTaskRequest:
    return ModelTaskRequest(
        task_id="01JPROVIDER0000000000000000",
        task_type="SECTION_DRAFT",
        role="WRITER",
        provider=provider,
        model=model,
        prompt_id=SECTION_DRAFT_V1.prompt_id,
        prompt_version=SECTION_DRAFT_V1.version,
        prompt_hash=SECTION_DRAFT_V1.prompt_hash,
        section_objective="Показать один конкретный механизм без лишних повторов",
        authority_inputs=[],
        authoritative_context={"language": "ru"},
        max_output_tokens=1000,
        max_cost_usd=max_cost_usd,
    )


def test_ai_pro_astra_is_priced_and_bounded() -> None:
    calls: list[httpx.Request] = []

    def handler(http_request: httpx.Request) -> httpx.Response:
        calls.append(http_request)
        return httpx.Response(
            200,
            json={
                "id": "resp_astra_fixture",
                "output_text": json.dumps({"text": "Тест Astra", "notes": []}),
                "usage": {"input_tokens": 1000, "output_tokens": 100},
            },
        )

    adapter = BookOSOpenAIResponsesAdapter(
        DictSecretStore({"openai_api_key": "test-openai-secret"}),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        endpoint="https://example.test/v1/responses",
    )
    result = adapter.generate(request("openai", "gpt-6-astra"), SECTION_DRAFT_V1)

    assert len(calls) == 1
    guard = result.usage["cost_guard"]
    assert guard["input_usd_per_million"] == 10.0
    assert guard["output_usd_per_million"] == 50.0
    assert guard["estimated_actual_cost_usd"] == 0.015
    assert guard["pricing_source_date"] == "2026-09-06"


def test_ai_ya_uses_yandex_openai_compatible_contract_without_leaking_secrets() -> None:
    captured: dict[str, object] = {}

    def handler(http_request: httpx.Request) -> httpx.Response:
        captured["authorization"] = http_request.headers.get("Authorization")
        captured["project"] = http_request.headers.get("OpenAI-Project")
        body = json.loads(http_request.content)
        captured["body"] = body
        return httpx.Response(
            200,
            json={
                "id": "yandex-fixture-1",
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": json.dumps(
                                {"text": "Структурированный текст Яндекса", "notes": []},
                                ensure_ascii=False,
                            ),
                        }
                    }
                ],
                "usage": {"prompt_tokens": 1000, "completion_tokens": 100},
            },
        )

    secrets = DictSecretStore(
        {
            "yandex_ai_studio_api_key": "test-yandex-secret",
            "yandex_folder_id": "b1g-test-folder",
        }
    )
    adapter = YandexChatCompletionsAdapter(
        secrets,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        endpoint="https://example.test/v1/chat/completions",
    )
    result = adapter.generate(request("yandex", "aliceai-llm"), SECTION_DRAFT_V1)

    assert result.provider_run_id == "yandex-fixture-1"
    assert result.output == {"text": "Структурированный текст Яндекса", "notes": []}
    assert captured["authorization"] == "Api-Key test-yandex-secret"
    assert captured["project"] == "b1g-test-folder"
    body = captured["body"]
    assert isinstance(body, dict)
    assert body["model"] == "gpt://b1g-test-folder/aliceai-llm"
    assert body["response_format"]["type"] == "json_schema"
    assert body["response_format"]["json_schema"]["strict"] is True
    serialized = json.dumps(body, ensure_ascii=False)
    assert "test-yandex-secret" not in serialized
    assert result.usage["input_tokens"] == 1000
    assert result.usage["output_tokens"] == 100
    guard = result.usage["cost_guard"]
    assert guard["pricing_source_date"] == "2026-09-06"
    assert guard["estimated_actual_cost_usd"] == 0.005082


def test_ai_ya_cost_cap_blocks_before_http() -> None:
    calls: list[httpx.Request] = []

    def handler(http_request: httpx.Request) -> httpx.Response:
        calls.append(http_request)
        return httpx.Response(500)

    adapter = YandexChatCompletionsAdapter(
        DictSecretStore(
            {
                "yandex_ai_studio_api_key": "test-yandex-secret",
                "yandex_folder_id": "b1g-test-folder",
            }
        ),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        endpoint="https://example.test/v1/chat/completions",
    )

    with pytest.raises(ModelBudgetError, match="exceeds cap"):
        adapter.generate(
            request("yandex", "aliceai-llm", max_cost_usd=0.001), SECTION_DRAFT_V1
        )
    assert calls == []


def test_ai_ya_rejects_unpriced_model_before_http() -> None:
    calls: list[httpx.Request] = []

    def handler(http_request: httpx.Request) -> httpx.Response:
        calls.append(http_request)
        return httpx.Response(500)

    adapter = YandexChatCompletionsAdapter(
        DictSecretStore(
            {
                "yandex_ai_studio_api_key": "test-yandex-secret",
                "yandex_folder_id": "b1g-test-folder",
            }
        ),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        endpoint="https://example.test/v1/chat/completions",
    )

    with pytest.raises(ModelBudgetError, match="unpriced Yandex model"):
        adapter.generate(request("yandex", "unknown-yandex-model"), SECTION_DRAFT_V1)
    assert calls == []
