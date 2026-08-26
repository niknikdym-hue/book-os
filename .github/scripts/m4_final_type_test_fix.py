from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"pattern missing in {path}: {old[:120]!r}")
    file.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    "services/local-core/src/book_os_core/research_adapters.py",
    "def _get(self, url: str, *, params: Mapping[str, object]) -> dict[str, Any]:",
    "def _get(\n        self,\n        url: str,\n        *,\n        params: Mapping[str, str | int | float | bool | None],\n    ) -> dict[str, Any]:",
)

replace_once(
    "services/local-core/src/book_os_core/research.py",
    '''class ResearchSearchRequest(BaseModel):\n    query: Annotated[str, Field(min_length=1, max_length=1000)]\n    providers: list[Literal["openalex", "crossref", "semantic_scholar"]] = Field(\n        default_factory=lambda: ["openalex", "crossref", "semantic_scholar"]\n    )\n''',
    '''def _default_research_providers() -> list[\n    Literal["openalex", "crossref", "semantic_scholar"]\n]:\n    return ["openalex", "crossref", "semantic_scholar"]\n\n\nclass ResearchSearchRequest(BaseModel):\n    query: Annotated[str, Field(min_length=1, max_length=1000)]\n    providers: list[Literal["openalex", "crossref", "semantic_scholar"]] = Field(\n        default_factory=_default_research_providers\n    )\n''',
)

replace_once(
    "apps/desktop/src/ResearchPanel.test.tsx",
    '  expect(screen.getByText(/SUPPORTS · Section 2 · ACTIVE/)).toBeInTheDocument();',
    '''  const supportLabel = screen\n    .getAllByText("SUPPORTS")\n    .find((element) => element.tagName === "STRONG");\n  expect(supportLabel?.parentElement).toHaveTextContent("SUPPORTS · Section 2 · ACTIVE");''',
)
