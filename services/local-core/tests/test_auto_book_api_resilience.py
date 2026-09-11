from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient
import httpx

from book_os_core.auto_book_api import build_auto_book_router
from book_os_core.book_context import (
    BookContextService,
    BookContextUpdateRequest,
    ProfileCreateRequest,
    ProfileRegistry,
)
from book_os_core.model_gateway import ModelGateway, ModelTaskRequest
from book_os_core.projects import NewBookRequest, ProjectService
from book_os_core.prompts import PromptTemplate


class DisconnectingAdapter:
    provider_name = "openai"

    def generate(self, request: ModelTaskRequest, prompt: PromptTemplate):
        raise httpx.RemoteProtocolError("Server disconnected without sending a response.")


def ready_book(tmp_path: Path) -> str:
    project = ProjectService(tmp_path).create_project(
        NewBookRequest(working_title="Disconnect Test", primary_subtype="Strategy")
    )
    registry = ProfileRegistry(tmp_path)
    author = registry.approve_profile(
        registry.create_profile(
            ProfileCreateRequest(kind="AUTHOR", content={"author_name": "Тестовый автор"})
        ).profile_id
    )
    style = registry.approve_profile(
        registry.create_profile(
            ProfileCreateRequest(
                kind="STYLE",
                content={
                    "style_name": "Test style",
                    "author_profile_id": author.profile_id,
                    "prohibited_patterns": [],
                    "benchmark_excerpts": [],
                },
            )
        ).profile_id
    )
    BookContextService(tmp_path).save_context(
        project.book_id,
        BookContextUpdateRequest(
            author_profile_id=author.profile_id,
            style_profile_id=style.profile_id,
            target_characters=40_000,
        ),
    )
    return project.book_id


def test_provider_disconnect_pauses_auto_book_without_losing_progress(tmp_path: Path) -> None:
    token = "test-token"
    gateway = ModelGateway({"openai": DisconnectingAdapter()})
    app = FastAPI()

    def require_token(authorization: str | None = Header(default=None)) -> None:
        if authorization != f"Bearer {token}":
            raise HTTPException(status_code=401, detail="unauthorized")

    app.include_router(build_auto_book_router(tmp_path, require_token, gateway))
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {token}"}
    book_id = ready_book(tmp_path)

    started = client.post(
        f"/api/projects/{book_id}/auto-book/start",
        headers=headers,
        json={
            "idea": "Проверить сохранение прогресса при кратком обрыве связи.",
            "model_choice": "ASTRA_HIGH",
            "max_cost_usd_per_request": 1.0,
            "max_total_cost_usd": 10.0,
            "max_requests": 20,
            "prepare_litres_docx": False,
            "owner_authorizes_auto_progress": True,
        },
    )
    assert started.status_code == 200
    assert started.json()["phase"] == "BOOK_CONTRACT"

    interrupted = client.post(
        f"/api/projects/{book_id}/auto-book/advance",
        headers=headers,
    )
    assert interrupted.status_code == 503
    assert "Прогресс Auto Book сохранён" in interrupted.json()["detail"]

    state = client.get(f"/api/projects/{book_id}/auto-book", headers=headers)
    assert state.status_code == 200
    payload = state.json()
    assert payload["status"] == "RUNNING"
    assert payload["phase"] == "BOOK_CONTRACT"
    assert payload["requests_used"] == 0
    assert "Server disconnected" in payload["error"]
    assert payload["last_action"] == "Temporary model connection interruption; progress saved"
