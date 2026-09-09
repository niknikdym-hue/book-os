from pathlib import Path

import pytest
from sqlalchemy import text

from book_os_core.db import create_database
from book_os_core.model_gateway import DeterministicFakeAdapter, ModelGateway
from book_os_core.model_routing import ModelRoutingError, ModelRoutingService
from book_os_core.planning import BookContractPlanningRequest, PlanningService
from book_os_core.projects import NewBookRequest, ProjectService


def test_openai_registry_exposes_owner_work_levels() -> None:
    providers = ModelRoutingService.provider_registry()
    openai = next(provider for provider in providers if provider.id == "openai")

    assert openai.label == "OpenAI"
    assert [model.id for model in openai.models][:2] == ["gpt-6-astra", "gpt-5.6-sol"]
    assert openai.work_levels == ["medium", "high", "xhigh"]

    for level in openai.work_levels:
        ModelRoutingService.validate_work_level("openai", level)
    with pytest.raises(ModelRoutingError, match="not registered"):
        ModelRoutingService.validate_work_level("openai", "max")


def test_auto_manual_operation_and_whole_book_pin(tmp_path: Path) -> None:
    project = ProjectService(tmp_path).create_project(
        NewBookRequest(working_title="Routing book", primary_subtype="Strategy")
    )
    routing = ModelRoutingService(tmp_path)

    auto = routing.resolve(
        project.book_id,
        "BOOK_CONTRACT_PROPOSAL",
        provider="openai",
        selection_mode="AUTO",
        selection_scope=None,
        model=None,
    )
    assert auto.provider == "openai"
    assert auto.provider_label == "OpenAI"
    assert auto.model == "gpt-6-astra"
    assert auto.selection_mode == "AUTO"
    assert auto.selection_scope is None

    operation = routing.resolve(
        project.book_id,
        "BOOK_CONTRACT_PROPOSAL",
        provider="yandex",
        selection_mode="MANUAL",
        selection_scope="OPERATION",
        model="aliceai-llm",
    )
    assert operation.provider == "yandex"
    assert operation.selection_scope == "OPERATION"
    assert routing.get_book_pin(project.book_id) is None

    book = routing.resolve(
        project.book_id,
        "BOOK_CONTRACT_PROPOSAL",
        provider="yandex",
        selection_mode="MANUAL",
        selection_scope="BOOK",
        model="aliceai-llm",
    )
    assert book.selection_scope == "BOOK"
    assert routing.get_book_pin(project.book_id) is not None

    pinned = routing.resolve(
        project.book_id,
        "ARCHITECTURE_PROPOSAL",
        provider="openai",
        selection_mode="AUTO",
        selection_scope=None,
        model=None,
    )
    assert pinned.provider == "yandex"
    assert pinned.model == "aliceai-llm"
    assert pinned.selection_mode == "MANUAL"
    assert pinned.selection_scope == "BOOK"

    routing.clear_book_pin(project.book_id)
    restored = routing.resolve(
        project.book_id,
        "ARCHITECTURE_PROPOSAL",
        provider="openai",
        selection_mode="AUTO",
        selection_scope=None,
        model=None,
    )
    assert restored.model == "gpt-6-astra"
    assert restored.selection_mode == "AUTO"


def test_routing_provenance_is_recorded_on_planning_run(tmp_path: Path) -> None:
    project = ProjectService(tmp_path).create_project(
        NewBookRequest(working_title="Routing provenance", primary_subtype="Strategy")
    )
    routing = ModelRoutingService(tmp_path)
    choice = routing.resolve(
        project.book_id,
        "BOOK_CONTRACT_PROPOSAL",
        provider="openai",
        selection_mode="AUTO",
        selection_scope=None,
        model=None,
    )
    planner = PlanningService(
        tmp_path,
        ModelGateway({"openai": DeterministicFakeAdapter()}),
    )
    run = planner.propose_book_contract(
        project.book_id,
        BookContractPlanningRequest(
            idea="Как система управленческих решений перестает зависеть от одного человека",
            provider=choice.provider,
            model=choice.model,
            max_cost_usd=1.0,
        ),
    )
    routing.record_run(project.book_id, run.run_id, choice)

    engine = create_database(
        ProjectService(tmp_path).projects_dir / project.book_id / "project.sqlite"
    )
    try:
        with engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        "SELECT provider,model,selection_mode,selection_scope,routing_rationale "
                        "FROM planning_runs WHERE run_id=:run_id"
                    ),
                    {"run_id": run.run_id},
                )
                .mappings()
                .one()
            )
    finally:
        engine.dispose()

    assert row["provider"] == "openai"
    assert row["model"] == "gpt-6-astra"
    assert row["selection_mode"] == "AUTO"
    assert row["selection_scope"] is None
    assert "Auto routing" in row["routing_rationale"]
