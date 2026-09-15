#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
path = root / "services/local-core/tests/test_auto_book_exports.py"
text = path.read_text(encoding="utf-8")
old_import = "from docx import Document\n"
new_import = "from docx import Document\nimport ebooklib  # type: ignore[import-untyped]\nfrom ebooklib import epub\n"
if text.count(old_import) != 1:
    raise SystemExit("expected one docx import")
text = text.replace(old_import, new_import, 1)
old = '''    runtime = _runtime(tmp_path)\n    exporter = AutoBookExporter(tmp_path, runtime)\n'''
new = '''    exporter = AutoBookExporter(tmp_path, DurableAutoBookRuntime(tmp_path))\n'''
if text.count(old) != 1:
    raise SystemExit("expected one generated _runtime fixture use")
text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("T07 export test fixture corrected")
