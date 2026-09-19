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


def append(rel: str, block: str) -> None:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    if block.strip() in text:
        raise SystemExit(f"block already present in {rel}")
    path.write_text(text.rstrip() + "\n\n" + block.strip() + "\n", encoding="utf-8")


GATES = "services/local-core/src/book_os_core/auto_book_gates.py"
FINALIZER = "services/local-core/src/book_os_core/auto_book_finalizer.py"
FINALIZER_TEST = "services/local-core/tests/test_auto_book_finalizer.py"
GATE_TEST = "services/local-core/tests/test_auto_book_gate_semantics.py"

replace_once(
    GATES,
    '''class EvidenceCheck(BaseModel):\n    gate: str\n    status: GateStatus\n    evidence: dict[str, Any] = Field(min_length=1)\n''',
    '''class EvidenceCheck(BaseModel):\n    gate: str\n    status: GateStatus\n    evidence: dict[str, Any] = Field(min_length=1)\n    evaluation_scope: Literal["STRUCTURAL_PREFLIGHT"] = "STRUCTURAL_PREFLIGHT"\n    semantic_quality_claimed: Literal[False] = False\n''',
)

replace_once(
    GATES,
    '''class AutoBookEvidenceGates:\n    """Deterministic evidence gates; reaching a workflow stage is never evidence."""\n''',
    '''class AutoBookEvidenceGates:\n    """Deterministic structural preflight gates; reaching a stage is never quality evidence.\n\n    These checks validate completeness, distinct fields and cheap structural invariants only.\n    They deliberately do not claim literary, intellectual, market or semantic quality.  Those\n    properties are evaluated later against the exact whole-book snapshot by the independent\n    critic and human authority.\n    """\n''',
)

# Give the existing final independent critic the actual acceptance criteria and a manifest proving
# every chapter of the exact snapshot is represented.  This remains the same single critic call;
# no additional provider operation is introduced.
replace_once(
    FINALIZER,
    '''        request = ModelTaskRequest(\n            task_id=hashlib.sha256(\n                f"{state.run_id}:critique:{snapshot.manifest_hash}".encode("utf-8")\n            ).hexdigest()[:26],\n''',
    '''        project = self.projects.get_project(book_id)\n        book_definition = (\n            project.book_contract.content if project.book_contract is not None else None\n        )\n        architecture = project.architecture.content if project.architecture is not None else None\n        if book_definition is None or architecture is None:\n            raise AutoBookGateError(\n                "independent whole-book review requires the approved Book Definition and architecture"\n            )\n        chapter_coverage_manifest = [\n            {\n                "chapter_id": chapter.chapter_id,\n                "paragraph_count": len(chapter.paragraphs),\n                "content_hash": hashlib.sha256(\n                    json.dumps(\n                        chapter.model_dump(mode="json"),\n                        ensure_ascii=False,\n                        sort_keys=True,\n                    ).encode("utf-8")\n                ).hexdigest(),\n            }\n            for chapter in snapshot.chapters\n        ]\n        request = ModelTaskRequest(\n            task_id=hashlib.sha256(\n                f"{state.run_id}:critique:{snapshot.manifest_hash}".encode("utf-8")\n            ).hexdigest()[:26],\n''',
)

replace_once(
    FINALIZER,
    '''            section_objective=(\n                "Independently review the complete exact pre-release snapshot; provide "\n                "location-specific evidence and a bounded correction action for every defect."\n            ),\n            authoritative_context={\n                "master_hash": snapshot.manifest_hash,\n                "complete_book": snapshot.model_dump(mode="json"),\n            },\n''',
    '''            section_objective=(\n                "Independently review the complete exact pre-release snapshot against the approved "\n                "Book Definition and architecture. Verify promise coverage, necessity and order of "\n                "chapters, long-range contradictions/repetition, terminology continuity, evidence "\n                "boundaries, introduction-to-conclusion integrity, and practical or explanatory "\n                "value appropriate to this nonfiction profile. Provide location-specific evidence "\n                "and a bounded correction action for every defect."\n            ),\n            authoritative_context={\n                "master_hash": snapshot.manifest_hash,\n                "complete_book": snapshot.model_dump(mode="json"),\n                "book_definition": book_definition,\n                "architecture": architecture,\n                "book_context": self._book_context(book_id),\n                "registered_claims": self._registered_claims(book_id),\n                "chapter_coverage_manifest": chapter_coverage_manifest,\n                "whole_book_review_required": True,\n                "structural_preflight_is_not_semantic_acceptance": True,\n            },\n''',
)

replace_once(
    FINALIZER_TEST,
    '''    exact_book = adapter.last_request.authoritative_context["complete_book"]\n    assert len(exact_book["chapters"]) == 2\n    assert adapter.last_request.authoritative_context["master_hash"]\n''',
    '''    exact_context = adapter.last_request.authoritative_context\n    exact_book = exact_context["complete_book"]\n    assert len(exact_book["chapters"]) == 2\n    assert exact_context["master_hash"]\n    assert exact_context["book_definition"]["central_promise"]\n    assert exact_context["architecture"]["parts"]\n    assert exact_context["whole_book_review_required"] is True\n    assert exact_context["structural_preflight_is_not_semantic_acceptance"] is True\n    coverage = exact_context["chapter_coverage_manifest"]\n    assert [item["chapter_id"] for item in coverage] == [\n        item["chapter_id"] for item in exact_book["chapters"]\n    ]\n    assert all(len(item["content_hash"]) == 64 for item in coverage)\n''',
)

# New provider-free regression makes the semantics explicit: nonsense may satisfy a cheap shape
# check, but the system must never serialize that as semantic/top-tier quality acceptance.
path = ROOT / GATE_TEST
if path.exists():
    raise SystemExit(f"unexpected existing test file: {GATE_TEST}")
path.write_text('''from book_os_core.auto_book_gates import AutoBookEvidenceGates\nfrom book_os_core.model_gateway import BookConceptProposalOutput\n\n\ndef _concept() -> BookConceptProposalOutput:\n    return BookConceptProposalOutput(\n        essence="Лиловый чайник объясняет квадратную тишину облаков",\n        reader_job="Собрать лиловый чайник для квадратной тишины",\n        reader_problem="Квадратная тишина мешает облачным чайникам двигаться",\n        reader_transformation="Облачный чайник применяет лиловую квадратную тишину иначе",\n        central_idea="Лиловый чайник связывает квадратную тишину с облаками",\n        central_promise="Читатель получит квадратную карту лиловых облачных чайников",\n        differentiation="Метод отличает облака через лиловый чайник и квадратную тишину",\n        why_now="Сейчас лиловые облака особенно квадратны для чайника",\n        scope_in=["Лиловые чайники и квадратные облака"],\n        scope_out=["Обычная кухня и реальная метеорология"],\n        series_place="Отдельная книга про квадратную тишину лиловых чайников",\n        overlap_risks=[],\n    )\n\n\ndef test_structural_preflight_never_claims_semantic_quality() -> None:\n    concept = _concept()\n    contract = {\n        "reader": "Читатель лиловых квадратных облачных чайников",\n        "reader_problem": "Квадратная тишина мешает облачным чайникам двигаться",\n        "central_promise": "Получить карту квадратных лиловых облачных чайников",\n        "central_thesis": "Лиловый чайник объясняет квадратную тишину через облачные связи",\n        "unique_angle": "Квадратная облачная тишина рассматривается через лиловый чайник",\n        "reader_trajectory": "От тишины облака к квадратной карте лилового чайника",\n        "explicit_exclusions": ["Реальная метеорология"],\n        "readiness_criteria": ["Карта собрана"],\n    }\n    result = AutoBookEvidenceGates.definition(contract, concept)\n    # The deliberately nonsensical copy can satisfy several token-count checks.  The contract is\n    # nevertheless only STRUCTURAL_PREFLIGHT evidence and cannot be called semantic quality.\n    assert any(item.status == "PASS" for item in result.checks)\n    assert all(item.evaluation_scope == "STRUCTURAL_PREFLIGHT" for item in result.checks)\n    assert all(item.semantic_quality_claimed is False for item in result.checks)\n\n\ndef test_gate_schema_labels_even_top_tier_name_as_structural_only() -> None:\n    result = AutoBookEvidenceGates.definition(\n        {\n            "reader": "Практикующий консультант с собственной услугой",\n            "reader_problem": "Не понимает почему заявки не превращаются в продажи",\n            "central_promise": "Найти и исправить узкие места системы продаж услуги",\n            "central_thesis": "Продажа услуги зависит от последовательности проверяемых решений клиента",\n            "unique_angle": "Диагностика потерь связывает каждое решение с измеримым действием",\n            "reader_trajectory": "От хаотичных действий к измеримой системе решений и проверок",\n            "explicit_exclusions": ["Создание самой услуги"],\n            "readiness_criteria": ["Каждый этап имеет проверяемый результат"],\n        },\n        BookConceptProposalOutput(\n            essence="Система продаж услуги",\n            reader_job="Продать профессиональную услугу предсказуемо",\n            reader_problem="Заявки не превращаются в оплаченные сделки",\n            reader_transformation="Читатель управляет измеримой системой продаж своей услуги",\n            central_idea="Каждая продажа состоит из последовательности решений клиента",\n            central_promise="Диагностировать потери и исправить конкретные этапы продаж",\n            differentiation="Фокус на экономике и решениях вместо набора рекламных приемов",\n            why_now="Стоимость привлечения растет и ошибки системы становятся дороже",\n            scope_in=["Диагностика воронки"],\n            scope_out=["Разработка продукта"],\n            series_place="Базовая книга о системе продаж услуг",\n            overlap_risks=[],\n        ),\n    )\n    check = next(item for item in result.checks if item.gate == "top_tier_global")\n    assert check.evaluation_scope == "STRUCTURAL_PREFLIGHT"\n    assert check.semantic_quality_claimed is False\n''', encoding="utf-8")

print("T04 semantic-quality/whole-book review hardening applied")
