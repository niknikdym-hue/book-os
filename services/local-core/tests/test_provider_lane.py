from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import httpx
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import text

from book_os_core.app import create_app
from book_os_core.db import create_database
from book_os_core.memory_embeddings import EmbeddingGateway, EmbeddingOutputError
from book_os_core.model_gateway import (
    AuthorityInputRef,
    ModelOutputError,
    ModelProviderError,
    ModelTaskRequest,
)
from book_os_core.prompts import SECTION_DRAFT_V1
from book_os_core.provider_lane import (
    GigaChatAdapter,
    GigaChatEmbeddingAdapter,
    LiveProbeBudget,
    ProviderLaneService,
    RussiaPolicy,
    YandexAdapter,
    YandexEmbeddingAdapter,
    build_live_probe_preflight,
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
        assert http_request.url.path == "/foundationModels/v1/completion"
        assert http_request.headers["Authorization"] == "Api-Key test-key"
        body = json.loads(http_request.content)
        assert body["jsonSchema"]["schema"]["type"] == "object"
        return httpx.Response(
            200,
            json={
                "id": "yc-1",
                "result": {
                    "alternatives": [
                        {"message": {"text": json.dumps({"text": "Synthetic", "notes": []})}}
                    ],
                    "usage": {"totalTokens": "2"},
                    "modelVersion": "yandexgpt:stage-a",
                },
            },
        )

    adapter = YandexAdapter(
        DictSecretStore({"yandex_ai_studio_api_key": "test-key"}),
        client=httpx.Client(transport=httpx.MockTransport(success)),
    )
    result = adapter.generate(request("yandex", "gpt://folder/yandexgpt/latest"), SECTION_DRAFT_V1)
    assert result.output["text"] == "Synthetic"
    assert result.usage["model_version"] == "yandexgpt:stage-a"
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
                lambda _: httpx.Response(
                    200,
                    json={
                        "result": {
                            "alternatives": [{"message": {"text": json.dumps({"notes": []})}}]
                        }
                    },
                )
            )
        ),
    )
    with pytest.raises(ModelOutputError, match="schema"):
        malformed.generate(request("yandex", "m"), SECTION_DRAFT_V1)

    provider_error = YandexAdapter(
        DictSecretStore({"yandex_ai_studio_api_key": "key"}),
        client=httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(503))),
    )
    with pytest.raises(ModelProviderError, match="503"):
        provider_error.generate(request("yandex", "m"), SECTION_DRAFT_V1)


def test_gigachat_mocked_oauth_cache_rate_limit_refusal_and_provenance() -> None:
    calls: list[str] = []

    def handler(http_request: httpx.Request) -> httpx.Response:
        calls.append(str(http_request.url))
        if http_request.url.path.endswith("/api/v2/oauth"):
            assert http_request.url.host == "ngw.devices.sberbank.ru"
            assert http_request.headers["RqUID"]
            return httpx.Response(200, json={"access_token": "access", "expires_in": 1800})
        assert http_request.url.host == "api.giga.chat"
        assert http_request.url.path == "/v1/chat/completions"
        body = json.loads(http_request.content)
        assert body["response_format"]["type"] == "json_schema"
        assert body["response_format"]["strict"] is True
        assert "json_schema" not in body["response_format"]
        return httpx.Response(
            200,
            json={
                "id": "gc-1",
                "model": "GigaChat-2-Pro:stage-a",
                "choices": [
                    {
                        "message": {"content": json.dumps({"text": "Synthetic", "notes": []})},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"total_tokens": 4},
            },
        )

    adapter = GigaChatAdapter(
        DictSecretStore({"gigachat_authorization_key": "test-auth"}),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    first = adapter.generate(request("gigachat", "GigaChat-2-Pro"), SECTION_DRAFT_V1)
    second = adapter.generate(request("gigachat", "GigaChat-2-Pro"), SECTION_DRAFT_V1)
    assert first.output["text"] == "Synthetic"
    assert second.output["text"] == "Synthetic"
    assert first.usage["model_version"] == "GigaChat-2-Pro:stage-a"
    assert sum(url.endswith("/api/v2/oauth") for url in calls) == 1
    assert "test-auth" not in repr(adapter)

    with pytest.raises(ValueError, match="commercial"):
        GigaChatAdapter(DictSecretStore({}), scope="GIGACHAT_API_PERS")

    def limited(http_request: httpx.Request) -> httpx.Response:
        if http_request.url.path.endswith("/api/v2/oauth"):
            return httpx.Response(200, json={"access_token": "access", "expires_in": 1800})
        return httpx.Response(429, json={"error": "rate limited"})

    limited_adapter = GigaChatAdapter(
        DictSecretStore({"gigachat_authorization_key": "auth"}),
        client=httpx.Client(transport=httpx.MockTransport(limited)),
    )
    with pytest.raises(ModelProviderError, match="429"):
        limited_adapter.generate(request("gigachat", "GigaChat-2-Pro"), SECTION_DRAFT_V1)

    def refusal(http_request: httpx.Request) -> httpx.Response:
        if http_request.url.path.endswith("/api/v2/oauth"):
            return httpx.Response(200, json={"access_token": "access", "expires_in": 1800})
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {"content": "{}"},
                        "finish_reason": "blacklist",
                    }
                ]
            },
        )

    refusal_adapter = GigaChatAdapter(
        DictSecretStore({"gigachat_authorization_key": "auth"}),
        client=httpx.Client(transport=httpx.MockTransport(refusal)),
    )
    with pytest.raises(ModelProviderError, match="refusal"):
        refusal_adapter.generate(request("gigachat", "GigaChat-2-Pro"), SECTION_DRAFT_V1)


def test_live_runner_is_never_implicit_and_requires_exact_plan(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("BOOK_OS_ALLOW_LIVE_PROVIDER", raising=False)
    service = ProviderLaneService(create_database(tmp_path / "runner.sqlite"))
    secrets = DictSecretStore({"yandex_ai_studio_api_key": "not-serialized"})
    preflight = build_live_probe_preflight(
        service,
        secrets,
        provider="yandex",
        model="yandexgpt",
        config_id="latest-discovery",
        region="RU",
        roles=("WRITER",),
        budget=LiveProbeBudget(1, 0, 1, 2.0),
        estimated_cost=None,
    )
    with pytest.raises(RuntimeError, match="BOOK_OS_ALLOW_LIVE_PROVIDER"):
        run_live_probe(preflight=preflight)
    assert "not-serialized" not in repr(preflight.public_plan())

    monkeypatch.setenv("BOOK_OS_ALLOW_LIVE_PROVIDER", "1")
    with pytest.raises(RuntimeError, match="exact approved"):
        run_live_probe(preflight=preflight, service=service, expected_plan_hash="wrong")
    result = run_live_probe(
        preflight=preflight,
        service=service,
        secrets=secrets,
        expected_plan_hash=preflight.plan_hash,
        request_executor=lambda _, __: {
            "outcome": "SUCCESS",
            "latency_ms": 3,
            "usage": {"total_tokens": 1},
            "cost": 0.5,
            "external_request_id": "mock-request",
        },
    )
    assert result["state"] == "EVIDENCE_AWAITING_OWNER_DECISION"
    assert service.promotion_evidence() == []


def test_mocked_embedding_adapters_return_exact_model_identity_and_validate_output() -> None:
    yandex_requests: list[dict[str, object]] = []

    def yandex(http_request: httpx.Request) -> httpx.Response:
        assert http_request.url.path == "/foundationModels/v1/textEmbedding"
        body = json.loads(http_request.content)
        yandex_requests.append(body)
        assert "text" in body and "texts" not in body
        return httpx.Response(
            200,
            json={"modelVersion": "yandex-embed-v1", "embedding": [0.1, 0.2], "numTokens": "2"},
        )

    yandex_gateway = EmbeddingGateway(
        {
            "yandex": YandexEmbeddingAdapter(
                DictSecretStore({"yandex_ai_studio_api_key": "key"}),
                client=httpx.Client(transport=httpx.MockTransport(yandex)),
            )
        }
    )
    yandex_result = yandex_gateway.embed(["one", "two"], provider="yandex", model="m")
    assert yandex_result.model_version == "yandex-embed-v1"
    assert len(yandex_result.vectors) == 2
    assert len(yandex_requests) == 2

    malformed_gateway = EmbeddingGateway(
        {
            "yandex": YandexEmbeddingAdapter(
                DictSecretStore({"yandex_ai_studio_api_key": "key"}),
                client=httpx.Client(
                    transport=httpx.MockTransport(lambda _: httpx.Response(200, json={}))
                ),
            )
        }
    )
    with pytest.raises(EmbeddingOutputError):
        malformed_gateway.embed(["synthetic"], provider="yandex", model="m")

    def giga(http_request: httpx.Request) -> httpx.Response:
        if http_request.url.path.endswith("/api/v2/oauth"):
            return httpx.Response(200, json={"access_token": "access", "expires_in": 1800})
        assert http_request.url.path == "/v1/embeddings"
        return httpx.Response(200, json={"model": "giga-v1", "data": [{"embedding": [0.1, 0.2]}]})

    giga_adapter = GigaChatAdapter(
        DictSecretStore({"gigachat_authorization_key": "auth"}),
        client=httpx.Client(transport=httpx.MockTransport(giga)),
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
    assert not writer.available
    assert any(attempt.reason == "PROVIDER_UNAVAILABLE" for attempt in writer.attempts)
    editor = service.route("EDITOR")
    assert not editor.available
    assert editor.reason == "QUALITY_NOT_PROMOTED"

    # A mocked probe never becomes production routing truth.

    with pytest.raises(ValueError, match="quality floor"):
        service.record_promotion(
            provider="gigachat",
            model="GigaChat-2-Pro",
            config_id="b2b",
            region="RU",
            role="WRITER",
            decision="PROMOTED",
            dataset_hash="d" * 64,
            scorecard_ref="scorecard:giga",
            quality_floor_passed=False,
            reason="blocked",
            actor="CENTRAL_BRAIN_TEST",
        )


def test_only_fresh_exact_live_probe_evidence_changes_production_health(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service = ProviderLaneService(create_database(tmp_path / "health.sqlite"))
    identity = {
        "provider": "yandex",
        "model": "yandexgpt",
        "config_id": "latest-discovery",
        "region": "RU",
    }
    service.record_probe(**identity, capability="generation", outcome="SUCCESS")
    assert (
        next(item for item in service.capabilities() if item.provider == "yandex").health
        == "UNKNOWN"
    )
    service.record_probe(**identity, capability="generation", outcome="UNAVAILABLE")
    assert (
        next(item for item in service.capabilities() if item.provider == "yandex").health
        == "UNKNOWN"
    )

    monkeypatch.setenv("BOOK_OS_ALLOW_LIVE_PROVIDER", "1")
    service.record_probe(**identity, capability="generation", outcome="SUCCESS", probe_type="LIVE")
    assert (
        next(item for item in service.capabilities() if item.provider == "yandex").health
        == "HEALTHY"
    )
    with service.engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE provider_probe_runs SET created_at='2000-01-01T00:00:00+00:00' "
                "WHERE provider='yandex' AND probe_type='LIVE'"
            )
        )
    assert (
        next(item for item in service.capabilities() if item.provider == "yandex").health
        == "UNKNOWN"
    )
    with pytest.raises(ValueError, match="region/legal/commercial"):
        service.record_promotion(
            provider="openai",
            model="gpt-4.1",
            config_id="development",
            region="RU",
            role="WRITER",
            decision="PROMOTED",
            dataset_hash="d" * 64,
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
    assert readiness.json()["implementation_ready"] is True
    assert readiness.json()["live_promotion_required"] is True
    assert readiness.json()["credentials"]["yandex"] in {"AVAILABLE", "NOT AVAILABLE"}
    preflight = client.post(
        "/api/provider-lane/preflight",
        headers=headers,
        json={
            "provider": "yandex",
            "model": "yandexgpt",
            "config_id": "latest-discovery",
            "roles": ["WRITER"],
            "max_generation_requests": 1,
            "max_embedding_requests": 0,
            "max_total_requests": 1,
        },
    )
    assert preflight.status_code == 200
    assert preflight.json()["state"] == "LIVE_PROMOTION_REQUIRED"
    assert len(preflight.json()["plan_hash"]) == 64
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
