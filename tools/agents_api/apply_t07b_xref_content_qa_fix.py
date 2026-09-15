#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve()
PATH = ROOT / "services/local-core/src/book_os_core/auto_book_exports.py"
text = PATH.read_text(encoding="utf-8")
old = '        value = re.sub(r"\\[([^\\]]+)\\]\\(#([^)]+)\\)", r"\\1 (см. \\2)", value)\n'
new = '        value = re.sub(r"\\[([^\\]]+)\\]\\(#([^)]+)\\)", r"\\1", value)\n'
if text.count(old) != 1:
    raise SystemExit(f"expected one plain-inline cross-reference QA anchor, found {text.count(old)}")
PATH.write_text(text.replace(old, new, 1), encoding="utf-8")
print("T07b cross-reference visible-text QA corrected")
