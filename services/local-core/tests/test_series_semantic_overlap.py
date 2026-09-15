from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from book_os_core.book_context import ProfileCreateRequest, ProfileRegistry
from book_os_core.projects import BookArchitecturePayload, BookContractPayload, ProjectService
from book_os_core.series_similarity import _CASE_RE, _best_marked_pair, semantic_series_findings
from book_os_core.series_workspace import (
    SeriesBookCreateRequest,
    SeriesCreateRequest,
    SeriesOverlapDispositionRequest,
    SeriesWorkspaceGateError,
    SeriesWorkspaceService,
)


def _book(
    book_id: str,
    *,
    idea: str,
    problem: str,
    result: str,
    mechanism: str,
) -> SimpleNamespace:
    return SimpleNamespace(
        book_id=book_id,
        unique_idea=idea,
        reader_problem=problem,
        reader_result=result,
        unique_mechanism=mechanism,
    )


def _source(sample: str) -> dict[str, object]:
    return {"analysis": {"sample": sample}}


def _dimensions(findings: list[object]) -> set[str]:
    return {str(getattr(item, "dimension")) for item in findings}


def test_paraphrased_thesis_is_blocked_after_semantic_normalization() -> None:
    left = _book(
        "L" * 26,
        idea=(
            "Покупатель услуги принимает решение, когда заранее видит доказательства результата "
            "и понимает риск выбора исполнителя"
        ),
        problem="Клиент сомневается в результате до покупки",
        result="Клиент принимает обоснованное решение",
        mechanism="Снизить риск через доказательства результата до оплаты",
    )
    right = _book(
        "R" * 26,
        idea=(
            "Продажа строится на снижении неопределенности: клиенту нужны подтверждения эффекта "
            "до оплаты"
        ),
        problem="Заказчик не уверен в эффекте перед договором",
        result="Заказчик делает уверенный выбор",
        mechanism="Подтверждения результата уменьшают неопределенность до сделки",
    )
    findings = semantic_series_findings(
        left,
        right,
        left_architecture=[],
        right_architecture=[],
        left_sources=[],
        right_sources=[],
    )
    assert "THESIS" in _dimensions(findings)
    finding = next(item for item in findings if item.dimension == "THESIS")
    assert finding.severity == "BLOCKING"
    assert finding.evidence["comparison_basis"] == "SEMANTIC_PASSPORT_V1"


def test_profession_swapped_architecture_is_blocked() -> None:
    left = _book(
        "A" * 26,
        idea="Отдельная территория психологической практики",
        problem="Управление расписанием",
        result="Устойчивая загрузка",
        mechanism="Работа с календарём",
    )
    right = _book(
        "B" * 26,
        idea="Отдельная территория юридической практики",
        problem="Управление документами",
        result="Предсказуемая подготовка",
        mechanism="Работа с регламентом",
    )
    left_architecture = [
        {
            "title": "Спрос психолога",
            "purpose": "Диагностировать спрос на услуги психолога",
            "new_contribution": "Карта запросов и критериев клиента",
        },
        {
            "title": "Доверие",
            "purpose": "Собрать доказательства доверия к психологу",
            "new_contribution": "Матрица подтверждений для решения клиента",
        },
        {
            "title": "Цена",
            "purpose": "Объяснить цену психологической услуги до покупки",
            "new_contribution": "Схема риска, стоимости и результата клиента",
        },
    ]
    right_architecture = [
        {
            "title": "Запрос юриста",
            "purpose": "Выявить потребность в юридических услугах",
            "new_contribution": "Схема запросов и критериев заказчика",
        },
        {
            "title": "Подтверждения",
            "purpose": "Укрепить доверие к юристу доказательствами",
            "new_contribution": "Карта подтверждений перед выбором заказчика",
        },
        {
            "title": "Стоимость",
            "purpose": "Объяснить стоимость юридической помощи до договора",
            "new_contribution": "Модель риска, цены и результата заказчика",
        },
    ]
    findings = semantic_series_findings(
        left,
        right,
        left_architecture=left_architecture,
        right_architecture=right_architecture,
        left_sources=[],
        right_sources=[],
    )
    architecture = next(item for item in findings if item.dimension == "ARCHITECTURE")
    assert architecture.severity == "BLOCKING"
    assert architecture.evidence["comparison_basis"] == "DOMAIN_NEUTRALIZED_CURRENT_ARCHITECTURE"


def test_reworded_case_and_renamed_tool_are_blocked() -> None:
    left = _book(
        "C" * 26,
        idea="Самостоятельная тема один",
        problem="Проблема один",
        result="Результат один",
        mechanism="Механизм один",
    )
    right = _book(
        "D" * 26,
        idea="Самостоятельная тема два",
        problem="Проблема два",
        result="Результат два",
        mechanism="Механизм два",
    )
    left_sample = (
        "Например, психолог получает запрос клиента о цене, но клиент отказывается без "
        "доказательств результата и уверенного решения. "
        "Матрица доверия помогает клиенту сопоставить риск, доказательства результата, цену и "
        "решение о покупке."
    )
    right_sample = (
        "Кейс: юрист слышит вопрос заказчика о стоимости; без подтверждения эффекта заказчик "
        "сомневается и не принимает решение. "
        "Карта уверенности позволяет заказчику сравнить неопределенность, подтверждения эффекта, "
        "стоимость и выбор перед оплатой."
    )
    findings = semantic_series_findings(
        left,
        right,
        left_architecture=[],
        right_architecture=[],
        left_sources=[_source(left_sample)],
        right_sources=[_source(right_sample)],
    )
    assert {"EXAMPLE", "TOOL"} <= _dimensions(findings)
    assert all(
        item.severity == "BLOCKING" for item in findings if item.dimension in {"EXAMPLE", "TOOL"}
    )


def test_profession_swapped_template_is_blocked_even_when_words_are_not_identical() -> None:
    left = _book(
        "E" * 26,
        idea="Территория один",
        problem="Проблема один",
        result="Результат один",
        mechanism="Механизм один",
    )
    right = _book(
        "F" * 26,
        idea="Территория два",
        problem="Проблема два",
        result="Результат два",
        mechanism="Механизм два",
    )
    left_text = (
        "Психолог сначала уточняет запрос клиента, затем показывает доказательства результата, "
        "объясняет цену и риск, после чего помогает клиенту принять решение о покупке услуги."
    )
    right_text = (
        "Юрист сначала уточняет запрос заказчика, затем показывает подтверждения эффекта, "
        "объясняет стоимость и неопределенность, после чего помогает заказчику сделать выбор "
        "перед договором."
    )
    findings = semantic_series_findings(
        left,
        right,
        left_architecture=[],
        right_architecture=[],
        left_sources=[_source(left_text)],
        right_sources=[_source(right_text)],
    )
    language = next(item for item in findings if item.dimension == "LANGUAGE")
    assert language.severity == "BLOCKING"
    assert language.evidence["comparison_basis"] == "PROFESSION_SWAPPED_TEMPLATE_V1"


def _approved_series(tmp_path: Path) -> tuple[SeriesWorkspaceService, str]:
    registry = ProfileRegistry(tmp_path)
    author = registry.approve_profile(
        registry.create_profile(
            ProfileCreateRequest(kind="AUTHOR", content={"author_name": "Тестовый автор"})
        ).profile_id
    )
    service = SeriesWorkspaceService(tmp_path)
    profile = service.create_series(
        SeriesCreateRequest(
            series_name="Семантическая серия",
            author_profile_id=author.profile_id,
            audience="Профессиональные практики",
            promise="Разные книги решают разные задачи",
            territory="Продажи профессиональных услуг",
        )
    )
    registry.approve_profile(profile.profile_id)
    return service, profile.profile_id


def test_semantic_architecture_finding_is_persisted_and_blocks_map_approval(tmp_path: Path) -> None:
    service, series_id = _approved_series(tmp_path)
    left = service.add_book(
        series_id,
        SeriesBookCreateRequest(
            title="Практика психолога",
            ordinal=1,
            unique_idea="Настроить рабочий календарь частной практики",
            reader_problem="Неровная загрузка недели",
            reader_result="Сбалансированное расписание",
            unique_mechanism="Ритм планирования приёмов",
        ),
    )
    right = service.add_book(
        series_id,
        SeriesBookCreateRequest(
            title="Практика юриста",
            ordinal=2,
            unique_idea="Организовать поток договорных документов",
            reader_problem="Документы теряются между этапами",
            reader_result="Предсказуемая подготовка дел",
            unique_mechanism="Регламент движения документов",
        ),
    )
    projects = ProjectService(tmp_path)
    contract = BookContractPayload(
        reader="Владелец профессиональной практики",
        reader_problem="Нужно управлять отдельной рабочей системой",
        central_promise="Получить проверяемую систему решений",
        central_thesis="Управляемость возникает из явных критериев и последовательных действий",
        unique_angle="Разобрать практику по наблюдаемым решениям",
        reader_trajectory="От симптомов к самостоятельной диагностике",
        explicit_exclusions=["Не каталог общих советов"],
        evidence_policy="Материальные утверждения требуют evidence",
        voice_genre_constraints="Точный практический нон-фикшн",
        readiness_criteria=["Читатель применяет критерий самостоятельно"],
    )
    left_arch = BookArchitecturePayload.model_validate(
        {
            "parts": [
                {
                    "title": "Работа психолога",
                    "purpose": "От спроса к решению",
                    "chapters": [
                        {
                            "title": "Спрос",
                            "purpose": "Диагностировать спрос на услуги психолога",
                            "new_contribution": "Карта запросов и критериев клиента",
                        },
                        {
                            "title": "Доверие",
                            "purpose": "Собрать доказательства доверия к психологу",
                            "new_contribution": "Матрица подтверждений для решения клиента",
                            "dependencies": ["Спрос"],
                            "transition": "От спроса к доверию",
                        },
                        {
                            "title": "Цена",
                            "purpose": "Объяснить цену психологической услуги до покупки",
                            "new_contribution": "Схема риска, стоимости и результата клиента",
                            "dependencies": ["Доверие"],
                            "transition": "От доверия к цене",
                        },
                    ],
                }
            ],
            "intellectual_progression": "Спрос, доверие, цена",
            "concept_allocation": "Каждая глава выполняет отдельную функцию",
            "promise_thesis_coverage": "Архитектура покрывает обещание",
            "major_transitions": "Каждый переход меняет решение читателя",
        }
    )
    right_arch = BookArchitecturePayload.model_validate(
        {
            "parts": [
                {
                    "title": "Работа юриста",
                    "purpose": "От потребности к договору",
                    "chapters": [
                        {
                            "title": "Потребность",
                            "purpose": "Выявить потребность в юридических услугах",
                            "new_contribution": "Схема запросов и критериев заказчика",
                        },
                        {
                            "title": "Подтверждения",
                            "purpose": "Укрепить доверие к юристу доказательствами",
                            "new_contribution": "Карта подтверждений перед выбором заказчика",
                            "dependencies": ["Потребность"],
                            "transition": "От запроса к доверию",
                        },
                        {
                            "title": "Стоимость",
                            "purpose": "Объяснить стоимость юридической помощи до договора",
                            "new_contribution": "Модель риска, цены и результата заказчика",
                            "dependencies": ["Подтверждения"],
                            "transition": "От доверия к стоимости",
                        },
                    ],
                }
            ],
            "intellectual_progression": "Потребность, доверие, стоимость",
            "concept_allocation": "Каждая глава выполняет отдельную функцию",
            "promise_thesis_coverage": "Архитектура покрывает обещание",
            "major_transitions": "Каждый переход меняет решение читателя",
        }
    )
    for entry, architecture in ((left, left_arch), (right, right_arch)):
        projects.save_book_contract(entry.book_id, contract)
        projects.approve_book_contract(entry.book_id)
        projects.save_architecture(entry.book_id, architecture)
        projects.approve_architecture(entry.book_id)

    result = service.analyze(series_id)
    semantic = [
        item
        for item in result.findings
        if item["dimension"] == "ARCHITECTURE"
        and item["evidence"].get("comparison_basis") == "DOMAIN_NEUTRALIZED_CURRENT_ARCHITECTURE"
    ]
    assert result.status == "BLOCKING"
    assert len(semantic) == 1
    reloaded = service.current_map(series_id)
    assert reloaded is not None and reloaded.status == "BLOCKING"
    assert any(
        item["evidence"].get("semantic_signature") == semantic[0]["evidence"]["semantic_signature"]
        for item in reloaded.findings
    )
    with pytest.raises(SeriesWorkspaceGateError, match="blocking overlap"):
        service.approve_map(series_id, result.map_hash, "Смысловой клон нельзя утвердить")


def test_added_or_reordered_chapter_does_not_disable_architecture_clone_detection() -> None:
    left = _book(
        "G" * 26,
        idea="Календарь частной практики",
        problem="Неровная загрузка",
        result="Стабильный график",
        mechanism="Планирование недели",
    )
    right = _book(
        "H" * 26,
        idea="Документы юридической практики",
        problem="Потери документов",
        result="Контролируемый документооборот",
        mechanism="Регламент дела",
    )
    base = [
        {
            "purpose": "Диагностировать спрос на услуги психолога",
            "new_contribution": "Карта запросов и критериев клиента",
        },
        {
            "purpose": "Собрать доказательства доверия к психологу",
            "new_contribution": "Матрица подтверждений для решения клиента",
        },
        {
            "purpose": "Объяснить цену психологической услуги до покупки",
            "new_contribution": "Схема риска стоимости и результата клиента",
        },
    ]
    disguised = [
        {
            "purpose": "Объяснить стоимость юридической помощи до договора",
            "new_contribution": "Модель риска цены и результата заказчика",
        },
        {
            "purpose": "Служебная дополнительная глава про организацию практики",
            "new_contribution": "Короткий организационный переход между решениями",
        },
        {
            "purpose": "Выявить потребность в юридических услугах",
            "new_contribution": "Схема запросов и критериев заказчика",
        },
        {
            "purpose": "Укрепить доверие к юристу доказательствами",
            "new_contribution": "Карта подтверждений перед выбором заказчика",
        },
    ]
    findings = semantic_series_findings(
        left,
        right,
        left_architecture=base,
        right_architecture=disguised,
        left_sources=[],
        right_sources=[],
    )
    architecture = next(item for item in findings if item.dimension == "ARCHITECTURE")
    assert architecture.severity == "BLOCKING"
    assert architecture.evidence["left_chapter_count"] == 3
    assert architecture.evidence["right_chapter_count"] == 4
    assert architecture.evidence["order_independent"] is True


def test_genuinely_different_architectures_in_same_field_are_not_blocked() -> None:
    left = _book(
        "I" * 26,
        idea="Экономика частной практики",
        problem="Непонятна маржинальность",
        result="Прозрачная экономика",
        mechanism="Модель юнит-экономики",
    )
    right = _book(
        "J" * 26,
        idea="Коммуникация с клиентом",
        problem="Теряются договорённости",
        result="Предсказуемая коммуникация",
        mechanism="Протокол встреч",
    )
    left_arch = [
        {
            "purpose": "Посчитать постоянные расходы практики",
            "new_contribution": "Карта затрат по месяцам",
        },
        {
            "purpose": "Определить прибыль на услугу",
            "new_contribution": "Формула маржинальности услуги",
        },
        {
            "purpose": "Проверить окупаемость рекламы",
            "new_contribution": "Порог допустимой стоимости привлечения",
        },
    ]
    right_arch = [
        {
            "purpose": "Подготовить первую встречу с клиентом",
            "new_contribution": "Сценарий сбора ожиданий",
        },
        {
            "purpose": "Фиксировать договорённости после разговора",
            "new_contribution": "Протокол итогов встречи",
        },
        {
            "purpose": "Разрешать конфликт ожиданий",
            "new_contribution": "Алгоритм уточнения спорных формулировок",
        },
        {
            "purpose": "Завершать проект без потери отношений",
            "new_contribution": "Сценарий финальной коммуникации",
        },
    ]
    findings = semantic_series_findings(
        left,
        right,
        left_architecture=left_arch,
        right_architecture=right_arch,
        left_sources=[],
        right_sources=[],
    )
    assert "ARCHITECTURE" not in _dimensions(findings)


def test_domain_independent_reordered_architecture_clone_is_blocked() -> None:
    left = _book(
        "K" * 26,
        idea="Самостоятельная практика музыканта",
        problem="Нет системы занятий",
        result="Измеримый прогресс",
        mechanism="Цикл диагностики, плана, практики и обратной связи",
    )
    right = _book(
        "M" * 26,
        idea="Самостоятельный ремонт квартиры",
        problem="Работы идут хаотично",
        result="Контролируемый ремонт",
        mechanism="Цикл оценки, плана, выполнения и контроля",
    )
    music = [
        {
            "purpose": "Оценить исходный уровень музыканта",
            "new_contribution": "Шкала критериев стартового уровня",
        },
        {
            "purpose": "Составить план ежедневной практики",
            "new_contribution": "Календарь приоритетов упражнений",
        },
        {
            "purpose": "Выполнить цикл практики по плану",
            "new_contribution": "Протокол действий на занятии",
        },
        {
            "purpose": "Отслеживать прогресс и корректировать ошибки",
            "new_contribution": "Шкала контроля и исправления",
        },
    ]
    renovation = [
        {
            "purpose": "Контролировать результат и исправлять отклонения ремонта",
            "new_contribution": "Шкала контроля и корректировки",
        },
        {
            "purpose": "Проверить исходное состояние квартиры",
            "new_contribution": "Матрица критериев стартового состояния",
        },
        {
            "purpose": "Предотвратить аварийные риски до начала работ",
            "new_contribution": "Короткий контроль безопасности",
        },
        {
            "purpose": "Подготовить план последовательности работ",
            "new_contribution": "Календарь приоритетов этапов",
        },
        {
            "purpose": "Выполнить работы по утверждённому плану",
            "new_contribution": "Протокол действий на этапе",
        },
    ]
    findings = semantic_series_findings(
        left,
        right,
        left_architecture=music,
        right_architecture=renovation,
        left_sources=[],
        right_sources=[],
    )
    architecture = next(item for item in findings if item.dimension == "ARCHITECTURE")
    assert architecture.severity == "BLOCKING"
    assert architecture.evidence["order_independent"] is True
    assert architecture.evidence["left_chapter_count"] == 4
    assert architecture.evidence["right_chapter_count"] == 5


def test_reworded_analogy_is_blocked_across_unrelated_domains() -> None:
    left = _book("N" * 26, idea="Музыка", problem="Хаос", result="Прогресс", mechanism="Практика")
    right = _book("P" * 26, idea="Ремонт", problem="Хаос", result="Контроль", mechanism="Этапы")
    left_text = (
        "Представьте обучение как навигацию: сначала оцениваем точку старта, затем строим план "
        "маршрута, отслеживаем прогресс и корректируем курс при ошибке."
    )
    right_text = (
        "Словно ремонт — это путешествие: сперва проверяем исходное состояние, потом составляем "
        "план пути, контролируем изменения и исправляем отклонения."
    )
    findings = semantic_series_findings(
        left,
        right,
        left_architecture=[],
        right_architecture=[],
        left_sources=[_source(left_text)],
        right_sources=[_source(right_text)],
    )
    analogy = next(item for item in findings if item.dimension == "ANALOGY")
    assert analogy.severity == "BLOCKING"
    assert analogy.evidence["comparison_basis"] == "PARAPHRASED_ANALOGY_V1"


def test_domain_independent_function_template_is_blocked_without_profession_terms() -> None:
    left = _book("Q" * 26, idea="Музыка", problem="Хаос", result="Прогресс", mechanism="Практика")
    right = _book("S" * 26, idea="Ремонт", problem="Хаос", result="Контроль", mechanism="Этапы")
    left_text = (
        "Сначала оцените исходное состояние, затем подготовьте план, выполните действия, "
        "отслеживайте прогресс и корректируйте ошибки по критериям результата."
    )
    right_text = (
        "Сначала проверьте стартовое состояние, затем составьте план, примените действия, "
        "контролируйте изменения и исправляйте отклонения по критериям результата."
    )
    findings = semantic_series_findings(
        left,
        right,
        left_architecture=[],
        right_architecture=[],
        left_sources=[_source(left_text)],
        right_sources=[_source(right_text)],
    )
    language = next(item for item in findings if item.dimension == "LANGUAGE")
    assert language.severity == "BLOCKING"
    assert language.evidence["comparison_basis"] == "DOMAIN_INDEPENDENT_FUNCTION_TEMPLATE_V2"


def test_overlap_exception_requires_explicit_human_actor(tmp_path: Path) -> None:
    service, series_id = _approved_series(tmp_path)
    service.add_book(
        series_id,
        SeriesBookCreateRequest(
            title="Первая книга",
            ordinal=1,
            unique_idea="Спрос, доверие, доказательства, риск, цена и решение",
            reader_problem="Клиент сомневается в выборе, цене, риске и результате",
            reader_result="Клиент принимает решение на основе доказательств",
            unique_mechanism="Диагностика спроса, доказательства доверия, оценка риска, цены и решения",
        ),
    )
    service.add_book(
        series_id,
        SeriesBookCreateRequest(
            title="Вторая книга",
            ordinal=2,
            unique_idea="Спрос, доверие, доказательства, риск, цена и решение",
            reader_problem="Клиент сомневается в выборе, цене, риске и результате",
            reader_result="Клиент принимает решение на основе доказательств",
            unique_mechanism="Диагностика спроса, доказательства доверия, оценка риска, цены и решения",
        ),
    )
    result = service.analyze(series_id)
    thesis = next(item for item in result.findings if item["dimension"] == "THESIS")
    with pytest.raises(SeriesWorkspaceGateError, match="explicit HUMAN actor"):
        service.dispose_overlap(
            series_id,
            thesis["finding_id"],
            SeriesOverlapDispositionRequest(
                classification="NEW_CONTEXT_APPLICATION",
                reason="Попытка автоматического исключения должна быть запрещена",
            ),
            actor="AI:AUTO",
        )


def test_new_series_records_strict_cross_book_uniqueness_policy(tmp_path: Path) -> None:
    service, series_id = _approved_series(tmp_path)
    profile = service.profiles.get_profile(series_id)
    rules = profile.content["cross_book_uniqueness_rules"]
    assert any("аналогий" in value and "шаблонов" in value for value in rules)
    assert any("HUMAN" in value and "finding" in value for value in rules)


def test_marked_pair_index_preserves_full_import_late_match() -> None:
    noise_left = "\n".join(
        f"Пример {index}: локальная история без общего механизма и без повторяемого решения."
        for index in range(250)
    )
    noise_right = "\n".join(
        f"Кейс {index}: отдельная ситуация без общего механизма и без повторяемого решения."
        for index in range(250)
    )
    repeated_left = (
        "Например, сначала оцените спрос и риск, затем соберите доказательства доверия, "
        "сравните цену и примите решение по проверяемым критериям результата."
    )
    repeated_right = (
        "Кейс: сначала проверьте спрос и риск, затем соберите подтверждения доверия, "
        "сопоставьте цену и примите решение по измеримым критериям результата."
    )
    pair = _best_marked_pair(
        noise_left + "\n" + repeated_left,
        noise_right + "\n" + repeated_right,
        marker=_CASE_RE,
        threshold=0.56,
    )
    assert pair is not None
    assert "спрос" in pair[0]
    assert "спрос" in pair[1]
