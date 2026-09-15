import json
from pathlib import Path
import re
from zipfile import ZipFile

from docx import Document
from pypdf import PdfReader
import pytest
from sqlalchemy import text

from book_os_core.audio_script import AudioScriptService
from book_os_core.auto_book import AutoBookGateError, AutoBookService, AutoBookStartRequest
from book_os_core.auto_book_finalizer import (
    AUDIO_SCRIPT_EDITOR_V1,
    AUTO_BOOK_FINAL_EDIT_V1,
    AutoBookFinalizer,
)
from book_os_core.auto_book_gates import AutoBookEvidenceGates
from book_os_core.auto_book_runtime import AutoBookOutputSelection, AutoBookStage
from book_os_core.book_context import (
    BookContextService,
    BookContextUpdateRequest,
    ProfileCreateRequest,
    ProfileRegistry,
)
from book_os_core.db import create_database
from book_os_core.literary_master import LiteraryMasterService
from book_os_core.model_gateway import (
    DeterministicFakeAdapter,
    ModelAdapterResult,
    ModelGateway,
    ModelTaskRequest,
)
from book_os_core.projects import NewBookRequest, ProjectService
from book_os_core.prompts import PromptTemplate
from book_os_core.research import (
    ClaimCreateRequest,
    ClaimUpdateRequest,
    EvidenceCreateRequest,
    SourceAccessRequest,
    SourceImportRequest,
)
from book_os_core.research_adapters import ResearchCandidate, ResearchGateway
from book_os_core.series_workspace import SeriesPresetRequest, SeriesWorkspaceService


_CHAPTER_MATERIAL = (
    (
        "Диагностика спроса",
        "Отделить наблюдаемый спрос покупателей от надежд автора курса",
        "Карта ситуаций, в которых покупатель действительно ищет изменение",
    ),
    (
        "Обещание результата",
        "Собрать проверяемое обещание вокруг задачи клиента и границ результата",
        "Матрица обещания, доказательства и допустимых оговорок",
    ),
    (
        "Экономика предложения",
        "Связать цену, издержки сопровождения и ценность результата для клиента",
        "Контур прибыльности предложения до запуска рекламной кампании",
    ),
    (
        "Маршрут доверия",
        "Показать путь от первого контакта до обоснованного решения о покупке",
        "Последовательность доказательств для разных сомнений клиента",
    ),
    (
        "Разговор о цене",
        "Подготовить спокойное честное объяснение цены и отказаться от ложного дефицита",
        "Сценарий сопоставления стоимости с ценностью и альтернативами",
    ),
    (
        "Система каналов",
        "Распределить роли контента, рекомендаций и прямого обращения",
        "Портфель каналов с понятной функцией каждого контакта",
    ),
    (
        "Разбор воронки",
        "Находить место потери намерения по наблюдаемому поведению клиента",
        "Диагностическая карта переходов без магических коэффициентов",
    ),
    (
        "Работа с возражениями",
        "Различать нехватку доверия, несоответствие задачи и ограничение бюджета",
        "Классификатор причин отказа и подходящих ответных действий",
    ),
    (
        "Повторные продажи",
        "Продолжать отношения после результата без навязчивого допродажа",
        "Цикл наблюдения новых задач уже состоявшегося клиента",
    ),
    (
        "Контроль прибыльности",
        "Соединить решения команды с устойчивостью всей системы продаж",
        "Регулярный обзор гипотез, затрат, ограничений и полученной ценности",
    ),
)


class CourseAcceptanceAdapter(DeterministicFakeAdapter):
    def __init__(self, chapter_count: int = 3) -> None:
        super().__init__()
        self.chapter_count = chapter_count

    def generate(self, request: ModelTaskRequest, prompt: PromptTemplate) -> ModelAdapterResult:
        self.last_request = request
        if request.task_type == "BOOK_CONTRACT_PROPOSAL":
            return ModelAdapterResult(
                provider_run_id="fixture-course-contract",
                output={
                    "reader": "Эксперт или владелец небольшой онлайн-школы",
                    "reader_problem": (
                        "Наборы идут волнами: автор не понимает, сколько можно тратить на привлечение, "
                        "какой объём потока выдержит сопровождение и где прибыль съедают возвраты"
                    ),
                    "central_promise": (
                        "Построить повторяемую модель набора на онлайн-курс, в которой стоимость "
                        "привлечения, ёмкость сопровождения, возвраты и повторные продажи сходятся "
                        "в прибыльный поток"
                    ),
                    "central_thesis": (
                        "Прибыль курса определяется не максимумом заявок, а согласованием стоимости "
                        "привлечения, размера набора, нагрузки сопровождения, возвратов и повторных "
                        "покупок"
                    ),
                    "unique_angle": (
                        "Управлять продажами курса как экономикой набора и пропускной способностью "
                        "образовательного продукта, а не как продажей экспертной услуги"
                    ),
                    "reader_trajectory": (
                        "От разовых запусков к расчёту допустимой стоимости привлечения, размера "
                        "набора и нагрузки сопровождения"
                    ),
                    "explicit_exclusions": [
                        "Не руководство по записи уроков",
                        "Не каталог образовательных платформ",
                    ],
                    "evidence_policy": (
                        "Материальные утверждения регистрируются и связываются с источниками"
                    ),
                    "voice_genre_constraints": "Практический деловой нон-фикшн без инфошума",
                    "readiness_criteria": [
                        "Читатель диагностирует слабое звено системы продаж",
                        "Читатель связывает решение с прибыльностью предложения",
                    ],
                },
                usage={"input_tokens": 100, "output_tokens": 160},
            )
        if request.task_type == "ARCHITECTURE_PROPOSAL":
            chapters = [
                {
                    "title": title,
                    "purpose": purpose,
                    "new_contribution": contribution,
                    "dependencies": [] if index == 0 else [_CHAPTER_MATERIAL[index - 1][0]],
                    "transition": (
                        "Следующая глава проверяет новый причинный вопрос системы продаж"
                    ),
                }
                for index, (title, purpose, contribution) in enumerate(
                    _CHAPTER_MATERIAL[: self.chapter_count]
                )
            ]
            return ModelAdapterResult(
                provider_run_id="fixture-course-architecture",
                output={
                    "parts": [
                        {
                            "title": "Система прибыльных продаж",
                            "purpose": "Последовательно собрать независимые элементы системы",
                            "chapters": chapters,
                        }
                    ],
                    "intellectual_progression": (
                        "От проверки спроса через устройство предложения к устойчивой экономике"
                    ),
                    "concept_allocation": "Каждая глава отвечает за отдельное решение читателя",
                    "promise_thesis_coverage": (
                        "Последовательность соединяет спрос, ценность и прибыльность"
                    ),
                    "major_transitions": (
                        "Каждый переход закрывает текущую причину и открывает следующую"
                    ),
                },
                usage={"input_tokens": 140, "output_tokens": 240},
            )
        if request.task_type == "CHAPTER_CONTRACT_PROPOSAL":
            return ModelAdapterResult(
                provider_run_id="fixture-course-chapter-contract",
                output={
                    "chapter_purpose": "Раскрыть отдельный механизм системы продаж",
                    "new_contribution": "Дать проверяемый шаг без повторения соседних глав",
                    "reader_prior_state": "Читатель видит симптом, но не причинный механизм",
                    "reader_after_state": "Читатель может проверить механизм на своей практике",
                    "required_claims": [
                        "Исследование решений покупателей показывает проверяемую связь между "
                        "обещанием результата и оценкой предложения"
                    ],
                    "required_or_permitted_research": [
                        "Проверить утверждение по полностью просмотренному источнику"
                    ],
                    "required_scenes_examples": [
                        "Таблица шагов и схема механизма там, где они помогают пониманию"
                    ],
                    "reserved_elsewhere": ["Не повторять механизмы соседних глав"],
                    "opening_requirements": "Начать с наблюдаемой ситуации покупателя",
                    "ending_requirements": "Закончить проверяемым следующим действием",
                    "transition_requirements": "Передать следующий вопрос следующей главе",
                },
                usage={"input_tokens": 100, "output_tokens": 160},
            )
        if request.task_type == "BOOKBENCH_JUDGE":
            return ModelAdapterResult(
                provider_run_id="fixture-independent-critic",
                output={
                    "verdict": "PASS",
                    "findings": [],
                    "confidence": 0.9,
                    "rationale": (
                        "Deterministic fixture found no blocking defect in the exact snapshot."
                    ),
                },
                usage={"input_tokens": 80, "output_tokens": 20},
            )
        if request.task_type == "SECTION_DRAFT":
            if prompt.prompt_id == AUTO_BOOK_FINAL_EDIT_V1.prompt_id:
                current = str(request.authoritative_context["current_manuscript_text"])
                corrections = request.authoritative_context.get("required_corrections", [])
                if corrections:
                    current += (
                        "\n\nУточнение цены: автор сопоставляет стоимость с измеримой ценностью, "
                        "издержками сопровождения и честно названными границами результата."
                    )
                return ModelAdapterResult(
                    provider_run_id="fixture-identity-final-edit",
                    output={"text": current, "notes": []},
                    usage={"input_tokens": 100, "output_tokens": 100},
                )
            if prompt.prompt_id == AUDIO_SCRIPT_EDITOR_V1.prompt_id:
                paragraphs = request.authoritative_context["source_paragraphs"]
                return ModelAdapterResult(
                    provider_run_id="fixture-audio-adaptation",
                    output={"text": "\n\n".join(str(value) for value in paragraphs), "notes": []},
                    usage={"input_tokens": 100, "output_tokens": 100},
                )
            match = re.search(r"chapter (\d+)", request.section_objective)
            ordinal = int(match.group(1)) if match else 1
            title, purpose, contribution = _CHAPTER_MATERIAL[ordinal - 1]
            required = " ".join(
                str(value)
                for value in request.authoritative_context["chapter_contract"].get(
                    "required_claims", []
                )
            )
            paragraph = (
                f"{required}. Глава «{title}» решает отдельную задачу: {purpose}. "
                f"Её новый вклад — {contribution}. Автор начинает с наблюдаемой ситуации клиента, "
                "проверяет причину затруднения, отделяет факт от предположения и связывает вывод "
                "с конкретным следующим действием. Пример рассматривается как способ проверить "
                "границы решения, а не как обещание универсального рецепта. В конце читатель "
                "получает критерий, по которому можно пересмотреть собственную практику."
            )
            text_value = "\n\n".join(
                f"{paragraph} Отдельный разбор {index} уточняет контекст применения."
                for index in range(1, 9)
            )
            return ModelAdapterResult(
                provider_run_id=f"fixture-course-draft-{ordinal}",
                output={"text": text_value, "notes": []},
                usage={"input_tokens": 120, "output_tokens": 800},
            )
        return super().generate(request, prompt)


class OfflineResearchAdapter:
    provider_name = "openalex"

    def search(self, query: str, *, limit: int = 5) -> list[ResearchCandidate]:
        del query, limit
        return [
            ResearchCandidate(
                provider="openalex",
                external_id="W-OFFLINE-COURSE-SALES",
                title="Проверяемое исследование решений покупателей онлайн-курсов",
                authors=["Тестовый исследователь"],
                publication_year=2025,
                doi="10.1000/book-os.course",
                canonical_url="https://example.test/course-sales",
                abstract="Локальная deterministic fixture без сетевого запроса.",
                inspected_excerpt=(
                    "Исследование решений покупателей показывает проверяемую связь между "
                    "обещанием результата и оценкой предложения."
                ),
                inspected_pointer="fixture://course-sales/results#buyer-decisions",
            )
        ]


def _standalone_book(tmp_path: Path, *, chapter_count: int = 3) -> tuple[str, AutoBookService]:
    project = ProjectService(tmp_path).create_project(
        NewBookRequest(working_title="Midpoint fixture", primary_subtype="Strategy")
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
                    "style_name": "Проверяемый стиль",
                    "author_profile_id": author.profile_id,
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
    return project.book_id, AutoBookService(
        tmp_path, ModelGateway({"openai": CourseAcceptanceAdapter(chapter_count)})
    )


def _run_to_done(
    service: AutoBookService, book_id: str, *, target_characters: int = 40_000
) -> object:
    state = service.start(
        book_id,
        AutoBookStartRequest(
            idea="Проверить полный цикл книги через конкретную задачу читателя.",
            target_characters=target_characters,
            max_cost_usd_per_request=1,
            max_total_cost_usd=100,
            max_requests=80,
            owner_authorizes_auto_progress=True,
            final_human_acceptance_required=False,
        ),
    )
    state = service.advance(book_id)
    state = service.accept_concept(book_id)
    for _ in range(120):
        if state.status != "RUNNING":
            break
        state = service.advance(book_id)
    assert state.status == "DONE"
    return state


@pytest.mark.parametrize("chapter_count", [2, 3, 4, 5, 10])
def test_midbook_audit_occurs_once_at_first_crossing_and_retry_is_idempotent(
    tmp_path: Path, chapter_count: int
) -> None:
    book_id, service = _standalone_book(tmp_path, chapter_count=chapter_count)
    state = _run_to_done(service, book_id)
    engine = create_database(tmp_path / "projects" / book_id / "project.sqlite")
    with engine.connect() as connection:
        count_before = connection.execute(
            text("SELECT COUNT(*) FROM production_checkpoints WHERE kind='MID_BOOK'")
        ).scalar_one()
    assert count_before == 1

    replay = state.model_copy(
        update={"status": "RUNNING", "phase": "MIDBOOK_AUDIT", "midbook_audit_completed": False}
    )
    service._write(replay)
    resumed = service.advance(book_id)
    assert resumed.midbook_audit_completed is True
    with engine.connect() as connection:
        count_after = connection.execute(
            text("SELECT COUNT(*) FROM production_checkpoints WHERE kind='MID_BOOK'")
        ).scalar_one()
    engine.dispose()
    assert count_after == 1


def test_over_target_quality_text_is_not_mechanically_truncated(tmp_path: Path) -> None:
    book_id, service = _standalone_book(tmp_path, chapter_count=2)
    state = _run_to_done(service, book_id, target_characters=4_000)
    drafts = [
        service.drafting.list_drafts(book_id, chapter.chapter_id)[0].text
        for chapter in ProjectService(tmp_path).get_project(book_id).chapters
    ]
    assert sum(len(value) for value in drafts) > 4_000
    assert all("Отдельный разбор 8" in value for value in drafts)
    assert state.output_path is not None
    with ZipFile(state.output_path) as archive:
        document = archive.read("word/document.xml").decode("utf-8")
    assert document.count("Отдельный разбор 8") == 2


def test_quality_gate_cannot_pass_generic_or_cloned_evidence() -> None:
    architecture = {
        "parts": [
            {
                "chapters": [
                    {
                        "title": "Одинаковая глава",
                        "purpose": "Повторить один общий механизм",
                        "new_contribution": "Повторить один общий механизм",
                        "dependencies": [],
                        "transition": "Перейти к тому же",
                    },
                    {
                        "title": "Одинаковая глава",
                        "purpose": "Повторить один общий механизм",
                        "new_contribution": "Повторить один общий механизм",
                        "dependencies": [],
                        "transition": "Перейти к тому же",
                    },
                ]
            }
        ],
        "intellectual_progression": "Повторить один общий механизм снова",
        "major_transitions": "Перейти к тому же общему механизму",
    }
    result = AutoBookEvidenceGates.architecture(architecture)
    assert result.status == "BLOCKING"
    assert {item.gate for item in result.checks if item.status == "BLOCKING"} >= {
        "chapter_functions",
        "new_contributions",
    }


def test_online_courses_linked_deterministic_acceptance_cycle(tmp_path: Path) -> None:
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
    project = ProjectService(tmp_path).create_project(
        NewBookRequest(working_title="Как продать онлайн-курсы", primary_subtype="Strategy")
    )
    style = registry.approve_profile(
        registry.create_profile(
            ProfileCreateRequest(
                kind="STYLE",
                content={
                    "style_name": "Елена Дым — деловой нон-фикшн",
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
    adapter = CourseAcceptanceAdapter(chapter_count=3)
    research_adapter = OfflineResearchAdapter()
    research_gateway = ResearchGateway(
        {
            "openalex": research_adapter,
            "crossref": research_adapter,
            "semantic_scholar": research_adapter,
        }
    )
    gateway = ModelGateway({"openai": adapter})
    service = AutoBookService(tmp_path, gateway, research_gateway)
    state = service.start(
        project.book_id,
        AutoBookStartRequest(
            idea=(
                "Хочу написать книгу о том, как продавать онлайн-курсы. "
                "Не про создание курсов, а про систему продаж и прибыльность."
            ),
            reader_hint="",
            author_name="Елена Дым",
            series_name="Секреты продвижения услуг",
            target_characters=300_000,
            model_choice="AUTO",
            outputs=AutoBookOutputSelection(
                full_manuscript_docx=True,
                litres_ebook_docx=True,
                reading_pdf=True,
                epub=True,
                audio_reading_docx=True,
                reader_extras=True,
                publisher_pack=True,
            ),
            max_cost_usd_per_request=1,
            max_total_cost_usd=100,
            max_requests=80,
            owner_authorizes_auto_progress=True,
            final_human_acceptance_required=False,
        ),
    )
    context = BookContextService(tmp_path).get_context(project.book_id)
    assert context.series_profile is not None
    assert context.series_profile.profile_id == series.series_profile_id
    assert context.include_bibliography is True
    assert any(
        item.book_id == project.book_id for item in workspace.books(series.series_profile_id)
    )

    state = service.advance(project.book_id)
    assert state.status == "AWAITING_CONCEPT_APPROVAL"
    assert state.concept is not None
    assert state.concept.reader_job
    assert state.concept.central_promise
    assert state.concept.differentiation
    assert "AI" in state.concept.why_now
    assert state.concept.scope_in and state.concept.scope_out and state.concept.series_place
    assert ProjectService(tmp_path).get_project(project.book_id).book_contract is None
    assert adapter.last_request is not None
    continuity = adapter.last_request.authoritative_context["book_context"]["series_continuity"]
    assert continuity["current_corpus"][0]["title"] == "Как продавать услуги"
    assert (
        continuity["current_corpus"][0]["usage_policy"]
        == "NEGATIVE_REFERENCE_FOR_ANTI_DUPLICATION_ONLY"
    )
    assert continuity["planned_book_boundaries"]
    assert continuity["legacy_manuscript"] is None

    state = service.accept_concept(project.book_id)
    for _ in range(80):
        if state.status != "RUNNING":
            break
        state = service.advance(project.book_id)
    assert state.status == "DONE"
    assert state.midbook_audit_completed is True
    assert state.research_source_count == 1
    assert state.quality_gate_evidence["architecture"]["status"] == "PASS"
    assert state.quality_gate_evidence["series_duplication"]["status"] == "PASS"
    manuscript_characters = sum(
        len(service.drafting.list_drafts(project.book_id, chapter.chapter_id)[0].text)
        for chapter in ProjectService(tmp_path).get_project(project.book_id).chapters
    )
    assert 4_000 < manuscript_characters < 300_000

    engine = create_database(tmp_path / "projects" / project.book_id / "project.sqlite")
    with engine.connect() as connection:
        midpoint_count = connection.execute(
            text("SELECT COUNT(*) FROM production_checkpoints WHERE kind='MID_BOOK'")
        ).scalar_one()
        unit = (
            connection.execute(
                text(
                    "SELECT mu.unit_id,mu.chapter_id,h.revision_id,h.revision_hash "
                    "FROM manuscript_units mu JOIN authority_heads h "
                    "ON h.entity_id=mu.authority_entity_id ORDER BY mu.ordinal LIMIT 1"
                )
            )
            .mappings()
            .one()
        )
    engine.dispose()
    assert midpoint_count == 1

    blocked_state = state.model_copy(update={"midbook_audit_completed": False})
    with pytest.raises(AutoBookGateError, match="mandatory MID_BOOK audit"):
        AutoBookFinalizer(tmp_path, gateway).finalize(
            project.book_id, blocked_state, prepare_litres_docx=True
        )

    final = AutoBookFinalizer(tmp_path, gateway).finalize(
        project.book_id, state, prepare_litres_docx=True
    )

    assert service.research is not None
    research = service.research
    used_source = research.list_sources(project.book_id)[0]
    assert used_source.access_status == "FULL_SOURCE_INSPECTED"
    assert used_source.inspected_pointer == "fixture://course-sales/results#buyer-decisions"
    duplicate = research.import_source(
        project.book_id,
        SourceImportRequest(
            candidate=ResearchCandidate(
                provider="crossref",
                external_id="10.1000/BOOK-OS.COURSE",
                title="То же исследование с другим metadata provider",
                doi="https://doi.org/10.1000/book-os.course",
                canonical_url="https://example.test/course-sales",
            )
        ),
    )
    assert duplicate.source_id == used_source.source_id
    automatic_claims = [
        claim for claim in research.list_claims(project.book_id) if claim.claim_type == "EMPIRICAL"
    ]
    assert len(automatic_claims) == 3
    assert all(claim.verification_state == "SUPPORTED" for claim in automatic_claims)
    assert all(
        research.list_evidence(project.book_id, claim.claim_id)[0].pointer
        == "fixture://course-sales/results#buyer-decisions"
        for claim in automatic_claims
    )
    current_claim = automatic_claims[0]
    unit = {
        "chapter_id": current_claim.chapter_id,
        "unit_id": current_claim.unit_id,
        "revision_id": current_claim.manuscript_revision_id,
        "revision_hash": current_claim.manuscript_revision_hash,
    }

    unused_source = research.import_source(
        project.book_id,
        SourceImportRequest(
            candidate=ResearchCandidate(
                provider="openalex",
                external_id="W-UNUSED",
                title="Неиспользованный источник",
                canonical_url="https://example.test/unused",
            )
        ),
    )
    inactive_source = research.import_source(
        project.book_id,
        SourceImportRequest(
            candidate=ResearchCandidate(
                provider="openalex",
                external_id="W-INACTIVE",
                title="Источник с неактивным evidence",
                canonical_url="https://example.test/inactive",
            )
        ),
    )
    research.mark_source_access(
        project.book_id,
        inactive_source.source_id,
        SourceAccessRequest(
            access_status="FULL_SOURCE_INSPECTED",
            actor="OWNER",
            note="Inspected only to exercise inactive evidence behavior.",
        ),
    )
    inactive_claim = research.create_claim(
        project.book_id,
        ClaimCreateRequest(
            chapter_id=str(unit["chapter_id"]),
            unit_id=str(unit["unit_id"]),
            manuscript_revision_id=str(unit["revision_id"]),
            manuscript_revision_hash=str(unit["revision_hash"]),
            normalized_text="Временное низкоматериальное утверждение",
            claim_type="AUTHORIAL",
            materiality="LOW",
        ),
    )
    research.add_evidence(
        project.book_id,
        inactive_claim.claim_id,
        EvidenceCreateRequest(
            source_id=inactive_source.source_id,
            relationship="SUPPORTS",
            pointer="Temporary fixture pointer",
            actor="OWNER",
        ),
    )
    research.update_claim(
        project.book_id,
        inactive_claim.claim_id,
        ClaimUpdateRequest(
            manuscript_revision_id=str(unit["revision_id"]),
            manuscript_revision_hash=str(unit["revision_hash"]),
            normalized_text="Изменённое низкоматериальное утверждение",
            claim_type="AUTHORIAL",
            materiality="LOW",
            required_evidence_level="TRACEABLE_SOURCE",
        ),
    )

    bibliography = AutoBookFinalizer(tmp_path, gateway)._verified_bibliography(project.book_id)
    assert len(bibliography) == 1
    assert "Проверяемое исследование" in bibliography[0]
    assert "DOI: 10.1000/book-os.course" in bibliography[0]
    assert "https://example.test/course-sales" in bibliography[0]
    assert unused_source.title not in bibliography
    assert inactive_source.title not in bibliography

    master = LiteraryMasterService(tmp_path).get_master(project.book_id, final.master_id)
    assert master.manifest["bibliography"]["integrity_gate"] == "PASS"
    assert master.manifest["bibliography"]["public_entries"] == bibliography
    assert master.manifest["bibliography"]["verified_used_sources"] == bibliography
    assert final.output_path is not None
    with ZipFile(final.output_path) as archive:
        assert "Библиография" in archive.read("word/document.xml").decode("utf-8")

    project_dir = tmp_path / "projects" / project.book_id
    by_kind = {item["output_kind"]: item for item in final.output_files}
    assert {
        "FULL_MANUSCRIPT_DOCX",
        "LITRES_EBOOK_DOCX",
        "READING_PDF",
        "EPUB",
        "READER_EXTRAS",
        "PUBLISHER_PACK",
    } <= set(by_kind)
    for kind in ("FULL_MANUSCRIPT_DOCX", "LITRES_EBOOK_DOCX", "READER_EXTRAS"):
        document = Document(project_dir / by_kind[kind]["relative_path"])
        assert "Библиография" in [paragraph.text for paragraph in document.paragraphs]
    pdf_text = "\n".join(
        page.extract_text() or ""
        for page in PdfReader(project_dir / by_kind["READING_PDF"]["relative_path"]).pages
    )
    assert "Библиография" in pdf_text
    with ZipFile(project_dir / by_kind["EPUB"]["relative_path"]) as archive:
        bibliography_files = [name for name in archive.namelist() if "bibliography" in name]
        assert len(bibliography_files) == 1
        assert "Проверяемое исследование" in archive.read(bibliography_files[0]).decode("utf-8")
    publisher = json.loads(
        (project_dir / by_kind["PUBLISHER_PACK"]["relative_path"]).read_text(encoding="utf-8")
    )
    assert publisher["public_bibliography"] == bibliography
    assert publisher["bibliographic_audit"]["verified_used_sources"] == bibliography

    assert final.audio_script_id is not None
    audio = AudioScriptService(tmp_path).get(project.book_id, final.audio_script_id)
    assert bibliography[0] not in audio.content.clean_recording_text()
    assert audio.provenance["source_attribution"] == bibliography

    runtime = service.runtime.get(project.book_id, state.run_id)
    operations = service.runtime.list_operations(project.book_id, state.run_id)
    completed_stages = {
        operation.stage
        for operation in operations
        if operation.operation.startswith("STAGE_GATE:") and operation.state == "SUCCEEDED"
    }
    assert {
        AutoBookStage.RESEARCH,
        AutoBookStage.MIDBOOK_AUDIT,
        AutoBookStage.WHOLE_BOOK_EDIT,
        AutoBookStage.FACT_CHECK,
        AutoBookStage.INDEPENDENT_CRITIQUE,
    } <= completed_stages
    assert runtime.status != "PACKAGE_READY", "human audio approval is still required"

    before_opt_out = {
        "sources": len(research.list_sources(project.book_id)),
        "claims": len(research.list_claims(project.book_id)),
        "evidence": sum(
            len(research.list_evidence(project.book_id, item.claim_id))
            for item in research.list_claims(project.book_id)
        ),
    }
    contexts = BookContextService(tmp_path)
    contexts.set_public_bibliography(project.book_id, include=False)
    assert (
        AutoBookFinalizer(tmp_path, gateway)._verified_bibliography(project.book_id) == bibliography
    )
    after_opt_out = {
        "sources": len(research.list_sources(project.book_id)),
        "claims": len(research.list_claims(project.book_id)),
        "evidence": sum(
            len(research.list_evidence(project.book_id, item.claim_id))
            for item in research.list_claims(project.book_id)
        ),
    }
    assert after_opt_out == before_opt_out
    restored = contexts.set_public_bibliography(project.book_id, include=True)
    assert restored.include_bibliography is True

    # A saved targeted change is executed against only chapter 3. Its dependent QA,
    # evidence, visuals and final candidate are rebuilt without touching other chapters.
    finalizer = AutoBookFinalizer(tmp_path, gateway)
    units = finalizer._current_units(project.book_id)
    engine = create_database(project_dir / "project.sqlite")
    try:
        with engine.connect() as connection:
            before_heads = {
                str(row["unit_id"]): (str(row["revision_id"]), str(row["revision_hash"]))
                for row in connection.execute(
                    text(
                        "SELECT mu.unit_id,h.revision_id,h.revision_hash FROM manuscript_units mu "
                        "JOIN authority_heads h ON h.entity_id=mu.authority_entity_id"
                    )
                ).mappings()
            }
    finally:
        engine.dispose()
    change_id = service.runtime.request_change(
        project.book_id,
        state.run_id,
        "Уточни объяснение цены в главе 3, не меняя остальные главы.",
    )
    change = finalizer.execute_change(project.book_id, state, change_id)
    assert change["status"] == "DONE"
    assert change["result"]["affected_chapter"] == 3
    chapter_three_units = {
        str(item["unit_id"]) for item in units if int(item["chapter_ordinal"]) == 3
    }
    engine = create_database(project_dir / "project.sqlite")
    try:
        with engine.connect() as connection:
            after_heads = {
                str(row["unit_id"]): (str(row["revision_id"]), str(row["revision_hash"]))
                for row in connection.execute(
                    text(
                        "SELECT mu.unit_id,h.revision_id,h.revision_hash FROM manuscript_units mu "
                        "JOIN authority_heads h ON h.entity_id=mu.authority_entity_id"
                    )
                ).mappings()
            }
            stale_outputs = connection.execute(
                text("SELECT COUNT(*) FROM auto_book_output_artifacts WHERE status='STALE'")
            ).scalar_one()
            superseded_audio = connection.execute(
                text("SELECT COUNT(*) FROM audio_scripts WHERE status='SUPERSEDED'")
            ).scalar_one()
    finally:
        engine.dispose()
    assert chapter_three_units
    assert all(after_heads[unit_id] != before_heads[unit_id] for unit_id in chapter_three_units)
    assert all(
        after_heads[unit_id] == before_heads[unit_id]
        for unit_id in before_heads
        if unit_id not in chapter_three_units
    )
    assert set(change["result"]["changed_unit_ids"]) == chapter_three_units
    assert stale_outputs > 0
    assert superseded_audio == 1
    next_candidate = finalizer._final_candidate(project.book_id, state.run_id)
    assert next_candidate["status"] == "AWAITING"
    finalizer.decide_final_candidate(
        project.book_id,
        state,
        accept=True,
        human_actor="Елена Дым",
        reason="Принят точный кандидат после адресной доработки главы 3",
    )
    rebuilt = finalizer.finalize(project.book_id, state, prepare_litres_docx=True)
    assert rebuilt.master_id != final.master_id
    assert rebuilt.output_files
    assert all(item["status"] == "READY" for item in rebuilt.output_files)
