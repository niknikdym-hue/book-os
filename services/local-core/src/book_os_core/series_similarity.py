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
    ("case", ("кейс", "пример", "истори", "ситуац", "сценари")),
)

_PROFESSION_RE = re.compile(
    r"\b(?:психолог\w*|юрист\w*|юридическ\w*|адвокат\w*|врач\w*|стоматолог\w*|"
    r"бухгалтер\w*|дизайнер\w*|риелтор\w*|репетитор\w*|коуч\w*|консультант\w*|"
    r"маркетолог\w*)\b",
    re.IGNORECASE,
)
_CASE_RE = re.compile(r"\b(?:например|кейс|пример|истори\w*|ситуаци\w*|сценари\w*)\b", re.I)
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
    if len(left) != len(right) or len(left) < 2:
        return None
    scores: list[float] = []
    shared: list[list[str]] = []
    for left_item, right_item in zip(left, right, strict=True):
        left_text = f"{left_item.get('purpose', '')} {left_item.get('new_contribution', '')}"
        right_text = f"{right_item.get('purpose', '')} {right_item.get('new_contribution', '')}"
        score = semantic_score(left_text, right_text)
        scores.append(score)
        shared.append(sorted(semantic_families(left_text) & semantic_families(right_text)))
    mean_score = sum(scores) / len(scores)
    if mean_score < 0.62 or min(scores) < 0.42:
        return None
    if sum(len(values) >= 2 for values in shared) < max(2, len(shared) - 1):
        return None
    return {
        "ordered_function_scores": [round(value, 4) for value in scores],
        "mean_function_score": round(mean_score, 4),
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
    left_values = [value for value in _sentences(left_sample) if marker.search(value)]
    right_values = [value for value in _sentences(right_sample) if marker.search(value)]
    best: tuple[str, str, float] | None = None
    for left in left_values:
        for right in right_values:
            score = semantic_score(left, right)
            if score < threshold:
                continue
            shared = semantic_families(left) & semantic_families(right)
            if len(shared) < 4:
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
    if template is not None:
        left_text, right_text, score = template
        evidence = {
            "template_similarity_score": round(score, 4),
            "left_excerpt": left_text[:500],
            "right_excerpt": right_text[:500],
            "profession_terms_neutralized": True,
            "comparison_basis": "PROFESSION_SWAPPED_TEMPLATE_V1",
        }
        evidence["semantic_signature"] = _signature("LANGUAGE", left_id, right_id, evidence)
        findings.append(SemanticSeriesFinding("LANGUAGE", "BLOCKING", evidence))

    return findings
