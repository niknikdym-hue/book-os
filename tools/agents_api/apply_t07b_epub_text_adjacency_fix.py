#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve()
PATH = ROOT / "services/local-core/src/book_os_core/auto_book_exports.py"
text = PATH.read_text(encoding="utf-8")
old = '''        semantic_text_parts: list[str] = []\n        for item in document_items:\n            try:\n                root = ET.fromstring(item.get_content())\n            except ET.ParseError as exc:\n                raise AutoBookExportError("EPUB semantic QA could not parse a document") from exc\n            semantic_text_parts.extend(root.itertext())\n        semantic_plain_text = " ".join(" ".join(semantic_text_parts).split())\n'''
new = '''        semantic_documents: list[str] = []\n        for item in document_items:\n            try:\n                root = ET.fromstring(item.get_content())\n            except ET.ParseError as exc:\n                raise AutoBookExportError("EPUB semantic QA could not parse a document") from exc\n            semantic_documents.append("".join(root.itertext()))\n        semantic_plain_text = " ".join(" ".join(semantic_documents).split())\n'''
if text.count(old) != 1:
    raise SystemExit(f"expected one EPUB semantic itertext block, found {text.count(old)}")
PATH.write_text(text.replace(old, new, 1), encoding="utf-8")
print("T07b EPUB inline text adjacency preserved in QA")
