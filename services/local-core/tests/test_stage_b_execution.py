from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from book_os_core.db import create_database
from book_os_core.model_gateway import AuthorityInputRef, ModelTaskRequest
from book_os_core.prompts import SECTION_DRAFT_V1
from book_os_core.provider_lane import ProviderLaneService
from book_os_core.secrets import DictSecretStore
from book_os_core.stage_b import StageBBudget, StageBCandidate, StageBPreflightService
from book_os_core.stage_b_execution import (
    StageBGenerationCase,
    assert_secret_safe_execution,
    execute_generation_cases,
)


def _service(tmp_path: Path) -> ProviderLaneService:
    return ProviderLaneService(create_database(tmp_path / "stage-b-execution.sqlite"))


def _request(role: str) -> ModelTaskRequest:
    return ModelTaskRequest(
        task_id=f"stage-b-{role.casefold()}",
        task_type="SECTION_DRAFT",
        role=role,
        provider="placeholder",
        model="placeholder",
        prompt_id=SECTION_DRAFT_V1.prompt_id,
        prompt_version=SECTION_DRAFT_V1.version,
        prompt_hash=SECTION_DRAFT_V1.prompt_hash,
        section_objective=f"Synthetic {role} evaluation case",
        authority_inputs=[
            AuthorityInputRef(
                revision_id=f"revision-{role.casefold()}",
                revision_hash="a" * 64,
                entity_type="chapter.contract",
            )
        ],
        authoritative_context={"synthetic": True},
    )


def test_yandex_mock_executes_exact_plan_and_persists_secret_safe_live_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = _service(tmp_path)
    sentinel = "YANDEX-STAGE-B-SECRET-SENTINEL"
    secrets = DictSecretStore({"yandex_ai_studio_api_key": sentinel})
    preflight = StageBPreflightService(service, secrets)
    plan = preflight.build_plan(
        StageBCandidate(
            "yandex",
            "yandexgpt",
            "latest-discovery",
            "RU",
            ("WRITER", "EDITOR"),
        ),
        StageBBudget(max_generation_requests=2, max_embedding_requests=0, max_total_requests=2),
    )
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        assert request.headers["Authorization"] == f"Api-Key {sentinel}"
        body = json.loads(request.content)
        assert body["modelUri"] == "yandexgpt"
        return httpx.Response(
            200,
            json={
                "id": f"yandex-run-{len(calls)}",
                "result": {
                    "alternatives": [
                        {
                            "message": {
                                "text": json.dumps(
                                    {
                                        "text": f"Synthetic output {len(calls)}",
                                        "notes": [],
                                    }
                                )
                            }
                        }
                    ],
                    "usage": {"inputTextTokens": "11", "completionTokens": "7"},
                    "modelVersion": "yandexgpt-stage-b-v1",
                },
            },
        )

    monkeypatch.setenv("BOOK_OS_ALLOW_LIVE_PROVIDER", "1")
    result = execute_generation_cases(
        preflight=preflight,
        plan=plan,
        authorized_plan_hash=plan.plan_hash,
        lane=service,
        secrets=secrets,
        cases=(
            StageBGenerationCase("writer-1", "WRITER", _request("WRITER"), SECTION_DRAFT_V1),
            StageBGenerationCase("editor-1", "EDITOR", _request("EDITOR"), SECTION_DRAFT_V1),
        ),
        transport=httpx.MockTransport(handler),
    )

    assert result.state == "EVIDENCE_AWAITING_OWNER_DECISION"
    assert result.plan_hash == plan.plan_hash
    assert result.budget_usage["generation_requests_used"] == 2
    assert result.budget_usage["total_requests_used"] == 2
    assert len(result.cases) == 2
    assert all(item.returned_model_version == "yandexgpt-stage-b-v1" for item in result.cases)
    assert [item.external_request_id for item in result.cases] == ["yandex-run-1", "yandex-run-2"]
    assert calls == [
        "/foundationModels/v1/completion",
        "/foundationModels/v1/completion",
    ]

    persisted = service.probe_evidence()
    assert len(persisted) == 2
    assert all(item["probe_type"] == "LIVE" for item in persisted)
    assert {item["external_request_id"] for item in persisted} == {
        "yandex-run-1",
        "yandex-run-2",
    }
    decoded_usage = [json.loads(item["usage_json"]) for item in persisted]
    assert {item["role"] for item in decoded_usage} == {"WRITER", "EDITOR"}
    assert all(item["model_version"] == "yandexgpt-stage-b-v1" for item in decoded_usage)

    assert service.promotion_evidence() == []
    assert_secret_safe_execution(result, (sentinel,))
    persisted_dump = json.dumps(persisted, sort_keys=True)
    assert sentinel not in persisted_dump


def test_execution_rejects_case_role_outside_authorized_plan_before_provider_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = _service(tmp_path)
    secrets = DictSecretStore({"yandex_ai_studio_api_key": "secret"})
    preflight = StageBPreflightService(service, secrets)
    plan = preflight.build_plan(
        StageBCandidate("yandex", "yandexgpt", "latest-discovery", "RU", ("WRITER",)),
        StageBBudget(1, 0, 1),
    )
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(500)

    monkeypatch.setenv("BOOK_OS_ALLOW_LIVE_PROVIDER", "1")
    with pytest.raises(ValueError, match="role"):
        execute_generation_cases(
            preflight=preflight,
            plan=plan,
            authorized_plan_hash=plan.plan_hash,
            lane=service,
            secrets=secrets,
            cases=(
                StageBGenerationCase("editor-1", "EDITOR", _request("EDITOR"), SECTION_DRAFT_V1),
            ),
            transport=httpx.MockTransport(handler),
        )
    assert calls == 0


def test_known_actual_cost_is_enforced_and_unknown_cost_is_not_faked(tmp_path: Path) -> None:
    service = _service(tmp_path)
    secrets = DictSecretStore({"yandex_ai_studio_api_key": "secret"})
    preflight = StageBPreflightService(service, secrets)
    plan = preflight.build_plan(
        StageBCandidate("yandex", "yandexgpt", "latest-discovery", "RU", ("WRITER",)),
        StageBBudget(1, 0, 1, max_actual_cost=0.1),
    )
    assert plan.estimated_cost is None
    assert plan.public_plan()["estimated_cost"] is None
