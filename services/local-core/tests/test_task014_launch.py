from __future__ import annotations

from pathlib import Path

import pytest

from book_os_core.anti_junk import AntiJunkCreateRequest, AntiJunkError, AntiJunkService
from book_os_core.model_gateway import (
    DeterministicFakeAdapter,
    ModelGateway,
    ModelOutputError,
    ModelTaskRequest,
)
from book_os_core.model_gateway_anti_junk import AntiJunkModelGateway
from book_os_core.planning import (
    ArchitecturePlanningRequest,
    BookContractPlanningRequest,
    ChapterContractPlanningRequest,
    PlanningGateError,
    PlanningService,
)
from book_os_core.projects import NewBookRequest, ProjectService
from book_os_core.prompts import SECTION_DRAFT_V1


def test_user_anti_junk_dictionary_is_local_deduplicated_and_editable(tmp_path: Path) -> None:
    service = AntiJunkService(tmp_path)
    system = service.list_entries()
    assert any(entry.value == "эта книга не о том" and entry.source == "SYSTEM" for entry in system)

    created = service.add(AntiJunkCreateRequest(value="сверхценный инсайт"))
    duplicate = service.add(AntiJunkCreateRequest(value="  сверхценный   инсайт  "))
    assert created.entry_id == duplicate.entry_id
    assert created.source == "USER"
    assert (tmp_path / "prose-anti-junk-user.json").is_file()

    service.remove(created.entry_id)
    assert all(entry.entry_id != created.entry_id for entry in service.list_entries())
    with pytest.raises(AntiJunkError, match="not found"):
        service.remove("SYSTEM-001")


def test_negative_first_principle_and_context_review_are_distinct(tmp_path: Path) -> None:
    service = AntiJunkService(tmp_path)
    negative = service.scan("Эта книга не о том, как стать идеальным руководителем.")
    assert any(hit["kind"] == "BANNED_TEMPLATE" for hit in negative)
    context = service.scan("Шум вентилятора мешал разговору, поэтому его выключили.")
    assert any(hit["value"] == "шум" and hit["kind"] == "CONTEXT_REVIEW" for hit in context)


def test_writer_output_with_banned_template_fails_closed(tmp_path: Path) -> None:
    gateway = AntiJunkModelGateway(
        ModelGateway({"fake": DeterministicFakeAdapter()}), AntiJunkService(tmp_path)
    )
    request = ModelTaskRequest(
        task_id="task-1",
        task_type="SECTION_DRAFT",
        role="WRITER",
        provider="fake",
        model="fake-writer",
        prompt_id=SECTION_DRAFT_V1.prompt_id,
        prompt_version=SECTION_DRAFT_V1.version,
        prompt_hash=SECTION_DRAFT_V1.prompt_hash,
        section_objective="Это не про скорость, а про качество.",
        authority_inputs=[],
        authoritative_context={},
        max_output_tokens=500,
        max_cost_usd=1.0,
    )
    with pytest.raises(ModelOutputError, match="anti-junk"):
        gateway.generate(request, SECTION_DRAFT_V1)


def test_planner_creates_drafts_only_and_preserves_human_gates(tmp_path: Path) -> None:
    projects = ProjectService(tmp_path)
    project = projects.create_project(
        NewBookRequest(working_title="Первая тестовая книга", primary_subtype="Strategy")
    )
    planner = PlanningService(tmp_path, ModelGateway({"fake": DeterministicFakeAdapter()}))

    contract_run = planner.propose_book_contract(
        project.book_id,
        BookContractPlanningRequest(
            idea="Почему решения возвращаются к владельцу растущей компании",
            provider="fake",
            model="fake-planner",
            max_cost_usd=1.0,
        ),
    )
    assert contract_run.project.book_contract is not None
    assert contract_run.project.book_contract.status == "DRAFT"
    assert contract_run.project.book_contract.authority_status == "DRAFT"

    with pytest.raises(PlanningGateError, match="Book Contract"):
        planner.propose_architecture(
            project.book_id,
            ArchitecturePlanningRequest(provider="fake", model="fake-planner", max_cost_usd=1.0),
        )

    projects.approve_book_contract(project.book_id)
    architecture_run = planner.propose_architecture(
        project.book_id,
        ArchitecturePlanningRequest(provider="fake", model="fake-planner", max_cost_usd=1.0),
    )
    assert architecture_run.project.architecture is not None
    assert architecture_run.project.architecture.status == "DRAFT"
    assert architecture_run.project.architecture.authority_status == "DRAFT"

    with pytest.raises(PlanningGateError, match="Architecture"):
        planner.propose_chapter_contract(
            project.book_id,
            "missing",
            ChapterContractPlanningRequest(provider="fake", model="fake-planner", max_cost_usd=1.0),
        )

    approved_architecture = projects.approve_architecture(project.book_id)
    chapter = approved_architecture.chapters[0]
    chapter_run = planner.propose_chapter_contract(
        project.book_id,
        chapter.chapter_id,
        ChapterContractPlanningRequest(provider="fake", model="fake-planner", max_cost_usd=1.0),
    )
    selected = next(
        item for item in chapter_run.project.chapters if item.chapter_id == chapter.chapter_id
    )
    assert selected.chapter_contract is not None
    assert selected.chapter_contract.status == "DRAFT"
    assert selected.chapter_contract.authority_status == "DRAFT"
