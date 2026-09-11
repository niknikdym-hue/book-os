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
                        "число в таблице."
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
