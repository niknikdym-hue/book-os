from pathlib import Path

from alembic import command
from sqlalchemy import create_engine, text

from book_os_core.audio_script import AudioScriptService
from book_os_core.auto_book import AutoBookService, AutoBookStartRequest
from book_os_core.auto_book_exports import MasterChapter, StructuredBookMaster
from book_os_core.auto_book_finalizer import AutoBookFinalizer
from book_os_core.book_context import (
    BookContextService,
    BookContextUpdateRequest,
    ProfileCreateRequest,
    ProfileRegistry,
)
from book_os_core.db import alembic_config, create_database
from book_os_core.model_gateway import (
    BookConceptProposalOutput,
    DeterministicFakeAdapter,
    ModelGateway,
)
from book_os_core.projects import NewBookRequest, ProjectService
from book_os_core.prompts import BOOK_CONCEPT_PROPOSAL_V1
from book_os_core.series_workspace import SeriesPresetRequest, SeriesWorkspaceService


def ready_book(tmp_path: Path) -> tuple[str, AutoBookService, DeterministicFakeAdapter]:
    project = ProjectService(tmp_path).create_project(
        NewBookRequest(working_title="Как продать онлайн-курсы", primary_subtype="Strategy")
    )
    registry = ProfileRegistry(tmp_path)
    author = registry.approve_profile(
        registry.create_profile(
            ProfileCreateRequest(kind="AUTHOR", content={"author_name": "Елена Дым"})
        ).profile_id
    )
    style = registry.approve_profile(
        registry.create_profile(
            ProfileCreateRequest(
                kind="STYLE",
                content={
                    "style_name": "Деловой нон-фикшн",
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
            target_characters=300_000,
        ),
    )
    adapter = DeterministicFakeAdapter()
    return project.book_id, AutoBookService(tmp_path, ModelGateway({"openai": adapter})), adapter


def start(service: AutoBookService, book_id: str, **overrides: object):
    payload = {
        "idea": "Как продать онлайн-курсы",
        "reader_hint": "",
        "target_characters": 300_000,
        "max_cost_usd_per_request": 1.0,
        "max_total_cost_usd": 20.0,
        "max_requests": 20,
        "owner_authorizes_auto_progress": True,
        **overrides,
    }
    return service.start(book_id, AutoBookStartRequest.model_validate(payload))


def test_short_one_sentence_idea_is_a_valid_raw_seed(tmp_path: Path) -> None:
    book_id, service, _ = ready_book(tmp_path)
    state = start(service, book_id)
    assert state.idea == "Как продать онлайн-курсы"
    assert state.phase == "CONCEPT_DEVELOPMENT"


def test_empty_audience_does_not_block_concept_development(tmp_path: Path) -> None:
    book_id, service, _ = ready_book(tmp_path)
    state = service.advance(book_id) if start(service, book_id).status == "RUNNING" else None
    assert state is not None and state.concept is not None
    assert state.concept.reader_job


def test_concept_development_precedes_book_definition(tmp_path: Path) -> None:
    book_id, service, _ = ready_book(tmp_path)
    state = start(service, book_id)
    assert ProjectService(tmp_path).get_project(book_id).book_contract is None
    state = service.advance(book_id)
    assert state.phase == "CONCEPT_REVIEW"
    assert ProjectService(tmp_path).get_project(book_id).book_contract is None


def test_concept_review_requires_author_confirmation(tmp_path: Path) -> None:
    book_id, service, _ = ready_book(tmp_path)
    state = service.advance(book_id) if start(service, book_id).status == "RUNNING" else None
    assert state is not None and state.status == "AWAITING_CONCEPT_APPROVAL"


def test_author_can_accept_proposed_concept(tmp_path: Path) -> None:
    book_id, service, _ = ready_book(tmp_path)
    service.advance(book_id) if start(service, book_id).status == "RUNNING" else None
    accepted = service.accept_concept(book_id)
    assert accepted.status == "RUNNING"
    assert accepted.phase == "BOOK_CONTRACT"


def test_author_can_edit_concept_before_acceptance(tmp_path: Path) -> None:
    book_id, service, _ = ready_book(tmp_path)
    proposed = service.advance(book_id) if start(service, book_id).status == "RUNNING" else None
    assert proposed is not None and proposed.concept is not None
    edited = proposed.concept.model_copy(update={"central_promise": "Точная новая формулировка"})
    accepted = service.accept_concept(book_id, edited)
    assert accepted.concept is not None
    assert accepted.concept.central_promise == "Точная новая формулировка"


def test_author_can_request_another_concept_variant(tmp_path: Path) -> None:
    book_id, service, _ = ready_book(tmp_path)
    first = service.advance(book_id) if start(service, book_id).status == "RUNNING" else None
    assert first is not None
    next_state = service.request_another_concept(book_id, "Нужен более практичный угол")
    assert next_state.phase == "CONCEPT_DEVELOPMENT"
    second = service.advance(book_id)
    assert second.concept_revision == 2


def test_approved_concept_is_generation_context_for_book_definition(tmp_path: Path) -> None:
    book_id, service, adapter = ready_book(tmp_path)
    proposed = service.advance(book_id) if start(service, book_id).status == "RUNNING" else None
    assert proposed is not None and proposed.concept is not None
    service.accept_concept(book_id)
    service.advance(book_id)
    assert adapter.last_request is not None
    assert adapter.last_request.task_type == "BOOK_CONTRACT_PROPOSAL"
    assert "AUTHOR-APPROVED CONCEPT" in adapter.last_request.authoritative_context["idea"]


def test_target_length_is_explicitly_guidance_not_padding(tmp_path: Path) -> None:
    book_id, service, adapter = ready_book(tmp_path)
    start(service, book_id)
    service.advance(book_id)
    assert adapter.last_request is not None
    context = adapter.last_request.authoritative_context["book_context"]
    assert context["target_characters"] == 300_000
    assert context["target_length_policy"] == "GUIDANCE_NOT_PADDING"


def test_series_corpus_is_labelled_negative_reference_not_template(tmp_path: Path) -> None:
    book_id, service, adapter = ready_book(tmp_path)
    service.planning.series_workspaces.generation_context = lambda _: {
        "usage_policy": "ANTI_DUPLICATION_NOT_GENERATION_TEMPLATE",
        "completed_book_corpus": [{"usage_policy": "NEGATIVE_REFERENCE_FOR_ANTI_DUPLICATION_ONLY"}],
    }
    start(service, book_id)
    service.advance(book_id)
    assert adapter.last_request is not None
    series = adapter.last_request.authoritative_context["book_context"]["series_continuity"]
    assert series["usage_policy"] == "ANTI_DUPLICATION_NOT_GENERATION_TEMPLATE"


def test_online_courses_acceptance_seed_receives_real_series_anti_dup_context(
    tmp_path: Path,
) -> None:
    registry = ProfileRegistry(tmp_path)
    author = registry.approve_profile(
        registry.create_profile(
            ProfileCreateRequest(kind="AUTHOR", content={"author_name": "Елена Дым"})
        ).profile_id
    )
    workspace = SeriesWorkspaceService(tmp_path)
    series = workspace.create_services_promotion_preset(
        SeriesPresetRequest(author_profile_id=author.profile_id)
    )
    registry.approve_profile(series.series_profile_id)
    course_book = next(item for item in series.books if item.title == "Как продать онлайн-курсы")
    style = registry.approve_profile(
        registry.create_profile(
            ProfileCreateRequest(
                kind="STYLE",
                content={
                    "style_name": "Деловой нон-фикшн",
                    "author_profile_id": author.profile_id,
                    "prohibited_patterns": [],
                    "benchmark_excerpts": [],
                },
            )
        ).profile_id
    )
    BookContextService(tmp_path).save_context(
        course_book.book_id,
        BookContextUpdateRequest(
            author_profile_id=author.profile_id,
            series_profile_id=series.series_profile_id,
            style_profile_id=style.profile_id,
            target_characters=300_000,
        ),
    )
    adapter = DeterministicFakeAdapter()
    service = AutoBookService(tmp_path, ModelGateway({"openai": adapter}))
    start(service, course_book.book_id)
    state = service.advance(course_book.book_id)
    assert state.concept is not None and state.concept.reader_job
    assert adapter.last_request is not None
    continuity = adapter.last_request.authoritative_context["book_context"]["series_continuity"]
    assert continuity["current_corpus_usage"] == "ANTI_DUPLICATION_NOT_GENERATION_TEMPLATE"
    assert continuity["current_corpus"][0]["title"] == "Как продавать услуги"
    assert (
        continuity["current_corpus"][0]["usage_policy"]
        == "NEGATIVE_REFERENCE_FOR_ANTI_DUPLICATION_ONLY"
    )


def test_concept_prompt_rejects_generic_template_clone() -> None:
    text_value = BOOK_CONCEPT_PROPOSAL_V1.developer_text
    assert "never as a writing template" in text_value
    assert "Reject generic template-clone logic" in text_value


def test_nonfiction_context_defaults_to_public_bibliography(tmp_path: Path) -> None:
    book_id, _, _ = ready_book(tmp_path)
    context = BookContextService(tmp_path).get_context(book_id)
    assert context.include_bibliography is True
    assert context.bibliography_preference == "AUTO_INCLUDED"


def test_author_can_explicitly_omit_only_public_bibliography(tmp_path: Path) -> None:
    book_id, service, _ = ready_book(tmp_path)
    start(service, book_id, omit_public_bibliography=True)
    context = BookContextService(tmp_path).get_context(book_id)
    assert context.include_bibliography is False
    assert context.public_bibliography_omitted is True


def test_bibliography_can_be_reenabled_later(tmp_path: Path) -> None:
    book_id, _, _ = ready_book(tmp_path)
    contexts = BookContextService(tmp_path)
    contexts.set_public_bibliography(book_id, include=False)
    restored = contexts.set_public_bibliography(book_id, include=True)
    assert restored.include_bibliography is True
    assert restored.public_bibliography_omitted is False


def test_omission_does_not_delete_internal_research_tables(tmp_path: Path) -> None:
    book_id, _, _ = ready_book(tmp_path)
    contexts = BookContextService(tmp_path)
    contexts.set_public_bibliography(book_id, include=False)
    engine = create_database(tmp_path / "projects" / book_id / "project.sqlite")
    with engine.connect() as connection:
        names = {
            row[0]
            for row in connection.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        }
    assert {"sources", "claims", "evidence", "source_access_history"} <= names


def test_public_audio_text_never_mechanically_narrates_bibliography(tmp_path: Path) -> None:
    book_id, _, _ = ready_book(tmp_path)
    master = StructuredBookMaster(
        title="Книга",
        author="Автор",
        chapters=[
            MasterChapter(chapter_id="chapter-1", title="Глава", paragraphs=["Текст главы."])
        ],
        bibliography=["Источник, который не надо читать голосом"],
    )
    content, _ = AudioScriptService(tmp_path).content_from_master(
        master, adaptation_mode="AUDIO_NATIVE"
    )
    assert "Источник, который не надо читать голосом" not in content.clean_recording_text()


def test_bibliography_builder_excludes_unverified_or_unused_sources(tmp_path: Path) -> None:
    book_id, service, _ = ready_book(tmp_path)
    assert (
        AutoBookFinalizer(tmp_path, service.planning.gateway)._verified_bibliography(book_id) == []
    )


def test_legacy_false_default_migrates_to_auto_included(tmp_path: Path) -> None:
    database_path = tmp_path / "legacy-0024.sqlite"
    command.upgrade(alembic_config(database_path), "0024")
    engine = create_engine(f"sqlite:///{database_path}")
    now = "2026-09-13T00:00:00Z"
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO book_projects(book_id,working_title,mode,domain,primary_subtype,"
                "profile_version,workflow_stage,created_at,updated_at) VALUES "
                "(:book,'Legacy','BOOK_FROM_ZERO','BUSINESS_NONFICTION','Strategy','0.1',"
                "'BOOK_DEFINITION',:now,:now)"
            ),
            {"book": "L" * 26, "now": now},
        )
        connection.execute(
            text(
                "INSERT INTO book_context_settings(book_id,include_bibliography,"
                "plan_illustrations,updated_at) VALUES (:book,0,0,:now)"
            ),
            {"book": "L" * 26, "now": now},
        )
    engine.dispose()
    command.upgrade(alembic_config(database_path), "0025")
    upgraded = create_engine(f"sqlite:///{database_path}")
    with upgraded.connect() as connection:
        row = connection.execute(
            text("SELECT include_bibliography,bibliography_preference FROM book_context_settings")
        ).one()
    assert row == (1, "AUTO_INCLUDED")


def test_concept_schema_requires_professional_core_fields() -> None:
    schema = BookConceptProposalOutput.model_json_schema()
    assert {"reader_job", "central_promise", "differentiation", "scope_in", "scope_out"} <= set(
        schema["required"]
    )
