#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()


def replace_once(rel: str, old: str, new: str) -> None:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected exactly one match in {rel}, got {count}: {old[:140]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def insert_before(rel: str, marker: str, addition: str) -> None:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    if addition in text:
        raise SystemExit(f"addition already present in {rel}")
    if text.count(marker) != 1:
        raise SystemExit(f"expected exactly one marker in {rel}: {marker[:120]!r}")
    path.write_text(text.replace(marker, addition + marker, 1), encoding="utf-8")


QUALITY = "services/local-core/src/book_os_core/auto_book_quality.py"
FINALIZER = "services/local-core/src/book_os_core/auto_book_finalizer.py"
QUALITY_TEST = "services/local-core/tests/test_auto_book_quality.py"
FINALIZER_TEST = "services/local-core/tests/test_auto_book_finalizer.py"

# F03: a Claim identity is the exact normalized proposition. Material edits such as numbers,
# negation, modality or scope must never be treated as the same fact merely because the lexical
# shell looks similar.
replace_once(
    QUALITY,
    '''    @classmethod\n    def _claim_shape(cls, value: str) -> str:\n        return re.sub(r"\\b\\d+(?:[.,]\\d+)?\\b", "#", cls._normalized(value))\n''',
    '''    @classmethod\n    def _claims_same_fact(cls, current: str, registered: str) -> bool:\n        return cls._normalized(current) == cls._normalized(registered)\n''',
)

replace_once(
    QUALITY,
    '''        normalized_ledger = [\n            (self._normalized(claim), self._claim_shape(claim), current)\n            for claim, current in registered_claims.items()\n        ]\n''',
    '''        normalized_ledger = [\n            (claim, current) for claim, current in registered_claims.items()\n        ]\n''',
)

replace_once(
    QUALITY,
    '''                ledger_match = next(\n                    (\n                        (candidate, current)\n                        for candidate, shape, current in normalized_ledger\n                        if candidate\n                        and (\n                            candidate in normalized\n                            or normalized in candidate\n                            or shape == self._claim_shape(claim)\n                        )\n                    ),\n                    None,\n                )\n''',
    '''                ledger_match = next(\n                    (\n                        (candidate, current)\n                        for candidate, current in normalized_ledger\n                        if self._claims_same_fact(claim, candidate)\n                    ),\n                    None,\n                )\n''',
)

# `normalized` is no longer used after exact identity matching.
replace_once(
    QUALITY,
    '''            for claim in self.material_claims(text):\n                normalized = self._normalized(claim)\n                ledger_match = next(\n''',
    '''            for claim in self.material_claims(text):\n                ledger_match = next(\n''',
)

# F02: relevance is not support. This deterministic predicate is intentionally conservative. It
# checks exact material values, polarity, causal strength and high lexical coverage before BOOK OS
# may create or reuse a SUPPORTS relationship from an inspected excerpt.
insert_before(
    FINALIZER,
    '''    def _ensure_research_claims(self, book_id: str, state: AutoBookRunView) -> dict[str, Any]:\n''',
    '''    @staticmethod\n    def _normalized_evidence_number(value: str) -> str:\n        return value.replace(" ", "").replace(",", ".")\n\n    @classmethod\n    def _excerpt_supports_claim(cls, claim_text: str, excerpt: str) -> bool:\n        claim = " ".join(re.findall(r"[а-яёa-z0-9.,%]+", claim_text.casefold()))\n        source = " ".join(re.findall(r"[а-яёa-z0-9.,%]+", excerpt.casefold()))\n        if not claim or not source:\n            return False\n\n        claim_numbers = {\n            cls._normalized_evidence_number(item)\n            for item in re.findall(r"\\d+(?:[\\s.,]\\d+)*", claim_text)\n        }\n        source_numbers = {\n            cls._normalized_evidence_number(item)\n            for item in re.findall(r"\\d+(?:[\\s.,]\\d+)*", excerpt)\n        }\n        if claim_numbers and not claim_numbers.issubset(source_numbers):\n            return False\n\n        negation = re.compile(r"\\b(?:не|нет|никогда|без)\\b", re.IGNORECASE)\n        if bool(negation.search(claim_text)) != bool(negation.search(excerpt)):\n            return False\n\n        strong_certainty = re.compile(\n            r"\\b(?:доказан\\w*|доказыва\\w*|гарантир\\w*|обязательно|всегда)\\b",\n            re.IGNORECASE,\n        )\n        hedged = re.compile(\n            r"\\b(?:может|могут|возможно|вероятно|предполага\\w*|потенциально)\\b",\n            re.IGNORECASE,\n        )\n        if strong_certainty.search(claim_text) and hedged.search(excerpt):\n            return False\n\n        causal = re.compile(\n            r"\\b(?:вызыва\\w*|приводит|увеличива\\w*|снижа\\w*|повыша\\w*|влияет)\\b",\n            re.IGNORECASE,\n        )\n        associative = re.compile(\n            r"\\b(?:связан\\w*|ассоциирован\\w*|коррелир\\w*)\\b",\n            re.IGNORECASE,\n        )\n        if causal.search(claim_text) and associative.search(excerpt) and not causal.search(excerpt):\n            return False\n\n        stopwords = {\n            "это", "эта", "этот", "эти", "для", "что", "как", "при", "или", "его", "ее",\n            "она", "они", "оно", "также", "свой", "свои", "через", "между", "после", "перед",\n            "процент", "процента", "процентов",\n        }\n        claim_tokens = {\n            token\n            for token in re.findall(r"[а-яёa-z]{4,}", claim_text.casefold())\n            if token not in stopwords\n        }\n        excerpt_tokens = set(re.findall(r"[а-яёa-z]{4,}", excerpt.casefold()))\n        if len(claim_tokens) < 2:\n            return False\n        coverage = len(claim_tokens & excerpt_tokens) / len(claim_tokens)\n        return coverage >= 0.8\n\n''',
)

replace_once(
    FINALIZER,
    '''                            item.status == "ACTIVE"\n                            and item.relationship in {"SUPPORTS", "PARTIALLY_SUPPORTS"}\n                            and bool(item.pointer.strip())\n                            and (source := source_by_id.get(item.source_id)) is not None\n                            and (\n                                not freshness_required\n                                or (\n                                    source.publication_year is not None\n                                    and source.publication_year >= cutoff\n                                )\n                            )\n''',
    '''                            item.status == "ACTIVE"\n                            and item.relationship == "SUPPORTS"\n                            and bool(item.pointer.strip())\n                            and (source := source_by_id.get(item.source_id)) is not None\n                            and item.pointer.strip() == cast(str, source.inspected_pointer).strip()\n                            and self._excerpt_supports_claim(\n                                claim_text, cast(str, source.inspected_excerpt)\n                            )\n                            and (\n                                not freshness_required\n                                or (\n                                    source.publication_year is not None\n                                    and source.publication_year >= cutoff\n                                )\n                            )\n''',
)

replace_once(
    FINALIZER,
    '''                    if not eligible_evidence():\n                        claim_tokens = set(re.findall(r"[а-яёa-z0-9]{4,}", claim_text.casefold()))\n                        source = next(\n                            (\n                                item\n                                for item in sources\n                                if (\n                                    not freshness_required\n                                    or (\n                                        item.publication_year is not None\n                                        and item.publication_year >= datetime.now(UTC).year - 3\n                                    )\n                                )\n                                if claim_tokens\n                                & set(\n                                    re.findall(\n                                        r"[а-яёa-z0-9]{4,}",\n                                        cast(str, item.inspected_excerpt).casefold(),\n                                    )\n                                )\n                            ),\n                            None,\n                        )\n''',
    '''                    if not eligible_evidence():\n                        source = next(\n                            (\n                                item\n                                for item in sources\n                                if (\n                                    not freshness_required\n                                    or (\n                                        item.publication_year is not None\n                                        and item.publication_year >= datetime.now(UTC).year - 3\n                                    )\n                                )\n                                if self._excerpt_supports_claim(\n                                    claim_text, cast(str, item.inspected_excerpt)\n                                )\n                            ),\n                            None,\n                        )\n''',
)

replace_once(
    FINALIZER,
    '''                                    note="Auto Book exact inspected-source match",\n''',
    '''                                    note=(\n                                        "Auto Book deterministic exact-value/polarity support check "\n                                        "against the inspected source excerpt"\n                                    ),\n''',
)

# Negative regressions for F03.
insert_before(
    QUALITY_TEST,
    '''def test_distant_repeat_and_quantified_contradiction_are_whole_book_findings() -> None:\n''',
    '''def test_material_number_change_never_reuses_old_claim_identity() -> None:\n    old_claim = "Конверсия составляет 20 процентов."\n    changed = master(["Конверсия составляет 80 процентов."])\n    report = AutoBookQualityEngine().review(\n        changed,\n        registered_claims={old_claim: True},\n        writer_identity="writer/openai",\n        reviewer_identity="critic/independent",\n    )\n    assert report.status == "REWORK"\n    assert any(item.code == "UNREGISTERED_MATERIAL_CLAIM" for item in report.findings)\n\n\ndef test_negation_change_never_reuses_old_claim_identity() -> None:\n    old_claim = "Реклама увеличивает продажи на 20 процентов."\n    changed = master(["Реклама не увеличивает продажи на 20 процентов."])\n    report = AutoBookQualityEngine().review(\n        changed,\n        registered_claims={old_claim: True},\n        writer_identity="writer/openai",\n        reviewer_identity="critic/independent",\n    )\n    assert report.status == "REWORK"\n    assert any(item.code == "UNREGISTERED_MATERIAL_CLAIM" for item in report.findings)\n\n\n''',
)

# Direct conservative support regressions for F02. Integration continues to use the existing
# ResearchService, so these tests pin the semantic predicate without any provider/network call.
insert_before(
    FINALIZER_TEST,
    '''def test_auto_book_finalizer_locks_master_before_litres_docx(tmp_path: Path) -> None:\n''',
    '''def test_inspected_excerpt_support_is_not_topic_overlap() -> None:\n    supports = AutoBookFinalizer._excerpt_supports_claim\n    claim = "Реклама увеличивает продажи на 20 процентов."\n    assert supports(\n        claim,\n        "Исследование показало: реклама увеличивает продажи на 20 процентов в этой выборке.",\n    )\n    assert not supports(\n        claim,\n        "Исследование показало: реклама не увеличивает продажи на 20 процентов в этой выборке.",\n    )\n    assert not supports(\n        claim,\n        "Исследование показало: реклама увеличивает продажи на 80 процентов в этой выборке.",\n    )\n    assert not supports(\n        claim,\n        "Исследование обсуждает рекламу и продажи, но не подтверждает указанную величину.",\n    )\n\n\ndef test_inspected_excerpt_cannot_upgrade_association_to_causation() -> None:\n    assert not AutoBookFinalizer._excerpt_supports_claim(\n        "Реклама увеличивает продажи на 20 процентов.",\n        "Реклама ассоциирована с продажами на уровне 20 процентов в исследованной группе.",\n    )\n\n\n''',
)

print("T02 evidence/claim hardening applied")
