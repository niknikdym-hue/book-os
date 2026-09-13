from pathlib import Path
from zipfile import ZipFile

from docx import Document

from book_os_core.auto_book_exports import (
    AutoBookExporter,
    MasterChapter,
    MasterTable,
    MasterVisual,
    StructuredBookMaster,
)
from book_os_core.auto_book_runtime import (
    AutoBookIntent,
    AutoBookOutputSelection,
    DurableAutoBookRuntime,
)
from book_os_core.projects import NewBookRequest, ProjectService


def setup_run(tmp_path: Path, outputs: AutoBookOutputSelection) -> tuple[str, str]:
    book_id = (
        ProjectService(tmp_path)
        .create_project(NewBookRequest(working_title="Fixture export", primary_subtype="Strategy"))
        .book_id
    )
    run = DurableAutoBookRuntime(tmp_path).create_run(
        book_id,
        AutoBookIntent(
            idea="Проверить один master и независимые производные результаты.",
            author_name="Елена Дым",
            outputs=outputs,
            max_total_cost_usd=5,
            max_cost_usd_per_request=1,
            max_requests=10,
        ),
    )
    return book_id, run.run_id


def fixture_master(*, suffix: str = "") -> StructuredBookMaster:
    tables = [
        MasterTable(
            object_id=f"table-{index}",
            title=f"Таблица {index}",
            headers=["Шаг", "Результат"],
            rows=[["Проверить", f"Получить результат {index}"]],
            audio_equivalent=(
                f"Таблица {index} показывает: сначала нужно проверить условие, "
                f"после чего получить результат {index}."
            ),
        )
        for index in range(1, 17)
    ]
    return StructuredBookMaster(
        title=f"Проверяемая книга{suffix}",
        author="Елена Дым",
        chapters=[
            MasterChapter(
                chapter_id="chapter-1",
                title="Глава 1. Решение",
                paragraphs=[
                    "Сильный практический текст объясняет механизм, границы и следующий шаг.",
                    "Каждый смысловой объект сохраняется во всех подходящих форматах.",
                ],
                tables=tables,
                visuals=[
                    MasterVisual(
                        object_id="chart-1",
                        kind="CHART",
                        title="Динамика результата",
                        caption="Рисунок 1. Условные данные для проверки экспорта.",
                        alt_text="Три столбца растут от одного до трёх.",
                        audio_equivalent=(
                            "График на условных данных показывает последовательный рост "
                            "показателя от одного до трёх."
                        ),
                        data=[("А", 1), ("Б", 2), ("В", 3)],
                        source_note="Условные fixture-данные, не фактическое утверждение",
                    )
                ],
            )
        ],
        bibliography=["Тестовый источник. URL: https://example.test/source"],
        publisher_annotation="Книга о проверяемом производственном цикле.",
    )


def test_selected_outputs_keep_sixteen_native_tables_and_audio_meaning(tmp_path: Path) -> None:
    selection = AutoBookOutputSelection(
        full_manuscript_docx=True,
        litres_ebook_docx=True,
        reading_pdf=True,
        epub=True,
        audio_reading_docx=True,
        audio_litres_docx=True,
        voice_text_txt=True,
        pronunciation_dictionary=True,
        reader_extras=True,
        publisher_pack=True,
    )
    book_id, run_id = setup_run(tmp_path, selection)
    bundle = AutoBookExporter(tmp_path, DurableAutoBookRuntime(tmp_path)).export_selected(
        book_id,
        run_id,
        fixture_master(),
        selection,
    )

    assert len(bundle.artifacts) == 10
    by_kind = {artifact.output_kind: artifact for artifact in bundle.artifacts}
    project_dir = tmp_path / "projects" / book_id

    manuscript = Document(project_dir / by_kind["FULL_MANUSCRIPT_DOCX"].relative_path)
    assert len(manuscript.tables) == 16
    assert "Библиография" in [paragraph.text for paragraph in manuscript.paragraphs]

    audio = Document(project_dir / by_kind["AUDIO_READING_DOCX"].relative_path)
    assert len(audio.tables) == 0
    audio_text = "\n".join(paragraph.text for paragraph in audio.paragraphs)
    assert "Таблица 16 показывает" in audio_text
    assert "График на условных данных" in audio_text

    voice = (project_dir / by_kind["VOICE_TEXT_TXT"].relative_path).read_text(encoding="utf-8")
    assert "Таблица 1 показывает" in voice
    assert "График на условных данных" in voice
    assert "|" not in voice

    pdf_payload = (project_dir / by_kind["READING_PDF"].relative_path).read_bytes()
    assert pdf_payload.startswith(b"%PDF-")
    with ZipFile(project_dir / by_kind["EPUB"].relative_path) as archive:
        assert "mimetype" in archive.namelist()

    visual = Path(bundle.output_directory) / "visuals" / "chart-1.png"
    assert visual.is_file()
    assert visual.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert all(artifact.qa["passed"] is True for artifact in bundle.artifacts)


def test_late_output_selection_exports_only_missing_derivative_and_marks_old_stale(
    tmp_path: Path,
) -> None:
    initial = AutoBookOutputSelection(full_manuscript_docx=True)
    book_id, run_id = setup_run(tmp_path, initial)
    runtime = DurableAutoBookRuntime(tmp_path)
    exporter = AutoBookExporter(tmp_path, runtime)
    first = exporter.export_selected(book_id, run_id, fixture_master(), initial)
    assert [item.output_kind for item in first.artifacts] == ["FULL_MANUSCRIPT_DOCX"]

    later = AutoBookOutputSelection(full_manuscript_docx=False, epub=True)
    second = exporter.export_selected(book_id, run_id, fixture_master(), later)
    assert [item.output_kind for item in second.artifacts] == ["EPUB"]
    assert len(runtime.list_artifacts(book_id, run_id)) == 2

    changed = AutoBookOutputSelection(full_manuscript_docx=True)
    exporter.export_selected(book_id, run_id, fixture_master(suffix=" — новая ревизия"), changed)
    manuscripts = [
        item
        for item in runtime.list_artifacts(book_id, run_id)
        if item.output_kind == "FULL_MANUSCRIPT_DOCX"
    ]
    assert [item.status for item in manuscripts] == ["STALE", "READY"]
