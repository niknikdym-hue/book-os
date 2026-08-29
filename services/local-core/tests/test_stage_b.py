from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import httpx
import pytest
from sqlalchemy import text

from book_os_core.bookbench import BookBenchReport, DimensionReport
from book_os_core.db import create_database
from book_os_core.model_gateway import AuthorityInputRef, ModelTaskRequest
from book_os_core.prompts import SECTION_DRAFT_V1
from book_os_core.provider_lane import ProviderLaneService
from book_os_core.secrets import DictSecretStore
from book_os_core.stage_b import (
    StageBBudget,
    StageBBudgetExceeded,
    StageBCandidate,
    StageBGateError,
    StageBPlanMismatch,
    StageBPreflightService,
    build_provider_runtime,
    production_capabilities,
    production_route,
    require_authorized_execution,
    role_evidence_from_report,
    simulate_outage,
)


def _request(provider: str, model: str, *, role: str = "WRITER") -> ModelTaskRequest:
    return ModelTaskRequest(
        task_id="stage-b-test",
        task_type="SECTION_DRAFT",
        role=role,
        provider=provider,
        model=model,
        prompt_id=SECTION_DRAFT_V1.prompt_id,
        prompt_version=SECTION_DRAFT_V1.version,
        prompt_hash=SECTION_DRAFT_V1.prompt_hash,
        section_objective="Synthetic Stage B test",
        authority_inputs=[
            AuthorityInputRef(
                revision_id="r",
                revision_hash="a" * 64,
                entity_type="chapter.contract",
            )
        ],
        authoritative_context={},
    )


def _service(tmp_path: Path) -> ProviderLaneService:
    return ProviderLaneService(create_database(tmp_path / "stage-b.sqlite"))


def _promote_writer(
    service: ProviderLaneService, provider: str, model: str, config_id: str
) -> None:
    service.record_promotion(
        provider=provider,
        model=model,
        config_id=config_id,
        region="RU",
        role="WRITER",
        decision="PROMOTED",
        dataset_hash="d" * 64,
        scorecard_ref=f"scorecard:{provider}",
        quality_floor_passed=True,
        reason="synthetic Stage B test evidence",
        actor="CENTRAL_BRAIN_TEST",
    )


def test_preflight_is_secret_safe_deterministic_and_fail_closed(tmp_path: Path) -> None:
    service = _service(tmp_path)
    sentinel = "TOP-SECRET-STAGE-B-SENTINEL"
    preflight = StageBPreflightService(
        service,
        DictSecretStore({"yandex_ai_studio_api_key": sentinel}),
    )
    candidate = StageBCandidate(
        "yandex",
        "yandexgpt",
        "latest-discovery",
        "RU",
        ("WRITER", "EDITOR"),
        require_embeddings=True,
    )
    budget = StageBBudget(2, 1, 3)
    plan = preflight.build_plan(candidate, budget)
    assert plan.blockers == ()
    assert plan.credential_state == "AVAILABLE"
    public = json.dumps(plan.public_plan(), sort_keys=True)
    assert sentinel not in public
    assert sentinel not in repr(plan)
    assert len(plan.plan_hash) == 64

    same = preflight.build_plan(candidate, budget)
    assert same.plan_hash == plan.plan_hash
    changed = preflight.build_plan(candidate, replace(budget, max_generation_requests=1))
    assert changed.plan_hash != plan.plan_hash

    missing = StageBPreflightService(service, DictSecretStore({})).build_plan(candidate, budget)
    assert "CREDENTIAL_MISSING" in missing.blockers

    openai = StageBCandidate("openai", "gpt-4.1", "development", "RU", ("WRITER",))
    blocked = StageBPreflightService(
        service, DictSecretStore({"openai_api_key": sentinel})
    ).build_plan(openai, StageBBudget(1, 0, 1))
    assert "REGION_NOT_SUPPORTED" in blocked.blockers
    assert "COMMERCIAL_PATH_NOT_VERIFIED" in blocked.blockers
    assert "PROVIDER_NOT_SUPPORTED_FOR_RU_STAGE_B" in blocked.blockers


def test_budgeted_gigachat_transport_counts_auth_and_generation_before_calls(
    tmp_path: Path,
) -> None:
    service = _service(tmp_path)
    preflight = StageBPreflightService(
        service,
        DictSecretStore({"gigachat_authorization_key": "sentinel-auth"}),
    )
    plan = preflight.build_plan(
        StageBCandidate("gigachat", "GigaChat-2-Pro", "b2b", "RU", ("WRITER",)),
        StageBBudget(
            max_generation_requests=1,
            max_embedding_requests=0,
            max_auth_requests=1,
            max_total_requests=2,
        ),
    )
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path.endswith("/api/v2/oauth"):
            return httpx.Response(200, json={"access_token": "access", "expires_in": 1800})
        return httpx.Response(
            200,
            json={
                "id": "giga-run-1",
                "model": "GigaChat-2-Pro:live-candidate",
                "choices": [
                    {
                        "message": {"content": json.dumps({"text": "Synthetic", "notes": []})},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"total_tokens": 4},
            },
        )

    runtime = build_provider_runtime(
        plan,
        DictSecretStore({"gigachat_authorization_key": "sentinel-auth"}),
        transport=httpx.MockTransport(handler),
    )
    try:
        result = runtime.generation.generate(
            _request("gigachat", "GigaChat-2-Pro"),
            SECTION_DRAFT_V1,
        )
        assert result.usage["model_version"] == "GigaChat-2-Pro:live-candidate"
        assert runtime.ledger.auth_requests == 1
        assert runtime.ledger.generation_requests == 1
        assert runtime.ledger.total_requests == 2
        assert calls == ["/api/v2/oauth", "/v1/chat/completions"]

        with pytest.raises(StageBBudgetExceeded, match="generation"):
            runtime.generation.generate(
                _request("gigachat", "GigaChat-2-Pro"),
                SECTION_DRAFT_V1,
            )
        assert calls == ["/api/v2/oauth", "/v1/chat/completions"]
    finally:
        runtime.close()


def test_mock_probe_never_changes_production_health_and_live_probe_is_exact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = _service(tmp_path)
    _promote_writer(service, "yandex", "yandexgpt", "latest-discovery")

    service.record_probe(
        provider="yandex",
        model="yandexgpt",
        config_id="latest-discovery",
        region="RU",
        capability="generation",
        outcome="SUCCESS",
        probe_type="MOCK",
    )
    yandex = next(
        item
        for item in production_capabilities(service, role="WRITER")
        if item.provider == "yandex"
    )
    assert yandex.health == "UNKNOWN"
    assert not production_route(service, role="WRITER").available

    monkeypatch.setenv("BOOK_OS_ALLOW_LIVE_PROVIDER", "1")
    service.record_probe(
        provider="yandex",
        model="yandexgpt",
        config_id="latest-discovery",
        region="RU",
        capability="generation",
        outcome="SUCCESS",
        probe_type="LIVE",
    )
    route = production_route(service, role="WRITER")
    assert route.available
    assert route.capability is not None
    assert route.capability.provider == "yandex"

    with service.engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE provider_probe_runs SET created_at='2000-01-01T00:00:00+00:00' "
                "WHERE probe_type='LIVE'"
            )
        )
    stale = production_capabilities(
        service,
        role="WRITER",
        now=datetime.now(timezone.utc),
        live_health_ttl=timedelta(hours=24),
    )
    stale_yandex = next(item for item in stale if item.provider == "yandex")
    assert stale_yandex.health == "UNKNOWN"


def test_simulated_outage_uses_only_promoted_compliant_fallback_without_persisting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = _service(tmp_path)
    _promote_writer(service, "gigachat", "GigaChat-2-Pro", "b2b")
    _promote_writer(service, "yandex", "yandexgpt", "latest-discovery")
    monkeypatch.setenv("BOOK_OS_ALLOW_LIVE_PROVIDER", "1")
    for provider, model, config in (
        ("gigachat", "GigaChat-2-Pro", "b2b"),
        ("yandex", "yandexgpt", "latest-discovery"),
    ):
        service.record_probe(
            provider=provider,
            model=model,
            config_id=config,
            region="RU",
            capability="generation",
            outcome="SUCCESS",
            probe_type="LIVE",
        )

    normal = production_route(service, role="WRITER")
    assert normal.available and normal.capability is not None
    assert normal.capability.provider == "gigachat"

    fallback = simulate_outage(
        service,
        role="WRITER",
        unavailable_provider="gigachat",
        unavailable_model="GigaChat-2-Pro",
        unavailable_config_id="b2b",
    )
    assert fallback.available and fallback.capability is not None
    assert fallback.capability.provider == "yandex"

    persisted = production_route(service, role="WRITER")
    assert persisted.available and persisted.capability is not None
    assert persisted.capability.provider == "gigachat"

    isolated = ProviderLaneService(create_database(tmp_path / "isolated.sqlite"))
    _promote_writer(isolated, "gigachat", "GigaChat-2-Pro", "b2b")
    isolated.record_probe(
        provider="gigachat",
        model="GigaChat-2-Pro",
        config_id="b2b",
        region="RU",
        capability="generation",
        outcome="SUCCESS",
        probe_type="LIVE",
    )
    unavailable = simulate_outage(
        isolated,
        role="WRITER",
        unavailable_provider="gigachat",
        unavailable_model="GigaChat-2-Pro",
        unavailable_config_id="b2b",
    )
    assert not unavailable.available
    assert unavailable.reason == "PROVIDER_UNAVAILABLE"


def test_authorized_execution_boundary_requires_flag_exact_hash_and_current_plan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = _service(tmp_path)
    preflight = StageBPreflightService(
        service, DictSecretStore({"yandex_ai_studio_api_key": "secret"})
    )
    plan = preflight.build_plan(
        StageBCandidate("yandex", "yandexgpt", "latest-discovery", "RU", ("WRITER",)),
        StageBBudget(1, 0, 1),
    )

    monkeypatch.delenv("BOOK_OS_ALLOW_LIVE_PROVIDER", raising=False)
    with pytest.raises(StageBGateError, match="BOOK_OS_ALLOW_LIVE_PROVIDER"):
        require_authorized_execution(preflight, plan, authorized_plan_hash=plan.plan_hash)

    monkeypatch.setenv("BOOK_OS_ALLOW_LIVE_PROVIDER", "1")
    with pytest.raises(StageBPlanMismatch):
        require_authorized_execution(preflight, plan, authorized_plan_hash="0" * 64)

    require_authorized_execution(preflight, plan, authorized_plan_hash=plan.plan_hash)


def test_bookbench_role_gate_preserves_blocking_missing_and_independence() -> None:
    report = BookBenchReport(
        snapshot_id="snap-1",
        snapshot_hash="a" * 64,
        current=True,
        dimensions=[
            DimensionReport(
                dimension="AUTHOR_VOICE",
                state="PASS",
                findings=[],
                run_ids=["r1"],
                metrics={},
            ),
            DimensionReport(
                dimension="AI_PROSE_PATHOLOGY",
                state="BLOCKING",
                findings=[],
                run_ids=["r2"],
                metrics={},
            ),
        ],
        blocking_dimensions=["AI_PROSE_PATHOLOGY"],
        generated_at="2026-08-29T00:00:00+00:00",
    )
    evidence = role_evidence_from_report(
        report,
        role="WRITER",
        dataset_id="dataset-1",
        dataset_hash="d" * 64,
        scorecard_ref="scorecard:writer",
        required_dimensions=(
            "AUTHOR_VOICE",
            "AI_PROSE_PATHOLOGY",
            "BOOK_CONTRACT_FULFILLMENT",
        ),
    )
    assert not evidence.promotable
    assert evidence.blocking_dimensions == ("AI_PROSE_PATHOLOGY",)
    assert evidence.missing_dimensions == ("BOOK_CONTRACT_FULFILLMENT",)

    evaluator = role_evidence_from_report(
        report.model_copy(update={"dimensions": [report.dimensions[0]], "blocking_dimensions": []}),
        role="EVALUATOR",
        dataset_id="dataset-1",
        dataset_hash="d" * 64,
        scorecard_ref="scorecard:evaluator",
        required_dimensions=("AUTHOR_VOICE",),
        independence_state="UNKNOWN",
        require_independence=True,
    )
    assert not evaluator.promotable
    assert "EVALUATOR_INDEPENDENCE" in evaluator.blocking_dimensions
