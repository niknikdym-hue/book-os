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
    if text.count(marker) != 1:
        raise SystemExit(f"expected exactly one marker in {rel}: {marker[:120]!r}")
    path.write_text(text.replace(marker, addition + marker, 1), encoding="utf-8")


FINALIZER = "services/local-core/src/book_os_core/auto_book_finalizer.py"
FINALIZER_TEST = "services/local-core/tests/test_auto_book_finalizer.py"

# F05: parse structural locators rather than treating everything after the first colon as chapter id.
insert_before(
    FINALIZER,
    '''    def _targeted_correction(\n''',
    '''    @staticmethod\n    def _correction_chapter_scope(findings: list[dict[str, Any]]) -> set[str] | None:\n        chapter_ids: set[str] = set()\n        book_scope = False\n        for item in findings:\n            location = str(item.get("location", "")).strip()\n            if not location:\n                raise AutoBookGateError("correction finding has no resolvable location")\n            if location == "BOOK" or location.casefold().startswith("book:"):\n                book_scope = True\n                continue\n            parts = [part.strip() for part in location.split(":")]\n            if len(parts) >= 2 and parts[0].casefold() == "chapter" and parts[1]:\n                if len(parts) > 2:\n                    tail = parts[2:]\n                    if len(tail) % 2 != 0:\n                        raise AutoBookGateError(\n                            f"correction locator is malformed: {location}"\n                        )\n                    allowed = {"paragraph", "unit", "span"}\n                    if any(tail[index].casefold() not in allowed for index in range(0, len(tail), 2)):\n                        raise AutoBookGateError(\n                            f"correction locator is unsupported: {location}"\n                        )\n                    if any(not tail[index] for index in range(1, len(tail), 2)):\n                        raise AutoBookGateError(\n                            f"correction locator is incomplete: {location}"\n                        )\n                chapter_ids.add(parts[1])\n                continue\n            raise AutoBookGateError(f"correction locator is unresolved: {location}")\n        if book_scope:\n            return None\n        if not chapter_ids:\n            raise AutoBookGateError("correction findings resolve to no chapter or BOOK target")\n        return chapter_ids\n\n''',
)

replace_once(
    FINALIZER,
    '''        chapter_ids = {\n            value.split(":", 1)[1]\n            for item in findings\n            if (value := str(item.get("location", ""))).startswith("chapter:")\n        }\n        targets = [\n            unit for unit in units if not chapter_ids or str(unit.get("chapter_id")) in chapter_ids\n        ]\n''',
    '''        chapter_ids = self._correction_chapter_scope(findings)\n        targets = [\n            unit\n            for unit in units\n            if chapter_ids is None or str(unit.get("chapter_id")) in chapter_ids\n        ]\n        if not targets:\n            requested = "BOOK" if chapter_ids is None else ", ".join(sorted(chapter_ids))\n            raise AutoBookGateError(\n                f"correction findings resolved to no current manuscript units: {requested}"\n            )\n''',
)

replace_once(
    FINALIZER,
    '''            relevant = [\n                item\n                for item in findings\n                if not chapter_ids\n                or str(item.get("location", "")) in {f"chapter:{unit.get('chapter_id')}", "BOOK"}\n            ]\n''',
    '''            relevant = [\n                item\n                for item in findings\n                if chapter_ids is None\n                or str(item.get("location", "")).strip().startswith(\n                    f"chapter:{unit.get('chapter_id')}"\n                )\n            ]\n''',
)

# A locked unit may be skipped during an ordinary idempotent final-edit pass, but a correction may
# never silently claim success against locked text.
replace_once(
    FINALIZER,
    '''            head = authority.get_head(entity_id)\n            if head.status == "LOCKED":\n                return\n''',
    '''            head = authority.get_head(entity_id)\n            if head.status == "LOCKED":\n                if correction_findings:\n                    raise AutoBookGateError(\n                        f"manuscript unit {unit['unit_id']} is LOCKED; correction requires a new authorized revision"\n                    )\n                return\n''',
)

# Locator regressions are deterministic and provider-free.
insert_before(
    FINALIZER_TEST,
    '''def test_inspected_excerpt_support_is_not_topic_overlap() -> None:\n''',
    '''def test_nested_correction_locator_targets_its_chapter() -> None:\n    assert AutoBookFinalizer._correction_chapter_scope(\n        [{"location": "chapter:c1:paragraph:3"}]\n    ) == {"c1"}\n    assert AutoBookFinalizer._correction_chapter_scope(\n        [{"location": "chapter:c1:unit:u2:span:4-9"}]\n    ) == {"c1"}\n\n\ndef test_book_correction_locator_selects_whole_book() -> None:\n    assert AutoBookFinalizer._correction_chapter_scope(\n        [{"location": "BOOK"}]\n    ) is None\n\n\ndef test_malformed_or_unresolved_correction_locator_fails_closed() -> None:\n    with pytest.raises(Exception, match="malformed|unresolved|incomplete"):\n        AutoBookFinalizer._correction_chapter_scope(\n            [{"location": "chapter:c1:paragraph"}]\n        )\n    with pytest.raises(Exception, match="unresolved"):\n        AutoBookFinalizer._correction_chapter_scope(\n            [{"location": "candidate:1"}]\n        )\n\n\n''',
)

print("T03 change-admission/locator hardening applied")
