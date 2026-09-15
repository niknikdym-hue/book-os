#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve()
PATH = ROOT / "services/local-core/src/book_os_core/auto_book_exports.py"
text = PATH.read_text(encoding="utf-8")
old_head = '''    def _pdf(self, master: StructuredBookMaster, output: Path, visual_dir: Path) -> dict[str, Any]:\n        self._validate_footnote_references(master, self._footnote_definitions(master))\n'''
new_head = '''    def _pdf(self, master: StructuredBookMaster, output: Path, visual_dir: Path) -> dict[str, Any]:\n        footnote_definitions = self._footnote_definitions(master)\n        self._validate_footnote_references(master, footnote_definitions)\n'''
if text.count(old_head) != 1:
    raise SystemExit(f"expected one PDF footnote-definition anchor, found {text.count(old_head)}")
text = text.replace(old_head, new_head, 1)
old_qa = '''        extracted_text = " ".join(\n            " ".join((page.extract_text() or "").split()) for page in reader.pages\n        )\n        required_fragments = [master.title, *(chapter.title for chapter in master.chapters)]\n'''
new_qa = '''        extracted_text = " ".join(\n            " ".join((page.extract_text() or "").split()) for page in reader.pages\n        )\n        for note_id in footnote_definitions:\n            extracted_text = extracted_text.replace(f"[{note_id}]", note_id)\n        required_fragments = [master.title, *(chapter.title for chapter in master.chapters)]\n'''
if text.count(old_qa) != 1:
    raise SystemExit(f"expected one PDF extracted-text QA anchor, found {text.count(old_qa)}")
PATH.write_text(text.replace(old_qa, new_qa, 1), encoding="utf-8")
print("T07b PDF footnote marker QA normalized")
