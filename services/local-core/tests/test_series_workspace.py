import base64
from io import BytesIO
from pathlib import Path

from docx import Document
import pytest

from book_os_core.book_context import ProfileCreateRequest, ProfileRegistry
from book_os_core.series_workspace import (
    SeriesBookCreateRequest,
    SeriesCreateRequest,
    SeriesExportSelection,
    SeriesImportRequest,
    SeriesPresetRequest,
    SeriesWorkspaceGateError,
    SeriesWorkspaceService,
)


def approved_author(tmp_path: Path) -> str:
    registry = ProfileRegistry(tmp_path)
    profile = registry.create_profile(
        ProfileCreateRequest(kind="AUTHOR", content={"author_name": "Елена Дым"})
    )
    return registry.approve_profile(profile.profile_id).profile_id


def new_series(tmp_path: Path) -> tuple[SeriesWorkspaceService, str]:
    service = SeriesWorkspaceService(tmp_path)
    profile = service.create_series(
        SeriesCreateRequest(
            series_name="Сильная серия",
            author_profile_id=approved_author(tmp_path),
            audience="Авторы практического нон-фикшн",
            promise="Каждая книга решает отдельную большую задачу",
            territory="Профессиональная работа с книгой",
        )
    )
    ProfileRegistry(tmp_path).approve_profile(profile.profile_id)
    return service, profile.profile_id


def book(title: str, ordinal: int, idea: str) -> SeriesBookCreateRequest:
    return SeriesBookCreateRequest(
        title=title,
        ordinal=ordinal,
        unique_idea=idea,
        reader_problem=f"Проблема для {title}",
        reader_result=f"Самостоятельный результат {title}",
        unique_mechanism=f"Уникальный механизм {title}",
        excluded_topics=["Территория соседней книги"],
    )


def test_series_map_is_persistent_owner_approved_and_becomes_stale(tmp_path: Path) -> None:
    service, series_id = new_series(tmp_path)
    first = service.add_book(series_id, book("Архитектура", 1, "Построить неповторимую структуру"))
    second = service.add_book(series_id, book("Редактура", 2, "Исправить сквозные дефекты текста"))
    service.approve_book_passport(series_id, first.book_id, first.passport_hash, "Утверждаю")
    service.approve_book_passport(series_id, second.book_id, second.passport_hash, "Утверждаю")

    result = service.analyze(series_id)
    assert result.status in {"PASS", "ATTENTION"}
    assert not result.approved
    approved = service.approve_map(series_id, result.map_hash, "Границы книг проверены")
    assert approved.approved
    service.require_current_map(series_id)

    service.add_book(series_id, book("Факты", 3, "Проверить доказательную основу"))
    stale = service.current_map(series_id)
    assert stale is not None and not stale.current
    with pytest.raises(SeriesWorkspaceGateError, match="Book Passports|missing or stale"):
        service.require_current_map(series_id)


def test_import_keeps_original_bytes_and_a_separate_structural_profile(tmp_path: Path) -> None:
    service, series_id = new_series(tmp_path)
    entry = service.add_book(
        series_id,
        book("Внешняя книга", 1, "Разобрать уже написанную авторскую рукопись"),
    )
    document = Document()
    document.add_heading("Глава первая", level=1)
    document.add_paragraph("Точный исходный текст не переписывается при импорте.")
    document.add_table(rows=2, cols=2)
    stream = BytesIO()
    document.save(stream)
    payload = stream.getvalue()

    imported = service.import_source(
        series_id,
        entry.book_id,
        SeriesImportRequest(
            filename="не-считать-названием.docx",
            content_base64=base64.b64encode(payload).decode(),
            rights_status="AUTHOR_MANUSCRIPT",
        ),
    )

    assert imported.analysis_status == "PARSED"
    assert imported.analysis["filename_is_not_book_title"] is True
    assert imported.analysis["headings"] == ["Глава первая"]
    assert imported.analysis["tables"] == 1
    stored = tmp_path / "projects" / entry.book_id / "series-imports"
    assert next(stored.iterdir()).read_bytes() == payload


def test_semantic_overlap_blocks_owner_map_approval(tmp_path: Path) -> None:
    service, series_id = new_series(tmp_path)
    repeated = "Одна книга объясняет центральный механизм продаж услуг через доверие клиента"
    service.add_book(series_id, book("Книга один", 1, repeated))
    service.add_book(series_id, book("Книга два", 2, repeated))

    result = service.analyze(series_id)
    assert result.status == "BLOCKING"
    with pytest.raises(SeriesWorkspaceGateError, match="blocking overlap"):
        service.approve_map(series_id, result.map_hash, "Одобряю")


def test_unapproved_book_passport_blocks_writing_gate(tmp_path: Path) -> None:
    service, series_id = new_series(tmp_path)
    service.add_book(series_id, book("Черновой паспорт", 1, "Новая отдельная задача"))
    result = service.analyze(series_id)
    service.approve_map(series_id, result.map_hash, "Различия проверены")
    with pytest.raises(SeriesWorkspaceGateError, match="Book Passports"):
        service.require_current_map(series_id)


def test_partial_import_fails_closed_and_cannot_be_approved(tmp_path: Path) -> None:
    service, series_id = new_series(tmp_path)
    entry = service.add_book(series_id, book("Скан", 1, "Разобрать скан книги"))
    service.import_source(
        series_id,
        entry.book_id,
        SeriesImportRequest(
            filename="scan.pdf",
            content_base64=base64.b64encode(b"not a valid pdf").decode(),
            rights_status="AUTHOR_MANUSCRIPT",
        ),
    )
    result = service.analyze(series_id)
    assert result.status == "BLOCKING"
    assert any(item["dimension"] == "SOURCE_QUALITY" for item in result.findings)
    with pytest.raises(SeriesWorkspaceGateError, match="blocking overlap"):
        service.approve_map(series_id, result.map_hash, "Пусть система проигнорирует ошибку")


def test_services_promotion_preset_is_idempotent_and_keeps_owner_order(tmp_path: Path) -> None:
    service = SeriesWorkspaceService(tmp_path)
    author_id = approved_author(tmp_path)
    first = service.create_services_promotion_preset(
        SeriesPresetRequest(author_profile_id=author_id)
    )
    second = service.create_services_promotion_preset(
        SeriesPresetRequest(author_profile_id=author_id)
    )

    assert first.series_profile_id == second.series_profile_id
    assert first.name == "Секреты продвижения услуг"
    assert [item.title for item in first.books[:4]] == [
        "Как продавать услуги",
        "Секреты продвижения услуг психолога в Яндекс Директ",
        "Как продвигать юридические услуги в Яндекс Директ: Практическое руководство",
        "Как продать онлайн-курсы",
    ]
    assert len(second.books) == 8
    assert second.profile_status == "DRAFT"


def test_import_can_be_explicitly_deleted_and_book_archived(tmp_path: Path) -> None:
    service, series_id = new_series(tmp_path)
    entry = service.add_book(series_id, book("Удаляемый источник", 1, "Проверить удаление"))
    imported = service.import_source(
        series_id,
        entry.book_id,
        SeriesImportRequest(
            filename="source.txt",
            content_base64=base64.b64encode("Текст автора".encode()).decode(),
            rights_status="AUTHOR_MANUSCRIPT",
        ),
    )
    source_path = next((tmp_path / "projects" / entry.book_id / "series-imports").iterdir())
    deleted = service.delete_import(series_id, entry.book_id, imported.source_id)
    assert deleted.status == "DELETED"
    assert not source_path.exists()
    archived = service.archive_book(series_id, entry.book_id)
    assert archived.status == "ARCHIVED"
    assert service.books(series_id)[0].status == "ARCHIVED"


def test_selected_series_export_does_not_start_planned_books(tmp_path: Path) -> None:
    service, series_id = new_series(tmp_path)
    service.add_book(series_id, book("Готовая", 1, "Самостоятельная готовая книга"))
    planned = service.add_book(series_id, book("Будущая", 2, "Отдельная будущая книга"))
    result = service.export_series(
        series_id,
        SeriesExportSelection(
            descriptions=True,
            series_and_book_passports=True,
            difference_map=True,
            sources_and_freshness=True,
            next_books_plan=True,
        ),
    )
    assert any(path.endswith("manifest.json") for path in result.files)
    assert any(path.endswith("План-следующих-книг.json") for path in result.files)
    assert service.books(series_id)[1].book_id == planned.book_id
    assert service.books(series_id)[1].status == "IDEA"
