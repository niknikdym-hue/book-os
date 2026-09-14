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


def insert_before(rel: str, marker: str, block: str) -> None:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    if text.count(marker) != 1:
        raise SystemExit(f"expected one marker in {rel}: {marker[:120]!r}")
    path.write_text(text.replace(marker, block + marker, 1), encoding="utf-8")


def append(rel: str, block: str) -> None:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    if block.strip() in text:
        raise SystemExit(f"block already present in {rel}")
    path.write_text(text.rstrip() + "\n\n" + block.strip() + "\n", encoding="utf-8")


SRC = "services/local-core/src/book_os_core/audio_script.py"
TEST = "services/local-core/tests/test_audio_script.py"

replace_once(
    SRC,
    '''class AudioTransformation(BaseModel):\n    source_unit_id: str = Field(min_length=1, max_length=300)\n    outcome: Literal["PRESERVED", "REWRITTEN", "MOVED", "OMITTED", "ADDED"]\n    summary: str = Field(min_length=1, max_length=4000)\n    material: bool = False\n    human_review_required: bool = False\n''',
    '''class AudioTransformation(BaseModel):\n    source_unit_id: str = Field(min_length=1, max_length=300)\n    outcome: Literal["PRESERVED", "REWRITTEN", "MOVED", "OMITTED", "ADDED"]\n    summary: str = Field(min_length=1, max_length=4000)\n    material: bool = False\n    human_review_required: bool = False\n    source_material_facts: list[str] = Field(default_factory=list, max_length=500)\n    audio_material_facts: list[str] = Field(default_factory=list, max_length=500)\n    material_fact_mismatch: bool = False\n''',
)

insert_before(
    SRC,
    '''class AudioScriptService:\n''',
    r'''def _material_fact_tokens(value: str) -> list[str]:
    """Extract stable material number/value identities from prose without model calls."""
    unit_map = {
        "%": "PERCENT",
        "процент": "PERCENT",
        "процента": "PERCENT",
        "процентов": "PERCENT",
        "₽": "RUB",
        "руб": "RUB",
        "руб.": "RUB",
        "рубль": "RUB",
        "рубля": "RUB",
        "рублей": "RUB",
        "$": "USD",
        "доллар": "USD",
        "доллара": "USD",
        "долларов": "USD",
        "€": "EUR",
        "евро": "EUR",
    }
    pattern = re.compile(
        r"(?<![\w])(?P<number>\d+(?:[\s\u00a0]\d{3})*(?:[.,]\d+)?)"
        r"\s*(?P<unit>%|процент(?:а|ов)?|₽|руб\.?|рубль|рубля|рублей|\$|"
        r"доллар(?:а|ов)?|€|евро)?",
        re.IGNORECASE,
    )
    result: list[str] = []
    for match in pattern.finditer(value):
        number = match.group("number").replace(" ", "").replace("\u00a0", "").replace(",", ".")
        unit_raw = (match.group("unit") or "").casefold()
        unit = unit_map.get(unit_raw, "NUMBER")
        result.append(f"{number}:{unit}")
    return sorted(result)


''',
)

insert_before(
    SRC,
    '''        listenability_findings = [\n''',
    '''        material_fact_findings = [\n            AudioQualityFinding(\n                code="MATERIAL_FACT_MISMATCH",\n                location=item.source_unit_id,\n                detail=(\n                    "AudioScript changed, omitted, or introduced material numeric/value facts: "\n                    f"source={item.source_material_facts}; audio={item.audio_material_facts}"\n                ),\n                severity="BLOCKING",\n            )\n            for item in transformations\n            if item.material_fact_mismatch\n        ]\n\n''',
)

replace_once(
    SRC,
    '''                [*fidelity, *fidelity_review] if mode == "SOURCE_FAITHFUL" else [],\n''',
    '''                [*material_fact_findings, *fidelity, *fidelity_review]\n                if mode == "SOURCE_FAITHFUL"\n                else [],\n''',
)
replace_once(
    SRC,
    '''                [*fidelity, *fidelity_review] if mode == "LISTENING_ADAPTATION" else [],\n''',
    '''                [*material_fact_findings, *fidelity, *fidelity_review]\n                if mode == "LISTENING_ADAPTATION"\n                else [],\n''',
)
replace_once(
    SRC,
    '''            transformations.append(\n                AudioTransformation(\n                    source_unit_id=chapter.chapter_id,\n                    outcome=outcome,\n                    summary=summary,\n                )\n            )\n''',
    '''            source_material_facts = _material_fact_tokens("\\n".join(chapter.paragraphs))\n            audio_material_facts = _material_fact_tokens("\\n".join(paragraphs))\n            transformations.append(\n                AudioTransformation(\n                    source_unit_id=chapter.chapter_id,\n                    outcome=outcome,\n                    summary=summary,\n                    source_material_facts=source_material_facts,\n                    audio_material_facts=audio_material_facts,\n                    material_fact_mismatch=(source_material_facts != audio_material_facts),\n                )\n            )\n''',
)

old_revise = '''            transformations=[\n                AudioTransformation(\n                    source_unit_id=section.source_chapter_id,\n                    outcome="REWRITTEN",\n                    summary=change_summary.strip(),\n                    material=True,\n                    human_review_required=True,\n                )\n                for section in content.sections\n            ],\n'''
new_revise = '''            transformations=[\n                AudioTransformation(\n                    source_unit_id=section.source_chapter_id,\n                    outcome="REWRITTEN",\n                    summary=change_summary.strip(),\n                    material=True,\n                    human_review_required=True,\n                    source_material_facts=(\n                        source_map[section.source_chapter_id].source_material_facts\n                        if section.source_chapter_id in source_map\n                        else []\n                    ),\n                    audio_material_facts=_material_fact_tokens(\n                        "\\n".join(section.recording_paragraphs())\n                    ),\n                    material_fact_mismatch=(\n                        bool(\n                            section.source_chapter_id in source_map\n                            and source_map[section.source_chapter_id].source_material_facts\n                        )\n                        and source_map[section.source_chapter_id].source_material_facts\n                        != _material_fact_tokens("\\n".join(section.recording_paragraphs()))\n                    ),\n                )\n                for section in content.sections\n            ],\n'''
# Insert source_map before create_proposal and replace transformation list.
replace_once(
    SRC,
    '''        revised = self.create_proposal(\n''',
    '''        source_map = {item.source_unit_id: item for item in current.transformations}\n        revised = self.create_proposal(\n''',
)
replace_once(SRC, old_revise, new_revise)

append(TEST, r'''
def test_audio_material_numbers_currency_and_percent_must_match_exact_source() -> None:
    service = AudioScriptService(Path("."))
    master = StructuredBookMaster(
        title="Книга",
        author="Автор",
        chapters=[
            MasterChapter(
                chapter_id="chapter-facts",
                title="Факты",
                paragraphs=["Цена составляет 1 500 ₽, а конверсия — 25% при диапазоне 10–20%."],
            )
        ],
    )
    preserved, preserved_map = service.content_from_master(
        master,
        adaptation_mode="SOURCE_FAITHFUL",
        adapted_chapters={
            "chapter-facts": "Для слушателя: цена составляет 1 500 ₽, конверсия — 25%, диапазон 10–20%."
        },
    )
    assert preserved_map[0].material_fact_mismatch is False
    assert preserved_map[0].source_material_facts == preserved_map[0].audio_material_facts
    assert not any(
        finding.code == "MATERIAL_FACT_MISMATCH"
        for check in service.evaluate(
            preserved,
            source_hash="f" * 64,
            mode="SOURCE_FAITHFUL",
            transformations=preserved_map,
        )
        for finding in check.findings
    )

    changed, changed_map = service.content_from_master(
        master,
        adaptation_mode="SOURCE_FAITHFUL",
        adapted_chapters={
            "chapter-facts": "Для слушателя: цена составляет 2 500 ₽, конверсия — 25%, диапазон 10–20%."
        },
    )
    assert changed_map[0].material_fact_mismatch is True
    checks = service.evaluate(
        changed,
        source_hash="f" * 64,
        mode="SOURCE_FAITHFUL",
        transformations=changed_map,
    )
    mismatch = [
        finding
        for check in checks
        for finding in check.findings
        if finding.code == "MATERIAL_FACT_MISMATCH"
    ]
    assert mismatch and mismatch[0].severity == "BLOCKING"


def test_human_audio_revision_cannot_silently_change_bound_material_value(tmp_path: Path) -> None:
    book_id = setup_book(tmp_path)
    service = AudioScriptService(tmp_path)
    master = StructuredBookMaster(
        title="Проверяемая аудиокнига",
        author="Елена Дым",
        chapters=[
            MasterChapter(
                chapter_id="chapter-1",
                title="Глава первая. Решение",
                paragraphs=["Стоимость решения составляет 1000 ₽."],
            )
        ],
    )
    content, mapping = service.content_from_master(
        master,
        adaptation_mode="SOURCE_FAITHFUL",
        adapted_chapters={"chapter-1": "Стоимость решения составляет 1000 ₽."},
    )
    proposed = service.create_proposal(
        book_id,
        source_kind="IMPORTED_SOURCE",
        source_identity="source.txt",
        source_hash="9" * 64,
        adaptation_mode="SOURCE_FAITHFUL",
        content=content,
        transformations=mapping,
        provenance={"provider_calls": 0},
    )
    revised_content = proposed.content.model_copy(deep=True)
    revised_content.sections[0].paragraphs = ["Стоимость решения составляет 9000 ₽."]
    revised = service.revise_by_human(
        book_id,
        proposed.audio_script_id,
        content=revised_content,
        human_actor="Owner",
        change_summary="Редакторская правка формулировки.",
    )
    assert any(
        finding.code == "MATERIAL_FACT_MISMATCH" and finding.severity == "BLOCKING"
        for check in revised.quality_checks
        for finding in check.findings
    )
    with pytest.raises(AudioScriptGateError, match="blocking checks"):
        service.approve(book_id, revised.audio_script_id, human_actor="Owner")
''')

print("T08 AudioScript material-fidelity hardening applied")
