from pathlib import Path

from book_os_core.model_routing import ModelRoutingService
from book_os_core.projects import NewBookRequest, ProjectService


def test_openai_auto_routes_core_book_creation_to_astra(tmp_path: Path) -> None:
    project = ProjectService(tmp_path).create_project(
        NewBookRequest(working_title="Astra-first Auto", primary_subtype="Strategy")
    )
    routing = ModelRoutingService(tmp_path)

    for operation in (
        "BOOK_CONTRACT_PROPOSAL",
        "ARCHITECTURE_PROPOSAL",
        "CHAPTER_CONTRACT_PROPOSAL",
        "SECTION_DRAFT",
    ):
        choice = routing.resolve(
            project.book_id,
            operation,
            provider="openai",
            selection_mode="AUTO",
            selection_scope=None,
            model=None,
        )
        assert choice.model == "gpt-6-astra"
        assert choice.selection_mode == "AUTO"
