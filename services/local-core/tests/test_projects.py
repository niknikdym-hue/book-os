from __future__ import annotations

from pathlib import Path

from alembic import command
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import text

from book_os_core.app import create_app
from book_os_core.db import alembic_config, create_database
from book_os_core.projects import (
    BUSINESS_SUBTYPES,
    BookArchitecturePayload,
    BookContractPayload,
    ChapterContractPayload,
    NewBookRequest,
    ProjectGateError,
    ProjectService,
)


def book_contract(title: str = "contract") -> BookContractPayload:
    return BookContractPayload(
        reader=f"Reader for {title}",
        reader_problem="A meaningful business problem",
        central_promise="A concrete transformation",
        central_thesis="A falsifiable central thesis",
        unique_angle="A distinct category angle",
        reader_trajectory="From confusion to a usable model",
        explicit_exclusions=["Not a generic motivational book"],
        evidence_policy="Material claims require traceable evidence",
        voice_genre_constraints="Business nonfiction, precise and concrete",
        readiness_criteria=["Promise is fulfilled", "Material claims are checked"],
    )


def architecture(chapter_ids: list[str | None] | None = None) -> BookArchitecturePayload:
    ids = chapter_ids or [None, None]
    return BookArchitecturePayload.model_validate(
        {
            "parts": [
                {
                    "title": "Part I",
                    "purpose": "Build the core model",
                    "chapters": [
                        {
                            "chapter_id": ids[0],
                            "title": "First chapter",
                            "purpose": "Introduce the problem",
                            "new_contribution": "Name the core mechanism",
                            "dependencies": [],
                            "transition": "Move from problem to model",
                        },
                        {
                            "chapter_id": ids[1],
                            "title": "Second chapter",
                            "purpose": "Build the model",
                            "new_contribution": "Explain the causal structure",
                            "dependencies": ["chapter-1"],
                            "transition": "Move to application",
                        },
                    ],
                }
            ],
            "intellectual_progression": "Problem → mechanism → application",
            "concept_allocation": "Core concepts are introduced once and reused deliberately",
            "promise_thesis_coverage": "Both chapters advance the central promise and thesis",
            "major_transitions": "Each chapter hands one explicit unresolved question to the next",
        }
    )


def chapter_contract() -> ChapterContractPayload:
    return ChapterContractPayload(
        chapter_purpose="Deliver the chapter's unique structural function",
        new_contribution="Introduce one idea not owned elsewhere",
        reader_prior_state="Reader sees the problem but lacks a model",
        reader_after_state="Reader can explain the mechanism",
        required_claims=["Claim A"],
        required_or_permitted_research=["Research question A"],
        required_scenes_examples=["Concrete business example"],
        reserved_elsewhere=["Detailed implementation belongs later"],
        opening_requirements="Open with a concrete tension",
        ending_requirements="End with a changed reader model",
        transition_requirements="Hand off the next question explicitly",
    )


def create_project(service: ProjectService):
    return service.create_project(
        NewBookRequest(
            working_title="Test Business Book",
            primary_subtype="Strategy",
            secondary_subtype="Leadership",
        )
    )


def test_m1_database_upgrades_to_m2(tmp_path: Path) -> None:
    database = tmp_path / "project.sqlite"
    config = alembic_config(database)
    command.upgrade(config, "0002")
    command.upgrade(config, "head")
    engine = create_database(database)
    with engine.connect() as connection:
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            == "0010"
        )
        tables = {
            row[0]
            for row in connection.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        }
    assert {"book_projects", "chapters", "working_revisions"} <= tables


def test_business_profile_validation_is_bounded() -> None:
    for subtype in BUSINESS_SUBTYPES:
        assert (
            NewBookRequest(working_title="Book", primary_subtype=subtype).primary_subtype == subtype
        )
    with pytest.raises(ValueError):
        NewBookRequest(working_title="Book", primary_subtype="Invalid")
    with pytest.raises(ValueError):
        NewBookRequest(
            working_title="Book", primary_subtype="Strategy", secondary_subtype="Strategy"
        )


def test_project_discovery_survives_service_restart(tmp_path: Path) -> None:
    first_service = ProjectService(tmp_path)
    created = create_project(first_service)
    assert (tmp_path / "projects" / created.book_id / "project.sqlite").is_file()
    assert (tmp_path / "projects" / created.book_id / "project-manifest.json").is_file()

    restarted = ProjectService(tmp_path)
    listed = restarted.list_projects()
    assert [item.book_id for item in listed] == [created.book_id]
    opened = restarted.get_project(created.book_id)
    assert opened.working_title == "Test Business Book"
    assert opened.workflow_stage == "BOOK DEFINITION"


def test_book_contract_approval_and_replacement_preserve_history(tmp_path: Path) -> None:
    service = ProjectService(tmp_path)
    project = create_project(service)
    saved = service.save_book_contract(project.book_id, book_contract("v1"))
    assert saved.book_contract is not None
    assert saved.book_contract.status == "DRAFT"

    approved = service.approve_book_contract(project.book_id)
    assert approved.book_contract is not None
    assert approved.book_contract.authority_status == "APPROVED"
    first_authority = approved.book_contract.authority_revision_id
    assert approved.workflow_stage == "ARCHITECTURE"

    edited = service.save_book_contract(project.book_id, book_contract("v2"))
    assert edited.book_contract is not None
    assert edited.book_contract.status == "DRAFT"
    reapproved = service.approve_book_contract(project.book_id)
    assert reapproved.book_contract is not None
    assert reapproved.book_contract.authority_revision_id != first_authority

    engine = create_database(tmp_path / "projects" / project.book_id / "project.sqlite")
    with engine.connect() as connection:
        revisions = (
            connection.execute(
                text(
                    "SELECT revision_id FROM revisions WHERE entity_id=:entity_id ORDER BY created_at"
                ),
                {"entity_id": reapproved.book_contract.entity_id},
            )
            .scalars()
            .all()
        )
        decisions = connection.execute(
            text(
                "SELECT COUNT(*) FROM decisions d JOIN change_proposals p "
                "ON p.proposal_id=d.proposal_id WHERE p.entity_id=:entity_id"
            ),
            {"entity_id": reapproved.book_contract.entity_id},
        ).scalar_one()
        approvals = connection.execute(
            text(
                "SELECT COUNT(*) FROM approvals a JOIN change_proposals p "
                "ON p.proposal_id=a.proposal_id WHERE p.entity_id=:entity_id"
            ),
            {"entity_id": reapproved.book_contract.entity_id},
        ).scalar_one()
    assert first_authority in revisions
    assert decisions == 2
    assert approvals == 2


def test_architecture_gate_and_stable_chapter_reorder(tmp_path: Path) -> None:
    service = ProjectService(tmp_path)
    project = create_project(service)
    draft = service.save_architecture(project.book_id, architecture())
    assert draft.architecture is not None
    with pytest.raises(ProjectGateError, match="Book Contract"):
        service.approve_architecture(project.book_id)

    service.save_book_contract(project.book_id, book_contract())
    service.approve_book_contract(project.book_id)
    saved = service.save_architecture(project.book_id, architecture())
    assert saved.architecture is not None
    saved_payload = BookArchitecturePayload.model_validate(saved.architecture.content)
    ids = [chapter.chapter_id for chapter in saved_payload.parts[0].chapters]
    assert all(ids)

    approved = service.approve_architecture(project.book_id)
    assert approved.architecture is not None
    assert approved.architecture.authority_status == "APPROVED"
    assert [chapter.chapter_id for chapter in approved.chapters] == ids

    reordered_payload = BookArchitecturePayload.model_validate(approved.architecture.content)
    reordered_payload.parts[0].chapters.reverse()
    reordered_payload.parts[0].chapters[0].title = "Second chapter renamed"
    service.save_architecture(project.book_id, reordered_payload)
    reordered = service.approve_architecture(project.book_id)
    assert [chapter.chapter_id for chapter in reordered.chapters] == list(reversed(ids))
    assert reordered.chapters[0].working_title == "Second chapter renamed"


def test_chapter_contract_requires_current_approved_architecture(tmp_path: Path) -> None:
    service = ProjectService(tmp_path)
    project = create_project(service)
    service.save_book_contract(project.book_id, book_contract())
    service.approve_book_contract(project.book_id)
    draft_architecture = service.save_architecture(project.book_id, architecture())
    assert draft_architecture.architecture is not None
    payload = BookArchitecturePayload.model_validate(draft_architecture.architecture.content)
    chapter_id = payload.parts[0].chapters[0].chapter_id
    assert chapter_id is not None

    with pytest.raises(ProjectGateError):
        service.save_chapter_contract(project.book_id, chapter_id, chapter_contract())

    approved = service.approve_architecture(project.book_id)
    chapter_id = approved.chapters[0].chapter_id
    saved = service.save_chapter_contract(project.book_id, chapter_id, chapter_contract())
    chapter = next(item for item in saved.chapters if item.chapter_id == chapter_id)
    assert chapter.chapter_contract is not None
    assert chapter.chapter_contract.status == "DRAFT"

    complete = service.approve_chapter_contract(project.book_id, chapter_id)
    chapter = next(item for item in complete.chapters if item.chapter_id == chapter_id)
    assert chapter.chapter_contract is not None
    assert chapter.chapter_contract.authority_status == "APPROVED"
    assert chapter.workflow_state == "CONTRACT_APPROVED"
    assert complete.workflow_stage == "WRITING"


def test_authenticated_api_reaches_approved_chapter_contract(tmp_path: Path) -> None:
    client = TestClient(create_app("token", tmp_path))
    assert client.get("/api/projects").status_code == 401
    headers = {"Authorization": "Bearer token"}
    created = client.post(
        "/api/projects",
        headers=headers,
        json={
            "working_title": "API Book",
            "primary_subtype": "Strategy",
            "secondary_subtype": None,
        },
    )
    assert created.status_code == 200
    book_id = created.json()["book_id"]

    assert (
        client.put(
            f"/api/projects/{book_id}/book-contract/draft",
            headers=headers,
            json=book_contract().model_dump(mode="json"),
        ).status_code
        == 200
    )
    assert (
        client.post(f"/api/projects/{book_id}/book-contract/approve", headers=headers).status_code
        == 200
    )
    architecture_response = client.put(
        f"/api/projects/{book_id}/architecture/draft",
        headers=headers,
        json=architecture().model_dump(mode="json"),
    )
    assert architecture_response.status_code == 200
    assert (
        client.post(f"/api/projects/{book_id}/architecture/approve", headers=headers).status_code
        == 200
    )
    chapter_id = client.get(f"/api/projects/{book_id}", headers=headers).json()["chapters"][0][
        "chapter_id"
    ]
    assert (
        client.put(
            f"/api/projects/{book_id}/chapters/{chapter_id}/contract/draft",
            headers=headers,
            json=chapter_contract().model_dump(mode="json"),
        ).status_code
        == 200
    )
    final = client.post(
        f"/api/projects/{book_id}/chapters/{chapter_id}/contract/approve", headers=headers
    )
    assert final.status_code == 200
    assert final.json()["workflow_stage"] == "WRITING"
    assert final.json()["chapters"][0]["chapter_contract"]["authority_status"] == "APPROVED"
