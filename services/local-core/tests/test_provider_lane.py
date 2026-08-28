from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import httpx
from fastapi.testclient import TestClient
import pytest

from book_os_core.app import create_app
from book_os_core.db import create_database
from book_os_core.memory_embeddings import EmbeddingGateway, EmbeddingOutputError
from book_os_core.model_gateway import (
    AuthorityInputRef,
    DeterministicFakeAdapter,
    ModelGateway,
    ModelOutputError,
    ModelProviderError,
    ModelTaskRequest,
)
from book_os_core.prompts import SECTION_DRAFT_V1
from book_os_core.provider_lane import (
    GigaChatAdapter,
    GigaChatEmbeddingAdapter,
    ProviderLaneService,
    RussiaPolicy,
    YandexAdapter,
    YandexEmbeddingAdapter,
    run_live_probe,
    seed_capabilities,
)
from book_os_core.secrets import DictSecretStore


def request(provider: str, model: str, *, role: str = "WRITER") -> ModelTaskRequest:
    return ModelTaskRequest(
        task_id="m8-test",
        task_type="SECTION_DRAFT",
        role=role,
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
    blocked = RussiaPolicy().route((openai,), role="WRITER")
    assert not blocked.available
    assert blocked.reason == "REGION_NOT_SUPPORTED"
    assert all("VPN" not in attempt.reason for attempt in blocked.attempts)


def test_deterministic_fallback_uses_only_eligible_promoted_healthy_route() -> None:
    yandex = next(item for item in seed_capabilities() if item.provider == "yandex")
    giga = next(
        item for item in seed_capabilities() if item.provider == "gigachat" and item.commercial
    )
    candidates = (
        replace(giga, promotion="PROMOTED", health="UNAVAILABLE"),
        replace(yandex, promotion="PROMOTED", health="HEALTHY"),
    )
    decision = RussiaPolicy().route(candidates, role="WRITER")
    assert decision.available
    assert decision.capability is not None
    assert decision.capability.provider == "yandex"
    assert any(attempt.reason == "PROVIDER_UNAVAILABLE" for attempt in decision.attempts)
    assert decision.attempts[-1].reason == "SELECTED"


def test_yandex_mocked_response_errors_and_secret_safety() -> None:
    def success(http_request: httpx.Request) -> httpx.Response:
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
        client=httpx.Client(transport=httpx.MockTransport(success)),
    )
    result = adapter.generate(request("yandex", "gpt://folder/yandexgpt/latest"), SECTION_DRAFT_V1)
    assert result.output["text"] == "Synthetic"
    assert "test-key" not in repr(result)

    missing = YandexAdapter(
        DictSecretStore({}), client=httpx.Client(transport=httpx.MockTransport(success))
    )
    with pytest.raises(ModelProviderError, match="credential"):
        missing.generate(request("yandex", "m"), SECTION_DRAFT_V1)

    malformed = YandexAdapter(
        DictSecretStore({"yandex_ai_studio_api_key": "key"}),
        client=httpx.Client(
            transport=httpx.MockTransport(
                lambda _: httpx.Response(200, json={"result": {"notes": []}})
            )
        ),
    )
    with pytest.raises(ModelOutputError, match="schema"):
        malformed.generate(request("yandex", "m"), SECTION_DRAFT_V1)


def test_gigachat_mocked_oauth_cache_rate_limit_and_secret_safety() -> None:
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

    def limited(http_request: httpx.Request) -> httpx.Response:
        if http_request.url.path.endswith("oauth"):
            return httpx.Response(200, json={"access_token": "access"})
        return httpx.Response(429, json={"error": "rate limited"})

    limited_adapter = GigaChatAdapter(
        DictSecretStore({"gigachat_authorization_key": "auth"}),
        client=httpx.Client(transport=httpx.MockTransport(limited)),
        endpoint="https://example.test",
    )
    with pytest.raises(ModelProviderError, match="429"):
        limited_adapter.generate(request("gigachat", "GigaChat-2-Pro"), SECTION_DRAFT_V1)


def test_live_runner_is_never_implicit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BOOK_OS_ALLOW_LIVE_PROVIDER", raising=False)
    with pytest.raises(RuntimeError, match="BOOK_OS_ALLOW_LIVE_PROVIDER"):
        run_live_probe()


def test_mocked_embedding_adapters_return_exact_model_identity_and_validate_output() -> None:
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

    malformed_gateway = EmbeddingGateway(
        {
            "yandex": YandexEmbeddingAdapter(
                DictSecretStore({"yandex_ai_studio_api_key": "key"}),
                client=httpx.Client(
                    transport=httpx.MockTransport(
                        lambda _: httpx.Response(200, json={"embeddings": [{}]})
                    )
                ),
            )
        }
    )
    with pytest.raises(EmbeddingOutputError):
        malformed_gateway.embed(["synthetic"], provider="yandex", model="m")

    def giga(http_request: httpx.Request) -> httpx.Response:
        if http_request.url.path.endswith("oauth"):
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


def test_persisted_role_promotion_probe_overlay_and_gateway_execution(tmp_path: Path) -> None:
    service = ProviderLaneService(create_database(tmp_path / "provider.sqlite"))
    dataset = "d" * 64
    service.record_promotion(
        provider="yandex",
        model="yandexgpt",
        config_id="latest-discovery",
        region="RU",
        role="WRITER",
        decision="PROMOTED",
        dataset_hash=dataset,
        scorecard_ref="scorecard:writer",
        quality_floor_passed=True,
        reason="synthetic Stage A evidence",
        actor="CENTRAL_BRAIN_TEST",
    )
    service.record_probe(
        provider="yandex",
        model="yandexgpt",
        config_id="latest-discovery",
        region="RU",
        capability="generation",
        outcome="SUCCESS",
    )
    writer = service.route("WRITER")
    assert writer.available
    assert writer.capability is not None and writer.capability.provider == "yandex"
    editor = service.route("EDITOR")
    assert not editor.available
    assert editor.reason == "QUALITY_NOT_PROMOTED"

    gateway = ModelGateway({"yandex": DeterministicFakeAdapter()})
    result = service.generate_ru(gateway, request("ignored", "ignored"), SECTION_DRAFT_V1)
    assert result.output["text"].startswith("Draft for:")

    with pytest.raises(ValueError, match="quality floor"):
        service.record_promotion(
            provider="gigachat",
            model="GigaChat-2-Pro",
            config_id="b2b",
            region="RU",
            role="WRITER",
            decision="PROMOTED",
            dataset_hash=dataset,
            scorecard_ref="scorecard:giga",
            quality_floor_passed=False,
            reason="blocked",
            actor="CENTRAL_BRAIN_TEST",
        )
    with pytest.raises(ValueError, match="region/legal/commercial"):
        service.record_promotion(
            provider="openai",
            model="gpt-4.1",
            config_id="development",
            region="RU",
            role="WRITER",
            decision="PROMOTED",
            dataset_hash=dataset,
            scorecard_ref="scorecard:openai",
            quality_floor_passed=True,
            reason="not permitted",
            actor="CENTRAL_BRAIN_TEST",
        )


def test_provider_lane_api_is_authenticated_secret_safe_and_structured(tmp_path: Path) -> None:
    client = TestClient(create_app("test-token", tmp_path))
    assert client.get("/api/provider-lane/capabilities").status_code == 401
    headers = {"Authorization": "Bearer test-token"}
    capabilities = client.get("/api/provider-lane/capabilities", headers=headers)
    assert capabilities.status_code == 200
    body = capabilities.json()
    assert any(item["provider"] == "yandex" for item in body)
    route = client.post(
        "/api/provider-lane/route", headers=headers, json={"role": "WRITER", "embeddings": False}
    )
    assert route.status_code == 200
    assert route.json()["available"] is False
    assert isinstance(route.json()["attempts"], list)
    readiness = client.get("/api/provider-lane/readiness", headers=headers)
    assert readiness.status_code == 200
    assert readiness.json()["region"] == "RU"
    assert readiness.json()["ready"] is False
    assert client.get("/api/provider-lane/promotions", headers=headers).status_code == 200
    assert client.get("/api/provider-lane/probes", headers=headers).status_code == 200
    serialized = json.dumps(
        {
            "capabilities": body,
            "route": route.json(),
            "readiness": readiness.json(),
        }
    )
    assert "test-token" not in serialized
    assert "use vpn" not in serialized.lower()
