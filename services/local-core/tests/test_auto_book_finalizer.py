import json
from pathlib import Path
from zipfile import ZipFile

import pytest
from sqlalchemy import text

from book_os_core.auto_book import AutoBookService, AutoBookStartRequest
from book_os_core.auto_book_finalizer import (
    AUDIO_SCRIPT_EDITOR_V1,
    AUTO_BOOK_FINAL_EDIT_V1,
    AutoBookFinalizer,
)
from book_os_core.audio_script import AudioScriptService
from book_os_core.auto_book_runtime import AutoBookOutputSelection
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


class SimulatedProcessCrash(BaseException):
    pass


class PublishingAdapter(DeterministicFakeAdapter):
    def generate(self, request: ModelTaskRequest, prompt: PromptTemplate) -> ModelAdapterResult:
        self.task_calls = [*getattr(self, "task_calls", []), request.task_id]
        if prompt.prompt_id == AUDIO_SCRIPT_EDITOR_V1.prompt_id:
            self.audio_prompt_calls = getattr(self, "audio_prompt_calls", 0) + 1
        if request.task_type != "SECTION_DRAFT":
            return super().generate(request, prompt)

        self.last_request = request
        if prompt.prompt_id == AUTO_BOOK_FINAL_EDIT_V1.prompt_id:
            contract = request.authoritative_context["chapter_contract"]
            required_claims = contract.get("required_claims", [])
            required = " ".join(str(value) for value in required_claims)
            objective = request.section_objective
            first_chapter = "chapter 1" in objective
            if first_chapter:
                paragraphs = [
                    (
                        "Утро начинается с очереди вопросов у двери владельца: скидка для клиента, "
                        "перенос срока поставки, спор двух руководителей. Пока каждый нестандартный "
                        "случай возвращается наверх, скорость компании определяется доступностью "
                        "одного человека, а не качеством процессов."
                    ),
                    (
                        "Диагностика начинается с маршрута решения. Полезно за одну рабочую неделю "
                        "отмечать, кто инициировал вопрос, кто мог решить его по роли и почему он всё "
                        "же дошёл до владельца. Такая карта показывает реальные узкие места лучше, "
                        "чем перечень должностных инструкций."
                    ),
                    (
                        "Один тип задержек возникает из-за отсутствия границ полномочий. Руководитель "
                        "знает свою цель, но не знает диапазон суммы, риска или срока, в пределах "
                        "которого вправе действовать самостоятельно. Неопределённость превращает "
                        "осторожность в постоянную эскалацию."
                    ),
                    (
                        "Другой источник возврата решений — скрытая цена ошибки. Если сотрудника "
                        "наказывают за неудачный самостоятельный выбор сильнее, чем за ожидание "
                        "согласования, рациональной стратегией становится бездействие. Здесь нужно "
                        "исправлять не характер людей, а правила обратной связи."
                    ),
                    (
                        "Полезный показатель — доля вопросов, которые повторно приходят к одному и "
                        "тому же руководителю. Повтор означает, что организация не превратила "
                        "единичное решение в правило, критерий или границу ответственности. Каждый "
                        "такой возврат сохраняет зависимость от памяти конкретного человека."
                    ),
                    (
                        "Карта решений отделяет редкие стратегические выборы от операционной рутины. "
                        "Владелец должен оставлять за собой вопросы, где цена ошибки действительно "
                        "меняет траекторию бизнеса, а не привычно подтверждать то, что команда уже "
                        "может определить по известным критериям."
                    ),
                    (
                        "После диагностики появляется проверяемая картина: какие категории вопросов "
                        "застревают, на каком уровне возникает неопределённость и какие последствия "
                        "она создаёт для клиента, сроков и загрузки руководителей. Это уже основание "
                        "для изменения системы, а не впечатление о слабой инициативе команды."
                    ),
                    (
                        "Завершение первой главы фиксирует самостоятельный вывод: зависимость от "
                        "владельца измеряется маршрутом возвращающихся решений, поэтому первым шагом "
                        "становится наблюдение и классификация, а не немедленная раздача полномочий."
                    ),
                ]
                marker = "первой"
            else:
                paragraphs = [
                    (
                        "После карты узких мест задача меняется: теперь нужно спроектировать права "
                        "решений так, чтобы ответственность не растворилась. Делегирование без "
                        "критериев создаёт новую проблему — свобода появляется раньше общего "
                        "понимания допустимого риска."
                    ),
                    (
                        "Для каждой повторяющейся категории полезно задать четыре элемента: владельца "
                        "решения, границы допустимого выбора, сигнал для консультации и точку "
                        "последующей проверки. Такая конструкция делает автономию наблюдаемой и не "
                        "требует согласования каждого шага."
                    ),
                    (
                        "Финансовый предел — только один вид границы. В работе с клиентом важнее могут "
                        "быть репутационный риск, необратимость обещания или влияние на другие "
                        "проекты. Поэтому хорошее правило описывает смысл исключения, а не просто "
                        "число в таблице или схеме."
                    ),
                    (
                        "Контроль переносится с разрешения до действия на проверку после действия. "
                        "Руководитель заранее знает, какие решения попадут в обзор и какие данные "
                        "нужно сохранить. Владелец получает прозрачность без превращения прозрачности "
                        "в очередной предварительный барьер."
                    ),
                    (
                        "Первые недели требуют короткого цикла обратной связи. Разбирается не вопрос "
                        "«кто виноват», а соответствие выбранного действия установленным критериям, "
                        "качество исходных данных и достаточность самих границ. Так система учится на "
                        "решениях, не отбирая их обратно у команды."
                    ),
                    (
                        "Если исключения начинают повторяться, правило пересматривают. Один редкий "
                        "эпизод может остаться исключением, но пять похожих случаев уже указывают на "
                        "новый класс решения. Именно эта обратная связь превращает делегирование из "
                        "разовой договорённости в работающий контур управления."
                    ),
                    (
                        "Результат виден по изменению поведения системы: меньше предварительных "
                        "согласований, быстрее реакция на стандартные ситуации и больше времени у "
                        "владельца на решения, которые нельзя свести к заранее известному правилу. "
                        "Самостоятельность становится свойством процесса, а не личной смелостью."
                    ),
                    (
                        "Завершение второй главы фиксирует другую модель читателя: права решений "
                        "работают вместе с границами, журналом последствий и регулярным пересмотром, "
                        "поэтому контроль сохраняется даже тогда, когда владелец перестаёт быть "
                        "обязательной точкой каждого выбора."
                    ),
                ]
                marker = "второй"
            text_value = f"{required}.\n\n" + "\n\n".join(paragraphs)
            if request.authoritative_context.get("required_corrections"):
                text_value += (
                    "\n\nТочечное уточнение связывает решение с проверяемым критерием, "
                    "не меняя содержание остальных глав."
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
    adapter = PublishingAdapter()
    gateway = ModelGateway({"openai": adapter})
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
            final_human_acceptance_required=False,
        ),
    )
    state = auto.advance(book_id)
    assert state.status == "AWAITING_CONCEPT_APPROVAL"
    state = auto.accept_concept(book_id)
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

    # Concept + six planning/writing calls, two final edits and one independent critique.
    assert final.requests_used == 10
    assert adapter.last_request is not None
    assert adapter.last_request.role == "EVALUATOR"
    assert adapter.last_request.task_type == "BOOKBENCH_JUDGE"
    assert adapter.last_request.task_payload["independent_context"] is True
    exact_book = adapter.last_request.authoritative_context["complete_book"]
    assert len(exact_book["chapters"]) == 2
    assert adapter.last_request.authoritative_context["master_hash"]
    assert final.output_path is not None
    output = Path(final.output_path)
    assert output.is_file()
    assert output.name == "litres-ready.docx"
    with ZipFile(output) as archive:
        document = archive.read("word/document.xml").decode("utf-8")
    assert "Книга после финальной редактуры" in document
    assert "Завершение первой главы" in document
    assert "Завершение второй главы" in document
    runtime = AutoBookService(tmp_path, gateway).runtime.get(book_id, state.run_id)
    assert runtime.progress_percent == 100

    engine = create_database(tmp_path / "projects" / book_id / "project.sqlite")
    try:
        with engine.connect() as connection:
            masters = (
                connection.execute(
                    text("SELECT master_id,status,manifest_hash FROM literary_masters")
                )
                .mappings()
                .all()
            )
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
            approval_rows = list(
                connection.execute(
                    text(
                        "SELECT approving_actor,approving_actor_kind,gates_json FROM approvals "
                        "ORDER BY approval_id"
                    )
                ).mappings()
            )
            approval_gates = [json.loads(str(row["gates_json"])) for row in approval_rows]
            visual_kinds = set(
                connection.execute(
                    text("SELECT kind FROM auto_book_visual_assets WHERE status='READY'")
                ).scalars()
            )
    finally:
        engine.dispose()

    assert len(masters) == 1
    assert masters[0]["master_id"] == final.master_id
    assert masters[0]["status"] == "LOCKED"
    assert masters[0]["manifest_hash"] == final.master_manifest_hash
    assert "LITRES_DOCX" in export_formats
    assert unit_statuses and set(unit_statuses) == {"APPROVED"}
    assert any(item.get("final_editorial_pass") is True for item in approval_gates)
    assert any(row["approving_actor_kind"] == "SYSTEM" for row in approval_rows)
    assert all(
        row["approving_actor_kind"] == "SYSTEM"
        for row in approval_rows
        if str(row["approving_actor"]).startswith("system:auto-book:")
    )
    assert all(
        item.get("delegated_authorization_id") and item.get("auto_book_run_id")
        for item, row in zip(approval_gates, approval_rows, strict=True)
        if row["approving_actor_kind"] == "SYSTEM"
    )
    assert {"TABLE", "SCHEME"} <= visual_kinds
    visual_files = list((tmp_path / "projects" / book_id / "exports").rglob("*.png"))
    assert visual_files
    assert all(path.read_bytes().startswith(b"\x89PNG") for path in visual_files)


def test_audio_first_uses_approved_listening_master_without_redundant_rewrite_then_waits_for_human(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    book_id = ready_book(tmp_path)
    gateway = ModelGateway({"openai": PublishingAdapter()})
    auto = AutoBookService(tmp_path, gateway)
    state = auto.start(
        book_id,
        AutoBookStartRequest(
            idea="Создать книгу сразу для последовательного прослушивания.",
            delivery_profile="AUDIO_FIRST",
            outputs=AutoBookOutputSelection(
                full_manuscript_docx=False,
                audio_reading_docx=True,
            ),
            max_cost_usd_per_request=2,
            max_total_cost_usd=30,
            max_requests=30,
            prepare_litres_docx=False,
            owner_authorizes_auto_progress=True,
            final_human_acceptance_required=False,
        ),
    )
    state = auto.advance(book_id)
    state = auto.accept_concept(book_id)
    for _ in range(40):
        if state.status != "RUNNING":
            break
        state = auto.advance(book_id)
    assert state.status == "DONE"

    finalizer = AutoBookFinalizer(tmp_path, gateway)
    final = finalizer.finalize(book_id, state, prepare_litres_docx=False)
    assert final.awaiting_audio_approval is True
    assert final.audio_script_id is not None
    assert not {
        "AUDIO_READING_DOCX",
        "VOICE_TEXT_TXT",
        "AUDIO_PRODUCTION_HANDOFF",
    } & {item["output_kind"] for item in final.output_files}

    proposed = AudioScriptService(tmp_path).get(book_id, final.audio_script_id)
    assert proposed.adaptation_mode == "AUDIO_NATIVE"
    assert proposed.provenance["redundant_rewrite_skipped"] is True
    assert proposed.status == "PROPOSED"
    attention = sorted(
        {
            finding.code
            for check in proposed.quality_checks
            for finding in check.findings
            if finding.severity == "ATTENTION"
        }
    )
    approved = AudioScriptService(tmp_path).approve(
        book_id,
        proposed.audio_script_id,
        human_actor="Owner",
        accepted_attention_codes=attention,
    )
    approved_hash = approved.content_hash
    original_export = finalizer.exporter.export_selected

    def fail_after_approval(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise OSError("simulated export filesystem failure")

    monkeypatch.setattr(finalizer.exporter, "export_selected", fail_after_approval)
    with pytest.raises(OSError, match="simulated export"):
        finalizer.complete_audio_outputs(book_id, state, approved)
    persisted = AudioScriptService(tmp_path).get(book_id, approved.audio_script_id)
    assert persisted.status == "APPROVED"
    assert persisted.content_hash == approved_hash
    monkeypatch.setattr(finalizer.exporter, "export_selected", original_export)
    completed = finalizer.complete_audio_outputs(book_id, state, approved)
    kinds = {item["output_kind"] for item in completed.output_files}
    assert {"AUDIO_READING_DOCX", "VOICE_TEXT_TXT", "AUDIO_PRODUCTION_HANDOFF"} <= kinds
    retried = AudioScriptService(tmp_path).get(book_id, approved.audio_script_id)
    assert retried.status == "APPROVED"
    assert retried.content_hash == approved_hash


def test_text_first_audio_output_runs_a_real_separate_audio_editorial_pass(
    tmp_path: Path,
) -> None:
    book_id = ready_book(tmp_path)
    adapter = PublishingAdapter()
    gateway = ModelGateway({"openai": adapter})
    auto = AutoBookService(tmp_path, gateway)
    state = auto.start(
        book_id,
        AutoBookStartRequest(
            idea="Создать текстовую книгу и отдельную версию для прослушивания.",
            delivery_profile="TEXT_FIRST",
            outputs=AutoBookOutputSelection(
                full_manuscript_docx=True,
                audio_reading_docx=True,
            ),
            max_cost_usd_per_request=2,
            max_total_cost_usd=40,
            max_requests=40,
            prepare_litres_docx=False,
            owner_authorizes_auto_progress=True,
            final_human_acceptance_required=False,
        ),
    )
    state = auto.advance(book_id)
    state = auto.accept_concept(book_id)
    for _ in range(40):
        if state.status != "RUNNING":
            break
        state = auto.advance(book_id)
    assert state.status == "DONE"

    final = AutoBookFinalizer(tmp_path, gateway).finalize(
        book_id,
        state,
        prepare_litres_docx=False,
    )
    assert final.awaiting_audio_approval is True
    assert final.audio_script_id is not None
    proposed = AudioScriptService(tmp_path).get(book_id, final.audio_script_id)
    assert proposed.adaptation_mode == "SOURCE_FAITHFUL"
    assert getattr(adapter, "audio_prompt_calls", 0) == len(proposed.content.sections)
    assert all(
        section.paragraphs[0].startswith("Черновой материал")
        for section in proposed.content.sections
    )
    assert len(proposed.provenance["model_runs"]) == len(proposed.content.sections)


def test_final_candidate_requires_real_human_acceptance_before_master_lock(
    tmp_path: Path,
) -> None:
    book_id = ready_book(tmp_path)
    gateway = ModelGateway({"openai": PublishingAdapter()})
    auto = AutoBookService(tmp_path, gateway)
    state = auto.start(
        book_id,
        AutoBookStartRequest(
            idea="Подготовить книгу и остановиться перед настоящим финальным решением автора.",
            max_cost_usd_per_request=2,
            max_total_cost_usd=30,
            max_requests=30,
            prepare_litres_docx=False,
            owner_authorizes_auto_progress=True,
        ),
    )
    state = auto.advance(book_id)
    state = auto.accept_concept(book_id)
    for _ in range(40):
        if state.status != "RUNNING":
            break
        state = auto.advance(book_id)
    assert state.status == "DONE"

    finalizer = AutoBookFinalizer(tmp_path, gateway)
    candidate_view = finalizer.finalize(book_id, state, prepare_litres_docx=False)
    assert candidate_view.awaiting_final_acceptance is True
    assert candidate_view.master_id is None
    engine = create_database(tmp_path / "projects" / book_id / "project.sqlite")
    try:
        with engine.connect() as connection:
            assert (
                connection.execute(text("SELECT COUNT(*) FROM literary_masters")).scalar_one() == 0
            )
    finally:
        engine.dispose()

    accepted = finalizer.decide_final_candidate(
        book_id,
        state,
        accept=True,
        human_actor="Тестовый автор",
        reason="Автор проверил точный финальный кандидат",
    )
    assert accepted["actor_kind"] == "HUMAN"
    released = finalizer.finalize(book_id, state, prepare_litres_docx=False)
    assert released.master_id is not None
    master = finalizer.literary.get_master(book_id, released.master_id)
    assert master.status == "LOCKED"
    assert master.human_actor == "Тестовый автор"
    assert master.acceptance_actor_kind == "HUMAN"


def test_stale_final_candidate_cannot_be_accepted(tmp_path: Path) -> None:
    book_id = ready_book(tmp_path)
    gateway = ModelGateway({"openai": PublishingAdapter()})
    auto = AutoBookService(tmp_path, gateway)
    state = auto.start(
        book_id,
        AutoBookStartRequest(
            idea="Проверить запрет принятия устаревшего финального снимка.",
            max_cost_usd_per_request=2,
            max_total_cost_usd=40,
            max_requests=40,
            prepare_litres_docx=False,
            owner_authorizes_auto_progress=True,
        ),
    )
    state = auto.advance(book_id)
    state = auto.accept_concept(book_id)
    for _ in range(40):
        if state.status != "RUNNING":
            break
        state = auto.advance(book_id)
    finalizer = AutoBookFinalizer(tmp_path, gateway)
    candidate = finalizer.finalize(book_id, state, prepare_litres_docx=False)
    assert candidate.final_candidate_id is not None
    unit = finalizer._current_units(book_id)[0]
    finalizer._final_edit_unit(
        book_id,
        state,
        unit,
        finalizer._book_context(book_id),
        correction_findings=[{"required_action": "Уточнить один абзац"}],
    )
    with pytest.raises(Exception, match="stale"):
        finalizer.decide_final_candidate(
            book_id,
            state,
            accept=True,
            human_actor="Тестовый автор",
            reason="Попытка принять старый снимок",
        )
    assert finalizer._final_candidate(book_id, state.run_id)["status"] == "STALE"


def test_final_edit_and_independent_critique_reuse_confirmed_results_after_crash(
    tmp_path: Path,
) -> None:
    book_id = ready_book(tmp_path)
    adapter = PublishingAdapter()
    gateway = ModelGateway({"openai": adapter})
    auto = AutoBookService(tmp_path, gateway)
    state = auto.start(
        book_id,
        AutoBookStartRequest(
            idea="Проверить crash recovery финальной редактуры и независимой критики.",
            max_cost_usd_per_request=2,
            max_total_cost_usd=40,
            max_requests=40,
            prepare_litres_docx=False,
            owner_authorizes_auto_progress=True,
        ),
    )
    state = auto.advance(book_id)
    state = auto.accept_concept(book_id)
    for _ in range(40):
        if state.status != "RUNNING":
            break
        state = auto.advance(book_id)

    first = AutoBookFinalizer(tmp_path, gateway)

    def crash_on_first_final_edit(operation: str, operation_id: str) -> None:
        del operation_id
        if operation.startswith("FINAL_EDIT:"):
            raise SimulatedProcessCrash(operation)

    setattr(first, "_after_paid_operation_commit", crash_on_first_final_edit)
    with pytest.raises(SimulatedProcessCrash):
        first.finalize(book_id, state, prepare_litres_docx=False)
    operations = first.runtime.list_operations(book_id, state.run_id)
    first_edit = next(item for item in operations if item.operation.startswith("FINAL_EDIT:"))
    assert first_edit.state == "SUCCEEDED"
    calls_after_edit_crash = len(adapter.task_calls)

    second = AutoBookFinalizer(tmp_path, gateway)

    def crash_on_critique(operation: str, operation_id: str) -> None:
        del operation_id
        if operation.startswith("INDEPENDENT_CRITIQUE:"):
            raise SimulatedProcessCrash(operation)

    setattr(second, "_after_paid_operation_commit", crash_on_critique)
    with pytest.raises(SimulatedProcessCrash):
        second.finalize(book_id, state, prepare_litres_docx=False)
    operations = second.runtime.list_operations(book_id, state.run_id)
    critique = next(
        item for item in operations if item.operation.startswith("INDEPENDENT_CRITIQUE:")
    )
    assert critique.state == "SUCCEEDED"
    assert len(adapter.task_calls) == calls_after_edit_crash + 2
    critique_calls = len(adapter.task_calls)

    recovered = AutoBookFinalizer(tmp_path, gateway).finalize(
        book_id, state, prepare_litres_docx=False
    )
    assert recovered.awaiting_final_acceptance is True
    assert len(adapter.task_calls) == critique_calls
