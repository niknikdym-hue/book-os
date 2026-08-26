from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from book_os_core.app import create_app
from book_os_core.memory_embeddings import DeterministicFakeEmbeddingAdapter, EmbeddingGateway
from book_os_core.projects import BookContractPayload, NewBookRequest, ProjectService


def book_contract() -> BookContractPayload:
    return BookContractPayload(
        reader="Business leaders",
        reader_problem="They lose whole-book context during local edits",
        central_promise="Reliable whole-book recall",
        central_thesis="Revision-aware memory prevents stale context drift",
        unique_angle="Memory is derived state, not authority",
        reader_trajectory="From local passage focus to whole-book awareness",
        explicit_exclusions=["No chatbot memory as authority"],
        evidence_policy="Material claims require traceable evidence",
        voice_genre_constraints="Precise business nonfiction",
        readiness_criteria=["Current context is recoverable without stale leakage"],
    )


def ready_book(data_dir: Path) -> str:
    projects = ProjectService(data_dir)
    project = projects.create_project(
        NewBookRequest(working_title="Memory API Book", primary_subtype="Strategy")
    )
    projects.save_book_contract(project.book_id, book_contract())
    projects.approve_book_contract(project.book_id)
    return project.book_id


def test_authenticated_memory_api_sync_rebuild_and_hybrid_search(tmp_path: Path) -> None:
    book_id = ready_book(tmp_path)
    embeddings = EmbeddingGateway(
        {"fake": DeterministicFakeEmbeddingAdapter(dimension=8, model_version="fake-v1")}
    )
    client = TestClient(create_app("token", tmp_path, embedding_gateway=embeddings))
    headers = {"Authorization": "Bearer token"}

    assert client.get(f"/api/projects/{book_id}/memory/status").status_code == 401
    assert client.post(f"/api/projects/{book_id}/memory/rebuild").status_code == 401

    status = client.get(f"/api/projects/{book_id}/memory/status", headers=headers)
    assert status.status_code == 200
    assert status.json()["status"] == "LEXICAL_READY"
    assert status.json()["document_count"] == 1

    lexical = client.post(
        f"/api/projects/{book_id}/memory/search",
        headers=headers,
        json={
            "query": "Reliable whole-book recall",
            "mode": "LEXICAL",
            "scope": "CURRENT",
            "object_kinds": ["BOOK_CONTRACT"],
            "exact_phrase": True,
        },
    )
    assert lexical.status_code == 200
    lexical_payload = lexical.json()
    assert len(lexical_payload) == 1
    assert lexical_payload[0]["object_kind"] == "BOOK_CONTRACT"
    assert lexical_payload[0]["currentness"] == "CURRENT"
    assert lexical_payload[0]["revision_id"]
    assert len(lexical_payload[0]["revision_hash"]) == 64

    rebuild = client.post(
        f"/api/projects/{book_id}/memory/rebuild",
        headers=headers,
        json={"provider": "fake", "model": "memory-test"},
    )
    assert rebuild.status_code == 200
    rebuilt = rebuild.json()
    assert rebuilt["status"] == "SEMANTIC_READY"
    assert rebuilt["document_count"] == 1
    assert rebuilt["embedding_count"] == 1
    assert rebuilt["provider"] == "fake"
    assert rebuilt["model"] == "memory-test"

    hybrid = client.post(
        f"/api/projects/{book_id}/memory/search",
        headers=headers,
        json={
            "query": "Reliable whole-book recall",
            "mode": "HYBRID",
            "scope": "CURRENT",
            "object_kinds": ["BOOK_CONTRACT"],
            "provider": "fake",
            "model": "memory-test",
        },
    )
    assert hybrid.status_code == 200
    hybrid_payload = hybrid.json()
    assert len(hybrid_payload) == 1
    assert hybrid_payload[0]["object_kind"] == "BOOK_CONTRACT"
    assert hybrid_payload[0]["currentness"] == "CURRENT"
    assert hybrid_payload[0]["fused_rank"] == 1
    assert hybrid_payload[0]["revision_id"] == lexical_payload[0]["revision_id"]
    assert hybrid_payload[0]["revision_hash"] == lexical_payload[0]["revision_hash"]
