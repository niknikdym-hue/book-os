#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve()


def replace_once(rel: str, old: str, new: str) -> None:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"expected one match in {rel}: {old[:120]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def append(rel: str, value: str) -> None:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    if value.strip() in text:
        raise SystemExit(f"test block already present in {rel}")
    path.write_text(text.rstrip() + "\n\n" + value.strip() + "\n", encoding="utf-8")


SIM = "services/local-core/src/book_os_core/series_similarity.py"
WORKSPACE = "services/local-core/src/book_os_core/series_workspace.py"
BASE = "services/local-core/src/book_os_core/series_workspace_base.py"
TEST = "services/local-core/tests/test_series_semantic_overlap.py"

replace_once(
    SIM,
    '''    ("case", ("кейс", "пример", "истори", "ситуац", "сценари")),\n)\n''',
    '''    ("assess", ("оцен", "провер", "измер", "тестир", "аудит", "inspect", "assess", "measure", "audit", "test")),\n    ("plan", ("план", "стратег", "маршрут", "приоритет", "очеред", "этап", "schedule", "plan", "strateg", "priorit", "roadmap")),\n    ("prepare", ("подготов", "настро", "готов", "setup", "prepar", "configur")),\n    ("organize", ("организ", "структур", "системат", "регламент", "процесс", "organize", "structur", "process")),\n    ("create", ("созда", "постро", "разработ", "проектир", "формир", "состав", "design", "build", "creat", "develop")),\n    ("execute", ("выполн", "внедр", "примен", "запуск", "провод", "практик", "реализ", "implement", "execut", "apply", "practic", "launch")),\n    ("monitor", ("контрол", "отслеж", "наблюд", "монитор", "учет", "track", "monitor", "control")),\n    ("improve", ("улучш", "оптимиз", "коррект", "исправ", "адапт", "совершен", "improv", "optimiz", "correct", "adapt")),\n    ("communicate", ("коммуникац", "переговор", "объясн", "обсужд", "сообщ", "диалог", "разговор", "communicat", "negot", "explain", "discuss")),\n    ("learn", ("обуч", "изуч", "осво", "понима", "запом", "learn", "study", "understand")),\n    ("document", ("документ", "запис", "фиксац", "протокол", "реестр", "журнал", "record", "document", "protocol")),\n    ("constraint", ("огранич", "границ", "услов", "правил", "критер", "constraint", "boundary", "rule", "criter")),\n    ("safety", ("безопас", "защит", "предотвращ", "ошиб", "сбо", "авари", "secure", "safe", "prevent", "error", "failure")),\n    ("resource", ("ресурс", "врем", "бюджет", "мощност", "нагруз", "capacity", "resource", "budget", "time")),\n    ("progress", ("прогресс", "динамик", "рост", "снижен", "изменен", "progress", "change", "growth")),\n    ("case", ("кейс", "пример", "истори", "ситуац", "сценари")),\n)\n''',
)

replace_once(
    SIM,
    '''_CASE_RE = re.compile(r"\\b(?:например|кейс|пример|истори\\w*|ситуаци\\w*|сценари\\w*)\\b", re.I)\n_TOOL_RE = re.compile(\n''',
    '''_CASE_RE = re.compile(r"\\b(?:например|кейс|пример|истори\\w*|ситуаци\\w*|сценари\\w*)\\b", re.I)\n_ANALOGY_RE = re.compile(\n    r"(?:\\bаналог\\w*\\b|\\bметафор\\w*\\b|\\bсловно\\b|\\bподобн\\w*\\b|"\n    r"\\bпредставьте\\b|как будто|\\bнапомина\\w*\\b)",\n    re.I,\n)\n_TOOL_RE = re.compile(\n''',
)

replace_once(
    SIM,
    '''def _signature(dimension: str, left_id: str, right_id: str, evidence: dict[str, Any]) -> str:\n''',
    '''def _domain_independent_template(\n    left_sample: str, right_sample: str\n) -> tuple[str, str, float] | None:\n    """Find a repeated functional sentence template without assuming a profession/domain list."""\n    left_rows = [\n        (value, semantic_families(value))\n        for value in _sentences(left_sample)\n        if len(semantic_families(value)) >= 4\n    ]\n    right_rows = [\n        (value, semantic_families(value))\n        for value in _sentences(right_sample)\n        if len(semantic_families(value)) >= 4\n    ]\n    inverted: dict[str, set[int]] = {}\n    for index, (_, families) in enumerate(right_rows):\n        for family in families:\n            inverted.setdefault(family, set()).add(index)\n\n    best: tuple[str, str, float] | None = None\n    for left_text, left_families in left_rows:\n        counts: dict[int, int] = {}\n        for family in left_families:\n            for index in inverted.get(family, set()):\n                counts[index] = counts.get(index, 0) + 1\n        for index, shared_count in counts.items():\n            if shared_count < 4:\n                continue\n            right_text, right_families = right_rows[index]\n            if left_text.casefold() == right_text.casefold():\n                continue\n            family_score = _jaccard(left_families, right_families)\n            if family_score < 0.60:\n                continue\n            token_score = semantic_score(left_text, right_text)\n            left_canonical = " ".join(sorted(left_families))\n            right_canonical = " ".join(sorted(right_families))\n            structure_score = SequenceMatcher(None, left_canonical, right_canonical).ratio()\n            score = max(token_score, family_score, structure_score)\n            if score < 0.72:\n                continue\n            lexical_overlap = len(semantic_tokens(left_text) & semantic_tokens(right_text))\n            if lexical_overlap < 3 and family_score < 0.75:\n                continue\n            if best is None or score > best[2]:\n                best = (left_text, right_text, score)\n    return best\n\n\ndef _signature(dimension: str, left_id: str, right_id: str, evidence: dict[str, Any]) -> str:\n''',
)

replace_once(
    SIM,
    '''    renamed_tool = _best_marked_pair(left_sample, right_sample, marker=_TOOL_RE, threshold=0.52)\n''',
    '''    repeated_analogy = _best_marked_pair(\n        left_sample, right_sample, marker=_ANALOGY_RE, threshold=0.52\n    )\n    if repeated_analogy is not None:\n        left_text, right_text, score = repeated_analogy\n        evidence = {\n            "semantic_analogy_score": round(score, 4),\n            "left_excerpt": left_text[:500],\n            "right_excerpt": right_text[:500],\n            "comparison_basis": "PARAPHRASED_ANALOGY_V1",\n        }\n        evidence["semantic_signature"] = _signature("ANALOGY", left_id, right_id, evidence)\n        findings.append(SemanticSeriesFinding("ANALOGY", "BLOCKING", evidence))\n\n    renamed_tool = _best_marked_pair(left_sample, right_sample, marker=_TOOL_RE, threshold=0.52)\n''',
)

replace_once(
    SIM,
    '''    template = _profession_swapped_template(left_sample, right_sample)\n    if template is not None:\n        left_text, right_text, score = template\n        evidence = {\n            "template_similarity_score": round(score, 4),\n            "left_excerpt": left_text[:500],\n            "right_excerpt": right_text[:500],\n            "profession_terms_neutralized": True,\n            "comparison_basis": "PROFESSION_SWAPPED_TEMPLATE_V1",\n        }\n        evidence["semantic_signature"] = _signature("LANGUAGE", left_id, right_id, evidence)\n        findings.append(SemanticSeriesFinding("LANGUAGE", "BLOCKING", evidence))\n''',
    '''    template = _profession_swapped_template(left_sample, right_sample)\n    template_basis = "PROFESSION_SWAPPED_TEMPLATE_V1"\n    if template is None:\n        template = _domain_independent_template(left_sample, right_sample)\n        template_basis = "DOMAIN_INDEPENDENT_FUNCTION_TEMPLATE_V2"\n    if template is not None:\n        left_text, right_text, score = template\n        evidence = {\n            "template_similarity_score": round(score, 4),\n            "left_excerpt": left_text[:500],\n            "right_excerpt": right_text[:500],\n            "profession_terms_neutralized": template_basis == "PROFESSION_SWAPPED_TEMPLATE_V1",\n            "domain_terms_neutralized": True,\n            "comparison_basis": template_basis,\n        }\n        evidence["semantic_signature"] = _signature("LANGUAGE", left_id, right_id, evidence)\n        findings.append(SemanticSeriesFinding("LANGUAGE", "BLOCKING", evidence))\n''',
)

replace_once(
    WORKSPACE,
    '''        accepted = request.classification != "UNACCEPTABLE_DUPLICATE"\n        finding_status = "ACCEPTED_EXCEPTION" if accepted else "OPEN"\n''',
    '''        accepted = request.classification != "UNACCEPTABLE_DUPLICATE"\n        if accepted and not actor.startswith("HUMAN:"):\n            raise SeriesWorkspaceGateError(\n                "overlap exceptions require an explicit HUMAN actor for this exact finding"\n            )\n        finding_status = "ACCEPTED_EXCEPTION" if accepted else "OPEN"\n''',
)

replace_once(
    BASE,
    '''            cross_book_uniqueness_rules=[\n                "Каждая книга даёт самостоятельный результат без обязательной покупки соседних книг.",\n                "Не маскировать смысловой дубль перефразированием.",\n            ],\n''',
    '''            cross_book_uniqueness_rules=[\n                "Каждая книга даёт самостоятельный результат без обязательной покупки соседних книг.",\n                "Не маскировать смысловой дубль перефразированием или сменой предметной области.",\n                "Материальные повторы тезисов, механизмов, кейсов, аналогий, шаблонов и функций между книгами запрещены.",\n                "Любое допустимое исключение требует адресного HUMAN-решения по конкретному finding; общего разрешения нет.",\n            ],\n''',
)

replace_once(
    TEST,
    '''from book_os_core.series_workspace import (\n    SeriesBookCreateRequest,\n    SeriesCreateRequest,\n    SeriesWorkspaceGateError,\n    SeriesWorkspaceService,\n)\n''',
    '''from book_os_core.series_workspace import (\n    SeriesBookCreateRequest,\n    SeriesCreateRequest,\n    SeriesOverlapDispositionRequest,\n    SeriesWorkspaceGateError,\n    SeriesWorkspaceService,\n)\n''',
)

append(TEST, r'''
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
        {"purpose": "Оценить исходный уровень музыканта", "new_contribution": "Шкала критериев стартового уровня"},
        {"purpose": "Составить план ежедневной практики", "new_contribution": "Календарь приоритетов упражнений"},
        {"purpose": "Выполнить цикл практики по плану", "new_contribution": "Протокол действий на занятии"},
        {"purpose": "Отслеживать прогресс и корректировать ошибки", "new_contribution": "Шкала контроля и исправления"},
    ]
    renovation = [
        {"purpose": "Контролировать результат и исправлять отклонения ремонта", "new_contribution": "Шкала контроля и корректировки"},
        {"purpose": "Проверить исходное состояние квартиры", "new_contribution": "Матрица критериев стартового состояния"},
        {"purpose": "Предотвратить аварийные риски до начала работ", "new_contribution": "Короткий контроль безопасности"},
        {"purpose": "Подготовить план последовательности работ", "new_contribution": "Календарь приоритетов этапов"},
        {"purpose": "Выполнить работы по утверждённому плану", "new_contribution": "Протокол действий на этапе"},
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
            unique_idea="Решение строится на снижении риска через проверяемые доказательства",
            reader_problem="Читатель не уверен в результате и критериях выбора",
            reader_result="Читатель принимает проверяемое решение",
            unique_mechanism="Оценить риск, собрать доказательства и проверить решение",
        ),
    )
    service.add_book(
        series_id,
        SeriesBookCreateRequest(
            title="Вторая книга",
            ordinal=2,
            unique_idea="Уверенный выбор возникает после оценки неопределённости и подтверждений результата",
            reader_problem="Читатель сомневается в результате и способе выбора",
            reader_result="Читатель делает обоснованный выбор",
            unique_mechanism="Проверить риск, собрать подтверждения и оценить решение",
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
''')

print("T05b universal series and human-exception hardening applied")
