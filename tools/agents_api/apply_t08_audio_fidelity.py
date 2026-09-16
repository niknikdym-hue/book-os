#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve()


def replace_once(rel: str, old: str, new: str, label: str) -> None:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one exact anchor in {rel}, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def insert_before(rel: str, marker: str, block: str, label: str) -> None:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    count = text.count(marker)
    if count != 1:
        raise SystemExit(f"{label}: expected one marker in {rel}, found {count}")
    path.write_text(text.replace(marker, block + marker, 1), encoding="utf-8")


def append_once(rel: str, marker: str, block: str, label: str) -> None:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    if marker in text:
        raise SystemExit(f"{label}: marker already present in {rel}")
    path.write_text(text.rstrip() + "\n\n" + block.strip() + "\n", encoding="utf-8")


SRC = "services/local-core/src/book_os_core/audio_script.py"
ATTENTION = "services/local-core/src/book_os_core/audio_attention.py"
API = "services/local-core/src/book_os_core/audio_script_api.py"
FINALIZER = "services/local-core/src/book_os_core/auto_book_finalizer.py"
TEST = "services/local-core/tests/test_audio_script.py"
API_TEST = "services/local-core/tests/test_audio_script_api.py"

replace_once(
    SRC,
    '''class AudioTransformation(BaseModel):\n    source_unit_id: str = Field(min_length=1, max_length=300)\n    outcome: Literal["PRESERVED", "REWRITTEN", "MOVED", "OMITTED", "ADDED"]\n    summary: str = Field(min_length=1, max_length=4000)\n    material: bool = False\n    human_review_required: bool = False\n''',
    '''class AudioTransformation(BaseModel):\n    source_unit_id: str = Field(min_length=1, max_length=300)\n    outcome: Literal["PRESERVED", "REWRITTEN", "MOVED", "OMITTED", "ADDED"]\n    summary: str = Field(min_length=1, max_length=4000)\n    material: bool = False\n    human_review_required: bool = False\n    source_text_hash: str | None = Field(default=None, min_length=64, max_length=64)\n    required_numeric_values: list[str] = Field(default_factory=list, max_length=200)\n    material_review_items: list[str] = Field(default_factory=list, max_length=100)\n''',
    "extend AudioTransformation with exact-source fidelity ledger",
)

insert_before(
    SRC,
    '''class AudioScriptService:\n''',
    r'''def _numeric_values(value: str) -> list[str]:
    """Return ordered canonical numeric values while preserving grouped thousands/decimals."""
    raw = re.findall(
        r"(?<!\d)(?:\d{1,3}(?:[ \u00a0]\d{3})+|\d+)(?:[.,]\d+)?(?!\d)",
        value,
    )
    result: list[str] = []
    for item in raw:
        normalized = item.replace(" ", "").replace("\u00a0", "").replace(",", ".")
        if normalized not in result:
            result.append(normalized)
    return result


def _material_review_items(value: str) -> list[str]:
    """Identify source statements whose semantic force cannot be proven by token overlap."""
    marker = re.compile(
        r"\b(?:однако|но|при этом|хотя|если|только|лишь|не означает|не доказывает|"
        r"не гарантирует|ограничени\w*|оговорк\w*|вывод\w*|следовательно|поэтому|итак|"
        r"нельзя|может|могут|не всегда)\b",
        re.IGNORECASE,
    )
    items: list[str] = []
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", value):
        cleaned = " ".join(sentence.split())
        if cleaned and marker.search(cleaned) and cleaned not in items:
            items.append(cleaned[:1200])
    return items[:100]


''',
    "add material fidelity extractors",
)

replace_once(
    SRC,
    '''        required_numbers = {\n            value for value in item.source_facts if re.fullmatch(r"[\\d.,%]+", value)\n        }\n        audible_numbers: set[str] = set()\n        for value in required_numbers:\n            normalized = value.rstrip("%").replace(",", ".")\n            audible_numbers.add(normalized)\n            try:\n                number = float(normalized)\n                if number.is_integer():\n                    audible_numbers.add(str(int(number)))\n            except ValueError:\n                pass\n        if audible_numbers and not any(value in item.explanation for value in audible_numbers):\n            return False\n''',
    '''        required_numbers = _numeric_values(" ".join(item.source_facts))\n        if required_numbers:\n            audible_numbers = set(_numeric_values(item.explanation))\n            unique_required = list(dict.fromkeys(required_numbers))\n            if len(unique_required) <= 12:\n                if not set(unique_required).issubset(audible_numbers):\n                    return False\n            else:\n                anchors = {unique_required[0], unique_required[-1]}\n                covered = set(unique_required) & audible_numbers\n                if not anchors.issubset(audible_numbers) or len(covered) < 3:\n                    return False\n''',
    "require material visual numbers",
)

replace_once(
    SRC,
    '''        fidelity = [\n            AudioQualityFinding(\n                code="MATERIAL_CHANGE_REQUIRES_HUMAN",\n                location=item.source_unit_id,\n                detail=item.summary,\n                severity="ATTENTION",\n            )\n            for item in transformations\n            if item.material and item.outcome in {"OMITTED", "ADDED", "MOVED"}\n        ]\n\n        listenability_findings = [\n''',
    '''        fidelity = [\n            AudioQualityFinding(\n                code="MATERIAL_CHANGE_REQUIRES_HUMAN",\n                location=item.source_unit_id,\n                detail=item.summary,\n                severity="ATTENTION",\n            )\n            for item in transformations\n            if item.material and item.outcome in {"OMITTED", "ADDED", "MOVED"}\n        ]\n        section_recordings = {\n            section.source_chapter_id: "\\n".join(section.recording_paragraphs())\n            for section in content.sections\n        }\n        material_fidelity: list[AudioQualityFinding] = []\n        for transformation in transformations:\n            if transformation.outcome == "ADDED" or transformation.source_text_hash is None:\n                continue\n            section_text = section_recordings.get(transformation.source_unit_id, "")\n            audible_numbers = set(_numeric_values(section_text))\n            for value in transformation.required_numeric_values:\n                if value not in audible_numbers:\n                    material_fidelity.append(\n                        AudioQualityFinding(\n                            code="MATERIAL_NUMBER_DROPPED",\n                            location=transformation.source_unit_id,\n                            detail=(\n                                f"Исходное материальное числовое значение {value} отсутствует "\n                                "в аудиотексте этого раздела."\n                            ),\n                            severity="BLOCKING",\n                        )\n                    )\n            if mode != "AUDIO_NATIVE":\n                material_fidelity.append(\n                    AudioQualityFinding(\n                        code="MATERIAL_SECTION_FIDELITY_HUMAN_REVIEW_REQUIRED",\n                        location=(\n                            f"{transformation.source_unit_id}:source:"\n                            f"{transformation.source_text_hash[:12]}"\n                        ),\n                        detail=(\n                            "Человек должен сверить exact source section с AudioScript и подтвердить "\n                            "сохранение всех материальных утверждений, оговорок и выводов."\n                        ),\n                        severity="ATTENTION",\n                    )\n                )\n                for index, statement in enumerate(transformation.material_review_items, start=1):\n                    material_fidelity.append(\n                        AudioQualityFinding(\n                            code="MATERIAL_STATEMENT_HUMAN_REVIEW_REQUIRED",\n                            location=f"{transformation.source_unit_id}:material:{index}",\n                            detail=f"Сверить смысл исходного утверждения: {statement}",\n                            severity="ATTENTION",\n                        )\n                    )\n\n        listenability_findings = [\n''',
    "add exact-section material fidelity checks",
)

replace_once(
    SRC,
    '''            check(\n                "SOURCE_FIDELITY",\n                [*fidelity, *fidelity_review] if mode == "SOURCE_FAITHFUL" else [],\n            ),\n            check(\n                "SEMANTIC_FIDELITY",\n                [*fidelity, *fidelity_review] if mode == "LISTENING_ADAPTATION" else [],\n            ),\n''',
    '''            check(\n                "SOURCE_FIDELITY",\n                [*fidelity, *material_fidelity, *fidelity_review]\n                if mode == "SOURCE_FAITHFUL"\n                else [],\n            ),\n            check(\n                "SEMANTIC_FIDELITY",\n                [*fidelity, *material_fidelity, *fidelity_review]\n                if mode == "LISTENING_ADAPTATION"\n                else [],\n            ),\n''',
    "wire material fidelity into mandatory checks",
)

replace_once(
    SRC,
    '''        pronunciation_review = (\n            [\n                AudioQualityFinding(\n                    code="PRONUNCIATION_LEDGER_REVIEW_REQUIRED",\n                    location="whole-script",\n                    detail="Найденные имена, термины или сокращения требуют проверки произношения.",\n                    severity="ATTENTION",\n                )\n            ]\n            if re.search(r"\\b(?:[А-ЯЁA-Z]{2,}|[A-Za-z][A-Za-z0-9.+-]{2,})\\b", recording)\n            else []\n        )\n''',
    '''        pronunciation_review = (\n            [\n                AudioQualityFinding(\n                    code="PRONUNCIATION_LEDGER_REVIEW_REQUIRED",\n                    location="whole-script",\n                    detail="Найденные имена, термины или сокращения требуют проверки произношения.",\n                    severity="ATTENTION",\n                )\n            ]\n            if self.discover_pronunciation(content)\n            else []\n        )\n''',
    "make ambiguous-stress terms visible to pronunciation gate",
)

replace_once(
    SRC,
    '''            transformations.append(\n                AudioTransformation(\n                    source_unit_id=chapter.chapter_id,\n                    outcome=outcome,\n                    summary=summary,\n                )\n            )\n''',
    '''            source_text = "\\n\\n".join(chapter.paragraphs)\n            transformations.append(\n                AudioTransformation(\n                    source_unit_id=chapter.chapter_id,\n                    outcome=outcome,\n                    summary=summary,\n                    source_text_hash=hashlib.sha256(source_text.encode("utf-8")).hexdigest(),\n                    required_numeric_values=_numeric_values(source_text),\n                    material_review_items=_material_review_items(source_text),\n                )\n            )\n''',
    "persist exact-source fidelity ledger",
)

replace_once(
    SRC,
    '''        attention_codes = {\n            finding.code\n            for item in current.quality_checks\n            for finding in item.findings\n            if finding.severity == "ATTENTION"\n        }\n        accepted: set[str] = set(accepted_attention_codes or [])\n        if attention_codes - accepted:\n            raise AudioScriptGateError(\n                "human must explicitly disposition every ATTENTION finding before approval"\n            )\n        approval = {\n            "actor": human_actor,\n            "actor_kind": "HUMAN",\n            "approved_at": utc_now(),\n            "source_hash": current.source_hash,\n            "script_hash": current.content_hash,\n            "accepted_attention_codes": sorted(accepted),\n        }\n''',
    '''        from .audio_attention import attention_finding_key\n\n        attention_findings = [\n            finding\n            for item in current.quality_checks\n            for finding in item.findings\n            if finding.severity == "ATTENTION"\n        ]\n        required = {attention_finding_key(finding) for finding in attention_findings}\n        accepted: set[str] = set(accepted_attention_codes or [])\n        missing = required - accepted\n        unexpected = accepted - required\n        if missing:\n            raise AudioScriptGateError(\n                "human must explicitly disposition every ATTENTION finding by exact location"\n            )\n        if unexpected:\n            raise AudioScriptGateError(\n                "accepted ATTENTION disposition does not match the current exact findings"\n            )\n        approval = {\n            "actor": human_actor,\n            "actor_kind": "HUMAN",\n            "approved_at": utc_now(),\n            "source_hash": current.source_hash,\n            "script_hash": current.content_hash,\n            "accepted_attention_codes": sorted(accepted),\n            "accepted_attention_findings": sorted(accepted),\n        }\n''',
    "make service-level approval exact-finding only",
)

replace_once(
    ATTENTION,
    '''    legacy_codes = {finding.code for finding in findings}\n    return sorted(accepted | legacy_codes)\n''',
    '''    unexpected = sorted(accepted - set(required))\n    if unexpected:\n        raise AudioScriptGateError(\n            "accepted ATTENTION disposition does not match the current exact findings"\n        )\n    return sorted(accepted)\n''',
    "remove legacy aggregate-code bridge",
)
replace_once(
    ATTENTION,
    '''    The returned list deliberately includes both the exact finding keys and their legacy codes.\n    AudioScriptService can therefore keep its existing code-level compatibility while the public\n    author workflows fail closed unless every current finding/location was individually accepted.\n    The exact keys are retained in the approval JSON for auditability.\n''',
    '''    The returned list contains only exact finding identities. Code-only compatibility is\n    deliberately rejected so no aggregate disposition can silently cover a different location or\n    changed detail. The exact keys are retained in approval JSON for auditability.\n''',
    "document strict exact finding contract",
)

replace_once(
    API,
    '''            accepted_values = accepted_attention_values(\n                current,\n                payload.accepted_attention_codes,\n            )\n            script = scripts.approve(\n                book_id,\n                audio_script_id,\n                human_actor=payload.human_actor,\n                accepted_attention_codes=accepted_values,\n            )\n''',
    '''            accepted_values = accepted_attention_values(\n                current,\n                payload.accepted_attention_codes,\n            )\n            script = (\n                current\n                if current.status == "APPROVED" and current.ready_for_export\n                else scripts.approve(\n                    book_id,\n                    audio_script_id,\n                    human_actor=payload.human_actor,\n                    accepted_attention_codes=accepted_values,\n                )\n            )\n''',
    "allow idempotent export retry after exact approval",
)

replace_once(
    FINALIZER,
    '''        "meaning, claims, evidence, qualifications and conclusions. Break overloaded syntax and "\n        "long lists, verbalize numbers unambiguously, replace page-dependent references, clarify "\n''',
    '''        "meaning, claims, evidence, qualifications and conclusions. Break overloaded syntax and "\n        "long lists, preserve every numeric value exactly as digits while verbalizing units and "\n        "symbols unambiguously, replace page-dependent references, clarify "\n''',
    "make numeric auditability explicit in audio prompt",
)

replace_once(
    TEST,
    '''from book_os_core.audio_script import (\n''',
    '''from book_os_core.audio_attention import attention_finding_key\nfrom book_os_core.audio_script import (\n''',
    "import exact finding key in service tests",
)
replace_once(
    TEST,
    '''    attention = sorted(\n        {\n            finding.code\n            for check in proposed.quality_checks\n            for finding in check.findings\n            if finding.severity == "ATTENTION"\n        }\n    )\n    approved = service.approve(\n        book_id,\n        proposed.audio_script_id,\n        human_actor="Owner",\n        accepted_attention_codes=attention,\n    )\n''',
    '''    aggregate_codes = sorted(\n        {\n            finding.code\n            for check in proposed.quality_checks\n            for finding in check.findings\n            if finding.severity == "ATTENTION"\n        }\n    )\n    with pytest.raises(AudioScriptGateError, match="exact location"):\n        service.approve(\n            book_id,\n            proposed.audio_script_id,\n            human_actor="Owner",\n            accepted_attention_codes=aggregate_codes,\n        )\n    attention = sorted(\n        attention_finding_key(finding)\n        for check in proposed.quality_checks\n        for finding in check.findings\n        if finding.severity == "ATTENTION"\n    )\n    approved = service.approve(\n        book_id,\n        proposed.audio_script_id,\n        human_actor="Owner",\n        accepted_attention_codes=attention,\n    )\n''',
    "make direct service approval exact-finding only",
)

append_once(
    TEST,
    "test_material_fidelity_blocks_dropped_numeric_values",
    r'''def test_material_fidelity_blocks_dropped_numeric_values_and_requires_exact_section_review() -> None:
    service = AudioScriptService(Path("."))
    master = StructuredBookMaster(
        title="Книга о проверяемых данных",
        author="Автор",
        chapters=[
            MasterChapter(
                chapter_id="chapter-material",
                title="Материальный вывод",
                paragraphs=[
                    (
                        "Конверсия выросла с 20 до 35%, но это не доказывает причинность. "
                        "Вывод: при бюджете 50 000 ₽ масштабирование допустимо только после "
                        "повторной проверки."
                    )
                ],
            )
        ],
    )
    dropped_content, dropped_map = service.content_from_master(
        master,
        adaptation_mode="SOURCE_FAITHFUL",
        adapted_chapters={
            "chapter-material": (
                "Конверсия выросла с 20 процентов, но это не доказывает причинность. "
                "Вывод: при бюджете 50 000 рублей масштабирование допустимо только после "
                "повторной проверки."
            )
        },
    )
    dropped_checks = service.evaluate(
        dropped_content,
        source_hash="f" * 64,
        mode="SOURCE_FAITHFUL",
        transformations=dropped_map,
    )
    source_fidelity = next(item for item in dropped_checks if item.check_kind == "SOURCE_FIDELITY")
    assert source_fidelity.state == "BLOCKING"
    assert any(
        finding.code == "MATERIAL_NUMBER_DROPPED" and "35" in finding.detail
        for finding in source_fidelity.findings
    )

    complete_content, complete_map = service.content_from_master(
        master,
        adaptation_mode="SOURCE_FAITHFUL",
        adapted_chapters={
            "chapter-material": (
                "Конверсия выросла с 20 до 35 процентов, но это не доказывает причинность. "
                "Вывод: при бюджете 50 000 рублей масштабирование допустимо только после "
                "повторной проверки."
            )
        },
    )
    complete_checks = service.evaluate(
        complete_content,
        source_hash="f" * 64,
        mode="SOURCE_FAITHFUL",
        transformations=complete_map,
    )
    source_fidelity = next(item for item in complete_checks if item.check_kind == "SOURCE_FIDELITY")
    assert not any(finding.code == "MATERIAL_NUMBER_DROPPED" for finding in source_fidelity.findings)
    assert any(
        finding.code == "MATERIAL_SECTION_FIDELITY_HUMAN_REVIEW_REQUIRED"
        and "source:" in finding.location
        for finding in source_fidelity.findings
    )
    assert any(
        finding.code == "MATERIAL_STATEMENT_HUMAN_REVIEW_REQUIRED"
        and "не доказывает причинность" in finding.detail
        for finding in source_fidelity.findings
    )


def test_small_multiline_visual_must_preserve_every_numeric_value() -> None:
    service = AudioScriptService(Path("."))
    weak = AudioScriptContent(
        title="Визуальные данные",
        author="Автор",
        sections=[
            AudioScriptSection(
                source_chapter_id="chapter-table",
                title="Таблица",
                paragraphs=["Сравним три сегмента."],
                visual_decisions=[
                    AudioVisualDecision(
                        object_id="table-three-rows",
                        kind="TABLE",
                        title="Конверсия сегментов",
                        disposition="AUDIO_EXPLANATION",
                        placement_after_paragraph=1,
                        explanation=(
                            "Таблица сравнивает три сегмента: первый показывает 20, "
                            "а третий показывает 40, поэтому значения различаются заметно."
                        ),
                        source_facts=["Сегмент А", "20", "Сегмент Б", "35", "Сегмент В", "40"],
                    )
                ],
            )
        ],
    )
    checks = service.evaluate(
        weak,
        source_hash="1" * 64,
        mode="AUDIO_NATIVE",
        transformations=[
            AudioTransformation(
                source_unit_id="chapter-table",
                outcome="PRESERVED",
                summary="Audio-native source.",
            )
        ],
    )
    visual = next(item for item in checks if item.check_kind == "VISUAL_DEPENDENCY_RESOLVED")
    assert visual.state == "BLOCKING"

    strong = weak.model_copy(deep=True)
    strong.sections[0].visual_decisions[0].explanation = (
        "Таблица сравнивает три сегмента: первый показывает 20, второй 35, "
        "а третий 40; поэтому значения различаются заметно."
    )
    checks = service.evaluate(
        strong,
        source_hash="1" * 64,
        mode="AUDIO_NATIVE",
        transformations=[
            AudioTransformation(
                source_unit_id="chapter-table",
                outcome="PRESERVED",
                summary="Audio-native source.",
            )
        ],
    )
    visual = next(item for item in checks if item.check_kind == "VISUAL_DEPENDENCY_RESOLVED")
    assert visual.state == "PASS"


def test_ambiguous_stress_alone_requires_pronunciation_ledger_review() -> None:
    service = AudioScriptService(Path("."))
    content = AudioScriptContent(
        title="Проверка произношения",
        author="Автор",
        sections=[
            AudioScriptSection(
                source_chapter_id="chapter-stress",
                title="Произношение",
                paragraphs=["Старинный замок описан в примере для слушателя."],
            )
        ],
    )
    checks = service.evaluate(
        content,
        source_hash="2" * 64,
        mode="AUDIO_NATIVE",
        transformations=[
            AudioTransformation(
                source_unit_id="chapter-stress",
                outcome="PRESERVED",
                summary="Audio-native source.",
            )
        ],
    )
    pronunciation = next(
        item for item in checks if item.check_kind == "ACRONYM_AND_TERM_PRONUNCIATION"
    )
    assert pronunciation.state == "ATTENTION"
''',
    "append T08 fidelity regressions",
)

replace_once(
    API_TEST,
    '''import base64\nfrom pathlib import Path\n''',
    '''import base64\nimport json\nfrom pathlib import Path\n\nfrom docx import Document\n''',
    "import consistency helpers in API test",
)
replace_once(
    API_TEST,
    '''    assert source_path.read_bytes() == original\n    assert result["audio_script"]["approval"]["actor_kind"] == "HUMAN"\n\n    reopened = client.post(\n''',
    '''    assert source_path.read_bytes() == original\n    assert result["audio_script"]["approval"]["actor_kind"] == "HUMAN"\n\n    reading = next(\n        item for item in result["artifacts"] if item["output_kind"] == "AUDIO_READING_DOCX"\n    )\n    reading_doc = Document(tmp_path / "projects" / book_id / reading["relative_path"])\n    doc_blocks = [\n        paragraph.text.strip() for paragraph in reading_doc.paragraphs if paragraph.text.strip()\n    ]\n    voice_blocks = [value.strip() for value in voice_text.split("\\n\\n") if value.strip()]\n    assert doc_blocks == voice_blocks\n\n    handoff = next(\n        item for item in result["artifacts"] if item["output_kind"] == "AUDIO_PRODUCTION_HANDOFF"\n    )\n    manifest = json.loads(\n        (tmp_path / "projects" / book_id / handoff["relative_path"]).read_text(encoding="utf-8")\n    )\n    assert manifest["audio_script_hash"] == result["audio_script"]["content_hash"]\n    assert manifest["recording_text"]["content_hash"] == voice["content_hash"]\n\n    retried = client.post(\n        f"/api/projects/{book_id}/audio-scripts/{script['audio_script_id']}/approve",\n        json={\n            "human_actor": "Елена Дым",\n            "accepted_attention_codes": [],\n            "reading_docx": True,\n            "litres_docx": True,\n            "pronunciation_dictionary": True,\n        },\n    )\n    assert retried.status_code == 200, retried.text\n    assert retried.json()["audio_script"]["content_hash"] == result["audio_script"]["content_hash"]\n    assert adapter.calls == 1\n\n    reopened = client.post(\n''',
    "prove retry plus DOCX/TXT/handoff consistency",
)

print("T08 AudioScript fidelity/exact-approval/retry hardening applied")
