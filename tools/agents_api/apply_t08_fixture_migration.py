#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
exports = root / "services/local-core/tests/test_auto_book_exports.py"
finalizer = root / "services/local-core/tests/test_auto_book_finalizer.py"


def replace_exact(path: Path, old: str, new: str, expected: int, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected:
        raise SystemExit(f"{label}: expected {expected} matches, found {count}")
    path.write_text(text.replace(old, new), encoding="utf-8")


replace_exact(
    exports,
    "from book_os_core.audio_script import AudioScriptService\n",
    "from book_os_core.audio_attention import attention_finding_key\n"
    "from book_os_core.audio_script import AudioScriptService\n",
    1,
    "export tests exact-attention import",
)
replace_exact(
    exports,
    '''                        audio_equivalent=(\n                            "График на условных данных показывает последовательный рост "\n                            "показателя от 1 до 3; для записи числа нужно произнести словами."\n                        ),\n''',
    '''                        audio_equivalent=(\n                            "График на условных данных показывает три значения: 1, 2 и 3; "\n                            "показатель последовательно растёт от первого значения к третьему."\n                        ),\n''',
    1,
    "visual fixture must narrate every small-chart value",
)
old_attention = '''attention = sorted(\n        {\n            finding.code\n            for check in proposed.quality_checks\n            for finding in check.findings\n            if finding.severity == "ATTENTION"\n        }\n    )'''
new_attention = '''attention = sorted(\n        attention_finding_key(finding)\n        for check in proposed.quality_checks\n        for finding in check.findings\n        if finding.severity == "ATTENTION"\n    )'''
replace_exact(
    exports,
    old_attention,
    new_attention,
    1,
    "top-level export fixture exact findings",
)
old_nested_attention = '''attention = sorted(\n            {\n                finding.code\n                for check in proposed.quality_checks\n                for finding in check.findings\n                if finding.severity == "ATTENTION"\n            }\n        )'''
new_nested_attention = '''attention = sorted(\n            attention_finding_key(finding)\n            for check in proposed.quality_checks\n            for finding in check.findings\n            if finding.severity == "ATTENTION"\n        )'''
replace_exact(
    exports,
    old_nested_attention,
    new_nested_attention,
    1,
    "nested export fixture exact findings",
)

replace_exact(
    finalizer,
    "from book_os_core.audio_script import AudioScriptService\n",
    "from book_os_core.audio_attention import attention_finding_key\n"
    "from book_os_core.audio_script import AudioScriptService\n",
    1,
    "finalizer test exact-attention import",
)
replace_exact(
    finalizer,
    old_attention,
    new_attention,
    1,
    "finalizer exact findings",
)

print("T08 legacy fixtures migrated to exact findings and complete visual narration")
