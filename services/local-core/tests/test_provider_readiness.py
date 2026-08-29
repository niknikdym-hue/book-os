from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from book_os_core.app import create_app
from book_os_core.db import create_database
from book_os_core.provider_lane import ProviderLaneService


def _promote(
    lane: ProviderLaneService,
    role: str,
) -> None:
    lane.record_promotion(
        provider="yandex",
        model="yandexgpt",
        config_id="latest-discovery",
        region="RU",
        role=role,
        decision="PROMOTED",
        dataset_hash="d" * 64,
        scorecard_ref=f"m8-stage-b:{role.casefold()}",
        quality_floor_passed=True,
        reason="synthetic readiness test",
        actor="CENTRAL_BRAIN_TEST",
        independence_state="INDEPENDENT" if role == "EVALUATOR" else "UNKNOWN",
    )


def test_runtime_readiness_requires_writer_and_editor_but_not_evaluator(
    tmp_path: Path, monkeypatch
) -> None:
    lane = ProviderLaneService(create_database(tmp_path / "provider-lane.sqlite"))
    _promote(lane, "WRITER")
    _promote(lane, "EDITOR")
    monkeypatch.setenv("BOOK_OS_ALLOW_LIVE_PROVIDER", "1")
    lane.record_probe(
        provider="yandex",
        model="yandexgpt",
        config_id="latest-discovery",
        region="RU",
        capability="generation",
        outcome="SUCCESS",
        probe_type="LIVE",
    )
    monkeypatch.delenv("BOOK_OS_ALLOW_LIVE_PROVIDER", raising=False)

    client = TestClient(create_app("test-token", tmp_path))
    response = client.get(
        "/api/provider-lane/readiness",
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["required_launch_roles"] == ["WRITER", "EDITOR"]
    assert payload["routes_ready"] is True
    assert payload["ready"] is True
    assert payload["live_promotion_required"] is False
    assert payload["roles"]["WRITER"]["available"] is True
    assert payload["roles"]["EDITOR"]["available"] is True
    assert payload["roles"]["EVALUATOR"]["available"] is False
    assert payload["evaluation_role"]["available"] is False
    assert payload["production_ready"] is False
    assert payload["credentials_ready"] is False
