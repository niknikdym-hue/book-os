#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve()


def replace_once(rel: str, old: str, new: str) -> None:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"expected one match in {rel}: {old[:100]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def append(rel: str, value: str) -> None:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    if value.strip() in text:
        raise SystemExit(f"test block already present in {rel}")
    path.write_text(text.rstrip() + "\n\n" + value.strip() + "\n", encoding="utf-8")


SRC = "services/local-core/src/book_os_core/series_similarity.py"
TEST = "services/local-core/tests/test_series_semantic_overlap.py"

old = '''def _sequence_score(\n    left: list[dict[str, str]], right: list[dict[str, str]]\n) -> dict[str, Any] | None:\n    if len(left) != len(right) or len(left) < 2:\n        return None\n    scores: list[float] = []\n    shared: list[list[str]] = []\n    for left_item, right_item in zip(left, right, strict=True):\n        left_text = f"{left_item.get('purpose', '')} {left_item.get('new_contribution', '')}"\n        right_text = f"{right_item.get('purpose', '')} {right_item.get('new_contribution', '')}"\n        score = semantic_score(left_text, right_text)\n        scores.append(score)\n        shared.append(sorted(semantic_families(left_text) & semantic_families(right_text)))\n    mean_score = sum(scores) / len(scores)\n    if mean_score < 0.62 or min(scores) < 0.42:\n        return None\n    if sum(len(values) >= 2 for values in shared) < max(2, len(shared) - 1):\n        return None\n    return {\n        "ordered_function_scores": [round(value, 4) for value in scores],\n        "mean_function_score": round(mean_score, 4),\n        "shared_semantic_functions": shared,\n        "comparison_basis": "DOMAIN_NEUTRALIZED_CURRENT_ARCHITECTURE",\n    }\n'''
new = '''def _sequence_score(\n    left: list[dict[str, str]], right: list[dict[str, str]]\n) -> dict[str, Any] | None:\n    """Compare chapter functions independent of chapter count and order.\n\n    A cloned architecture must not escape merely by inserting, splitting, merging or reordering\n    chapters.  We therefore greedily match the smaller architecture to unique best matches in the\n    larger architecture, and require both high matched coverage and high semantic-function overlap.\n    The conservative thresholds keep ordinary books in the same field from becoming false positives.\n    """\n    if len(left) < 2 or len(right) < 2:\n        return None\n\n    def text(item: dict[str, str]) -> str:\n        return f"{item.get('purpose', '')} {item.get('new_contribution', '')}".strip()\n\n    left_texts = [text(item) for item in left]\n    right_texts = [text(item) for item in right]\n    smaller_is_left = len(left_texts) <= len(right_texts)\n    smaller = left_texts if smaller_is_left else right_texts\n    larger = right_texts if smaller_is_left else left_texts\n\n    candidates: list[tuple[float, int, int]] = []\n    for small_index, small_text in enumerate(smaller):\n        for large_index, large_text in enumerate(larger):\n            candidates.append((semantic_score(small_text, large_text), small_index, large_index))\n    candidates.sort(reverse=True)\n\n    used_small: set[int] = set()\n    used_large: set[int] = set()\n    matches: list[tuple[float, int, int]] = []\n    for score, small_index, large_index in candidates:\n        if small_index in used_small or large_index in used_large:\n            continue\n        used_small.add(small_index)\n        used_large.add(large_index)\n        matches.append((score, small_index, large_index))\n        if len(matches) == len(smaller):\n            break\n\n    if len(matches) < 2:\n        return None\n    matches.sort(key=lambda item: item[1])\n    scores = [item[0] for item in matches]\n    shared: list[list[str]] = []\n    pair_rows: list[dict[str, Any]] = []\n    for score, small_index, large_index in matches:\n        small_text = smaller[small_index]\n        large_text = larger[large_index]\n        functions = sorted(semantic_families(small_text) & semantic_families(large_text))\n        shared.append(functions)\n        pair_rows.append(\n            {\n                "left_index": small_index if smaller_is_left else large_index,\n                "right_index": large_index if smaller_is_left else small_index,\n                "score": round(score, 4),\n                "shared_functions": functions,\n            }\n        )\n\n    mean_score = sum(scores) / len(scores)\n    count_ratio = min(len(left), len(right)) / max(len(left), len(right))\n    semantic_coverage = sum(score >= 0.42 for score in scores) / len(scores)\n    function_pairs = sum(len(values) >= 2 for values in shared)\n    required_function_pairs = max(2, len(matches) - 1)\n    aggregate_score = semantic_score(" ".join(left_texts), " ".join(right_texts))\n\n    if count_ratio < 0.6:\n        return None\n    if semantic_coverage < 0.8 or mean_score < 0.62 or aggregate_score < 0.58:\n        return None\n    if function_pairs < required_function_pairs:\n        return None\n    return {\n        "matched_function_pairs": pair_rows,\n        "mean_function_score": round(mean_score, 4),\n        "aggregate_function_score": round(aggregate_score, 4),\n        "chapter_count_ratio": round(count_ratio, 4),\n        "left_chapter_count": len(left),\n        "right_chapter_count": len(right),\n        "order_independent": True,\n        "shared_semantic_functions": shared,\n        "comparison_basis": "DOMAIN_NEUTRALIZED_CURRENT_ARCHITECTURE",\n    }\n'''
replace_once(SRC, old, new)

append(TEST, r'''
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
        {"purpose": "Диагностировать спрос на услуги психолога", "new_contribution": "Карта запросов и критериев клиента"},
        {"purpose": "Собрать доказательства доверия к психологу", "new_contribution": "Матрица подтверждений для решения клиента"},
        {"purpose": "Объяснить цену психологической услуги до покупки", "new_contribution": "Схема риска стоимости и результата клиента"},
    ]
    disguised = [
        {"purpose": "Объяснить стоимость юридической помощи до договора", "new_contribution": "Модель риска цены и результата заказчика"},
        {"purpose": "Служебная дополнительная глава про организацию практики", "new_contribution": "Короткий организационный переход между решениями"},
        {"purpose": "Выявить потребность в юридических услугах", "new_contribution": "Схема запросов и критериев заказчика"},
        {"purpose": "Укрепить доверие к юристу доказательствами", "new_contribution": "Карта подтверждений перед выбором заказчика"},
    ]
    findings = semantic_series_findings(
        left, right,
        left_architecture=base,
        right_architecture=disguised,
        left_sources=[], right_sources=[],
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
        {"purpose": "Посчитать постоянные расходы практики", "new_contribution": "Карта затрат по месяцам"},
        {"purpose": "Определить прибыль на услугу", "new_contribution": "Формула маржинальности услуги"},
        {"purpose": "Проверить окупаемость рекламы", "new_contribution": "Порог допустимой стоимости привлечения"},
    ]
    right_arch = [
        {"purpose": "Подготовить первую встречу с клиентом", "new_contribution": "Сценарий сбора ожиданий"},
        {"purpose": "Фиксировать договорённости после разговора", "new_contribution": "Протокол итогов встречи"},
        {"purpose": "Разрешать конфликт ожиданий", "new_contribution": "Алгоритм уточнения спорных формулировок"},
        {"purpose": "Завершать проект без потери отношений", "new_contribution": "Сценарий финальной коммуникации"},
    ]
    findings = semantic_series_findings(
        left, right,
        left_architecture=left_arch,
        right_architecture=right_arch,
        left_sources=[], right_sources=[],
    )
    assert "ARCHITECTURE" not in _dimensions(findings)
''')

print("T05 series uniqueness hardening applied")
