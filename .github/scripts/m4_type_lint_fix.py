from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"pattern missing in {path}: {old!r}")
    file.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    "services/local-core/src/book_os_core/research.py",
    "from typing import Annotated, Any, Literal, cast",
    "from typing import Annotated, Literal, cast",
)
replace_once(
    "apps/desktop/src/ResearchPanel.test.tsx",
    'const api: ResearchApi = async function api<T>(method, path, body): Promise<T> {',
    '''const api: ResearchApi = async function api<T>(\n  method: "GET" | "POST" | "PUT",\n  path: string,\n  body?: unknown,\n): Promise<T> {''',
)
