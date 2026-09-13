from __future__ import annotations

import base64
import binascii
import hashlib
from html import unescape
import json
from pathlib import Path
import re
from typing import Any, Literal, cast
from zipfile import BadZipFile, ZipFile

from docx import Document
from pydantic import BaseModel, Field
from pypdf.errors import PdfReadError
from sqlalchemy import text

from .authority import canonical_json, new_ulid
from .authority_types import JSONValue, utc_now
from .book_context import (
    ProfileCreateRequest,
    ProfileRegistry,
    SeriesProfileContent,
)
from .db import create_database
from .projects import NewBookRequest, ProjectService


SeriesBookStatus = Literal[
    "IDEA",
    "DEFINITION",
    "ARCHITECTURE",
    "WRITING",
    "EDITING",
    "FINAL_REVIEW",
    "READY",
    "ARCHIVED",
]
RightsStatus = Literal[
    "AUTHOR_MANUSCRIPT",
    "PUBLISHED_OWN_BOOK",
    "LICENSED_MATERIAL",
    "REFERENCE_ONLY",
]


class SeriesWorkspaceError(RuntimeError):
    pass


class SeriesWorkspaceGateError(SeriesWorkspaceError):
    pass


class SeriesCreateRequest(BaseModel):
    series_name: str = Field(min_length=1, max_length=300)
    author_profile_id: str = Field(min_length=26, max_length=26)
    audience: str = Field(default="", max_length=6000)
    promise: str = Field(default="", max_length=6000)
    territory: str = Field(default="", max_length=6000)
    prohibited_territories: list[str] = Field(default_factory=list)


class SeriesBookCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    ordinal: int = Field(ge=1, le=500)
    unique_idea: str = Field(min_length=1, max_length=12000)
    reader_problem: str = Field(min_length=1, max_length=12000)
    reader_result: str = Field(min_length=1, max_length=12000)
    unique_mechanism: str = Field(min_length=1, max_length=12000)
    excluded_topics: list[str] = Field(default_factory=list)
    source_kind: Literal["BOOK_OS", "IMPORTED", "PLANNED"] = "PLANNED"


class SeriesImportRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=1000)
    content_base64: str = Field(min_length=1, max_length=40_000_000, repr=False)
    rights_status: RightsStatus


class SeriesPresetRequest(BaseModel):
    author_profile_id: str = Field(min_length=26, max_length=26)


class SeriesMutationView(BaseModel):
    status: Literal["ARCHIVED", "DELETED"]
    series_profile_id: str
    book_id: str
    source_id: str | None = None
    map_is_now_stale: bool = True


class SeriesExportSelection(BaseModel):
    complete_manuscripts: bool = False
    editorial_and_litres: bool = False
    audio_editions: bool = False
    descriptions: bool = True
    series_and_book_passports: bool = True
    difference_map: bool = True
    visual_materials: bool = False
    sources_and_freshness: bool = True
    next_books_plan: bool = True

    def selected(self) -> list[str]:
        return [name for name, enabled in self.model_dump().items() if enabled]


class SeriesExportView(BaseModel):
    series_profile_id: str
    map_hash: str | None
    selected: list[str]
    files: list[str]
    output_directory: str


class SeriesBookView(BaseModel):
    series_book_id: str
    series_profile_id: str
    book_id: str
    title: str
    ordinal: int
    unique_idea: str
    reader_problem: str
    reader_result: str
    unique_mechanism: str
    excluded_topics: list[str]
    source_kind: str
    status: SeriesBookStatus
    passport_hash: str
    passport_approved: bool
    imported_sources: list[dict[str, Any]] = Field(default_factory=list)
    updated_at: str


class SeriesImportedSourceView(BaseModel):
    source_id: str
    series_profile_id: str
    book_id: str
    filename: str
    format: str
    content_hash: str
    rights_status: RightsStatus
    analysis_status: Literal["PARSED", "PARTIAL", "FAILED"]
    analysis: dict[str, Any]
    created_at: str


class SeriesMapView(BaseModel):
    map_hash: str
    status: Literal["PASS", "ATTENTION", "BLOCKING"]
    findings: list[dict[str, Any]]
    approved: bool
    current: bool = True


class SeriesWorkspaceView(BaseModel):
    series_profile_id: str
    name: str
    profile_status: str
    profile_revision: int
    audience: str
    promise: str
    territory: str
    prohibited_territories: list[str]
    books: list[SeriesBookView]
    map: SeriesMapView | None


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[а-яёa-z0-9]{4,}", value.casefold()))


def _normalized_text(value: str) -> str:
    return " ".join(re.findall(r"[а-яёa-z0-9]+", value.casefold()))


class SeriesWorkspaceService:
    """Cross-project series read model reusing Series Profile and Task 017 gates.

    Each book remains an isolated project database. The service scans only explicit
    `series_books` membership and never infers a series from a title or filename.
    """

    MAX_IMPORT_BYTES = 25_000_000
    SERVICES_PROMOTION_NAME = "Секреты продвижения услуг"
    SERVICES_PROMOTION_TERRITORY = (
        "Выбор исполнителя и превращение спроса в оплаченные услуги с учётом "
        "нематериальности результата, доверия до покупки и ограниченной "
        "производственной мощности исполнителя."
    )
    SERVICES_PROMOTION_EXCLUSIONS = [
        "маркетплейсы",
        "общие скрипты переписки",
        "старт бизнеса с минимальным бюджетом",
        "управление кассовыми разрывами",
        "общие руководства по квизам и SMM",
        "AI-SEO",
        "нейровидео",
        "удалённая карьера",
    ]
    SERVICES_PROMOTION_BOOKS = [
        ("Как продавать услуги", "Системно превращать спрос и доверие в оплату услуги", "IMPORTED"),
        (
            "Секреты продвижения услуг психолога в Яндекс Директ",
            "Привлечение клиентов психолога через Яндекс Директ",
            "IMPORTED",
        ),
        (
            "Как продвигать юридические услуги в Яндекс Директ: Практическое руководство",
            "Привлечение клиентов юридических услуг через Яндекс Директ",
            "IMPORTED",
        ),
        ("Как продать онлайн-курсы", "Продажа образовательного продукта как услуги", "IMPORTED"),
        ("Продажи услуг компаниям", "Продажи профессиональных услуг B2B", "PLANNED"),
        ("Местные услуги", "Продажи услуг в локальном спросе", "PLANNED"),
        ("Дорогие услуги", "Продажи услуг с высокой ценой и длинным решением", "PLANNED"),
        (
            "Повторные продажи и рекомендации",
            "Рост услуг через повторные обращения и рекомендации",
            "PLANNED",
        ),
    ]

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.projects = ProjectService(data_dir)
        self.profiles = ProfileRegistry(data_dir)

    def _engine(self, book_id: str):
        self.projects.get_project(book_id)
        return create_database(self.projects.projects_dir / book_id / "project.sqlite")

    def create_series(self, request: SeriesCreateRequest):
        content = SeriesProfileContent(
            series_name=request.series_name.strip(),
            author_profile_id=request.author_profile_id,
            purpose_positioning="\n\n".join(
                value
                for value in (
                    f"Аудитория: {request.audience.strip()}" if request.audience.strip() else "",
                    f"Обещание серии: {request.promise.strip()}" if request.promise.strip() else "",
                    f"Территория: {request.territory.strip()}" if request.territory.strip() else "",
                )
                if value
            ),
            thematic_territories=[request.territory] if request.territory.strip() else [],
            future_book_reservations=request.prohibited_territories,
            cross_book_uniqueness_rules=[
                "Каждая книга даёт самостоятельный результат без обязательной покупки соседних книг.",
                "Не маскировать смысловой дубль перефразированием.",
            ],
            exclusion_dimensions=[
                "тезисы",
                "архитектура",
                "примеры и кейсы",
                "метафоры",
                "инструменты",
                "язык",
                "визуалы",
            ],
            prewriting_overlap_requirements=[
                "Актуальная карта различий и утверждённый паспорт книги обязательны до WRITING."
            ],
            whole_book_audit_requirements=[
                "Перед финализацией проверить качество книги и серии как системы."
            ],
        )
        return self.profiles.create_profile(
            ProfileCreateRequest(kind="SERIES", content=content.model_dump(mode="json"))
        )

    def create_services_promotion_preset(self, request: SeriesPresetRequest) -> SeriesWorkspaceView:
        author = self.profiles.get_profile(request.author_profile_id)
        if author.kind != "AUTHOR" or author.status != "APPROVED":
            raise SeriesWorkspaceGateError("preset requires an approved Author Profile")
        existing = next(
            (
                profile
                for profile in self.profiles.list_profiles("SERIES")
                if profile.name == self.SERVICES_PROMOTION_NAME
                and profile.content.get("author_profile_id") == request.author_profile_id
            ),
            None,
        )
        if existing is None:
            profile = self.create_series(
                SeriesCreateRequest(
                    series_name=self.SERVICES_PROMOTION_NAME,
                    author_profile_id=request.author_profile_id,
                    audience="Предприниматели и специалисты, продающие профессиональные услуги",
                    promise=(
                        "Каждая книга решает отдельную крупную задачу продвижения и продажи услуг"
                    ),
                    territory=self.SERVICES_PROMOTION_TERRITORY,
                    prohibited_territories=self.SERVICES_PROMOTION_EXCLUSIONS,
                )
            )
        else:
            profile = existing
        present = {item.ordinal for item in self.books(profile.profile_id)}
        for ordinal, (title, idea, source_kind) in enumerate(
            self.SERVICES_PROMOTION_BOOKS, start=1
        ):
            if ordinal in present:
                continue
            self.add_book(
                profile.profile_id,
                SeriesBookCreateRequest(
                    title=title,
                    ordinal=ordinal,
                    unique_idea=idea,
                    reader_problem=f"Отдельная задача книги: {idea}",
                    reader_result=f"Практический результат: {idea}",
                    unique_mechanism=f"Границы и механизм уточняются в паспорте книги № {ordinal}",
                    excluded_topics=self.SERVICES_PROMOTION_EXCLUSIONS,
                    source_kind=cast(Any, source_kind),
                ),
            )
        return next(
            item for item in self.workspaces() if item.series_profile_id == profile.profile_id
        )

    def add_book(
        self,
        series_profile_id: str,
        request: SeriesBookCreateRequest,
    ) -> SeriesBookView:
        profile = self.profiles.get_profile(series_profile_id)
        if profile.kind != "SERIES":
            raise SeriesWorkspaceError("profile is not a series")
        project = self.projects.create_project(
            NewBookRequest(working_title=request.title.strip(), primary_subtype="Strategy")
        )
        now = utc_now()
        engine = self._engine(project.book_id)
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO series_books(series_book_id,series_profile_id,book_id,ordinal,"
                        "unique_idea,reader_problem,reader_result,unique_mechanism,excluded_topics_json,"
                        "source_kind,status,created_at,updated_at) VALUES (:id,:series,:book,:ordinal,"
                        ":idea,:problem,:result,:mechanism,:excluded,:source,'IDEA',:created,:updated)"
                    ),
                    {
                        "id": new_ulid(),
                        "series": series_profile_id,
                        "book": project.book_id,
                        "ordinal": request.ordinal,
                        "idea": request.unique_idea.strip(),
                        "problem": request.reader_problem.strip(),
                        "result": request.reader_result.strip(),
                        "mechanism": request.unique_mechanism.strip(),
                        "excluded": json.dumps(request.excluded_topics, ensure_ascii=False),
                        "source": request.source_kind,
                        "created": now,
                        "updated": now,
                    },
                )
        finally:
            engine.dispose()
        return next(
            item for item in self.books(series_profile_id) if item.book_id == project.book_id
        )

    def books(self, series_profile_id: str) -> list[SeriesBookView]:
        result: list[SeriesBookView] = []
        for project in self.projects.list_projects():
            engine = self._engine(project.book_id)
            try:
                with engine.connect() as connection:
                    row = (
                        connection.execute(
                            text(
                                "SELECT * FROM series_books WHERE series_profile_id=:series "
                                "AND book_id=:book"
                            ),
                            {"series": series_profile_id, "book": project.book_id},
                        )
                        .mappings()
                        .first()
                    )
                    if row is None:
                        continue
                    passport_material = {
                        "title": project.working_title,
                        "ordinal": int(row["ordinal"]),
                        "unique_idea": str(row["unique_idea"]),
                        "reader_problem": str(row["reader_problem"]),
                        "reader_result": str(row["reader_result"]),
                        "unique_mechanism": str(row["unique_mechanism"]),
                        "excluded_topics": json.loads(str(row["excluded_topics_json"])),
                    }
                    passport_hash = hashlib.sha256(
                        canonical_json(cast(dict[str, JSONValue], passport_material)).encode()
                    ).hexdigest()
                    passport_approved = (
                        connection.execute(
                            text(
                                "SELECT 1 FROM series_author_decisions "
                                "WHERE series_profile_id=:series AND book_id=:book "
                                "AND decision_kind='BOOK_PASSPORT' AND input_hash=:hash "
                                "AND decision='APPROVED' LIMIT 1"
                            ),
                            {
                                "series": series_profile_id,
                                "book": project.book_id,
                                "hash": passport_hash,
                            },
                        ).scalar_one_or_none()
                        is not None
                    )
                    imported_sources = [
                        {
                            **dict(source),
                            "analysis": json.loads(str(source["analysis_json"])),
                        }
                        for source in connection.execute(
                            text(
                                "SELECT * FROM series_imported_sources WHERE book_id=:book "
                                "ORDER BY created_at,source_id"
                            ),
                            {"book": project.book_id},
                        ).mappings()
                    ]
            finally:
                engine.dispose()
            if row is not None:
                result.append(
                    SeriesBookView(
                        series_book_id=str(row["series_book_id"]),
                        series_profile_id=str(row["series_profile_id"]),
                        book_id=str(row["book_id"]),
                        title=project.working_title,
                        ordinal=int(row["ordinal"]),
                        unique_idea=str(row["unique_idea"]),
                        reader_problem=str(row["reader_problem"]),
                        reader_result=str(row["reader_result"]),
                        unique_mechanism=str(row["unique_mechanism"]),
                        excluded_topics=cast(
                            list[str], json.loads(str(row["excluded_topics_json"]))
                        ),
                        source_kind=str(row["source_kind"]),
                        status=cast(SeriesBookStatus, str(row["status"])),
                        passport_hash=passport_hash,
                        passport_approved=passport_approved,
                        imported_sources=[
                            {
                                "source_id": source["source_id"],
                                "filename": source["filename"],
                                "format": source["format"],
                                "content_hash": source["content_hash"],
                                "rights_status": source["rights_status"],
                                "analysis_status": source["analysis_status"],
                                "analysis": source["analysis"],
                            }
                            for source in imported_sources
                        ],
                        updated_at=str(row["updated_at"]),
                    )
                )
        return sorted(result, key=lambda item: (item.ordinal, item.book_id))

    def approve_book_passport(
        self, series_profile_id: str, book_id: str, passport_hash: str, reason: str
    ) -> SeriesBookView:
        book = next(
            (item for item in self.books(series_profile_id) if item.book_id == book_id), None
        )
        if book is None:
            raise SeriesWorkspaceError("book does not belong to this series")
        if book.passport_hash != passport_hash:
            raise SeriesWorkspaceGateError("book passport changed; review the current version")
        engine = self._engine(book_id)
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO series_author_decisions(decision_id,series_profile_id,book_id,"
                        "decision_kind,input_hash,decision,reason,actor,created_at) VALUES "
                        "(:id,:series,:book,'BOOK_PASSPORT',:hash,'APPROVED',:reason,'OWNER',:created)"
                    ),
                    {
                        "id": new_ulid(),
                        "series": series_profile_id,
                        "book": book_id,
                        "hash": passport_hash,
                        "reason": reason.strip() or "Owner approved the current Book Passport",
                        "created": utc_now(),
                    },
                )
        finally:
            engine.dispose()
        return next(item for item in self.books(series_profile_id) if item.book_id == book_id)

    @staticmethod
    def _extract(filename: str, payload: bytes) -> tuple[str, str, dict[str, Any]]:
        suffix = Path(filename).suffix.casefold()
        fmt = {
            ".docx": "DOCX",
            ".txt": "TXT",
            ".md": "MARKDOWN",
            ".markdown": "MARKDOWN",
            ".pdf": "PDF",
            ".epub": "EPUB",
        }.get(suffix)
        if fmt is None:
            raise SeriesWorkspaceError("supported series imports: DOCX, TXT, PDF, EPUB, Markdown")
        text_value = ""
        headings: list[str] = []
        tables = 0
        table_signatures: list[str] = []
        visuals = 0
        warnings: list[str] = []
        try:
            if fmt in {"TXT", "MARKDOWN"}:
                text_value = payload.decode("utf-8")
                headings = [
                    line.lstrip("# ").strip()
                    for line in text_value.splitlines()
                    if line.startswith("#")
                ]
            elif fmt == "DOCX":
                from io import BytesIO

                document = Document(BytesIO(payload))
                text_value = "\n".join(item.text for item in document.paragraphs)
                headings = [
                    item.text.strip()
                    for item in document.paragraphs
                    if item.text.strip()
                    and item.style is not None
                    and item.style.name.startswith("Heading")
                ]
                tables = len(document.tables)
                table_signatures = [
                    hashlib.sha256(
                        "\u241f".join(
                            "\u241e".join(cell.text.strip() for cell in row.cells)
                            for row in table.rows
                        ).encode("utf-8")
                    ).hexdigest()
                    for table in document.tables
                ]
                visuals = len(document.inline_shapes)
            elif fmt == "PDF":
                try:
                    from io import BytesIO
                    from pypdf import PdfReader

                    reader = PdfReader(BytesIO(payload))
                    text_value = "\n".join(page.extract_text() or "" for page in reader.pages)
                    if not text_value.strip():
                        warnings.append("Текст не распознан; для скана нужен OCR")
                except ImportError:
                    warnings.append("PDF сохранён; модуль извлечения текста недоступен")
            elif fmt == "EPUB":
                from io import BytesIO

                with ZipFile(BytesIO(payload)) as archive:
                    html_parts = [
                        archive.read(name).decode("utf-8", errors="replace")
                        for name in archive.namelist()
                        if name.casefold().endswith((".xhtml", ".html", ".htm"))
                    ]
                raw = "\n".join(html_parts)
                headings = [
                    unescape(re.sub(r"<[^>]+>", " ", value)).strip()
                    for value in re.findall(r"<h[1-6][^>]*>(.*?)</h[1-6]>", raw, re.I | re.S)
                ]
                text_value = unescape(re.sub(r"<[^>]+>", " ", raw))
        except (BadZipFile, OSError, PdfReadError, UnicodeError, ValueError) as exc:
            return fmt, "FAILED", {"warnings": [f"Файл не разобран: {exc}"]}
        normalized = " ".join(text_value.split())
        status = "PARSED" if normalized and not warnings else "PARTIAL"
        analysis = {
            "characters": len(normalized),
            "headings": headings[:300],
            "tables": tables,
            "table_signatures": table_signatures,
            "visuals": visuals,
            "sample": text_value[:20_000],
            "warnings": warnings,
            "filename_is_not_book_title": True,
        }
        return fmt, status, analysis

    def import_source(
        self,
        series_profile_id: str,
        book_id: str,
        request: SeriesImportRequest,
    ) -> SeriesImportedSourceView:
        membership = next(
            (item for item in self.books(series_profile_id) if item.book_id == book_id),
            None,
        )
        if membership is None:
            raise SeriesWorkspaceError("book does not belong to this series")
        try:
            payload = base64.b64decode(request.content_base64, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise SeriesWorkspaceError("import is not valid base64") from exc
        if not payload or len(payload) > self.MAX_IMPORT_BYTES:
            raise SeriesWorkspaceError("series import must be between 1 byte and 25 MB")
        content_hash = hashlib.sha256(payload).hexdigest()
        fmt, analysis_status, analysis = self._extract(request.filename, payload)
        relative = f"series-imports/{content_hash}{Path(request.filename).suffix.casefold()}"
        output = self.projects.projects_dir / book_id / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        if not output.exists():
            output.write_bytes(payload)
        now = utc_now()
        source_id = new_ulid()
        engine = self._engine(book_id)
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO series_imported_sources(source_id,series_profile_id,book_id,"
                        "filename,format,relative_path,content_hash,rights_status,analysis_status,"
                        "analysis_json,created_at) VALUES (:id,:series,:book,:filename,:format,"
                        ":path,:hash,:rights,:status,:analysis,:created)"
                    ),
                    {
                        "id": source_id,
                        "series": series_profile_id,
                        "book": book_id,
                        "filename": Path(request.filename).name,
                        "format": fmt,
                        "path": relative,
                        "hash": content_hash,
                        "rights": request.rights_status,
                        "status": analysis_status,
                        "analysis": json.dumps(analysis, ensure_ascii=False, sort_keys=True),
                        "created": now,
                    },
                )
        finally:
            engine.dispose()
        return SeriesImportedSourceView(
            source_id=source_id,
            series_profile_id=series_profile_id,
            book_id=book_id,
            filename=Path(request.filename).name,
            format=fmt,
            content_hash=content_hash,
            rights_status=request.rights_status,
            analysis_status=cast(Any, analysis_status),
            analysis=analysis,
            created_at=now,
        )

    def _source_rows(self, book_id: str) -> list[dict[str, Any]]:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                return [
                    {**dict(row), "analysis": json.loads(str(row["analysis_json"]))}
                    for row in connection.execute(
                        text("SELECT * FROM series_imported_sources WHERE book_id=:book"),
                        {"book": book_id},
                    ).mappings()
                ]
        finally:
            engine.dispose()

    def _map_hash(self, series_profile_id: str, books: list[SeriesBookView]) -> str:
        profile = self.profiles.get_profile(series_profile_id)
        material = {
            "profile_hash": profile.content_hash,
            "books": [book.model_dump(mode="json") for book in books],
            "sources": {
                book.book_id: sorted(row["content_hash"] for row in self._source_rows(book.book_id))
                for book in books
            },
        }
        return hashlib.sha256(
            canonical_json(cast(dict[str, JSONValue], material)).encode()
        ).hexdigest()

    def analyze(self, series_profile_id: str) -> SeriesMapView:
        books = self.books(series_profile_id)
        if not books:
            raise SeriesWorkspaceGateError("series has no books")
        map_hash = self._map_hash(series_profile_id, books)
        findings: list[dict[str, Any]] = []
        for book in books:
            for source in self._source_rows(book.book_id):
                if source["analysis_status"] != "PARSED":
                    findings.append(
                        {
                            "finding_id": new_ulid(),
                            "book_id": book.book_id,
                            "compared_book_id": book.book_id,
                            "dimension": "SOURCE_QUALITY",
                            "severity": "BLOCKING",
                            "evidence": {
                                "source_id": source["source_id"],
                                "analysis_status": source["analysis_status"],
                                "warnings": source["analysis"].get("warnings", []),
                            },
                        }
                    )
        for index, left in enumerate(books):
            left_text = " ".join(
                (left.unique_idea, left.reader_problem, left.reader_result, left.unique_mechanism)
            )
            left_tokens = _tokens(left_text)
            for right in books[index + 1 :]:
                right_text = " ".join(
                    (
                        right.unique_idea,
                        right.reader_problem,
                        right.reader_result,
                        right.unique_mechanism,
                    )
                )
                right_tokens = _tokens(right_text)
                union = left_tokens | right_tokens
                score = len(left_tokens & right_tokens) / len(union) if union else 0.0
                if score >= 0.35:
                    findings.append(
                        {
                            "finding_id": new_ulid(),
                            "book_id": left.book_id,
                            "compared_book_id": right.book_id,
                            "dimension": "THESIS",
                            "severity": "BLOCKING" if score >= 0.55 else "ATTENTION",
                            "evidence": {
                                "token_jaccard": round(score, 4),
                                "shared_terms": sorted(left_tokens & right_tokens)[:30],
                            },
                        }
                    )
                left_sources = self._source_rows(left.book_id)
                right_sources = self._source_rows(right.book_id)
                left_headings = [
                    heading.casefold()
                    for row in left_sources
                    for heading in row["analysis"].get("headings", [])
                ]
                right_headings = [
                    heading.casefold()
                    for row in right_sources
                    for heading in row["analysis"].get("headings", [])
                ]
                if left_headings and left_headings == right_headings:
                    findings.append(
                        {
                            "finding_id": new_ulid(),
                            "book_id": left.book_id,
                            "compared_book_id": right.book_id,
                            "dimension": "ARCHITECTURE",
                            "severity": "BLOCKING",
                            "evidence": {"identical_heading_sequence": left_headings[:50]},
                        }
                    )
                left_samples = " ".join(
                    str(row["analysis"].get("sample", "")) for row in left_sources
                )
                right_samples = " ".join(
                    str(row["analysis"].get("sample", "")) for row in right_sources
                )

                def matching_sentences(pattern: str) -> list[str]:
                    left_values = {
                        _normalized_text(sentence)
                        for sentence in re.split(r"[.!?\n]+", left_samples)
                        if re.search(pattern, sentence, re.I) and len(_tokens(sentence)) >= 7
                    }
                    right_values = {
                        _normalized_text(sentence)
                        for sentence in re.split(r"[.!?\n]+", right_samples)
                        if re.search(pattern, sentence, re.I) and len(_tokens(sentence)) >= 7
                    }
                    return sorted((left_values & right_values) - {""})

                for dimension, pattern in (
                    ("EXAMPLE", r"\b(?:например|кейс|истори[яи]|ситуаци[яи])\b"),
                    ("METAPHOR", r"\b(?:словно|будто|метафор|аналог)[а-яё]*\b"),
                    ("TOOL", r"\b(?:матриц|чек-лист|алгоритм|упражнен|формул)[а-яё-]*\b"),
                ):
                    duplicates = matching_sentences(pattern)
                    if duplicates:
                        findings.append(
                            {
                                "finding_id": new_ulid(),
                                "book_id": left.book_id,
                                "compared_book_id": right.book_id,
                                "dimension": dimension,
                                "severity": "BLOCKING",
                                "evidence": {"matching_passages": duplicates[:10]},
                            }
                        )

                left_tables = {
                    signature
                    for row in left_sources
                    for signature in row["analysis"].get("table_signatures", [])
                }
                right_tables = {
                    signature
                    for row in right_sources
                    for signature in row["analysis"].get("table_signatures", [])
                }
                if left_tables & right_tables:
                    findings.append(
                        {
                            "finding_id": new_ulid(),
                            "book_id": left.book_id,
                            "compared_book_id": right.book_id,
                            "dimension": "VISUAL",
                            "severity": "BLOCKING",
                            "evidence": {
                                "matching_table_hashes": sorted(left_tables & right_tables)
                            },
                        }
                    )

                left_paragraphs = [
                    _normalized_text(value)
                    for value in left_samples.split("\n")
                    if len(_tokens(value)) >= 20
                ]
                right_paragraphs = {
                    _normalized_text(value)
                    for value in right_samples.split("\n")
                    if len(_tokens(value)) >= 20
                }
                repeated_language = [
                    value for value in left_paragraphs if value in right_paragraphs
                ]
                if repeated_language:
                    findings.append(
                        {
                            "finding_id": new_ulid(),
                            "book_id": left.book_id,
                            "compared_book_id": right.book_id,
                            "dimension": "LANGUAGE",
                            "severity": "BLOCKING",
                            "evidence": {"matching_paragraphs": repeated_language[:5]},
                        }
                    )
        status = (
            "BLOCKING"
            if any(item["severity"] == "BLOCKING" for item in findings)
            else "ATTENTION"
            if findings
            else "PASS"
        )
        anchor = books[0].book_id
        engine = self._engine(anchor)
        now = utc_now()
        try:
            with engine.begin() as connection:
                for item in findings:
                    connection.execute(
                        text(
                            "INSERT INTO series_similarity_findings(finding_id,series_profile_id,"
                            "book_id,compared_book_id,dimension,severity,evidence_json,map_hash,status,"
                            "created_at) VALUES (:id,:series,:book,:compared,:dimension,:severity,"
                            ":evidence,:hash,'OPEN',:created)"
                        ),
                        {
                            "id": item["finding_id"],
                            "series": series_profile_id,
                            "book": item["book_id"],
                            "compared": item["compared_book_id"],
                            "dimension": item["dimension"],
                            "severity": item["severity"],
                            "evidence": json.dumps(item["evidence"], ensure_ascii=False),
                            "hash": map_hash,
                            "created": now,
                        },
                    )
                connection.execute(
                    text(
                        "INSERT INTO series_map_runs(map_run_id,series_profile_id,book_id,map_hash,"
                        "status,finding_count,created_at) VALUES (:id,:series,:book,:hash,:status,"
                        ":count,:created)"
                    ),
                    {
                        "id": new_ulid(),
                        "series": series_profile_id,
                        "book": anchor,
                        "hash": map_hash,
                        "status": status,
                        "count": len(findings),
                        "created": now,
                    },
                )
        finally:
            engine.dispose()
        return SeriesMapView(
            map_hash=map_hash,
            status=cast(Any, status),
            findings=findings,
            approved=False,
        )

    def approve_map(self, series_profile_id: str, map_hash: str, reason: str) -> SeriesMapView:
        current = self.current_map(series_profile_id)
        if current is None or not current.current or current.map_hash != map_hash:
            raise SeriesWorkspaceGateError("series map is missing or stale")
        if current.status == "BLOCKING":
            raise SeriesWorkspaceGateError(
                "blocking overlap cannot be approved without resolving or recording exceptions"
            )
        books = self.books(series_profile_id)
        anchor = books[0].book_id
        engine = self._engine(anchor)
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO series_author_decisions(decision_id,series_profile_id,book_id,"
                        "decision_kind,input_hash,decision,reason,actor,created_at) VALUES (:id,:series,"
                        ":book,'OVERLAP_MAP',:hash,'APPROVED',:reason,'OWNER',:created)"
                    ),
                    {
                        "id": new_ulid(),
                        "series": series_profile_id,
                        "book": anchor,
                        "hash": map_hash,
                        "reason": reason.strip()
                        or "Owner approved the current series difference map",
                        "created": utc_now(),
                    },
                )
        finally:
            engine.dispose()
        return self.current_map(series_profile_id) or current

    def current_map(self, series_profile_id: str) -> SeriesMapView | None:
        books = self.books(series_profile_id)
        if not books:
            return None
        current_hash = self._map_hash(series_profile_id, books)
        engine = self._engine(books[0].book_id)
        try:
            with engine.connect() as connection:
                run = (
                    connection.execute(
                        text(
                            "SELECT * FROM series_map_runs WHERE series_profile_id=:series "
                            "ORDER BY created_at DESC,map_run_id DESC LIMIT 1"
                        ),
                        {"series": series_profile_id},
                    )
                    .mappings()
                    .first()
                )
                if run is None:
                    return None
                findings = [
                    {
                        "finding_id": str(row["finding_id"]),
                        "book_id": str(row["book_id"]),
                        "compared_book_id": str(row["compared_book_id"]),
                        "dimension": str(row["dimension"]),
                        "severity": str(row["severity"]),
                        "status": str(row["status"]),
                        "evidence": json.loads(str(row["evidence_json"])),
                    }
                    for row in connection.execute(
                        text(
                            "SELECT * FROM series_similarity_findings WHERE map_hash=:hash "
                            "ORDER BY created_at,finding_id"
                        ),
                        {"hash": str(run["map_hash"])},
                    ).mappings()
                ]
                approved = (
                    connection.execute(
                        text(
                            "SELECT 1 FROM series_author_decisions WHERE series_profile_id=:series "
                            "AND decision_kind='OVERLAP_MAP' AND input_hash=:hash "
                            "AND decision='APPROVED' LIMIT 1"
                        ),
                        {"series": series_profile_id, "hash": current_hash},
                    ).scalar_one_or_none()
                    is not None
                )
        finally:
            engine.dispose()
        return SeriesMapView(
            map_hash=str(run["map_hash"]),
            status=cast(Any, str(run["status"])),
            findings=findings,
            approved=approved,
            current=str(run["map_hash"]) == current_hash,
        )

    def archive_book(self, series_profile_id: str, book_id: str) -> SeriesMutationView:
        membership = next(
            (item for item in self.books(series_profile_id) if item.book_id == book_id), None
        )
        if membership is None:
            raise SeriesWorkspaceError("book does not belong to this series")
        engine = self._engine(book_id)
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "UPDATE series_books SET status='ARCHIVED',updated_at=:updated "
                        "WHERE series_profile_id=:series AND book_id=:book"
                    ),
                    {
                        "updated": utc_now(),
                        "series": series_profile_id,
                        "book": book_id,
                    },
                )
        finally:
            engine.dispose()
        return SeriesMutationView(
            status="ARCHIVED", series_profile_id=series_profile_id, book_id=book_id
        )

    def delete_import(
        self, series_profile_id: str, book_id: str, source_id: str
    ) -> SeriesMutationView:
        engine = self._engine(book_id)
        try:
            with engine.begin() as connection:
                row = (
                    connection.execute(
                        text(
                            "SELECT relative_path FROM series_imported_sources "
                            "WHERE source_id=:source AND series_profile_id=:series AND book_id=:book"
                        ),
                        {"source": source_id, "series": series_profile_id, "book": book_id},
                    )
                    .mappings()
                    .one_or_none()
                )
                if row is None:
                    raise SeriesWorkspaceError("imported source not found in this series book")
                connection.execute(
                    text("DELETE FROM series_imported_sources WHERE source_id=:source"),
                    {"source": source_id},
                )
            source_path = self.projects.projects_dir / book_id / str(row["relative_path"])
            source_path.unlink(missing_ok=True)
        finally:
            engine.dispose()
        return SeriesMutationView(
            status="DELETED",
            series_profile_id=series_profile_id,
            book_id=book_id,
            source_id=source_id,
        )

    def export_series(
        self, series_profile_id: str, selection: SeriesExportSelection
    ) -> SeriesExportView:
        selected = selection.selected()
        if not selected:
            raise SeriesWorkspaceGateError("select at least one series output")
        workspace = next(
            (item for item in self.workspaces() if item.series_profile_id == series_profile_id),
            None,
        )
        if workspace is None or not workspace.books:
            raise SeriesWorkspaceGateError("series has no book passports to export")
        anchor = workspace.books[0]
        output = (
            self.projects.projects_dir
            / anchor.book_id
            / "exports"
            / f"series-{series_profile_id}-{(workspace.map.map_hash[:12] if workspace.map else 'draft')}"
        )
        output.mkdir(parents=True, exist_ok=True)
        files: list[Path] = []

        def write_json(filename: str, payload: Any) -> None:
            path = output / filename
            path.write_text(
                json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                encoding="utf-8",
            )
            files.append(path)

        if selection.series_and_book_passports:
            write_json("Серия-и-паспорта-книг.json", workspace.model_dump(mode="json"))
        if selection.difference_map:
            write_json(
                "Карта-различий-и-повторов.json",
                None if workspace.map is None else workspace.map.model_dump(mode="json"),
            )
        if selection.sources_and_freshness:
            write_json(
                "Источники-и-качество-разбора.json",
                {
                    book.book_id: [
                        {
                            "source_id": row["source_id"],
                            "filename": row["filename"],
                            "content_hash": row["content_hash"],
                            "rights_status": row["rights_status"],
                            "analysis_status": row["analysis_status"],
                            "warnings": row["analysis"].get("warnings", []),
                        }
                        for row in self._source_rows(book.book_id)
                    ]
                    for book in workspace.books
                },
            )
        if selection.next_books_plan:
            write_json(
                "План-следующих-книг.json",
                [
                    book.model_dump(mode="json")
                    for book in workspace.books
                    if book.source_kind == "PLANNED" or book.status == "IDEA"
                ],
            )
        if selection.descriptions:
            path = output / "Описание-серии-и-книг.md"
            path.write_text(
                "\n".join(
                    [
                        f"# {workspace.name}",
                        "",
                        workspace.promise or workspace.territory,
                        "",
                        *[
                            f"## {book.ordinal}. {book.title}\n\n{book.reader_result}"
                            for book in workspace.books
                        ],
                    ]
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            files.append(path)
        existing: dict[str, list[str]] = {}
        for book in workspace.books:
            book_exports = self.projects.projects_dir / book.book_id / "exports"
            existing[book.book_id] = (
                sorted(str(path) for path in book_exports.rglob("*") if path.is_file())
                if book_exports.is_dir()
                else []
            )
        write_json(
            "manifest.json",
            {
                "series_profile_id": series_profile_id,
                "map_hash": workspace.map.map_hash if workspace.map else None,
                "map_current": workspace.map.current if workspace.map else False,
                "map_approved": workspace.map.approved if workspace.map else False,
                "selected": selected,
                "existing_book_outputs": existing,
                "writing_started": False,
                "note": (
                    "Series export aggregates existing book outputs and metadata; it never starts "
                    "writing another book."
                ),
            },
        )
        return SeriesExportView(
            series_profile_id=series_profile_id,
            map_hash=workspace.map.map_hash if workspace.map else None,
            selected=selected,
            files=[str(path) for path in files],
            output_directory=str(output),
        )

    def require_current_map(self, series_profile_id: str) -> None:
        profile = self.profiles.get_profile(series_profile_id)
        if profile.status != "APPROVED":
            raise SeriesWorkspaceGateError("Series Bible must be approved")
        unapproved = [
            book.title
            for book in self.books(series_profile_id)
            if book.status != "ARCHIVED" and not book.passport_approved
        ]
        if unapproved:
            raise SeriesWorkspaceGateError(
                "Book Passports require Owner approval: " + "; ".join(unapproved[:6])
            )
        result = self.current_map(series_profile_id)
        if result is None or not result.current:
            raise SeriesWorkspaceGateError("series difference map is missing or stale")
        if result.status == "BLOCKING" or not result.approved:
            raise SeriesWorkspaceGateError("series difference map has not passed Owner review")

    def workspaces(self) -> list[SeriesWorkspaceView]:
        result: list[SeriesWorkspaceView] = []
        for profile in self.profiles.list_profiles("SERIES"):
            content = SeriesProfileContent.model_validate(profile.content)
            purpose = content.purpose_positioning
            result.append(
                SeriesWorkspaceView(
                    series_profile_id=profile.profile_id,
                    name=profile.name,
                    profile_status=profile.status,
                    profile_revision=profile.current_revision,
                    audience=purpose,
                    promise=purpose,
                    territory="; ".join(content.thematic_territories),
                    prohibited_territories=content.future_book_reservations,
                    books=self.books(profile.profile_id),
                    map=self.current_map(profile.profile_id),
                )
            )
        return result
