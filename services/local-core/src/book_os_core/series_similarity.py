from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import hashlib
import json
import re
from typing import Any


@dataclass(frozen=True)
class SemanticSeriesFinding:
    dimension: str
    severity: str
    evidence: dict[str, Any]


_TOKEN = re.compile(r"[а-яёa-z0-9-]{3,}", re.IGNORECASE)
_SENTENCE = re.compile(r"[^.!?\n]+[.!?]?", re.MULTILINE)

_STOP = {
    "автор",
    "будет",
    "быть",
    "важно",
    "весь",
    "всей",
    "всего",
    "глав",
    "глава",
    "главы",
    "для",
    "его",
    "если",
    "еще",
    "книга",
    "книги",
    "котор",
    "может",
    "нужно",
    "один",
    "после",
    "перед",
    "помог",
    "почему",
    "при",
    "про",
    "свой",
    "такой",
    "только",
    "через",
    "читатель",
    "эта",
    "это",
}

# Deterministic semantic families. These are deliberately narrow and auditable: the goal is not
# general NLP, but catching the exact nonfiction-series clone patterns that lexical Jaccard misses.
_FAMILIES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "domain_actor",
        (
            "психолог",
            "юрист",
            "юридич",
            "адвокат",
            "врач",
            "медицин",
            "стоматолог",
            "бухгалтер",
            "дизайнер",
            "риелтор",
            "репетитор",
            "коуч",
            "консультант",
            "маркетолог",
            "агентств",
            "клиник",
        ),
    ),
    ("client", ("клиент", "покупател", "заказчик", "пациент", "ученик", "слушател")),
    ("diagnose", ("диагност", "анализ", "выяв", "обнаруж", "наход", "определ", "разобра")),
    ("demand", ("спрос", "потребност", "запрос", "намерени")),
    ("offer", ("предложени", "оффер", "обещани", "позиционир")),
    ("evidence", ("доказател", "подтвержд", "портфоли", "отзыв", "репутац")),
    ("trust", ("довер", "уверенн", "надежн")),
    ("risk", ("риск", "неопредел", "сомнени", "опасени")),
    ("economics", ("цен", "стоимост", "тариф", "марж", "прибыл", "экономик", "окуп")),
    ("acquisition", ("привлеч", "продвиж", "реклам", "трафик", "лид", "охват")),
    ("qualification", ("квалифиц", "отбор", "фильтр", "соответств")),
    ("conversion", ("продаж", "покупк", "оплат", "договор", "сделк", "конверси")),
    ("decision", ("решени", "выбор", "сравнен", "сопостав", "выбира")),
    ("objection", ("возраж", "отказ", "сомнева", "барьер")),
    ("retention", ("повтор", "возвращ", "удерж", "рекомендац", "лояльн")),
    ("outcome", ("результат", "эффект", "изменени", "трансформац")),
    ("local", ("город", "район", "географ", "локальн", "местн")),
    ("ads", ("директ", "контекстн", "объявлен", "кампан", "ключев")),
    (
        "tool",
        (
            "матриц",
            "карт",
            "чек-лист",
            "чеклист",
            "алгоритм",
            "модель",
            "формул",
            "таблиц",
            "схем",
            "шкал",
            "канва",
        ),
    ),
    (
        "assess",
        (
            "оцен",
            "провер",
            "измер",
            "тестир",
            "аудит",
            "inspect",
            "assess",
            "measure",
            "audit",
            "test",
        ),
    ),
    (
        "plan",
        (
            "план",
            "стратег",
            "маршрут",
            "приоритет",
            "очеред",
            "этап",
            "schedule",
            "plan",
            "strateg",
            "priorit",
            "roadmap",
        ),
    ),
    ("prepare", ("подготов", "настро", "готов", "setup", "prepar", "configur")),
    (
        "organize",
        (
            "организ",
            "структур",
            "системат",
            "регламент",
            "процесс",
            "organize",
            "structur",
            "process",
        ),
    ),
    (
        "create",
        (
            "созда",
            "постро",
            "разработ",
            "проектир",
            "формир",
            "состав",
            "design",
            "build",
            "creat",
            "develop",
        ),
    ),
    (
        "execute",
        (
            "выполн",
            "внедр",
            "примен",
            "запуск",
            "провод",
            "практик",
            "реализ",
            "implement",
            "execut",
            "apply",
            "practic",
            "launch",
        ),
    ),
    ("monitor", ("контрол", "отслеж", "наблюд", "монитор", "учет", "track", "monitor", "control")),
    (
        "improve",
        (
            "улучш",
            "оптимиз",
            "коррект",
            "исправ",
            "адапт",
            "совершен",
            "improv",
            "optimiz",
            "correct",
            "adapt",
        ),
    ),
    (
        "communicate",
        (
            "коммуникац",
            "переговор",
            "объясн",
            "обсужд",
            "сообщ",
            "диалог",
            "разговор",
            "communicat",
            "negot",
            "explain",
            "discuss",
        ),
    ),
    ("learn", ("обуч", "изуч", "осво", "понима", "запом", "learn", "study", "understand")),
    (
        "document",
        (
            "документ",
            "запис",
            "фиксац",
            "протокол",
            "реестр",
            "журнал",
            "record",
            "document",
            "protocol",
        ),
    ),
    (
        "constraint",
        (
            "огранич",
            "границ",
            "услов",
            "правил",
            "критер",
            "constraint",
            "boundary",
            "rule",
            "criter",
        ),
    ),
    (
        "safety",
        (
            "безопас",
            "защит",
            "предотвращ",
            "ошиб",
            "сбо",
            "авари",
            "secure",
            "safe",
            "prevent",
            "error",
            "failure",
        ),
    ),
    (
        "resource",
        ("ресурс", "врем", "бюджет", "мощност", "нагруз", "capacity", "resource", "budget", "time"),
    ),
    (
        "progress",
        ("прогресс", "динамик", "рост", "снижен", "изменен", "progress", "change", "growth"),
    ),
    ("case", ("кейс", "пример", "истори", "ситуац", "сценари")),
)

_PROFESSION_RE = re.compile(
    r"\b(?:психолог\w*|юрист\w*|юридическ\w*|адвокат\w*|врач\w*|стоматолог\w*|"
    r"бухгалтер\w*|дизайнер\w*|риелтор\w*|репетитор\w*|коуч\w*|консультант\w*|"
    r"маркетолог\w*)\b",
    re.IGNORECASE,
)
_CASE_RE = re.compile(r"\b(?:например|кейс|пример|истори\w*|ситуаци\w*|сценари\w*)\b", re.I)
_ANALOGY_RE = re.compile(
    r"(?:\bаналог\w*\b|\bметафор\w*\b|\bсловно\b|\bподобн\w*\b|"
    r"\bпредставьте\b|как будто|\bнапомина\w*\b)",
    re.I,
)
_TOOL_RE = re.compile(
    r"\b(?:матриц\w*|карт\w*|чек-?лист\w*|алгоритм\w*|модел\w*|формул\w*|"
    r"таблиц\w*|схем\w*|шкал\w*|канва\w*)\b",
    re.IGNORECASE,
)


def _family(token: str) -> str | None:
    for family, prefixes in _FAMILIES:
        if any(token.startswith(prefix) for prefix in prefixes):
            return family
    return None


def semantic_tokens(value: str) -> set[str]:
    result: set[str] = set()
    for raw in _TOKEN.findall(value.casefold()):
        token = raw.strip("-")
        if not token or token in _STOP:
            continue
        family = _family(token)
        if family is not None:
            result.add(family)
            continue
        # A short deterministic stem collapses ordinary Russian inflection without pretending to
        # perform semantic inference. Keep numerals intact because they can distinguish cases.
        result.add(token if token.isdigit() else token[:7])
    return result


def semantic_families(value: str) -> set[str]:
    return {
        family
        for raw in _TOKEN.findall(value.casefold())
        if (family := _family(raw.strip("-"))) is not None
    }


def _jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def semantic_score(left: str, right: str) -> float:
    # Lexical stems catch near-paraphrases; semantic families catch synonym/profession/tool swaps.
    return max(
        _jaccard(semantic_tokens(left), semantic_tokens(right)),
        _jaccard(semantic_families(left), semantic_families(right)),
    )


def _sequence_score(
    left: list[dict[str, str]], right: list[dict[str, str]]
) -> dict[str, Any] | None:
    """Compare chapter functions independent of chapter count and order.

    A cloned architecture must not escape merely by inserting, splitting, merging or reordering
    chapters.  We therefore greedily match the smaller architecture to unique best matches in the
    larger architecture, and require both high matched coverage and high semantic-function overlap.
    The conservative thresholds keep ordinary books in the same field from becoming false positives.
    """
    if len(left) < 2 or len(right) < 2:
        return None

    def text(item: dict[str, str]) -> str:
        return f"{item.get('purpose', '')} {item.get('new_contribution', '')}".strip()

    left_texts = [text(item) for item in left]
    right_texts = [text(item) for item in right]
    smaller_is_left = len(left_texts) <= len(right_texts)
    smaller = left_texts if smaller_is_left else right_texts
    larger = right_texts if smaller_is_left else left_texts

    candidates: list[tuple[float, int, int]] = []
    for small_index, small_text in enumerate(smaller):
        for large_index, large_text in enumerate(larger):
            candidates.append((semantic_score(small_text, large_text), small_index, large_index))
    candidates.sort(reverse=True)

    used_small: set[int] = set()
    used_large: set[int] = set()
    matches: list[tuple[float, int, int]] = []
    for score, small_index, large_index in candidates:
        if small_index in used_small or large_index in used_large:
            continue
        used_small.add(small_index)
        used_large.add(large_index)
        matches.append((score, small_index, large_index))
        if len(matches) == len(smaller):
            break

    if len(matches) < 2:
        return None
    matches.sort(key=lambda item: item[1])
    scores = [item[0] for item in matches]
    shared: list[list[str]] = []
    pair_rows: list[dict[str, Any]] = []
    for score, small_index, large_index in matches:
        small_text = smaller[small_index]
        large_text = larger[large_index]
        functions = sorted(semantic_families(small_text) & semantic_families(large_text))
        shared.append(functions)
        pair_rows.append(
            {
                "left_index": small_index if smaller_is_left else large_index,
                "right_index": large_index if smaller_is_left else small_index,
                "score": round(score, 4),
                "shared_functions": functions,
            }
        )

    mean_score = sum(scores) / len(scores)
    count_ratio = min(len(left), len(right)) / max(len(left), len(right))
    semantic_coverage = sum(score >= 0.42 for score in scores) / len(scores)
    function_pairs = sum(len(values) >= 2 for values in shared)
    required_function_pairs = max(2, len(matches) - 1)
    aggregate_score = semantic_score(" ".join(left_texts), " ".join(right_texts))

    if count_ratio < 0.6:
        return None
    if semantic_coverage < 0.75 or mean_score < 0.62 or aggregate_score < 0.58:
        return None
    if function_pairs < required_function_pairs:
        return None
    return {
        "matched_function_pairs": pair_rows,
        "mean_function_score": round(mean_score, 4),
        "aggregate_function_score": round(aggregate_score, 4),
        "chapter_count_ratio": round(count_ratio, 4),
        "left_chapter_count": len(left),
        "right_chapter_count": len(right),
        "order_independent": True,
        "shared_semantic_functions": shared,
        "comparison_basis": "DOMAIN_NEUTRALIZED_CURRENT_ARCHITECTURE",
    }


def _sentences(sample: str) -> list[str]:
    return [value.strip() for value in _SENTENCE.findall(sample) if len(_TOKEN.findall(value)) >= 7]


def _best_marked_pair(
    left_sample: str,
    right_sample: str,
    *,
    marker: re.Pattern[str],
    threshold: float,
) -> tuple[str, str, float] | None:
    """Find the best marked semantic pair without a full corpus cross-product.

    A material finding already requires at least four shared semantic families. Build an inverted
    index over those families first, then score only candidate pairs that can satisfy that exact
    requirement. This preserves the previous decision rule while bounding work on long imports
    containing hundreds of marked sentences.
    """
    left_rows: list[tuple[str, set[str], set[str]]] = []
    right_rows: list[tuple[str, set[str], set[str]]] = []
    for value in _sentences(left_sample):
        if not marker.search(value):
            continue
        families = semantic_families(value)
        if len(families) < 4:
            continue
        left_rows.append((value, families, semantic_tokens(value)))
    for value in _sentences(right_sample):
        if not marker.search(value):
            continue
        families = semantic_families(value)
        if len(families) < 4:
            continue
        right_rows.append((value, families, semantic_tokens(value)))

    inverted: dict[str, set[int]] = {}
    for index, (_, families, _) in enumerate(right_rows):
        for family in families:
            inverted.setdefault(family, set()).add(index)

    best: tuple[str, str, float] | None = None
    for left, left_families, left_tokens in left_rows:
        counts: dict[int, int] = {}
        for family in left_families:
            for index in inverted.get(family, set()):
                counts[index] = counts.get(index, 0) + 1
        for index, shared_count in counts.items():
            if shared_count < 4:
                continue
            right, right_families, right_tokens = right_rows[index]
            score = max(
                _jaccard(left_tokens, right_tokens),
                _jaccard(left_families, right_families),
            )
            if score < threshold:
                continue
            if best is None or score > best[2]:
                best = (left, right, score)
    return best


def _profession_swapped_template(
    left_sample: str, right_sample: str
) -> tuple[str, str, float] | None:
    left_values = [value for value in _sentences(left_sample) if _PROFESSION_RE.search(value)]
    right_values = [value for value in _sentences(right_sample) if _PROFESSION_RE.search(value)]
    best: tuple[str, str, float] | None = None
    for left in left_values:
        for right in right_values:
            if left.casefold() == right.casefold():
                continue
            token_score = semantic_score(left, right)
            left_canonical = " ".join(sorted(semantic_tokens(left)))
            right_canonical = " ".join(sorted(semantic_tokens(right)))
            order_score = SequenceMatcher(None, left_canonical, right_canonical).ratio()
            score = max(token_score, order_score)
            if score < 0.78:
                continue
            if len(semantic_tokens(left) & semantic_tokens(right)) < 8:
                continue
            if best is None or score > best[2]:
                best = (left, right, score)
    return best


def _domain_independent_template(
    left_sample: str, right_sample: str
) -> tuple[str, str, float] | None:
    """Find a repeated functional sentence template without assuming a profession/domain list."""
    left_rows = [
        (value, semantic_families(value))
        for value in _sentences(left_sample)
        if len(semantic_families(value)) >= 4
    ]
    right_rows = [
        (value, semantic_families(value))
        for value in _sentences(right_sample)
        if len(semantic_families(value)) >= 4
    ]
    inverted: dict[str, set[int]] = {}
    for index, (_, families) in enumerate(right_rows):
        for family in families:
            inverted.setdefault(family, set()).add(index)

    best: tuple[str, str, float] | None = None
    for left_text, left_families in left_rows:
        counts: dict[int, int] = {}
        for family in left_families:
            for index in inverted.get(family, set()):
                counts[index] = counts.get(index, 0) + 1
        for index, shared_count in counts.items():
            if shared_count < 4:
                continue
            right_text, right_families = right_rows[index]
            if left_text.casefold() == right_text.casefold():
                continue
            family_score = _jaccard(left_families, right_families)
            if family_score < 0.60:
                continue
            token_score = semantic_score(left_text, right_text)
            left_canonical = " ".join(sorted(left_families))
            right_canonical = " ".join(sorted(right_families))
            structure_score = SequenceMatcher(None, left_canonical, right_canonical).ratio()
            score = max(token_score, family_score, structure_score)
            if score < 0.72:
                continue
            lexical_overlap = len(semantic_tokens(left_text) & semantic_tokens(right_text))
            if lexical_overlap < 3 and family_score < 0.75:
                continue
            if best is None or score > best[2]:
                best = (left_text, right_text, score)
    return best


def _signature(dimension: str, left_id: str, right_id: str, evidence: dict[str, Any]) -> str:
    material = json.dumps(
        {
            "dimension": dimension,
            "left": left_id,
            "right": right_id,
            "evidence": evidence,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def semantic_series_findings(
    left: Any,
    right: Any,
    *,
    left_architecture: list[dict[str, str]],
    right_architecture: list[dict[str, str]],
    left_sources: list[dict[str, Any]],
    right_sources: list[dict[str, Any]],
) -> list[SemanticSeriesFinding]:
    """Find high-confidence cross-book clones missed by exact lexical matching.

    This layer is intentionally conservative. Every emitted finding is explainable from the
    normalized token/function evidence and therefore safe to use as a fail-closed pre-writing gate.
    """

    findings: list[SemanticSeriesFinding] = []
    left_id = str(left.book_id)
    right_id = str(right.book_id)

    left_passport = " ".join(
        (left.unique_idea, left.reader_problem, left.reader_result, left.unique_mechanism)
    )
    right_passport = " ".join(
        (right.unique_idea, right.reader_problem, right.reader_result, right.unique_mechanism)
    )
    passport_score = semantic_score(left_passport, right_passport)
    shared_families = semantic_families(left_passport) & semantic_families(right_passport)
    if passport_score >= 0.5 and len(shared_families) >= 3:
        evidence = {
            "semantic_paraphrase_score": round(passport_score, 4),
            "shared_semantic_families": sorted(shared_families),
            "domain_terms_neutralized": True,
            "comparison_basis": "SEMANTIC_PASSPORT_V1",
        }
        evidence["semantic_signature"] = _signature("THESIS", left_id, right_id, evidence)
        findings.append(SemanticSeriesFinding("THESIS", "BLOCKING", evidence))

    architecture_evidence = _sequence_score(left_architecture, right_architecture)
    if architecture_evidence is not None:
        architecture_evidence["semantic_signature"] = _signature(
            "ARCHITECTURE", left_id, right_id, architecture_evidence
        )
        findings.append(SemanticSeriesFinding("ARCHITECTURE", "BLOCKING", architecture_evidence))

    left_sample = "\n".join(str(row.get("analysis", {}).get("sample", "")) for row in left_sources)
    right_sample = "\n".join(
        str(row.get("analysis", {}).get("sample", "")) for row in right_sources
    )

    repeated_case = _best_marked_pair(left_sample, right_sample, marker=_CASE_RE, threshold=0.56)
    if repeated_case is not None:
        left_text, right_text, score = repeated_case
        evidence = {
            "semantic_case_score": round(score, 4),
            "left_excerpt": left_text[:500],
            "right_excerpt": right_text[:500],
            "comparison_basis": "PARAPHRASED_CASE_V1",
        }
        evidence["semantic_signature"] = _signature("EXAMPLE", left_id, right_id, evidence)
        findings.append(SemanticSeriesFinding("EXAMPLE", "BLOCKING", evidence))

    repeated_analogy = _best_marked_pair(
        left_sample, right_sample, marker=_ANALOGY_RE, threshold=0.44
    )
    if repeated_analogy is not None:
        left_text, right_text, score = repeated_analogy
        evidence = {
            "semantic_analogy_score": round(score, 4),
            "left_excerpt": left_text[:500],
            "right_excerpt": right_text[:500],
            "comparison_basis": "PARAPHRASED_ANALOGY_V1",
        }
        evidence["semantic_signature"] = _signature("ANALOGY", left_id, right_id, evidence)
        findings.append(SemanticSeriesFinding("ANALOGY", "BLOCKING", evidence))

    renamed_tool = _best_marked_pair(left_sample, right_sample, marker=_TOOL_RE, threshold=0.52)
    if renamed_tool is not None:
        left_text, right_text, score = renamed_tool
        evidence = {
            "semantic_tool_score": round(score, 4),
            "left_excerpt": left_text[:500],
            "right_excerpt": right_text[:500],
            "tool_names_neutralized": True,
            "comparison_basis": "RENAMED_TOOL_V1",
        }
        evidence["semantic_signature"] = _signature("TOOL", left_id, right_id, evidence)
        findings.append(SemanticSeriesFinding("TOOL", "BLOCKING", evidence))

    template = _profession_swapped_template(left_sample, right_sample)
    template_basis = "PROFESSION_SWAPPED_TEMPLATE_V1"
    if template is None:
        template = _domain_independent_template(left_sample, right_sample)
        template_basis = "DOMAIN_INDEPENDENT_FUNCTION_TEMPLATE_V2"
    if template is not None:
        left_text, right_text, score = template
        evidence = {
            "template_similarity_score": round(score, 4),
            "left_excerpt": left_text[:500],
            "right_excerpt": right_text[:500],
            "profession_terms_neutralized": template_basis == "PROFESSION_SWAPPED_TEMPLATE_V1",
            "domain_terms_neutralized": True,
            "comparison_basis": template_basis,
        }
        evidence["semantic_signature"] = _signature("LANGUAGE", left_id, right_id, evidence)
        findings.append(SemanticSeriesFinding("LANGUAGE", "BLOCKING", evidence))

    return findings
