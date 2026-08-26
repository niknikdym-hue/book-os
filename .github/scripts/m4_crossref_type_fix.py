from pathlib import Path

path = Path("services/local-core/src/book_os_core/research_adapters.py")
text = path.read_text(encoding="utf-8")
old = "        params: dict[str, object] = {\n"
new = "        params: dict[str, str | int | float | bool | None] = {\n"
if old not in text:
    raise SystemExit("Crossref params annotation not found")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
