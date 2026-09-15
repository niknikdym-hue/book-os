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

replace_once(
    FINALIZER,
    r'''    @staticmethod
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
    r'''    @staticmethod
    def _percentage_chart_spec(paragraphs: list[str]) -> dict[str, Any] | None:
        comparable_context = re.compile(
            r"\b(?:одн(?:ой|ого)\s+(?:выборк\w*|групп\w*|совокупност\w*|когорт\w*)|"
            r"общ(?:ая|ей|его)\s+(?:выборк\w*|групп\w*|совокупност\w*)|"
            r"составляют\s+одн\w+\s+(?:выборк\w*|групп\w*|совокупност\w*)|"
            r"распределени\w*|структур\w*\s+(?:выборк\w*|групп\w*|совокупност\w*)|"
            r"из\s+\d+\s+(?:наблюден\w*|случа\w*|ответ\w*|покупател\w*|участник\w*))\b",
            re.IGNORECASE,
        )
        for paragraph_index, paragraph in enumerate(paragraphs, start=1):
            if comparable_context.search(paragraph) is None:
                continue
            points: list[tuple[str, float]] = []
            for match in re.finditer(
                r"([^.!?;:\n]{2,80}?)\s+(\d+(?:[.,]\d+)?)\s*%",
                paragraph,
            ):
                label = " ".join(match.group(1).split()).strip(" ,;:-")
                if not label:
                    continue
                value = float(match.group(2).replace(",", "."))
                if 0 <= value <= 100:
                    points.append((label, value))
            unique = {label.casefold() for label, _ in points}
            if len(points) < 2 or len(unique) != len(points):
                continue
            context = " ".join(paragraph.split())
            spoken = "; ".join(f"{label} — {value:g} процентов" for label, value in points)
            return {
                "data": points,
                "unit": "%",
                "conditions": context,
                "source_paragraph": paragraph_index,
                "placement_after_paragraph": paragraph_index,
                "purpose": "Сравнить процентные значения с явно указанной общей базой сравнения",
                "caption": "Сравнение процентных значений",
                "alt_text": f"Диаграмма сравнивает значения на общей базе: {spoken}.",
                "audio_equivalent": (
                    f"Диаграмма использует одну явно указанную базу сравнения. {spoken}."
                ),
            }
        return None

''',
)

insert_before(
    FINALIZER,
    '''    def _execute_visual_policy(\n''',
    r'''    @staticmethod
    def _visual_source_is_current(
        row: dict[str, Any], current_revisions: set[tuple[str, str]]
    ) -> bool:
        revision_id = str(row.get("source_revision_id") or "")
        revision_hash = str(row.get("source_revision_hash") or "")
        return bool(revision_id and revision_hash and (revision_id, revision_hash) in current_revisions)

''',
)

replace_once(
    FINALIZER,
    '''    def _visual_asset_rows(
        self, book_id: str, *, state_run_id: str | None, chapter_id: str
    ) -> list[dict[str, Any]]:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                rows = list(
                    connection.execute(
                        text(
                            "SELECT v.* FROM auto_book_visual_assets v "
                            "WHERE v.chapter_id=:chapter_id AND v.status='READY' "
                            + ("AND v.run_id=:run_id " if state_run_id else "")
                            + "ORDER BY v.created_at,v.asset_id"
                        ),
                        {"chapter_id": chapter_id, "run_id": state_run_id},
                    ).mappings()
                )
        finally:
            engine.dispose()
        return [{**dict(row), "data": json.loads(str(row["data_json"]))} for row in rows]
''',
    '''    def _visual_asset_rows(
        self, book_id: str, *, state_run_id: str | None, chapter_id: str
    ) -> list[dict[str, Any]]:
        relevant_units = [
            item for item in self._current_units(book_id) if str(item["chapter_id"]) == chapter_id
        ]
        engine = self._engine(book_id)
        authority = AuthorityService(engine)
        current_revisions: set[tuple[str, str]] = set()
        try:
            for unit in relevant_units:
                head = authority.get_head(str(unit["authority_entity_id"]))
                current_revisions.add((head.revision_id, head.revision_hash))
            with engine.begin() as connection:
                rows = list(
                    connection.execute(
                        text(
                            "SELECT v.* FROM auto_book_visual_assets v "
                            "WHERE v.chapter_id=:chapter_id AND v.status='READY' "
                            + ("AND v.run_id=:run_id " if state_run_id else "")
                            + "ORDER BY v.created_at,v.asset_id"
                        ),
                        {"chapter_id": chapter_id, "run_id": state_run_id},
                    ).mappings()
                )
                current_rows: list[dict[str, Any]] = []
                for raw in rows:
                    row = dict(raw)
                    if not self._visual_source_is_current(row, current_revisions):
                        connection.execute(
                            text(
                                "UPDATE auto_book_visual_assets SET status='STALE' "
                                "WHERE asset_id=:asset_id AND status='READY'"
                            ),
                            {"asset_id": str(row["asset_id"])},
                        )
                        continue
                    current_rows.append(row)
        finally:
            engine.dispose()
        return [
            {**row, "data": json.loads(str(row["data_json"]))} for row in current_rows
        ]
''',
)

replace_once(
    FINALIZER,
    '''                visual_required = any(token in requirements for token in ("график", "диаграм", "схем"))
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
''',
    '''                chart_required = any(token in requirements for token in ("график", "диаграм"))
                scheme_required = "схем" in requirements
                illustration_required = any(
                    token in requirements for token in ("иллюстрац", "рисунок", "изображен")
                )
                wants_table = table_required or "таблиц" in manuscript_lower
                wants_chart = chart_required or any(
                    token in manuscript_lower for token in ("график", "диаграм")
                )
                paragraphs = [p.strip() for p in manuscript.split("\n\n") if p.strip()]
                assets: list[tuple[str, dict[str, Any], str, str, str, int, str]] = []
                unresolved: list[str] = []
                unavailable_optional: list[str] = []

                if wants_table:
                    table_spec = self._numbered_step_table_spec(paragraphs)
                    if table_spec is None:
                        if table_required:
                            unresolved.append("TABLE: no explicit structured rows in the exact source")
                    else:
                        data = {
                            "spec_version": "visual-spec.v1",
                            "type": "TABLE",
                            "headers": table_spec["headers"],
                            "rows": table_spec["rows"],
                            "unit": None,
                            "conditions": "Rows are copied from explicit numbered steps in exact source.",
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

                if wants_chart:
                    chart_spec = self._percentage_chart_spec(paragraphs)
                    if chart_spec is None:
                        if chart_required:
                            unresolved.append(
                                "CHART: percentages lack an explicit common denominator/comparable context"
                            )
                    else:
                        data = {
                            "spec_version": "visual-spec.v1",
                            "type": "CHART",
                            "data": chart_spec["data"],
                            "unit": chart_spec["unit"],
                            "conditions": chart_spec["conditions"],
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

                if scheme_required:
                    unresolved.append(
                        "SCHEME: programmatic scheme route is not trustworthy enough for READY"
                    )
                if illustration_required:
                    unresolved.append(
                        "ILLUSTRATION: no reviewed owner-supplied/programmatic illustration spec exists"
                    )
                elif policy.include_optional_illustrations and "иллюстрац" in manuscript_lower:
                    unavailable_optional.append("ILLUSTRATION")

                if unresolved:
                    raise AutoBookGateError(
                        "required visual material has no truthful VisualSpec: " + "; ".join(unresolved)
                    )

                for kind, data, caption, audio, purpose, placement, alt_text in assets:
''',
)

replace_once(
    FINALIZER,
    '''                                "kind": kind,
                                "data": data,
                                "placement_after_paragraph": placement,
                                "revision_hash": head.revision_hash,
''',
    '''                                "kind": kind,
                                "data": data,
                                "placement_after_paragraph": placement,
                                "revision_id": head.revision_id,
                                "revision_hash": head.revision_hash,
''',
)

replace_once(
    FINALIZER,
    '''                                "source": f"revision:{head.revision_id}#{head.revision_hash}",
''',
    '''                                "source": (
                                    f"revision:{head.revision_id}#{head.revision_hash}:"
                                    f"paragraph:{placement}"
                                ),
''',
)

replace_once(
    FINALIZER,
    '''        return {"policy": policy.model_dump(mode="json"), "created": sorted(set(created))}
''',
    '''        return {
            "policy": policy.model_dump(mode="json"),
            "created": sorted(set(created)),
            "capabilities": {
                "programmatic_tables": True,
                "programmatic_charts": True,
                "programmatic_schemes": False,
                "generative_illustrations": False,
            },
            "unavailable_optional": sorted(set(unavailable_optional)),
        }
''',
)

insert_before(
    TEST,
    '''def test_inspected_excerpt_support_is_not_topic_overlap() -> None:\n''',
    r'''def test_visual_chart_spec_rejects_same_paragraph_without_common_denominator() -> None:
    assert AutoBookFinalizer._percentage_chart_spec(
        ["Конверсия сайта 20%, а доля возвратов среди уже оплативших покупателей 35%."]
    ) is None


def test_visual_source_guard_rejects_stale_revision() -> None:
    row = {
        "source_revision_id": "01JOLDREVISION000000000000",
        "source_revision_hash": "a" * 64,
    }
    assert not AutoBookFinalizer._visual_source_is_current(
        row,
        {("01JCURRENTREVISION000000000", "b" * 64)},
    )
    assert AutoBookFinalizer._visual_source_is_current(
        row,
        {("01JOLDREVISION000000000000", "a" * 64)},
    )


''',
)

replace_once(
    TEST,
    '''    assert {"TABLE", "SCHEME"} <= visual_kinds
    visual_files = list((tmp_path / "projects" / book_id / "exports").rglob("*.png"))
    assert visual_files
    assert all(path.read_bytes().startswith(b"\\x89PNG") for path in visual_files)
''',
    '''    # Incidental prose mentions of a table/scheme must not manufacture READY visuals.
    assert visual_kinds == set()
    visual_files = list((tmp_path / "projects" / book_id / "exports").rglob("*.png"))
    assert not visual_files
''',
)

print("T06b truthful visual semantics and source binding applied")
