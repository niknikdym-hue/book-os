from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from book_os_core.bookbench import BookBenchService
from book_os_core.db import create_database
from book_os_core.drafting import DraftSectionRequest, DraftingService
from book_os_core.model_gateway import DeterministicFakeAdapter, ModelGateway
from book_os_core.provider_lane import ProviderLaneService
from book_os_core.secrets import DictSecretStore
from book_os_core.stage_b import (
    StageBBudget,
    StageBCandidate,
    StageBGateError,
    StageBPreflightService,
)
from book_os_core.stage_b_bookbench import prepare_synthetic_project
from book_os_core.stage_b_judge import execute_independent_judges


def _snapshot(tmp_path: Path) -> tuple[str, str]:
    project = prepare_synthetic_project(tmp_path)
    drafting = DraftingService(
        tmp_path,
        ModelGateway({"fake": DeterministicFakeAdapter()}),
    )
    for chapter_id in project.chapter_ids:
        drafting.generate_section_draft(
            project.book_id,
            chapter_id,
            DraftSectionRequest(
                section_objective=f"Synthetic source for {chapter_id}",
                provider="fake",
                model="fake-writer-v1",
            ),
        )
    snapshot = BookBenchService(tmp_path).create_snapshot(project.book_id, scope="BOOK")
    return project.book_id, snapshot.snapshot_id


def test_independent_judge_uses_budgeted_provider_and_persists_probe_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    book_id, snapshot_id = _snapshot(tmp_path)
    lane = ProviderLaneService(create_database(tmp_path / "judge-provider-lane.sqlite"))
    sentinel = "M8-JUDGE-YANDEX-SECRET"
    secrets = DictSecretStore({"yandex_ai_studio_api_key": sentinel})
    preflight = StageBPreflightService(lane, secrets)
    plan = preflight.build_plan(
        StageBCandidate(
            "yandex",
            "yandexgpt",
            "latest-discovery",
            "RU",
            ("EVALUATOR",),
        ),
        StageBBudget(
            max_generation_requests=2,
            max_embedding_requests=0,
            max_total_requests=2,
        ),
    )
    calls: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/foundationModels/v1/completion"
        assert request.headers["Authorization"] == f"Api-Key {sentinel}"
        body = json.loads(request.content)
        calls.append(body)
        return httpx.Response(
            200,
            json={
                "id": f"judge-run-{len(calls)}",
                "result": {
                    "alternatives": [
                        {
                            "message": {
                                "text": json.dumps(
                                    {
                                        "verdict": "ATTENTION",
                                        "findings": [
                                            {
                                                "location": "candidate:1",
                                                "evidence": "Synthetic bounded judge signal",
                                                "recommended_action": "Human review of the bounded fixture.",
                                            }
                                        ],
                                        "confidence": 0.8,
                                        "rationale": "Synthetic M8 independent judge evidence.",
                                    }
                                )
                            }
                        }
                    ],
                    "usage": {"inputTextTokens": "40", "completionTokens": "20"},
                    "modelVersion": "yandexgpt-judge-exact-v1",
                },
            },
        )

    monkeypatch.setenv("BOOK_OS_ALLOW_LIVE_PROVIDER", "1")
    evidence = execute_independent_judges(
        data_dir=tmp_path,
        book_id=book_id,
        snapshot_id=snapshot_id,
        subject_identity={
            "provider": "gigachat",
            "model": "GigaChat-2-Pro",
            "config_id": "b2b",
        },
        dimensions=("AUTHOR_VOICE", "CONTRADICTION_INCONSISTENCY"),
        preflight=preflight,
        plan=plan,
        authorized_plan_hash=plan.plan_hash,
        lane=lane,
        secrets=secrets,
        transport=httpx.MockTransport(handler),
    )

    assert evidence.independence_state == "INDEPENDENT"
    assert len(evidence.evaluation_ids) == 2
    assert len(evidence.provider_probe_ids) == 2
    assert evidence.budget_usage["generation_requests_used"] == 2
    assert evidence.budget_usage["total_requests_used"] == 2
    assert len(calls) == 2
    probes = lane.probe_evidence()
    assert len(probes) == 2
    assert {row["external_request_id"] for row in probes} == {"judge-run-1", "judge-run-2"}
    assert all("yandexgpt-judge-exact-v1" in row["usage_json"] for row in probes)
    assert sentinel not in json.dumps(probes, sort_keys=True)


def test_same_config_judge_is_rejected_before_provider_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    book_id, snapshot_id = _snapshot(tmp_path)
    lane = ProviderLaneService(create_database(tmp_path / "same-judge-lane.sqlite"))
    secrets = DictSecretStore({"yandex_ai_studio_api_key": "secret"})
    preflight = StageBPreflightService(lane, secrets)
    plan = preflight.build_plan(
        StageBCandidate(
            "yandex",
            "yandexgpt",
            "latest-discovery",
            "RU",
            ("EVALUATOR",),
        ),
        StageBBudget(1, 0, 1),
    )
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(500)

    monkeypatch.setenv("BOOK_OS_ALLOW_LIVE_PROVIDER", "1")
    with pytest.raises(StageBGateError, match="independent"):
        execute_independent_judges(
            data_dir=tmp_path,
            book_id=book_id,
            snapshot_id=snapshot_id,
            subject_identity={
                "provider": "yandex",
                "model": "yandexgpt",
                "config_id": "latest-discovery",
            },
            dimensions=("AUTHOR_VOICE",),
            preflight=preflight,
            plan=plan,
            authorized_plan_hash=plan.plan_hash,
            lane=lane,
            secrets=secrets,
            transport=httpx.MockTransport(handler),
        )
    assert calls == 0
