import json
from pathlib import Path
from zipfile import ZipFile

from sqlalchemy import text

from book_os_core.auto_book import AutoBookService, AutoBookStartRequest
from book_os_core.auto_book_finalizer import AUTO_BOOK_FINAL_EDIT_V1, AutoBookFinalizer
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


class PublishingAdapter(DeterministicFakeAdapter):
    def generate(self, request: ModelTaskRequest, prompt: PromptTemplate) -> ModelAdapterResult:
        if request.task_type != "SECTION_DRAFT":
            return super().generate(request, prompt)

        self.last_request = request
        if prompt.prompt_id == AUTO_BOOK_FINAL_EDIT_V1.prompt_id:
            contract = request.authoritative_context["chapter_contract"]
            required_claims = contract.get("required_claims", [])
            required = " ".join(str(value) for value in required_claims)
            objective = request.section_objective
            marker = "первой" if "chapter 1" in objective else "второй"
            sentences = [
                (
                    f"В {marker} главе тезис {index} развивается через отдельное наблюдение о системе "
                    f"решений, ответственности и проверяемом результате {index}."
                )
                for index in range(1, 55)
            ]
            text_value = (
                f"{required}. "
                + " ".join(sentences)
                + f" Завершение {marker} главы фиксирует самостоятельный вывод без повторения соседней главы."
            )
            return ModelAdapterResult(
                provider_run_id=f"final-{marker}",
                output={"text": text_value, "notes": []},
                usage={"input_tokens": 900, "output_tokens": 1800},
            )

        raw = (
            "Черновой материал раскрывает механизм управления через наблюдаемую ситуацию, "
            "последствие решения и практический вывод для читателя. "
        )
        return ModelAdapterResult(
            provider_run_id="raw-draft",
            output={"text": raw * 70, "notes": []},
            usage={"input_tokens": 400, "output_tokens": 1600},
        )


def ready_book(tmp_path: Path) -> str:
    project = ProjectService(tmp_path).create_project(
        NewBookRequest(working_title="Книга после финальной редактуры", primary_subtype="Strategy")
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
                    "style_name": "Плотный деловой стиль",
                    "author_profile_id": author.profile_id,
                    "literary_register": "Ясный современный нон-фикшн",
                    "analytical_depth": "Высокая",
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


def test_auto_book_finalizer_locks_master_before_litres_docx(tmp_path: Path) -> None:
    book_id = ready_book(tmp_path)
    gateway = ModelGateway({"openai": PublishingAdapter()})
    auto = AutoBookService(tmp_path, gateway)
    state = auto.start(
        book_id,
        AutoBookStartRequest(
            idea="Показать, как качество решений переводится из ручного контроля в систему.",
            model_choice="AUTO",
            max_cost_usd_per_request=2.0,
            max_total_cost_usd=30.0,
            max_requests=30,
            prepare_litres_docx=True,
            owner_authorizes_auto_progress=True,
        ),
    )
    for _ in range(40):
        if state.status != "RUNNING":
            break
        state = auto.advance(book_id)
    assert state.status == "DONE"
    raw_output = Path(state.output_path or "")
    assert raw_output.is_file()

    final = AutoBookFinalizer(tmp_path, gateway).finalize(
        book_id,
        state,
        prepare_litres_docx=True,
    )

    assert final.requests_used == 8
    assert final.output_path is not None
    output = Path(final.output_path)
    assert output.is_file()
    assert output.name == "litres-ready.docx"
    with ZipFile(output) as archive:
        document = archive.read("word/document.xml").decode("utf-8")
    assert "Книга после финальной редактуры" in document
    assert "Завершение первой главы" in document
    assert "Завершение второй главы" in document

    engine = create_database(tmp_path / "projects" / book_id / "project.sqlite")
    try:
        with engine.connect() as connection:
            masters = connection.execute(
                text("SELECT master_id,status,manifest_hash FROM literary_masters")
            ).mappings().all()
            export_formats = set(
                connection.execute(text("SELECT format FROM literary_master_exports")).scalars()
            )
            unit_statuses = list(
                connection.execute(
                    text(
                        "SELECT (SELECT s.status FROM revision_status_history s "
                        "WHERE s.revision_id=h.revision_id ORDER BY s.created_at DESC,"
                        "s.status_event_id DESC LIMIT 1) FROM manuscript_units mu "
                        "JOIN authority_heads h ON h.entity_id=mu.authority_entity_id"
                    )
                ).scalars()
            )
            approval_gates = [
                json.loads(value)
                for value in connection.execute(text("SELECT gates_json FROM approvals")).scalars()
            ]
    finally:
        engine.dispose()

    assert len(masters) == 1
    assert masters[0]["master_id"] == final.master_id
    assert masters[0]["status"] == "LOCKED"
    assert masters[0]["manifest_hash"] == final.master_manifest_hash
    assert "LITRES_DOCX" in export_formats
    assert unit_statuses and set(unit_statuses) == {"APPROVED"}
    assert any(item.get("final_editorial_pass") is True for item in approval_gates)
