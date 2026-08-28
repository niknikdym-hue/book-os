from __future__ import annotations

import json

import httpx
import pytest

from book_os_core.model_gateway import AuthorityInputRef, ModelTaskRequest
from book_os_core.memory_embeddings import EmbeddingGateway
from book_os_core.prompts import SECTION_DRAFT_V1
from book_os_core.provider_lane import (
    GigaChatAdapter,
    GigaChatEmbeddingAdapter,
    RussiaPolicy,
    YandexAdapter,
    YandexEmbeddingAdapter,
    seed_capabilities,
)
from book_os_core.secrets import DictSecretStore


def request(provider: str, model: str) -> ModelTaskRequest:
    return ModelTaskRequest(
        task_id="m8-test",
        task_type="SECTION_DRAFT",
        role="WRITER",
        provider=provider,
        model=model,
        prompt_id=SECTION_DRAFT_V1.prompt_id,
        prompt_version=SECTION_DRAFT_V1.version,
        prompt_hash=SECTION_DRAFT_V1.prompt_hash,
        section_objective="Synthetic M8 test",
        authority_inputs=[
            AuthorityInputRef(
                revision_id="r", revision_hash="a" * 64, entity_type="chapter.contract"
            )
        ],
        authoritative_context={},
    )


def test_ru_policy_rejects_unpromoted_and_openai_without_vpn_fallback() -> None:
    decision = RussiaPolicy().route(seed_capabilities(), role="WRITER")
    assert not decision.available
    assert decision.reason == "QUALITY_NOT_PROMOTED"
    openai = next(item for item in seed_capabilities() if item.provider == "openai")
    assert not RussiaPolicy().route((openai,), role="WRITER").available


def test_yandex_mocked_response_is_structured_and_secret_safe() -> None:
    def handler(http_request: httpx.Request) -> httpx.Response:
        assert http_request.headers["Authorization"] == "Api-Key test-key"
        return httpx.Response(
            200,
            json={
                "id": "yc-1",
                "result": {"text": "Synthetic", "notes": []},
                "usage": {"tokens": 2},
            },
        )

    adapter = YandexAdapter(
        DictSecretStore({"yandex_ai_studio_api_key": "test-key"}),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    result = adapter.generate(request("yandex", "gpt://folder/yandexgpt/latest"), SECTION_DRAFT_V1)
    assert result.output["text"] == "Synthetic"
    assert "test-key" not in repr(result)


def test_gigachat_mocked_oauth_is_cached_and_secret_safe() -> None:
    calls: list[str] = []

    def handler(http_request: httpx.Request) -> httpx.Response:
        calls.append(str(http_request.url))
        if http_request.url.path.endswith("oauth"):
            return httpx.Response(200, json={"access_token": "access", "expires_in": 1800})
        return httpx.Response(
            200,
            json={
                "id": "gc-1",
                "choices": [
                    {"message": {"content": json.dumps({"text": "Synthetic", "notes": []})}}
                ],
            },
        )

    adapter = GigaChatAdapter(
        DictSecretStore({"gigachat_authorization_key": "test-auth"}),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        endpoint="https://example.test",
    )
    assert (
        adapter.generate(request("gigachat", "GigaChat-2-Pro"), SECTION_DRAFT_V1).output["text"]
        == "Synthetic"
    )
    assert (
        adapter.generate(request("gigachat", "GigaChat-2-Pro"), SECTION_DRAFT_V1).output["text"]
        == "Synthetic"
    )
    assert sum(url.endswith("oauth") for url in calls) == 1
    assert "test-auth" not in repr(adapter)


def test_live_runner_is_never_implicit(monkeypatch: pytest.MonkeyPatch) -> None:
    from book_os_core.provider_lane import run_live_probe

    monkeypatch.delenv("BOOK_OS_ALLOW_LIVE_PROVIDER", raising=False)
    with pytest.raises(RuntimeError, match="BOOK_OS_ALLOW_LIVE_PROVIDER"):
        run_live_probe()


def test_mocked_embedding_adapters_return_exact_model_identity() -> None:
    def yandex(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"model": "yandex-v1", "embeddings": [{"embedding": [0.1, 0.2]}]}
        )

    yandex_gateway = EmbeddingGateway(
        {
            "yandex": YandexEmbeddingAdapter(
                DictSecretStore({"yandex_ai_studio_api_key": "key"}),
                client=httpx.Client(transport=httpx.MockTransport(yandex)),
            )
        }
    )
    assert (
        yandex_gateway.embed(["synthetic"], provider="yandex", model="m").model_version
        == "yandex-v1"
    )

    def giga(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("oauth"):
            return httpx.Response(200, json={"access_token": "access"})
        return httpx.Response(200, json={"model": "giga-v1", "data": [{"embedding": [0.1, 0.2]}]})

    giga_adapter = GigaChatAdapter(
        DictSecretStore({"gigachat_authorization_key": "auth"}),
        client=httpx.Client(transport=httpx.MockTransport(giga)),
        endpoint="https://example.test",
    )
    giga_gateway = EmbeddingGateway({"gigachat": GigaChatEmbeddingAdapter(giga_adapter)})
    assert (
        giga_gateway.embed(["synthetic"], provider="gigachat", model="m").model_version == "giga-v1"
    )
