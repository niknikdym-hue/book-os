from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import text

from book_os_core.app import create_app
from book_os_core.authority import AuthorityService
from book_os_core.db import create_database
from book_os_core.drafting import DraftSectionRequest, DraftingService
from book_os_core.model_gateway import DeterministicFakeAdapter, ModelGateway
from book_os_core.projects import (
    BookArchitecturePayload,
    BookContractPayload,
    ChapterContractPayload,
    NewBookRequest,
    ProjectService,
)


def book_contract() -> BookContractPayload:
    return BookContractPayload(
        reader="Business leaders",
        reader_problem="Material edits can bypass editorial review",
        central_promise="A visible human editorial decision loop",
        central_thesis="Exact-base decisions protect manuscript authority",
        unique_angle="Findings and proposals stay separate from authority",
        reader_trajectory="From silent edits to auditable decisions",
        explicit_exclusions=["No autonomous approval"],
        evidence_policy="Material claims require traceable evidence",
        voice_genre_constraints="Precise business nonfiction",
        readiness_criteria=["Every material edit has a human decision"],
    )


def architecture() -> BookArchitecturePayload:
    return BookArchitecturePayload.model_validate(
        {
            "parts": [
                {
                    "title": "Part I",
                    "purpose": "Exercise the editorial API",
                    "chapters": [
                        {
                            "chapter_id": None,
                            "title": "Decision Loop",
                            "purpose": "Explain exact-base editing",
                            "new_contribution": "One governed change path",
                            "dependencies": [],
                            "transition": "Move from diagnosis to decision",
                        }
                    ],
                }
            ],
            "intellectual_progression": "finding → proposal → decision",
            "concept_allocation": "One editorial loop",
            "promise_thesis_coverage": "The chapter demonstrates human acceptance",
            "major_transitions": "Diagnosis becomes a bounded proposal",
        }
    )


def chapter_contract() -> ChapterContractPayload:
    return ChapterContractPayload(
        chapter_purpose="Explain exact-base editorial decisions",
        new_contribution="Separate diagnosis from authority",
        reader_prior_state="Reader sees editing as direct text replacement",
        reader_after_state="Reader sees editing as governed review",
        required_claims=["human acceptance protects editorial authority"],
        required_or_permitted_research=["Use verified evidence only"],
        required_scenes_examples=["One editorial decision example"],
        reserved_elsewhere=["BookBench belongs later"],
        opening_requirements="Open with an invisible edit",
        ending_requirements="End with a visible decision",
        transition_requirements="Hand off to BookBench",
    )


def ready_unit(data_dir: Path) -> tuple[str, str, str, str, str, str]:
    projects = ProjectService(data_dir)
    project = projects.create_project(
        NewBookRequest(working_title="Editorial API Book", primary_subtype="Strategy")
    )
    projects.save_book_contract(project.book_id, book_contract())
    projects.approve_book_contract(project.book_id)
    projects.save_architecture(project.book_id, architecture())
    project = projects.approve_architecture(project.book_id)
    chapter_id = project.chapters[0].chapter_id
    projects.save_chapter_contract(project.book_id, chapter_id, chapter_contract())
    projects.approve_chapter_contract(project.book_id, chapter_id)

    drafting = DraftingService(data_dir, ModelGateway({"fake": DeterministicFakeAdapter()}))
    draft = drafting.generate_section_draft(
        project.book_id,
        chapter_id,
        DraftSectionRequest(
            section_objective="Explain the controlled editorial decision loop",
            provider="fake",
            model="fake-writer",
        ),
    )
    assert draft.unit_id and draft.revision_id and draft.revision_hash and draft.text

    engine = create_database(data_dir / "projects" / project.book_id / "project.sqlite")
    with engine.connect() as connection:
        entity_id = connection.execute(
            text("SELECT authority_entity_id FROM manuscript_units WHERE unit_id=:unit_id"),
            {"unit_id": draft.unit_id},
        ).scalar_one()
    return (
        project.book_id,
        chapter_id,
        draft.unit_id,
        str(entity_id),
        draft.revision_id,
        draft.revision_hash,
    )


def test_authenticated_editorial_api_finding_proposal_accept_and_corpus(tmp_path: Path) -> None:
    book_id, chapter_id, unit_id, entity_id, revision_id, revision_hash = ready_unit(tmp_path)
    client = TestClient(create_app("token", tmp_path))
    headers = {"Authorization": "Bearer token"}

    assert client.get(f"/api/projects/{book_id}/editorial/inbox").status_code == 401
    assert client.post(f"/api/projects/{book_id}/editorial/run/cross-book").status_code == 401

    developmental = client.post(
        f"/api/projects/{book_id}/editorial/run/developmental/{chapter_id}",
        headers=headers,
    )
    assert developmental.status_code == 200
    assert developmental.json()["role"] == "DEVELOPMENTAL_EDITOR"

    finding_response = client.post(
        f"/api/projects/{book_id}/editorial/findings",
        headers=headers,
        json={
            "role": "LITERARY_EDITOR",
            "category": "API_EDITORIAL_REWRITE",
            "target_kind": "MANUSCRIPT_UNIT",
            "target_id": unit_id,
            "base_revision_id": revision_id,
            "base_revision_hash": revision_hash,
            "diagnosis": "The current passage needs one bounded editorial revision.",
            "why": "The proposed change should be reviewed before authority changes.",
            "evidence": {"source": "human review fixture"},
            "severity": "MAJOR",
            "confidence": 0.95,
            "expected_effect": "Improve clarity without silent mutation.",
            "risks": "Meaning could drift if accepted blindly.",
            "actor": "OWNER",
            "actor_kind": "HUMAN",
        },
    )
    assert finding_response.status_code == 200
    finding = finding_response.json()
    finding_id = finding["finding_id"]
    assert finding["status"] == "OPEN"

    proposed_text = "A revised passage accepted only through the human Decision Inbox."
    proposal_response = client.post(
        f"/api/projects/{book_id}/editorial/findings/{finding_id}/proposals",
        headers=headers,
        json={
            "proposed_text": proposed_text,
            "rationale": "Replace the bounded passage after explicit review.",
            "actor": "editor-model",
            "actor_kind": "AI",
        },
    )
    assert proposal_response.status_code == 200
    proposal = proposal_response.json()
    proposal_id = proposal["proposal_id"]
    assert proposal["stale"] is False
    assert "--- current" in proposal["diff"]
    assert "+++ proposed" in proposal["diff"]
    assert proposed_text in proposal["diff"]

    inbox = client.get(f"/api/projects/{book_id}/editorial/inbox", headers=headers)
    assert inbox.status_code == 200
    inbox_item = next(item for item in inbox.json() if item["finding"]["finding_id"] == finding_id)
    assert inbox_item["latest_proposal"]["proposal_id"] == proposal_id
    assert inbox_item["stale"] is False

    ai_accept = client.post(
        f"/api/projects/{book_id}/editorial/findings/{finding_id}/proposals/{proposal_id}/accept",
        headers=headers,
        json={"actor": "editor-model", "actor_kind": "AI", "reason": "self approve"},
    )
    assert ai_accept.status_code == 409

    accepted = client.post(
        f"/api/projects/{book_id}/editorial/findings/{finding_id}/proposals/{proposal_id}/accept",
        headers=headers,
        json={"actor": "OWNER", "actor_kind": "HUMAN", "reason": "approved after review"},
    )
    assert accepted.status_code == 200
    accepted_payload = accepted.json()
    assert accepted_payload["decision"] == "ACCEPT"
    assert accepted_payload["finding"]["status"] == "RESOLVED"
    assert accepted_payload["accepted_revision_id"]
    assert accepted_payload["approval_id"]

    engine = create_database(tmp_path / "projects" / book_id / "project.sqlite")
    head = AuthorityService(engine).get_head(entity_id)
    assert head.revision_id == accepted_payload["accepted_revision_id"]
    assert head.status == "APPROVED"

    corpus = client.get(
        f"/api/projects/{book_id}/editorial/findings/{finding_id}/corpus",
        headers=headers,
    )
    assert corpus.status_code == 200
    corpus_payload = corpus.json()
    assert corpus_payload["original_revision"]["revision_id"] == revision_id
    assert corpus_payload["proposals"][0]["proposal_id"] == proposal_id
    assert corpus_payload["decisions"][0]["decision"] == "ACCEPT"
    assert corpus_payload["approvals"][0]["approved_revision_id"] == head.revision_id
    assert corpus_payload["current_final_revision"]["revision_id"] == head.revision_id
