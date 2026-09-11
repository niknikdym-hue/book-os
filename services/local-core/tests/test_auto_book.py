import json
from pathlib import Path
from zipfile import ZipFile

from sqlalchemy import text

from book_os_core.auto_book import AutoBookService, AutoBookStartRequest
from book_os_core.book_context import (
    BookContextService,
    BookContextUpdateRequest,
    ProfileCreateRequest,
    ProfileRegistry,
)
from book_os_core.db import create_database
from book_os_core.model_gateway import (
    DeterministicFakeAdapter,
    ModelAdapterResult,
    ModelGateway,
    ModelTaskRequest,
)
from book_os_core.projects import NewBookRequest, ProjectService
from book_os_core.prompts import PromptTemplate


class LongOpenAIAdapter(DeterministicFakeAdapter):
    def generate(self, request: ModelTaskRequest, prompt: PromptTemplate) -> ModelAdapterResult:
        if request.task_type == "SECTION_DRAFT":
            self.last_request = request
            paragraph = (
                "Это связный абзац будущей книги: мысль развивается последовательно, "
                "без служебных пометок и без повторения инструкции автору. "
            )
            return ModelAdapterResult(
                provider_run_id="fake-long-draft",
                output={"text": paragraph * 80, "notes": []},
                usage={"input_tokens": 100, "output_tokens": 2000},
            )
        return super().generate(request, prompt)


def ready_book(tmp_path: Path, *, with_series: bool = False) -> str:
    project = ProjectService(tmp_path).create_project(
        NewBookRequest(working_title="Auto Book Test", primary_subtype="Strategy")
    )
    registry = ProfileRegistry(tmp_path)
    author = registry.create_profile(
        ProfileCreateRequest(kind="AUTHOR", content={"author_name": "Тестовый автор"})
    )
    author = registry.approve_profile(author.profile_id)
    style = registry.create_profile(
        ProfileCreateRequest(
            kind="STYLE",
            content={
                "style_name": "Auto Book style",
                "author_profile_id": author.profile_id,
                "literary_register": "Ясный деловой нон-фикшн",
                "prohibited_patterns": [],
                "benchmark_excerpts": [],
            },
        )
    )
    style = registry.approve_profile(style.profile_id)
    series_id: str | None = None
    if with_series:
        series = registry.create_profile(
            ProfileCreateRequest(
                kind="SERIES",
                content={
                    "series_name": "Тестовая серия",
                    "author_profile_id": author.profile_id,
                    "purpose_positioning": "Проверить owner-authorized Auto Book lane",
                    "planned_books": ["Auto Book Test"],
                    "future_book_reservations": ["Следующая книга серии"],
                    "cross_book_uniqueness_rules": ["Не повторять центральный механизм"],
                },
            )
        )
        series = registry.approve_profile(series.profile_id)
        series_id = series.profile_id
    BookContextService(tmp_path).save_context(
        project.book_id,
        BookContextUpdateRequest(
            author_profile_id=author.profile_id,
            series_profile_id=series_id,
            style_profile_id=style.profile_id,
            target_characters=40_000,
        ),
    )
    return project.book_id


def run_auto_book(tmp_path: Path, book_id: str) -> tuple[AutoBookService, object]:
    service = AutoBookService(tmp_path, ModelGateway({"openai": LongOpenAIAdapter()}))
    state = service.start(
        book_id,
        AutoBookStartRequest(
            idea="Показать, как владелец компании передаёт качество решений в систему управления.",
            model_choice="AUTO",
            max_cost_usd_per_request=2.0,
            max_total_cost_usd=20.0,
            max_requests=20,
            prepare_litres_docx=True,
            owner_authorizes_auto_progress=True,
        ),
    )
    for _ in range(30):
        if state.status != "RUNNING":
            break
        state = service.advance(book_id)
    return service, state


def assert_completed_book(tmp_path: Path, book_id: str, service: AutoBookService, state: object) -> None:
    assert getattr(state, "status") == "DONE"
    assert getattr(state, "phase") == "DONE"
    assert getattr(state, "requests_used") == 6
    output_path = getattr(state, "output_path")
    assert output_path is not None
    output = Path(output_path)
    assert output.is_file()

    with ZipFile(output) as archive:
        names = set(archive.namelist())
        assert "word/document.xml" in names
        document = archive.read("word/document.xml").decode("utf-8")
    assert "Auto Book Test" not in document
    assert "Тестовый автор" not in document
    assert "Это связный абзац будущей книги" in document

    project = ProjectService(tmp_path).get_project(book_id)
    assert len(project.chapters) == 2
    for chapter in project.chapters:
        assert chapter.chapter_contract is not None
        assert chapter.chapter_contract.authority_status == "APPROVED"
        assert service.drafting.list_drafts(book_id, chapter.chapter_id)


def test_auto_book_runs_end_to_end_and_creates_litres_docx(tmp_path: Path) -> None:
    book_id = ready_book(tmp_path)
    service, state = run_auto_book(tmp_path, book_id)
    assert_completed_book(tmp_path, book_id, service, state)

    engine = create_database(tmp_path / "projects" / book_id / "project.sqlite")
    try:
        with engine.connect() as connection:
            gates = [
                json.loads(value)
                for value in connection.execute(text("SELECT gates_json FROM approvals")).scalars()
            ]
    finally:
        engine.dispose()
    assert any(item.get("owner_auto_book_authorization") is True for item in gates)


def test_series_auto_book_uses_owner_authorization_without_fake_passes(tmp_path: Path) -> None:
    book_id = ready_book(tmp_path, with_series=True)
    service, state = run_auto_book(tmp_path, book_id)
    assert_completed_book(tmp_path, book_id, service, state)

    engine = create_database(tmp_path / "projects" / book_id / "project.sqlite")
    try:
        with engine.connect() as connection:
            fake_gate_counts = {
                "definitions": connection.execute(text("SELECT COUNT(*) FROM definition_packs")).scalar_one(),
                "production_contracts": connection.execute(
                    text("SELECT COUNT(*) FROM chapter_production_contracts")
                ).scalar_one(),
                "chapter_admissions": connection.execute(
                    text("SELECT COUNT(*) FROM chapter_admissions")
                ).scalar_one(),
            }
            gates = [
                json.loads(value)
                for value in connection.execute(text("SELECT gates_json FROM approvals")).scalars()
            ]
    finally:
        engine.dispose()

    assert fake_gate_counts == {
        "definitions": 0,
        "production_contracts": 0,
        "chapter_admissions": 0,
    }
    assert any(item.get("owner_auto_book_authorization") is True for item in gates)
