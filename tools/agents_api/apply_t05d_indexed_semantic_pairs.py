#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve()


def replace_once(rel: str, old: str, new: str) -> None:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"expected one match in {rel}: {old[:140]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


SIM = "services/local-core/src/book_os_core/series_similarity.py"
TEST = "services/local-core/tests/test_series_semantic_overlap.py"

replace_once(
    SIM,
    '''def _best_marked_pair(\n    left_sample: str,\n    right_sample: str,\n    *,\n    marker: re.Pattern[str],\n    threshold: float,\n) -> tuple[str, str, float] | None:\n    left_values = [value for value in _sentences(left_sample) if marker.search(value)]\n    right_values = [value for value in _sentences(right_sample) if marker.search(value)]\n    best: tuple[str, str, float] | None = None\n    for left in left_values:\n        for right in right_values:\n            score = semantic_score(left, right)\n            if score < threshold:\n                continue\n            shared = semantic_families(left) & semantic_families(right)\n            if len(shared) < 4:\n                continue\n            if best is None or score > best[2]:\n                best = (left, right, score)\n    return best\n''',
    '''def _best_marked_pair(\n    left_sample: str,\n    right_sample: str,\n    *,\n    marker: re.Pattern[str],\n    threshold: float,\n) -> tuple[str, str, float] | None:\n    \"\"\"Find the best marked semantic pair without a full corpus cross-product.\n\n    A material finding already requires at least four shared semantic families. Build an inverted\n    index over those families first, then score only candidate pairs that can satisfy that exact\n    requirement. This preserves the previous decision rule while bounding work on long imports\n    containing hundreds of marked sentences.\n    \"\"\"\n    left_rows: list[tuple[str, set[str], set[str]]] = []\n    right_rows: list[tuple[str, set[str], set[str]]] = []\n    for value in _sentences(left_sample):\n        if not marker.search(value):\n            continue\n        families = semantic_families(value)\n        if len(families) < 4:\n            continue\n        left_rows.append((value, families, semantic_tokens(value)))\n    for value in _sentences(right_sample):\n        if not marker.search(value):\n            continue\n        families = semantic_families(value)\n        if len(families) < 4:\n            continue\n        right_rows.append((value, families, semantic_tokens(value)))\n\n    inverted: dict[str, set[int]] = {}\n    for index, (_, families, _) in enumerate(right_rows):\n        for family in families:\n            inverted.setdefault(family, set()).add(index)\n\n    best: tuple[str, str, float] | None = None\n    for left, left_families, left_tokens in left_rows:\n        counts: dict[int, int] = {}\n        for family in left_families:\n            for index in inverted.get(family, set()):\n                counts[index] = counts.get(index, 0) + 1\n        for index, shared_count in counts.items():\n            if shared_count < 4:\n                continue\n            right, right_families, right_tokens = right_rows[index]\n            score = max(\n                _jaccard(left_tokens, right_tokens),\n                _jaccard(left_families, right_families),\n            )\n            if score < threshold:\n                continue\n            if best is None or score > best[2]:\n                best = (left, right, score)\n    return best\n''',
)

append_test = r'''
def test_marked_pair_index_preserves_full_import_late_match() -> None:
    noise_left = "\n".join(
        f"Пример {index}: локальная история без общего механизма и без повторяемого решения."
        for index in range(250)
    )
    noise_right = "\n".join(
        f"Кейс {index}: отдельная ситуация без общего механизма и без повторяемого решения."
        for index in range(250)
    )
    repeated_left = (
        "Например, сначала оцените спрос и риск, затем соберите доказательства доверия, "
        "сравните цену и примите решение по проверяемым критериям результата."
    )
    repeated_right = (
        "Кейс: сначала проверьте спрос и риск, затем соберите подтверждения доверия, "
        "сопоставьте цену и примите решение по измеримым критериям результата."
    )
    pair = _best_marked_pair(
        noise_left + "\n" + repeated_left,
        noise_right + "\n" + repeated_right,
        marker=_CASE_RE,
        threshold=0.56,
    )
    assert pair is not None
    assert "спрос" in pair[0]
    assert "спрос" in pair[1]
'''

path = ROOT / TEST
text = path.read_text(encoding="utf-8")
if "test_marked_pair_index_preserves_full_import_late_match" in text:
    raise SystemExit("performance regression test already present")
# Private helper imports are intentional here: this is a deterministic algorithm regression test.
text = text.replace(
    "from book_os_core.series_similarity import semantic_series_findings\n",
    "from book_os_core.series_similarity import _CASE_RE, _best_marked_pair, semantic_series_findings\n",
    1,
)
path.write_text(text.rstrip() + "\n\n" + append_test.strip() + "\n", encoding="utf-8")

print("T05d indexed semantic pair matching applied")
