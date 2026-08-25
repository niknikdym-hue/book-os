from pathlib import Path


def replace_schema_assertions() -> None:
    path = Path("services/local-core/tests/test_authority.py")
    text = path.read_text()
    old = '== "0002"'
    count = text.count(old)
    if count not in {0, 1}:
        raise SystemExit(f"unexpected old-schema assertion count: {count}")
    if count == 1:
        path.write_text(text.replace(old, '== "0003"'))


def fix_architecture_authority_source() -> None:
    path = Path("services/local-core/src/book_os_core/projects.py")
    text = path.read_text()
    old_line = "        architecture = BookArchitecturePayload.model_validate(project.architecture.content)"
    new_line = (
        "        architecture = BookArchitecturePayload.model_validate(\n"
        "            self._authority_content(book_id, project.architecture)\n"
        "        )"
    )
    if old_line in text:
        text = text.replace(old_line, new_line, 1)

    method_marker = (
        "    def _authority_content(self, book_id: str, document: DocumentView) -> dict[str, Any]:\n"
    )
    if method_marker not in text:
        insertion = '''    def _authority_content(self, book_id: str, document: DocumentView) -> dict[str, Any]:
        engine = self._engine(book_id)
        try:
            revision = AuthorityService(engine).get_revision(document.authority_revision_id)
            return cast(dict[str, Any], revision["content"])
        finally:
            engine.dispose()

'''
        anchor = "    def _save_project_document(\n"
        if anchor not in text:
            raise SystemExit("project service insertion anchor missing")
        text = text.replace(anchor, insertion + anchor, 1)
    path.write_text(text)


def expose_working_status_in_ui() -> None:
    path = Path("apps/desktop/src/App.tsx")
    text = path.read_text()
    replacements = {
        "status={project.book_contract?.authority_status}": "status={project.book_contract?.status}",
        "status={project.architecture?.authority_status}": "status={project.architecture?.status}",
        "status={selectedChapter?.chapter_contract?.authority_status}": "status={selectedChapter?.chapter_contract?.status}",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    path.write_text(text)


replace_schema_assertions()
fix_architecture_authority_source()
expose_working_status_in_ui()
