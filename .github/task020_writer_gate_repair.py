from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one match, got {count}: {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


drafting = Path("services/local-core/src/book_os_core/drafting.py")
replace_once(
    drafting,
    "from .prompts import SECTION_DRAFT_V1\n",
    "from .prompts import SECTION_DRAFT_V1\nfrom .series_production import SeriesProductionService\n",
)
replace_once(
    drafting,
    "        self._routing = ModelRoutingService(data_dir)\n        self._contexts = BookContextService(data_dir)\n",
    "        self._routing = ModelRoutingService(data_dir)\n        self._contexts = BookContextService(data_dir)\n        self._production = SeriesProductionService(data_dir)\n",
)
replace_once(
    drafting,
    "        try:\n            choice = self._resolve_choice(book_id, request)\n",
    "        try:\n            admission = self._production.admission_status(book_id, chapter_id)\n            if not admission.writing_allowed:\n                raise DraftingGateError(\n                    \"WRITING_NOT_ALLOWED: \" + \"; \".join(admission.blockers)\n                )\n            choice = self._resolve_choice(book_id, request)\n",
)

tests = Path("services/local-core/tests/test_drafting.py")
marker = "    return service, project.book_id, chapter_id\n\n\ndef test_fake_success_creates_draft_with_exact_provenance"
inserted = '''    return service, project.book_id, chapter_id


def test_writer_requires_task017_admission_before_adapter_or_task_creation(tmp_path: Path) -> None:
    projects = ProjectService(tmp_path)
    project = projects.create_project(
        NewBookRequest(working_title="Admission Gate Test", primary_subtype="Strategy")
    )
    projects.save_book_contract(project.book_id, book_contract())
    projects.approve_book_contract(project.book_id)
    projects.save_architecture(project.book_id, architecture())
    project = projects.approve_architecture(project.book_id)
    chapter_id = project.chapters[0].chapter_id
    projects.save_chapter_contract(project.book_id, chapter_id, chapter_contract())
    projects.approve_chapter_contract(project.book_id, chapter_id)

    fake = DeterministicFakeAdapter()
    drafting = DraftingService(tmp_path, ModelGateway({"fake": fake}))
    with pytest.raises(DraftingGateError, match="WRITING_NOT_ALLOWED"):
        drafting.generate_section_draft(
            project.book_id,
            chapter_id,
            DraftSectionRequest(
                section_objective="Must be blocked before adapter",
                provider="fake",
                model="fake-writer",
            ),
        )

    assert fake.last_request is None
    engine = create_database(tmp_path / "projects" / project.book_id / "project.sqlite")
    with engine.connect() as connection:
        assert connection.execute(text("SELECT COUNT(*) FROM bounded_tasks")).scalar_one() == 0
        assert connection.execute(text("SELECT COUNT(*) FROM model_runs")).scalar_one() == 0
    engine.dispose()


def test_fake_success_creates_draft_with_exact_provenance'''
replace_once(tests, marker, inserted)
