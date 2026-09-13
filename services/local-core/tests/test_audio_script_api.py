import base64
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient
import httpx

from book_os_core.audio_script_api import build_audio_script_router
from book_os_core.auto_book_runtime import DurableAutoBookRuntime
from book_os_core.model_gateway import DeterministicFakeAdapter, ModelGateway
from book_os_core.projects import NewBookRequest, ProjectService


class CountingAdapter:
    provider_name = "openai"

    def __init__(self) -> None:
        self.calls = 0
        self.delegate = DeterministicFakeAdapter()

    def generate(self, request: object, prompt: object) -> object:
        self.calls += 1
        return self.delegate.generate(request, prompt)  # type: ignore[arg-type]


def client_for(tmp_path: Path, adapter: object) -> tuple[TestClient, str]:
    book_id = (
        ProjectService(tmp_path)
        .create_project(NewBookRequest(working_title="Готовая книга", primary_subtype="Strategy"))
        .book_id
    )
    app = FastAPI()

    def require_token(authorization: str | None = Header(default=None)) -> None:
        if authorization != "Bearer token":
            raise HTTPException(status_code=401, detail="unauthorized")

    app.include_router(
        build_audio_script_router(
            tmp_path,
            require_token,
            ModelGateway({"openai": adapter}),  # type: ignore[dict-item]
        )
    )
    return TestClient(app, headers={"Authorization": "Bearer token"}), book_id


def request_payload() -> dict[str, object]:
    source = (
        "Глава первая. Клиенту нужен понятный механизм решения. "
        "Вторая часть сохраняет существенную оговорку и вывод автора."
    ).encode()
    return {
        "source_filename": "approved-source.txt",
        "source_content_base64": base64.b64encode(source).decode(),
        "title": "Готовая книга",
        "author": "Елена Дым",
        "adaptation_mode": "SOURCE_FAITHFUL",
        "model_choice": "AUTO",
        "max_cost_usd_per_request": 1,
        "max_total_cost_usd": 5,
        "max_requests": 5,
        "owner_authorizes_paid_requests": True,
    }


def test_authenticated_existing_book_audio_flow_keeps_source_and_requires_human_approval(
    tmp_path: Path,
) -> None:
    adapter = CountingAdapter()
    client, book_id = client_for(tmp_path, adapter)
    unauthorized = TestClient(client.app).post(
        f"/api/projects/{book_id}/audio-scripts/prepare",
        json=request_payload(),
    )
    assert unauthorized.status_code == 401

    prepared = client.post(
        f"/api/projects/{book_id}/audio-scripts/prepare",
        json=request_payload(),
    )
    assert prepared.status_code == 200, prepared.text
    body = prepared.json()
    script = body["audio_script"]
    repeated = client.post(
        f"/api/projects/{book_id}/audio-scripts/prepare",
        json=request_payload(),
    )
    assert repeated.status_code == 200
    assert repeated.json()["run_id"] == body["run_id"]
    assert repeated.json()["audio_script"]["audio_script_id"] == script["audio_script_id"]
    assert adapter.calls == 1
    durable = DurableAutoBookRuntime(tmp_path).get(book_id, body["run_id"])
    assert durable.intent.attachments[0].content_hash == script["source_hash"]
    assert durable.intent.outputs.voice_text_txt is True
    assert script["status"] == "PROPOSED"
    assert script["adaptation_mode"] == "SOURCE_FAITHFUL"
    assert script["source_hash"] != script["content_hash"]
    source_path = tmp_path / "projects" / book_id / script["provenance"]["source_relative_path"]
    original = source_path.read_bytes()

    denied = client.post(
        f"/api/projects/{book_id}/audio-scripts/{script['audio_script_id']}/approve",
        json={"human_actor": "Елена Дым", "accepted_attention_codes": []},
    )
    assert denied.status_code == 409

    attention = sorted(
        {
            finding["code"]
            for check in script["quality_checks"]
            for finding in check["findings"]
            if finding["severity"] == "ATTENTION"
        }
    )
    approved = client.post(
        f"/api/projects/{book_id}/audio-scripts/{script['audio_script_id']}/approve",
        json={
            "human_actor": "Елена Дым",
            "accepted_attention_codes": attention,
            "reading_docx": True,
            "litres_docx": True,
            "pronunciation_dictionary": True,
        },
    )
    assert approved.status_code == 200, approved.text
    result = approved.json()
    kinds = {item["output_kind"] for item in result["artifacts"]}
    assert kinds == {
        "AUDIO_READING_DOCX",
        "AUDIO_LITRES_DOCX",
        "VOICE_TEXT_TXT",
        "PRONUNCIATION_DICTIONARY",
        "AUDIO_PRODUCTION_HANDOFF",
    }
    voice = next(item for item in result["artifacts"] if item["output_kind"] == "VOICE_TEXT_TXT")
    voice_text = (tmp_path / "projects" / book_id / voice["relative_path"]).read_text()
    assert "audio_script_id" not in voice_text
    assert "source_hash" not in voice_text
    assert "<speak" not in voice_text
    assert source_path.read_bytes() == original
    assert result["audio_script"]["approval"]["actor_kind"] == "HUMAN"

    reopened = client.post(
        f"/api/projects/{book_id}/audio-scripts/prepare",
        json=request_payload(),
    )
    assert reopened.status_code == 200
    assert reopened.json()["audio_script"]["status"] == "APPROVED"
    assert {item["output_kind"] for item in reopened.json()["artifacts"]} == {
        "AUDIO_READING_DOCX",
        "VOICE_TEXT_TXT",
        "PRONUNCIATION_DICTIONARY",
        "AUDIO_PRODUCTION_HANDOFF",
    }
    assert adapter.calls == 1


class DisconnectingAdapter:
    provider_name = "openai"

    def __init__(self) -> None:
        self.calls = 0

    def generate(self, request: object, prompt: object) -> object:
        self.calls += 1
        raise httpx.ReadError("connection ended after request dispatch")


def test_unknown_paid_outcome_is_persisted_and_not_reported_as_retryable_success(
    tmp_path: Path,
) -> None:
    adapter = DisconnectingAdapter()
    client, book_id = client_for(tmp_path, adapter)
    response = client.post(
        f"/api/projects/{book_id}/audio-scripts/prepare",
        json=request_payload(),
    )
    assert response.status_code == 503
    latest = DurableAutoBookRuntime(tmp_path).latest(book_id)
    assert latest is not None
    assert latest.status == "UNKNOWN_OUTCOME"
    assert latest.unknown_cost_usd == 1
    repeated = client.post(
        f"/api/projects/{book_id}/audio-scripts/prepare",
        json=request_payload(),
    )
    assert repeated.status_code == 503
    assert adapter.calls == 1
