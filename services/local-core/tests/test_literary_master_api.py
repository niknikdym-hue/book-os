from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from book_os_core.app import create_app
from book_os_core.projects import NewBookRequest, ProjectService


def test_literary_master_api_is_authenticated_and_reports_release_blockers(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    project = ProjectService(data_dir).create_project(
        NewBookRequest(
            working_title="API Release Test",
            primary_subtype="Strategy",
        )
    )
    client = TestClient(create_app("test-token", data_dir))
    readiness_url = f"/api/projects/{project.book_id}/literary-master/readiness"

    assert client.get(readiness_url).status_code == 401

    response = client.get(
        readiness_url,
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ready"] is False
    assert "BOOK_CONTRACT_MISSING" in {item["code"] for item in payload["blockers"]}

    create_response = client.post(
        f"/api/projects/{project.book_id}/literary-masters",
        headers={"Authorization": "Bearer test-token"},
        json={"human_actor": "Elena"},
    )
    assert create_response.status_code == 409
    assert "release gate failed" in create_response.json()["detail"]


def test_literary_master_api_validates_human_actor(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    project = ProjectService(data_dir).create_project(
        NewBookRequest(working_title="Actor Test", primary_subtype="Strategy")
    )
    client = TestClient(create_app("test-token", data_dir))
    response = client.post(
        f"/api/projects/{project.book_id}/literary-masters",
        headers={"Authorization": "Bearer test-token"},
        json={"human_actor": ""},
    )
    assert response.status_code == 422
