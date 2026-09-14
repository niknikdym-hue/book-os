from __future__ import annotations

import base64
import binascii
import hashlib
from html import unescape
import json
from pathlib import Path
import re
import shutil
from typing import Any, Literal, cast
from zipfile import BadZipFile, ZipFile

from docx import Document
from pydantic import BaseModel, Field
from pypdf.errors import PdfReadError
from sqlalchemy import text
from sqlalchemy.engine import Engine

from .authority import canonical_json, new_ulid
from .authority_types import JSONValue, utc_now
from .book_context import (
    ProfileCreateRequest,
    ProfileRegistry,
    ProfileView,
    SeriesProfileContent,
)
from .db import create_database
from .projects import NewBookRequest, ProjectService
from .project_lifecycle import ProjectLifecycleService


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
SeriesBookOrigin = Literal["NEW", "LEGACY_TITLE_ONLY", "CURRENT_REWRITTEN", "IMPORTED"]
SeriesBookLifecycle = Literal[
    "PLANNED",
    "DEFINITION",
    "ARCHITECTURE",
    "WRITING",
    "EDITING",
    "COMPLETED",
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
    origin_kind: SeriesBookOrigin | None = None
    lifecycle: SeriesBookLifecycle = "PLANNED"


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
    origin_kind: SeriesBookOrigin
    lifecycle: SeriesBookLifecycle
    legacy_content_allowed: bool
    current_corpus_eligible: bool
    definition_ready: bool
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
        (
            "Как продавать услуги",
            "Задача клиента, предложение, границы услуги, цена, доказательства и путь до оплаты",
            "CURRENT_REWRITTEN",
            "COMPLETED",
        ),
        (
            "Секреты продвижения услуг психолога в Яндекс Директ",
            "Направления практики, поисковый спрос, деликатные обещания и путь до первой встречи",
            "LEGACY_TITLE_ONLY",
            "PLANNED",
        ),
        (
            "Как продвигать юридические услуги в Яндекс Директ: Практическое руководство",
            "Юридические направления, срочность, география, квалификация заявки и путь до договора",
            "LEGACY_TITLE_ONLY",
            "PLANNED",
        ),
        (
            "Как продать онлайн-курсы",
            "Проверка спроса, достижимый результат, формат, программа, сопровождение и набор",
            "LEGACY_TITLE_ONLY",
            "PLANNED",
        ),
        (
            "Как продавать услуги компаниям: от первого контакта до договора",
            "Решение о покупке внутри компании: участники, пилот, согласование и закупка",
            "NEW",
            "PLANNED",
        ),
        (
            "Как продвигать местные услуги: клиенты в вашем городе и районе",
            "Территориальная доступность: локальный поиск, отзывы, партнёрства, выезд и запись",
            "NEW",
            "PLANNED",
        ),
        (
            "Как продавать дорогие услуги: доверие, доказательства и выбор исполнителя",
            "Высокий риск, долгий выбор, портфолио, диагностика, этапность и обсуждение цены",
            "NEW",
            "PLANNED",
        ),
        (
            "Как возвращать клиентов: повторные продажи и рекомендации в услугах",
            "Отношения после первой продажи: следующий заказ, сопровождение, возврат и рекомендации",
            "NEW",
            "PLANNED",
        ),
    ]

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.projects = ProjectService(data_dir)
        self.profiles = ProfileRegistry(data_dir)
        self.project_lifecycle = ProjectLifecycleService(data_dir)

    def _engine(self, book_id: str) -> Engine:
        self.projects.get_project(book_id)
        return create_database(self.projects.projects_dir / book_id / "project.sqlite")

    def create_series(self, request: SeriesCreateRequest) -> ProfileView:
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
        present = {item.ordinal: item for item in self.books(profile.profile_id)}
        for ordinal, (title, idea, origin_kind, lifecycle) in enumerate(
            self.SERVICES_PROMOTION_BOOKS, start=1
        ):
            if ordinal in present:
                self._reconcile_services_promotion_book(
                    present[ordinal],
                    title,
                    idea,
                    cast(SeriesBookOrigin, origin_kind),
                    cast(SeriesBookLifecycle, lifecycle),
                )
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
                    source_kind=("BOOK_OS" if origin_kind == "CURRENT_REWRITTEN" else "PLANNED"),
                    origin_kind=cast(SeriesBookOrigin, origin_kind),
                    lifecycle=cast(SeriesBookLifecycle, lifecycle),
                ),
            )
        return next(
            item for item in self.workspaces() if item.series_profile_id == profile.profile_id
        )

    def _reconcile_services_promotion_book(
        self,
        book: SeriesBookView,
        title: str,
        idea: str,
        origin_kind: SeriesBookOrigin,
        lifecycle: SeriesBookLifecycle,
    ) -> None:
        """Repair the known preset metadata without deleting any owner files."""
        del idea  # Existing owner-edited passport content is never overwritten by preset repair.
        if (
            book.ordinal > 1
            and book.origin_kind in {"LEGACY_TITLE_ONLY", "NEW"}
            and book.lifecycle != "PLANNED"
        ):
            # A started project is real work; preset repair must never rewind it to planned.
            return
        expected_source = "BOOK_OS" if origin_kind == "CURRENT_REWRITTEN" else "PLANNED"
        expected_status = "READY" if lifecycle == "COMPLETED" else "IDEA"
        if (
            book.title == title
            and book.origin_kind == origin_kind
            and book.lifecycle == lifecycle
            and not book.legacy_content_allowed
            and book.source_kind == expected_source
            and book.status == expected_status
        ):
            return
        engine = self._engine(book.book_id)
        now = utc_now()
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "UPDATE book_projects SET working_title=:title,updated_at=:updated "
                        "WHERE book_id=:book"
                    ),
                    {"title": title, "updated": now, "book": book.book_id},
                )
                connection.execute(
                    text(
                        "UPDATE series_books SET origin_kind=:origin,"
                        "lifecycle=:lifecycle,legacy_content_allowed=0,source_kind=:source,"
                        "status=:status,updated_at=:updated WHERE series_book_id=:membership"
                    ),
                    {
                        "origin": origin_kind,
                        "lifecycle": lifecycle,
                        "source": "BOOK_OS" if origin_kind == "CURRENT_REWRITTEN" else "PLANNED",
                        "status": "READY" if lifecycle == "COMPLETED" else "IDEA",
                        "updated": now,
                        "membership": book.series_book_id,
                    },
                )
        finally:
            engine.dispose()
        manifest_path = self.projects.projects_dir / book.book_id / "project-manifest.json"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["working_title"] = title
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                encoding="utf-8",
            )
        except (OSError, json.JSONDecodeError):
            # The database remains authoritative; do not destroy a malformed owner manifest.
            pass

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
        origin_kind = (
            request.origin_kind
            or {
                "BOOK_OS": "NEW",
                "IMPORTED": "IMPORTED",
                "PLANNED": "NEW",
            }[request.source_kind]
        )
        now = utc_now()
        engine = self._engine(project.book_id)
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO series_books(series_book_id,series_profile_id,book_id,ordinal,"
                        "unique_idea,reader_problem,reader_result,unique_mechanism,excluded_topics_json,"
                        "source_kind,status,origin_kind,lifecycle,legacy_content_allowed,"
                        "created_at,updated_at) VALUES (:id,:series,:book,:ordinal,"
                        ":idea,:problem,:result,:mechanism,:excluded,:source,:status,:origin,"
                        ":lifecycle,:legacy_allowed,:created,:updated)"
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
                        "status": "READY" if request.lifecycle == "COMPLETED" else "IDEA",
                        "origin": origin_kind,
                        "lifecycle": request.lifecycle,
                        "legacy_allowed": (
                            request.source_kind == "IMPORTED" and origin_kind == "IMPORTED"
                        ),
                        "created": now,
                        "updated": now,
                    },
                )
        finally:
            engine.dispose()
        return next(
            item for item in self.books(series_profile_id) if item.book_id == project.book_id
        )

    def bind_existing_book(
        self,
        series_profile_id: str,
        book_id: str,
        *,
        idea: str,
    ) -> SeriesBookView:
        """Idempotently bind a normal Create Book project to an exact existing series.

        When its title matches a planned title-only/new placeholder, that placeholder is archived
        and superseded without copying manuscript material. Otherwise a new final ordinal is used.
        """
        profile = self.profiles.get_profile(series_profile_id)
        if profile.kind != "SERIES" or profile.status != "APPROVED":
            raise SeriesWorkspaceGateError("Series Bible must be approved before binding a book")
        project = self.projects.get_project(book_id)
        memberships = [
            item
            for candidate in self.profiles.list_profiles("SERIES")
            for item in self.books(candidate.profile_id)
            if item.book_id == book_id
        ]
        if memberships:
            if len(memberships) != 1 or memberships[0].series_profile_id != series_profile_id:
                raise SeriesWorkspaceGateError("book already belongs to another explicit series")
            return memberships[0]

        books = self.books(series_profile_id)
        title_matches = [
            item
            for item in books
            if item.title.strip().casefold() == project.working_title.strip().casefold()
        ]
        if len(title_matches) > 1:
            raise SeriesWorkspaceGateError(
                "series title is ambiguous; choose the exact series book"
            )
        placeholder = title_matches[0] if title_matches else None
        if placeholder is not None and (
            placeholder.lifecycle != "PLANNED"
            or placeholder.origin_kind not in {"LEGACY_TITLE_ONLY", "NEW"}
        ):
            raise SeriesWorkspaceGateError(
                "an active series book already uses this title; choose it instead of creating a duplicate"
            )

        ordinal = (
            placeholder.ordinal
            if placeholder is not None
            else max((item.ordinal for item in books), default=0) + 1
        )
        unique_idea = (
            "BOOK OS разрабатывает новую концепцию с нуля по границам Series Bible"
            if placeholder is not None and placeholder.origin_kind == "LEGACY_TITLE_ONLY"
            else idea.strip()
        )
        reader_problem = (
            "Определяется заново на этапе подтверждения концепции"
            if placeholder is not None
            else idea.strip()
        )
        reader_result = (
            "Определяется заново на этапе Book Definition"
            if placeholder is not None
            else f"Практический результат по задаче: {idea.strip()}"
        )
        mechanism = (
            "Определяется заново; материалы других книг не являются шаблоном"
            if placeholder is not None
            else "Будет определён подтверждённой концепцией и Book Definition"
        )
        excluded = placeholder.excluded_topics if placeholder is not None else []
        origin = placeholder.origin_kind if placeholder is not None else "NEW"
        now = utc_now()
        engine = self._engine(book_id)
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO series_books(series_book_id,series_profile_id,book_id,ordinal,"
                        "unique_idea,reader_problem,reader_result,unique_mechanism,excluded_topics_json,"
                        "source_kind,status,origin_kind,lifecycle,legacy_content_allowed,"
                        "created_at,updated_at) VALUES (:id,:series,:book,:ordinal,:idea,:problem,"
                        ":result,:mechanism,:excluded,:source,'DEFINITION',:origin,'DEFINITION',0,"
                        ":created,:updated)"
                    ),
                    {
                        "id": new_ulid(),
                        "series": series_profile_id,
                        "book": book_id,
                        "ordinal": ordinal,
                        "idea": unique_idea,
                        "problem": reader_problem,
                        "result": reader_result,
                        "mechanism": mechanism,
                        "excluded": json.dumps(excluded, ensure_ascii=False),
                        "source": "PLANNED" if placeholder is not None else "BOOK_OS",
                        "origin": origin,
                        "created": now,
                        "updated": now,
                    },
                )
        finally:
            engine.dispose()

        if placeholder is not None:
            placeholder_engine = self._engine(placeholder.book_id)
            try:
                with placeholder_engine.begin() as connection:
                    connection.execute(
                        text(
                            "UPDATE series_books SET superseded_by_book_id=:fresh,lifecycle='ARCHIVED',"
                            "status='ARCHIVED',updated_at=:updated WHERE series_book_id=:membership"
                        ),
                        {
                            "fresh": book_id,
                            "updated": now,
                            "membership": placeholder.series_book_id,
                        },
                    )
            finally:
                placeholder_engine.dispose()
            self.project_lifecycle.archive(placeholder.book_id)

        return next(item for item in self.books(series_profile_id) if item.book_id == book_id)

    def books(self, series_profile_id: str) -> list[SeriesBookView]:
        result: list[SeriesBookView] = []
        for summary in self.projects.list_projects():
            project = self.projects.get_project(summary.book_id)
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
                    if row is None or row["superseded_by_book_id"] is not None:
                        continue
                    contract_view = project.book_contract
                    definition_ready = (
                        contract_view is not None and contract_view.authority_status == "APPROVED"
                    )
                    contract = contract_view.content if definition_ready and contract_view else {}
                    unique_idea = str(contract.get("unique_angle", row["unique_idea"]))
                    reader_problem = str(contract.get("reader_problem", row["reader_problem"]))
                    reader_result = str(contract.get("central_promise", row["reader_result"]))
                    unique_mechanism = str(contract.get("central_thesis", row["unique_mechanism"]))
                    excluded_topics = cast(
                        list[str],
                        contract.get(
                            "explicit_exclusions",
                            json.loads(str(row["excluded_topics_json"])),
                        ),
                    )
                    passport_material = {
                        "title": project.working_title,
                        "ordinal": int(row["ordinal"]),
                        "unique_idea": unique_idea,
                        "reader_problem": reader_problem,
                        "reader_result": reader_result,
                        "unique_mechanism": unique_mechanism,
                        "excluded_topics": excluded_topics,
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
                        unique_idea=unique_idea,
                        reader_problem=reader_problem,
                        reader_result=reader_result,
                        unique_mechanism=unique_mechanism,
                        excluded_topics=excluded_topics,
                        source_kind=str(row["source_kind"]),
                        status=cast(SeriesBookStatus, str(row["status"])),
                        origin_kind=cast(SeriesBookOrigin, str(row["origin_kind"])),
                        lifecycle=cast(SeriesBookLifecycle, str(row["lifecycle"])),
                        legacy_content_allowed=bool(row["legacy_content_allowed"]),
                        current_corpus_eligible=(
                            str(row["origin_kind"]) == "CURRENT_REWRITTEN"
                            and str(row["lifecycle"]) == "COMPLETED"
                        ),
                        definition_ready=definition_ready,
                        passport_hash=passport_hash,
                        passport_approved=passport_approved,
                        imported_sources=[]
                        if str(row["origin_kind"]) == "LEGACY_TITLE_ONLY"
                        else [
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

    def start_fresh_book(self, series_profile_id: str, book_id: str) -> SeriesBookView:
        """Create a clean project for a planned/rewrite entry without copying legacy payload."""
        book = next(
            (item for item in self.books(series_profile_id) if item.book_id == book_id), None
        )
        if book is None:
            raise SeriesWorkspaceError("book does not belong to this series")
        if book.lifecycle != "PLANNED" or book.origin_kind not in {"LEGACY_TITLE_ONLY", "NEW"}:
            raise SeriesWorkspaceGateError("only a planned new or title-only book can be started")
        if book.origin_kind == "LEGACY_TITLE_ONLY":
            idea = "BOOK OS предложит новую концепцию с нуля по границам Series Bible"
            reader_problem = "Определяется заново на этапе Book Definition"
            reader_result = "Определяется заново на этапе Book Definition"
            mechanism = "Определяется заново; старая структура и методики запрещены"
            excluded = []
        else:
            idea = book.unique_idea
            reader_problem = book.reader_problem
            reader_result = book.reader_result
            mechanism = book.unique_mechanism
            excluded = book.excluded_topics
        fresh = self.add_book(
            series_profile_id,
            SeriesBookCreateRequest(
                title=book.title,
                ordinal=book.ordinal,
                unique_idea=idea,
                reader_problem=reader_problem,
                reader_result=reader_result,
                unique_mechanism=mechanism,
                excluded_topics=excluded,
                source_kind="PLANNED",
                origin_kind=book.origin_kind,
                lifecycle="DEFINITION",
            ),
        )
        engine = self._engine(book.book_id)
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "UPDATE series_books SET superseded_by_book_id=:fresh,lifecycle='ARCHIVED',"
                        "status='ARCHIVED',updated_at=:updated WHERE series_book_id=:membership"
                    ),
                    {
                        "fresh": fresh.book_id,
                        "updated": utc_now(),
                        "membership": book.series_book_id,
                    },
                )
        finally:
            engine.dispose()
        self.project_lifecycle.archive(book.book_id)
        return fresh

    def generation_context(self, book_id: str) -> dict[str, Any] | None:
        """Return bounded series context; manuscript text is never a planning input here."""
        target: SeriesBookView | None = None
        profile_id: str | None = None
        for profile in self.profiles.list_profiles("SERIES"):
            candidate = next(
                (item for item in self.books(profile.profile_id) if item.book_id == book_id), None
            )
            if candidate is not None:
                if target is not None:
                    raise SeriesWorkspaceGateError("book belongs to more than one explicit series")
                target = candidate
                profile_id = profile.profile_id
        if target is None or profile_id is None:
            return None
        current_corpus = [
            {
                "book_id": item.book_id,
                "title": item.title,
                "territory": item.unique_idea,
                "passport_hash": item.passport_hash,
                "usage_policy": "NEGATIVE_REFERENCE_FOR_ANTI_DUPLICATION_ONLY",
            }
            for item in self.books(profile_id)
            if item.book_id != book_id and item.current_corpus_eligible
        ]
        planned_boundaries = [
            {
                "book_id": item.book_id,
                "title": item.title,
                "reserved_territory": item.unique_idea,
                "reader_problem": item.reader_problem,
                "usage_policy": "BOUNDARY_ONLY_NOT_GENERATION_TEMPLATE",
            }
            for item in self.books(profile_id)
            if item.book_id != book_id and item.lifecycle == "PLANNED"
        ]
        return {
            "series_profile_id": profile_id,
            "origin_kind": target.origin_kind,
            "lifecycle": target.lifecycle,
            "legacy_title": target.title if target.origin_kind == "LEGACY_TITLE_ONLY" else None,
            "allowed_legacy_fields": ["title"] if target.origin_kind == "LEGACY_TITLE_ONLY" else [],
            "legacy_payload_allowed": target.legacy_content_allowed,
            "legacy_manuscript": None,
            "legacy_outline": None,
            "legacy_chapters": None,
            "legacy_examples": None,
            "legacy_sources": None,
            "current_corpus": current_corpus,
            "current_corpus_usage": "ANTI_DUPLICATION_NOT_GENERATION_TEMPLATE",
            "planned_book_boundaries": planned_boundaries,
        }

    def approve_book_passport(
        self,
        series_profile_id: str,
        book_id: str,
        passport_hash: str,
        reason: str,
        *,
        actor: str = "HUMAN:OWNER",
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
                        "(:id,:series,:book,'BOOK_PASSPORT',:hash,'APPROVED',:reason,:actor,:created)"
                    ),
                    {
                        "id": new_ulid(),
                        "series": series_profile_id,
                        "book": book_id,
                        "hash": passport_hash,
                        "reason": reason.strip() or "Owner approved the current Book Passport",
                        "actor": actor,
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
        if membership.origin_kind == "LEGACY_TITLE_ONLY":
            raise SeriesWorkspaceGateError(
                "legacy-title-only books accept the title only; start a new version instead"
            )
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

    def _architecture_material(self, book_id: str) -> list[dict[str, str]]:
        project = self.projects.get_project(book_id)
        if project.architecture is None:
            return []
        return [
            {
                "title": str(chapter.get("title", "")),
                "purpose": str(chapter.get("purpose", "")),
                "new_contribution": str(chapter.get("new_contribution", "")),
            }
            for part in project.architecture.content.get("parts", [])
            if isinstance(part, dict)
            for chapter in part.get("chapters", [])
            if isinstance(chapter, dict)
        ]

    def _map_hash(self, series_profile_id: str, books: list[SeriesBookView]) -> str:
        profile = self.profiles.get_profile(series_profile_id)
        material = {
            "profile_hash": profile.content_hash,
            "books": [book.model_dump(mode="json") for book in books],
            "architectures": {
                book.book_id: self._architecture_material(book.book_id) for book in books
            },
            "sources": {
                book.book_id: sorted(
                    row["content_hash"]
                    for row in (
                        []
                        if book.origin_kind == "LEGACY_TITLE_ONLY"
                        else self._source_rows(book.book_id)
                    )
                )
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
            for source in (
                [] if book.origin_kind == "LEGACY_TITLE_ONLY" else self._source_rows(book.book_id)
            ):
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
                left_sources = (
                    []
                    if left.origin_kind == "LEGACY_TITLE_ONLY"
                    else self._source_rows(left.book_id)
                )
                right_sources = (
                    []
                    if right.origin_kind == "LEGACY_TITLE_ONLY"
                    else self._source_rows(right.book_id)
                )
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

                left_architecture = self._architecture_material(left.book_id)
                right_architecture = self._architecture_material(right.book_id)
                if left_architecture and right_architecture:
                    left_sequence = [
                        _normalized_text(str(item["title"])) for item in left_architecture
                    ]
                    right_sequence = [
                        _normalized_text(str(item["title"])) for item in right_architecture
                    ]
                    if left_sequence == right_sequence:
                        findings.append(
                            {
                                "finding_id": new_ulid(),
                                "book_id": left.book_id,
                                "compared_book_id": right.book_id,
                                "dimension": "ARCHITECTURE",
                                "severity": "BLOCKING",
                                "evidence": {
                                    "identical_chapter_sequence": left_sequence,
                                    "comparison_basis": "CURRENT_BOOK_ARCHITECTURE",
                                },
                            }
                        )
                    left_functions = _tokens(
                        " ".join(
                            f"{item['purpose']} {item['new_contribution']}"
                            for item in left_architecture
                        )
                    )
                    right_functions = _tokens(
                        " ".join(
                            f"{item['purpose']} {item['new_contribution']}"
                            for item in right_architecture
                        )
                    )
                    function_union = left_functions | right_functions
                    function_score = (
                        len(left_functions & right_functions) / len(function_union)
                        if function_union
                        else 0.0
                    )
                    if function_score >= 0.65 and left_sequence != right_sequence:
                        findings.append(
                            {
                                "finding_id": new_ulid(),
                                "book_id": left.book_id,
                                "compared_book_id": right.book_id,
                                "dimension": "ARCHITECTURE",
                                "severity": "BLOCKING" if function_score >= 0.8 else "ATTENTION",
                                "evidence": {
                                    "function_token_jaccard": round(function_score, 4),
                                    "shared_terms": sorted(left_functions & right_functions)[:30],
                                    "comparison_basis": "CURRENT_BOOK_ARCHITECTURE",
                                },
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
                    persisted_evidence = {
                        **item["evidence"],
                        "subject_book_id": item["book_id"],
                        "compared_book_id": item["compared_book_id"],
                    }
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
                            # The map is stored in the anchor project's database. Its local
                            # book_projects FK cannot point at another project's database, so
                            # exact pair identities are retained in evidence and restored below.
                            "book": anchor,
                            "compared": item["compared_book_id"],
                            "dimension": item["dimension"],
                            "severity": item["severity"],
                            "evidence": json.dumps(persisted_evidence, ensure_ascii=False),
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

    def approve_map(
        self,
        series_profile_id: str,
        map_hash: str,
        reason: str,
        *,
        actor: str = "HUMAN:OWNER",
    ) -> SeriesMapView:
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
                        ":book,'OVERLAP_MAP',:hash,'APPROVED',:reason,:actor,:created)"
                    ),
                    {
                        "id": new_ulid(),
                        "series": series_profile_id,
                        "book": anchor,
                        "hash": map_hash,
                        "reason": reason.strip()
                        or "Owner approved the current series difference map",
                        "actor": actor,
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
                findings = []
                for row in connection.execute(
                    text(
                        "SELECT * FROM series_similarity_findings WHERE map_hash=:hash "
                        "ORDER BY created_at,finding_id"
                    ),
                    {"hash": str(run["map_hash"])},
                ).mappings():
                    evidence = json.loads(str(row["evidence_json"]))
                    findings.append(
                        {
                            "finding_id": str(row["finding_id"]),
                            "book_id": str(evidence.get("subject_book_id", row["book_id"])),
                            "compared_book_id": str(
                                evidence.get("compared_book_id", row["compared_book_id"])
                            ),
                            "dimension": str(row["dimension"]),
                            "severity": str(row["severity"]),
                            "status": str(row["status"]),
                            "evidence": evidence,
                        }
                    )
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
                        "UPDATE series_books SET status='ARCHIVED',lifecycle='ARCHIVED',"
                        "updated_at=:updated "
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
                    book.book_id: []
                    if book.origin_kind == "LEGACY_TITLE_ONLY"
                    else [
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
        packaged: dict[str, list[str]] = {}
        missing: dict[str, list[str]] = {}
        requested_assets = any(
            (
                selection.complete_manuscripts,
                selection.editorial_and_litres,
                selection.audio_editions,
                selection.visual_materials,
            )
        )
        packaged_asset_count = 0
        category_kinds = {
            "complete_manuscripts": {"FULL_MANUSCRIPT_DOCX"},
            "editorial_and_litres": {
                "LITRES_EBOOK_DOCX",
                "READING_PDF",
                "EPUB",
                "PUBLISHER_PACK",
            },
            "audio_editions": {
                "AUDIO_READING_DOCX",
                "AUDIO_LITRES_DOCX",
                "VOICE_TEXT_TXT",
                "PRONUNCIATION_DICTIONARY",
                "AUDIO_PRODUCTION_HANDOFF",
            },
        }
        for book in workspace.books:
            book_exports = self.projects.projects_dir / book.book_id / "exports"
            engine = self._engine(book.book_id)
            try:
                with engine.connect() as connection:
                    rows = list(
                        connection.execute(
                            text(
                                "SELECT a.output_kind,a.relative_path FROM auto_book_output_artifacts a "
                                "JOIN auto_book_runtime_runs r ON r.run_id=a.run_id "
                                "WHERE r.book_id=:book_id AND a.status='READY' "
                                "ORDER BY a.created_at,a.artifact_id"
                            ),
                            {"book_id": book.book_id},
                        ).mappings()
                    )
            finally:
                engine.dispose()
            visual_paths = (
                [path for path in book_exports.rglob("*.png") if output not in path.parents]
                if book_exports.is_dir()
                else []
            )
            if not rows and not visual_paths:
                # Planned or title-only books have no derivatives yet and belong in the series
                # plan, not as false missing-file errors in a package of completed books.
                packaged[book.book_id] = []
                continue
            requested_categories = [
                category for category in category_kinds if bool(getattr(selection, category))
            ]
            copied_for_book: list[str] = []
            missing_for_book: list[str] = []
            destination = output / "books" / f"{book.ordinal:03d}-{book.book_id}"
            for category in requested_categories:
                category_rows = [
                    row for row in rows if row["output_kind"] in category_kinds[category]
                ]
                if not category_rows:
                    missing_for_book.append(category)
                    continue
                for row in category_rows:
                    source = self.projects.projects_dir / book.book_id / str(row["relative_path"])
                    if not source.is_file():
                        missing_for_book.append(f"{category}:{row['output_kind']}")
                        continue
                    category_destination = destination / category / str(row["output_kind"])
                    category_destination.mkdir(parents=True, exist_ok=True)
                    target = category_destination / source.name
                    shutil.copy2(source, target)
                    files.append(target)
                    copied_for_book.append(target.relative_to(output).as_posix())
                    packaged_asset_count += 1
            if selection.visual_materials:
                if not visual_paths:
                    missing_for_book.append("visual_materials")
                for source in visual_paths:
                    visual_destination = destination / "visual_materials"
                    visual_destination.mkdir(parents=True, exist_ok=True)
                    target = visual_destination / source.name
                    shutil.copy2(source, target)
                    files.append(target)
                    copied_for_book.append(target.relative_to(output).as_posix())
                    packaged_asset_count += 1
            packaged[book.book_id] = sorted(set(copied_for_book))
            if missing_for_book:
                missing[book.book_id] = sorted(set(missing_for_book))
        if missing:
            raise SeriesWorkspaceGateError(
                "selected series derivatives are missing: "
                + json.dumps(missing, ensure_ascii=False, sort_keys=True)
            )
        if requested_assets and packaged_asset_count == 0:
            raise SeriesWorkspaceGateError("selected series derivatives are not ready yet")
        write_json(
            "manifest.json",
            {
                "series_profile_id": series_profile_id,
                "map_hash": workspace.map.map_hash if workspace.map else None,
                "map_current": workspace.map.current if workspace.map else False,
                "map_approved": workspace.map.approved if workspace.map else False,
                "selected": selected,
                "packaged_book_outputs": packaged,
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
            if book.lifecycle in {"DEFINITION", "ARCHITECTURE", "WRITING", "EDITING"}
            and not book.passport_approved
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
            if profile.name == self.SERVICES_PROMOTION_NAME:
                by_ordinal = {item.ordinal: item for item in self.books(profile.profile_id)}
                for ordinal, (title, idea, origin_kind, lifecycle) in enumerate(
                    self.SERVICES_PROMOTION_BOOKS, start=1
                ):
                    if ordinal in by_ordinal:
                        self._reconcile_services_promotion_book(
                            by_ordinal[ordinal],
                            title,
                            idea,
                            cast(SeriesBookOrigin, origin_kind),
                            cast(SeriesBookLifecycle, lifecycle),
                        )
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
