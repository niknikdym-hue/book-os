from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from book_os_core.app import create_app
from book_os_core.projects import NewBookRequest, ProjectService


def _project(data_dir: Path) -> str:
    return ProjectService(data_dir).create_project(
        NewBookRequest(working_title="Pilot API Book", primary_subtype="Strategy")
    ).book_id


def test_pilot_api_requires_auth_and_exposes_fail_closed_summary(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    book_id = _project(data_dir)
    client = TestClient(create_app("test-token", data_dir))

    assert client.post(f"/api/projects/{book_id}/pilots", json={"human_actor": "Elena"}).status_code == 401

    start = client.post(
        f"/api/projects/{book_id}/pilots",
        headers={"Authorization": "Bearer test-token"},
        json={"human_actor": "Elena"},
    )
    assert start.status_code == 200
    pilot_id = start.json()["pilot_id"]

    summary = client.get(
        f"/api/projects/{book_id}/pilots/{pilot_id}/summary",
        headers={"Authorization": "Bearer test-token"},
    )
    assert summary.status_code == 200
    payload = summary.json()
    assert payload["go_no_go"]["ready"] is False
    assert "LITERARY_MASTER_MISSING" in payload["go_no_go"]["blockers"]
    assert "AI_RUN_EVIDENCE_MISSING" in payload["go_no_go"]["blockers"]

    decision = client.post(
        f"/api/projects/{book_id}/pilots/{pilot_id}/final-decision",
        headers={"Authorization": "Bearer test-token"},
        json={
            "decision": "GO",
            "actor": "Elena",
            "actor_kind": "HUMAN",
            "reason": "Too early",
        },
    )
    assert decision.status_code == 409
    assert "evidence is not ready" in decision.json()["detail"]


def test_pilot_api_records_stage_observation_and_zero_call_openai_preflight(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    book_id = _project(data_dir)
    client = TestClient(create_app("test-token", data_dir))
    headers = {"Authorization": "Bearer test-token"}
    pilot_id = client.post(
        f"/api/projects/{book_id}/pilots",
        headers=headers,
        json={"human_actor": "Elena"},
    ).json()["pilot_id"]

    event = client.post(
        f"/api/projects/{book_id}/pilots/{pilot_id}/stage-events",
        headers=headers,
        json={
            "stage": "IDEA",
            "event_kind": "COMPLETED",
            "actor": "Elena",
            "actor_kind": "HUMAN",
            "human_minutes": 15,
            "outcome": "SUCCESS",
            "metadata": {},
        },
    )
    assert event.status_code == 200
    assert event.json()["stage"] == "IDEA"

    observation = client.post(
        f"/api/projects/{book_id}/pilots/{pilot_id}/observations",
        headers=headers,
        json={
            "stage": "IDEA",
            "category": "WORKFLOW_FRICTION",
            "severity": "ATTENTION",
            "actor": "Elena",
            "actor_kind": "HUMAN",
            "description": "Synthetic API fixture",
        },
    )
    assert observation.status_code == 200
    observation_id = observation.json()["observation_id"]

    resolved = client.post(
        f"/api/projects/{book_id}/pilots/{pilot_id}/observations/{observation_id}/resolve",
        headers=headers,
        json={"actor": "Elena", "actor_kind": "HUMAN", "reason": "Reviewed fixture"},
    )
    assert resolved.status_code == 200
    assert resolved.json()["resolved_at"] is not None

    preflight = client.post(
        f"/api/projects/{book_id}/pilots/{pilot_id}/openai-preflight",
        headers=headers,
        json={
            "writer_model": "writer-model",
            "evaluator_model": "evaluator-model",
            "editor_lane": "deterministic-m6-current",
        },
    )
    assert preflight.status_code == 200
    preflight_payload = preflight.json()
    assert preflight_payload["credential_state"] in {"AVAILABLE", "NOT_AVAILABLE"}
    assert preflight_payload["external_calls"] == 0
    assert preflight_payload["paid_calls"] == 0
    assert set(preflight_payload) == {
        "provider",
        "credential_state",
        "writer_model",
        "evaluator_model",
        "editor_lane",
        "external_calls",
        "paid_calls",
    }
