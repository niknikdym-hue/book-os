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


FINALIZER = "services/local-core/src/book_os_core/auto_book_finalizer.py"
TEST = "services/local-core/tests/test_auto_book_finalizer.py"

insert_before(
    FINALIZER,
    '''    def _execute_visual_policy(\n''',
    r'''    @staticmethod
    def _numbered_step_table_spec(paragraphs: list[str]) -> dict[str, Any] | None:
        rows: list[list[str]] = []
        indices: list[int] = []
        for paragraph_index, paragraph in enumerate(paragraphs, start=1):
            match = re.match(r"^\s*(\d{1,2})[.)]\s+(.+?)\s*$", paragraph, re.DOTALL)
            if match is None:
                continue
            rows.append([match.group(1), match.group(2).strip()])
            indices.append(paragraph_index)
        if len(rows) < 3:
            return None
        return {
            "headers": ["Шаг", "Действие"],
            "rows": rows,
            "source_paragraphs": indices,
            "placement_after_paragraph": max(indices),
            "purpose": "Собрать явно перечисленные шаги главы в сравнимую последовательность",
            "caption": "Последовательность шагов главы",
            "alt_text": "Таблица перечисляет все явно пронумерованные шаги главы без сокращения.",
            "audio_equivalent": " ".join(
                f"Шаг {number}: {action}" for number, action in rows
            ),
        }

    @staticmethod
    def _percentage_chart_spec(paragraphs: list[str]) -> dict[str, Any] | None:
        for paragraph_index, paragraph in enumerate(paragraphs, start=1):
            points: list[tuple[str, float]] = []
            for match in re.finditer(
                r"([^.!?;:\n]{2,80}?)\s+(\d+(?:[.,]\d+)?)\s*%",
                paragraph,
            ):
                label = " ".join(match.group(1).split()).strip(" ,;:-")
                if not label:
                    continue
                value = float(match.group(2).replace(",", "."))
                points.append((label, value))
            unique = {label.casefold() for label, _ in points}
            if len(points) < 2 or len(unique) != len(points):
                continue
            spoken = "; ".join(f"{label} — {value:g} процентов" for label, value in points)
            return {
                "data": points,
                "unit": "%",
                "source_paragraph": paragraph_index,
                "placement_after_paragraph": paragraph_index,
                "purpose": "Сравнить процентные значения из одного явно связанного фрагмента",
                "caption": "Сравнение процентных значений",
                "alt_text": f"Диаграмма сравнивает: {spoken}.",
                "audio_equivalent": f"Процентные значения: {spoken}.",
            }
        return None

''',
)

old = '''                wants_table = "таблиц" in requirements or "таблиц" in manuscript.casefold()
                wants_visual = any(
                    token in requirements or token in manuscript.casefold()
                    for token in ("график", "диаграм", "схем")
                )
                paragraphs = [p.strip() for p in manuscript.split("\n\n") if p.strip()]
                assets: list[tuple[str, dict[str, Any], str, str]] = []
                if wants_table and paragraphs:
                    rows = [
                        [str(index), paragraph[:240]]
                        for index, paragraph in enumerate(paragraphs[:4], 1)
                    ]
                    spoken_rows = " ".join(
                        f"Шаг {index}: {paragraph[:240]}"
                        for index, paragraph in enumerate(paragraphs[:4], 1)
                    )
                    assets.append(
                        (
                            "TABLE",
                            {"headers": ["Шаг", "Содержание"], "rows": rows},
                            "Ключевые шаги главы",
                            "Таблица последовательно перечисляет ключевые шаги главы. "
                            + spoken_rows,
                        )
                    )
                if wants_visual:
                    points = [
                        (
                            label.strip()[-50:] or f"Показатель {index}",
                            float(value.replace(",", ".")),
                        )
                        for index, (label, value) in enumerate(
                            re.findall(r"([^.!?\n]{1,60}?)\s+(\d+(?:[.,]\d+)?)\s*%", manuscript),
                            1,
                        )
                    ][:8]
                    kind = "CHART" if points else "SCHEME"
                    assets.append(
                        (
                            kind,
                            {"data": points},
                            "Наглядное объяснение механизма главы",
                            (
                                "Диаграмма вслух перечисляет значения и объясняет их соотношение "
                                "в контексте главы."
                                if points
                                else "Схема последовательно объясняет механизм, его этапы и связь "
                                "с выводом главы."
                            ),
                        )
                    )
                for kind, data, caption, audio in assets:
'''
new = '''                manuscript_lower = manuscript.casefold()
                table_required = "таблиц" in requirements
                visual_required = any(token in requirements for token in ("график", "диаграм", "схем"))
                wants_table = table_required or "таблиц" in manuscript_lower
                wants_visual = visual_required or any(
                    token in manuscript_lower for token in ("график", "диаграм", "схем")
                )
                paragraphs = [p.strip() for p in manuscript.split("\n\n") if p.strip()]
                assets: list[tuple[str, dict[str, Any], str, str, str, int, str]] = []
                unresolved: list[str] = []

                if wants_table:
                    table_spec = self._numbered_step_table_spec(paragraphs)
                    if table_spec is None:
                        if table_required:
                            unresolved.append("TABLE: no explicit structured rows in the exact source")
                    else:
                        data = {
                            "headers": table_spec["headers"],
                            "rows": table_spec["rows"],
                            "source_paragraphs": table_spec["source_paragraphs"],
                        }
                        assets.append(
                            (
                                "TABLE",
                                data,
                                str(table_spec["caption"]),
                                str(table_spec["audio_equivalent"]),
                                str(table_spec["purpose"]),
                                int(table_spec["placement_after_paragraph"]),
                                str(table_spec["alt_text"]),
                            )
                        )

                if wants_visual:
                    chart_spec = self._percentage_chart_spec(paragraphs)
                    if chart_spec is None:
                        if visual_required:
                            unresolved.append(
                                "VISUAL: no coherent same-context numeric series for a programmatic chart"
                            )
                    else:
                        data = {
                            "data": chart_spec["data"],
                            "unit": chart_spec["unit"],
                            "source_paragraph": chart_spec["source_paragraph"],
                        }
                        assets.append(
                            (
                                "CHART",
                                data,
                                str(chart_spec["caption"]),
                                str(chart_spec["audio_equivalent"]),
                                str(chart_spec["purpose"]),
                                int(chart_spec["placement_after_paragraph"]),
                                str(chart_spec["alt_text"]),
                            )
                        )

                if unresolved:
                    raise AutoBookGateError(
                        "required visual material has no truthful VisualSpec: " + "; ".join(unresolved)
                    )

                for kind, data, caption, audio, purpose, placement, alt_text in assets:
'''
replace_once(FINALIZER, old, new)

replace_once(
    FINALIZER,
    '''                                "purpose": caption,
                                "source": f"revision:{head.revision_id}#{head.revision_hash}",
                                "caption": caption,
                                "rights": "Created deterministically by BOOK OS from the manuscript",
                                "alt": audio,
                                "audio": audio,
''',
    '''                                "purpose": purpose,
                                "source": f"revision:{head.revision_id}#{head.revision_hash}",
                                "caption": caption,
                                "rights": "Programmatic rendering from owner-controlled manuscript data",
                                "alt": alt_text,
                                "audio": audio,
''',
)
replace_once(
    FINALIZER,
    '''                                "kind": kind,
                                "data": data,
                                "revision_hash": head.revision_hash,
''',
    '''                                "kind": kind,
                                "data": data,
                                "placement_after_paragraph": placement,
                                "revision_hash": head.revision_hash,
''',
)
replace_once(
    FINALIZER,
    '''                                "INSERT OR IGNORE INTO auto_book_visual_assets(asset_id,run_id,kind,"
                                "purpose,placement,data_source,caption,origin,rights_note,alt_text,"
                                "audio_equivalent,content_hash,created_at,chapter_id,source_revision_id,"
                                "source_revision_hash,data_json,status) VALUES (:id,:run_id,:kind,:purpose,"
                                "'paragraph:0',:source,:caption,'PROGRAMMATIC',:rights,:alt,:audio,:hash,"
''',
    '''                                "INSERT OR IGNORE INTO auto_book_visual_assets(asset_id,run_id,kind,"
                                "purpose,placement,data_source,caption,origin,rights_note,alt_text,"
                                "audio_equivalent,content_hash,created_at,chapter_id,source_revision_id,"
                                "source_revision_hash,data_json,status) VALUES (:id,:run_id,:kind,:purpose,"
                                ":placement,:source,:caption,'PROGRAMMATIC',:rights,:alt,:audio,:hash,"
''',
)
replace_once(
    FINALIZER,
    '''                                "source": f"revision:{head.revision_id}#{head.revision_hash}",
''',
    '''                                "placement": f"paragraph:{placement}",
                                "source": f"revision:{head.revision_id}#{head.revision_hash}",
''',
)

insert_before(
    TEST,
    '''def test_inspected_excerpt_support_is_not_topic_overlap() -> None:\n''',
    r'''def test_visual_table_spec_requires_explicit_numbered_rows_without_truncation() -> None:
    paragraphs = [
        "Вводный абзац.",
        "1. Соберите исходные данные полностью, не обрезая смысл строки.",
        "2. Сравните варианты по одному и тому же критерию.",
        "3. Зафиксируйте решение и условие пересмотра.",
    ]
    spec = AutoBookFinalizer._numbered_step_table_spec(paragraphs)
    assert spec is not None
    assert spec["placement_after_paragraph"] == 4
    assert spec["rows"][0][1].endswith("не обрезая смысл строки.")
    assert "Шаг 3" in spec["audio_equivalent"]


def test_visual_chart_spec_uses_one_context_and_speaks_actual_values() -> None:
    spec = AutoBookFinalizer._percentage_chart_spec(
        [
            "Первый фрагмент содержит 99 процентов, но только одно значение.",
            "Канал А 20%, канал Б 35%, канал В 45% составляют одну выборку.",
        ]
    )
    assert spec is not None
    assert spec["placement_after_paragraph"] == 2
    assert [value for _, value in spec["data"]] == [20.0, 35.0, 45.0]
    assert "20 процентов" in spec["audio_equivalent"]
    assert "35 процентов" in spec["audio_equivalent"]
    assert "45 процентов" in spec["audio_equivalent"]


def test_visual_chart_spec_rejects_unrelated_single_percentages() -> None:
    assert AutoBookFinalizer._percentage_chart_spec(
        ["Один показатель 20 процентов.", "Другой несвязанный показатель 35 процентов."]
    ) is None


''',
)

print("T06 truthful VisualSpec hardening applied")
