from pathlib import Path

path = Path("services/local-core/src/book_os_core/memory.py")
text = path.read_text(encoding="utf-8")
old = '''        for row in chapters:\n            entity_id = cast(str | None, row["chapter_contract_entity_id"])\n            if not entity_id:\n                continue\n            head = authority.get_head(entity_id)\n            revision = authority.get_revision(head.revision_id)\n            payload = cast(dict[str, Any], revision["content"])\n            documents.append(\n                _CanonicalDocument(\n                    object_kind="CHAPTER_CONTRACT",\n                    object_id=entity_id,\n'''
new = '''        for row in chapters:\n            chapter_contract_entity_id = cast(str | None, row["chapter_contract_entity_id"])\n            if not chapter_contract_entity_id:\n                continue\n            head = authority.get_head(chapter_contract_entity_id)\n            revision = authority.get_revision(head.revision_id)\n            payload = cast(dict[str, Any], revision["content"])\n            documents.append(\n                _CanonicalDocument(\n                    object_kind="CHAPTER_CONTRACT",\n                    object_id=chapter_contract_entity_id,\n'''
if old not in text:
    raise SystemExit("Chapter Contract memory block not found")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
