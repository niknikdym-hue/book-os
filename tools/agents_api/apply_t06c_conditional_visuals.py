#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve()
FINALIZER = ROOT / "services/local-core/src/book_os_core/auto_book_finalizer.py"
TEST = ROOT / "services/local-core/tests/test_auto_book_finalizer.py"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"expected one match in {path}: {old[:120]!r} count={text.count(old)}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def insert_before(path: Path, marker: str, block: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(marker) != 1:
        raise SystemExit(f"expected one marker in {path}: {marker[:120]!r}")
    path.write_text(text.replace(marker, block + marker, 1), encoding="utf-8")


insert_before(
    FINALIZER,
    "    @staticmethod\n    def _numbered_step_table_spec",
    '''    @staticmethod
    def _visual_requirement_is_mandatory(
        requirements: str, stems: tuple[str, ...]
    ) -> bool:
        """Interpret conditional visual wording without turning every mention into a hard gate."""
        soft_markers = (
            "там, где",
            "там где",
            "если ",
            "при необходимости",
            "по необходимости",
            "когда это помогает",
            "где это помогает",
            "при наличии",
            "если это помогает",
        )
        strong_markers = (
            "обязатель",
            "требуется",
            "требуют",
            "должен",
            "должна",
            "должно",
            "должны",
            "необходим",
        )
        for segment in re.split(r"[.;\\n]+", requirements.casefold()):
            segment = " ".join(segment.split())
            if not segment or not any(stem in segment for stem in stems):
                continue
            if any(marker in segment for marker in strong_markers):
                return True
            if any(marker in segment for marker in soft_markers):
                continue
            # `required_scenes_examples` is a required contract field: an unqualified visual
            # mention is mandatory, while explicitly conditional wording is not.
            return True
        return False

''',
)

old_flags = '''                table_required = "таблиц" in requirements
                chart_required = any(token in requirements for token in ("график", "диаграм"))
                scheme_required = "схем" in requirements
                illustration_required = any(
                    token in requirements for token in ("иллюстрац", "рисунок", "изображен")
                )
                wants_table = table_required or "таблиц" in manuscript_lower
                wants_chart = chart_required or any(
                    token in manuscript_lower for token in ("график", "диаграм")
                )
'''
new_flags = '''                table_requested = "таблиц" in requirements or "таблиц" in manuscript_lower
                chart_requested = any(
                    token in requirements or token in manuscript_lower
                    for token in ("график", "диаграм")
                )
                scheme_requested = "схем" in requirements or "схем" in manuscript_lower
                illustration_requested = any(
                    token in requirements or token in manuscript_lower
                    for token in ("иллюстрац", "рисунок", "изображен")
                )
                table_required = self._visual_requirement_is_mandatory(
                    requirements, ("таблиц",)
                )
                chart_required = self._visual_requirement_is_mandatory(
                    requirements, ("график", "диаграм")
                )
                scheme_required = self._visual_requirement_is_mandatory(
                    requirements, ("схем",)
                )
                illustration_required = self._visual_requirement_is_mandatory(
                    requirements, ("иллюстрац", "рисунок", "изображен")
                )
                wants_table = table_requested
                wants_chart = chart_requested
'''
replace_once(FINALIZER, old_flags, new_flags)

replace_once(
    FINALIZER,
    '''                    if table_spec is None:
                        if table_required:
                            unresolved.append("TABLE: no explicit structured rows in the exact source")
''',
    '''                    if table_spec is None:
                        if table_required:
                            unresolved.append("TABLE: no explicit structured rows in the exact source")
                        elif table_requested:
                            unavailable_optional.append("TABLE")
''',
)
replace_once(
    FINALIZER,
    '''                    if chart_spec is None:
                        if chart_required:
                            unresolved.append(
                                "CHART: percentages lack an explicit common denominator/comparable context"
                            )
''',
    '''                    if chart_spec is None:
                        if chart_required:
                            unresolved.append(
                                "CHART: percentages lack an explicit common denominator/comparable context"
                            )
                        elif chart_requested:
                            unavailable_optional.append("CHART")
''',
)
replace_once(
    FINALIZER,
    '''                if scheme_required:
                    unresolved.append(
                        "SCHEME: programmatic scheme route is not trustworthy enough for READY"
                    )
                if illustration_required:
                    unresolved.append(
                        "ILLUSTRATION: no reviewed owner-supplied/programmatic illustration spec exists"
                    )
                elif policy.include_optional_illustrations and "иллюстрац" in manuscript_lower:
                    unavailable_optional.append("ILLUSTRATION")
''',
    '''                if scheme_required:
                    unresolved.append(
                        "SCHEME: programmatic scheme route is not trustworthy enough for READY"
                    )
                elif scheme_requested:
                    unavailable_optional.append("SCHEME")
                if illustration_required:
                    unresolved.append(
                        "ILLUSTRATION: no reviewed owner-supplied/programmatic illustration spec exists"
                    )
                elif illustration_requested or policy.include_optional_illustrations:
                    unavailable_optional.append("ILLUSTRATION")
''',
)

insert_before(
    TEST,
    "def test_visual_chart_spec_rejects_same_paragraph_without_common_denominator() -> None:\n",
    '''def test_conditional_visual_wording_is_not_a_hard_release_gate() -> None:
    requirements = "Таблица шагов и схема механизма там, где они помогают пониманию"
    assert not AutoBookFinalizer._visual_requirement_is_mandatory(requirements, ("таблиц",))
    assert not AutoBookFinalizer._visual_requirement_is_mandatory(requirements, ("схем",))


def test_explicit_visual_wording_remains_a_hard_release_gate() -> None:
    assert AutoBookFinalizer._visual_requirement_is_mandatory(
        "Обязательна таблица сравнения вариантов", ("таблиц",)
    )
    assert AutoBookFinalizer._visual_requirement_is_mandatory(
        "Требуется схема причинного механизма", ("схем",)
    )


''',
)

print("T06c conditional visual requirement semantics applied")
