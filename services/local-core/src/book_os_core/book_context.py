from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any, Literal, cast

from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import text
from sqlalchemy.engine import Engine

from .authority import new_ulid
from .authority_types import utc_now
from .db import create_database
from .projects import ProjectService

ProfileKind = Literal["AUTHOR", "SERIES", "STYLE"]
ProfileStatus = Literal["DRAFT", "APPROVED"]

_PROFILE_ID = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")


class BookContextError(RuntimeError):
    pass


class BookContextGateError(BookContextError):
    pass


class ProfileNotFound(BookContextError):
    pass


def _normalized_list(value: list[str]) -> list[str]:
    return [item.strip() for item in value if item.strip()]


class AuthorProfileContent(BaseModel):
    author_name: str = Field(min_length=1, max_length=300)
    expertise_constraints: str = Field(default="", max_length=6000)
    voice_requirements: str = Field(default="", max_length=6000)
    evidence_discipline: str = Field(default="", max_length=6000)
    storytelling_expectations: str = Field(default="", max_length=6000)
    rhythm_syntax: str = Field(default="", max_length=6000)
    irony_directness_temperature: str = Field(default="", max_length=6000)
    prose_prohibitions: list[str] = Field(default_factory=list)
    benchmark_excerpts: list[str] = Field(default_factory=list)

    @field_validator("author_name")
    @classmethod
    def strip_author_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("author name must not be blank")
        return normalized

    @field_validator("prose_prohibitions", "benchmark_excerpts")
    @classmethod
    def normalize_lists(cls, value: list[str]) -> list[str]:
        return _normalized_list(value)


class SeriesProfileContent(BaseModel):
    series_name: str = Field(min_length=1, max_length=300)
    author_profile_id: str = Field(min_length=26, max_length=26)
    purpose_positioning: str = Field(default="", max_length=6000)
    planned_books: list[str] = Field(default_factory=list)
    thematic_territories: list[str] = Field(default_factory=list)
    shared_invariants: list[str] = Field(default_factory=list)
    future_book_reservations: list[str] = Field(default_factory=list)
    cross_book_uniqueness_rules: list[str] = Field(default_factory=list)
    exclusion_dimensions: list[str] = Field(default_factory=list)
    prewriting_overlap_requirements: list[str] = Field(default_factory=list)
    whole_book_audit_requirements: list[str] = Field(default_factory=list)

    @field_validator("series_name")
    @classmethod
    def strip_series_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("series name must not be blank")
        return normalized

    @field_validator(
        "planned_books",
        "thematic_territories",
        "shared_invariants",
        "future_book_reservations",
        "cross_book_uniqueness_rules",
        "exclusion_dimensions",
        "prewriting_overlap_requirements",
        "whole_book_audit_requirements",
    )
    @classmethod
    def normalize_lists(cls, value: list[str]) -> list[str]:
        return _normalized_list(value)


class StyleProfileContent(BaseModel):
    style_name: str = Field(min_length=1, max_length=300)
    author_profile_id: str | None = Field(default=None, min_length=26, max_length=26)
    literary_register: str = Field(default="", max_length=3000)
    authorial_presence: str = Field(default="", max_length=3000)
    directness: str = Field(default="", max_length=3000)
    sentence_paragraph_rhythm: str = Field(default="", max_length=3000)
    scene_density: str = Field(default="", max_length=3000)
    evidence_density: str = Field(default="", max_length=3000)
    analytical_depth: str = Field(default="", max_length=3000)
    irony_humor: str = Field(default="", max_length=3000)
    emotional_temperature: str = Field(default="", max_length=3000)
    practical_instruction_intensity: str = Field(default="", max_length=3000)
    terminology_level: str = Field(default="", max_length=3000)
    prohibited_patterns: list[str] = Field(default_factory=list)
    benchmark_excerpts: list[str] = Field(default_factory=list)

    @field_validator("style_name")
    @classmethod
    def strip_style_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("style name must not be blank")
        return normalized

    @field_validator("prohibited_patterns", "benchmark_excerpts")
    @classmethod
    def normalize_lists(cls, value: list[str]) -> list[str]:
        return _normalized_list(value)


ProfileContent = AuthorProfileContent | SeriesProfileContent | StyleProfileContent


class ProfileRevisionView(BaseModel):
    revision: int
    status: ProfileStatus
    content_hash: str
    content: dict[str, Any]
    created_at: str
    approved_at: str | None = None


class ProfileView(BaseModel):
    profile_id: str
    kind: ProfileKind
    name: str
    status: ProfileStatus
    current_revision: int
    content_hash: str
    content: dict[str, Any]
    created_at: str
    updated_at: str


class ProfileCreateRequest(BaseModel):
    kind: ProfileKind
    content: dict[str, Any]


class ProfileUpdateRequest(BaseModel):
    content: dict[str, Any]


class BookContextUpdateRequest(BaseModel):
    author_profile_id: str
    series_profile_id: str | None = None
    style_profile_id: str
    target_characters: int = Field(gt=0)
    min_characters: int | None = Field(default=None, gt=0)
    max_characters: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def valid_range(self) -> BookContextUpdateRequest:
        if self.min_characters is not None and self.max_characters is not None:
            if self.min_characters > self.max_characters:
                raise ValueError("minimum characters cannot exceed maximum characters")
        if self.min_characters is not None and self.target_characters < self.min_characters:
            raise ValueError("target characters cannot be below minimum characters")
        if self.max_characters is not None and self.target_characters > self.max_characters:
            raise ValueError("target characters cannot exceed maximum characters")
        return self


class BookContextView(BaseModel):
    author_profile: ProfileView | None
    series_profile: ProfileView | None
    style_profile: ProfileView | None
    target_characters: int | None
    min_characters: int | None
    max_characters: int | None
    characters_unit: Literal["characters_with_spaces"] = "characters_with_spaces"
    ready_for_planning: bool


class ProfileRegistry:
    def __init__(self, data_dir: Path) -> None:
        self.path = data_dir / "context-profiles.json"

    @staticmethod
    def _validate_id(profile_id: str) -> None:
        if not _PROFILE_ID.fullmatch(profile_id):
            raise ProfileNotFound("invalid profile ID")

    @staticmethod
    def _canonical_content(content: dict[str, Any]) -> str:
        return json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @classmethod
    def _hash(cls, content: dict[str, Any]) -> str:
        return hashlib.sha256(cls._canonical_content(content).encode("utf-8")).hexdigest()

    @staticmethod
    def _load_model(kind: ProfileKind, content: dict[str, Any]) -> ProfileContent:
        if kind == "AUTHOR":
            return AuthorProfileContent.model_validate(content)
        if kind == "SERIES":
            return SeriesProfileContent.model_validate(content)
        return StyleProfileContent.model_validate(content)

    @staticmethod
    def _profile_name(kind: ProfileKind, content: ProfileContent) -> str:
        if kind == "AUTHOR":
            return cast(AuthorProfileContent, content).author_name
        if kind == "SERIES":
            return cast(SeriesProfileContent, content).series_name
        return cast(StyleProfileContent, content).style_name

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"version": 1, "profiles": {}}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise BookContextError("context profile registry is unreadable") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("profiles"), dict):
            raise BookContextError("context profile registry has invalid structure")
        return payload

    def _write(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(self.path)

    def _record(self, profile_id: str) -> dict[str, Any]:
        self._validate_id(profile_id)
        payload = self._read()
        raw = payload["profiles"].get(profile_id)
        if not isinstance(raw, dict):
            raise ProfileNotFound(f"profile not found: {profile_id}")
        return raw

    def _view_from_revision(
        self,
        profile_id: str,
        record: dict[str, Any],
        revision: dict[str, Any],
    ) -> ProfileView:
        kind = cast(ProfileKind, record["kind"])
        content = cast(dict[str, Any], revision["content"])
        model = self._load_model(kind, content)
        return ProfileView(
            profile_id=profile_id,
            kind=kind,
            name=self._profile_name(kind, model),
            status=cast(ProfileStatus, revision["status"]),
            current_revision=int(revision["revision"]),
            content_hash=str(revision["content_hash"]),
            content=content,
            created_at=str(record["created_at"]),
            updated_at=str(record["updated_at"]),
        )

    def _view(self, profile_id: str, record: dict[str, Any]) -> ProfileView:
        revisions = record.get("revisions")
        if not isinstance(revisions, list) or not revisions:
            raise BookContextError("profile has no revisions")
        current_revision = int(record["current_revision"])
        revision = next(
            (
                item
                for item in revisions
                if isinstance(item, dict) and int(item.get("revision", -1)) == current_revision
            ),
            None,
        )
        if not isinstance(revision, dict):
            raise BookContextError("profile current revision is missing")
        return self._view_from_revision(profile_id, record, revision)

    def list_profiles(self, kind: ProfileKind | None = None) -> list[ProfileView]:
        payload = self._read()
        result: list[ProfileView] = []
        for profile_id, raw in payload["profiles"].items():
            if not isinstance(raw, dict):
                continue
            if kind is not None and raw.get("kind") != kind:
                continue
            result.append(self._view(str(profile_id), raw))
        return sorted(result, key=lambda item: (item.kind, item.name.casefold()))

    def get_profile(self, profile_id: str) -> ProfileView:
        return self._view(profile_id, self._record(profile_id))

    def get_profile_by_hash(self, profile_id: str, content_hash: str) -> ProfileView:
        """Resolve the exact immutable profile revision bound to a book."""
        record = self._record(profile_id)
        revisions = record.get("revisions")
        if not isinstance(revisions, list):
            raise BookContextError("profile has no revisions")
        revision = next(
            (
                item
                for item in revisions
                if isinstance(item, dict) and str(item.get("content_hash", "")) == content_hash
            ),
            None,
        )
        if not isinstance(revision, dict):
            raise ProfileNotFound(f"profile revision not found: {profile_id}@{content_hash[:12]}")
        return self._view_from_revision(profile_id, record, revision)

    def create_profile(self, request: ProfileCreateRequest) -> ProfileView:
        model = self._load_model(request.kind, request.content)
        content = model.model_dump(mode="json")
        profile_id = new_ulid()
        now = utc_now()
        revision = {
            "revision": 1,
            "status": "DRAFT",
            "content_hash": self._hash(content),
            "content": content,
            "created_at": now,
            "approved_at": None,
        }
        payload = self._read()
        payload["profiles"][profile_id] = {
            "kind": request.kind,
            "name": self._profile_name(request.kind, model),
            "current_revision": 1,
            "created_at": now,
            "updated_at": now,
            "revisions": [revision],
        }
        self._write(payload)
        return self.get_profile(profile_id)

    def update_profile(self, profile_id: str, request: ProfileUpdateRequest) -> ProfileView:
        current = self.get_profile(profile_id)
        model = self._load_model(current.kind, request.content)
        content = model.model_dump(mode="json")
        payload = self._read()
        raw = payload["profiles"][profile_id]
        revisions = raw["revisions"]
        revision_number = int(raw["current_revision"]) + 1
        now = utc_now()
        revisions.append(
            {
                "revision": revision_number,
                "status": "DRAFT",
                "content_hash": self._hash(content),
                "content": content,
                "created_at": now,
                "approved_at": None,
            }
        )
        raw["name"] = self._profile_name(current.kind, model)
        raw["current_revision"] = revision_number
        raw["updated_at"] = now
        self._write(payload)
        return self.get_profile(profile_id)

    def approve_profile(self, profile_id: str) -> ProfileView:
        current = self.get_profile(profile_id)
        if current.status == "APPROVED":
            return current
        if current.kind == "SERIES":
            series_content = SeriesProfileContent.model_validate(current.content)
            author = self.get_profile(series_content.author_profile_id)
            if author.kind != "AUTHOR" or author.status != "APPROVED":
                raise BookContextGateError(
                    "Series Profile requires an approved Author Profile before approval"
                )
        if current.kind == "STYLE":
            style_content = StyleProfileContent.model_validate(current.content)
            if style_content.author_profile_id:
                author = self.get_profile(style_content.author_profile_id)
                if author.kind != "AUTHOR" or author.status != "APPROVED":
                    raise BookContextGateError(
                        "author-bound Style Profile requires an approved Author Profile"
                    )
        payload = self._read()
        raw = payload["profiles"][profile_id]
        current_revision = int(raw["current_revision"])
        revision = next(
            item for item in raw["revisions"] if int(item["revision"]) == current_revision
        )
        now = utc_now()
        revision["status"] = "APPROVED"
        revision["approved_at"] = now
        raw["updated_at"] = now
        self._write(payload)
        return self.get_profile(profile_id)


class BookContextService:
    def __init__(self, data_dir: Path) -> None:
        self.projects = ProjectService(data_dir)
        self.profiles = ProfileRegistry(data_dir)

    def _engine(self, book_id: str) -> Engine:
        self.projects.get_project(book_id)
        return create_database(self.projects.projects_dir / book_id / "project.sqlite")

    @staticmethod
    def _approved_kind(profile: ProfileView, kind: ProfileKind) -> None:
        if profile.kind != kind:
            raise BookContextGateError(f"profile {profile.profile_id} is not {kind}")
        if profile.status != "APPROVED":
            raise BookContextGateError(f"{kind} profile must be approved before binding")

    def get_context(self, book_id: str) -> BookContextView:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                row = (
                    connection.execute(
                        text("SELECT * FROM book_context_settings WHERE book_id=:book_id"),
                        {"book_id": book_id},
                    )
                    .mappings()
                    .first()
                )
        finally:
            engine.dispose()
        if row is None:
            return BookContextView(
                author_profile=None,
                series_profile=None,
                style_profile=None,
                target_characters=None,
                min_characters=None,
                max_characters=None,
                ready_for_planning=False,
            )

        author = (
            self.profiles.get_profile_by_hash(
                str(row["author_profile_id"]), str(row["author_profile_hash"])
            )
            if row["author_profile_id"] and row["author_profile_hash"]
            else None
        )
        series = (
            self.profiles.get_profile_by_hash(
                str(row["series_profile_id"]), str(row["series_profile_hash"])
            )
            if row["series_profile_id"] and row["series_profile_hash"]
            else None
        )
        style = (
            self.profiles.get_profile_by_hash(
                str(row["style_profile_id"]), str(row["style_profile_hash"])
            )
            if row["style_profile_id"] and row["style_profile_hash"]
            else None
        )
        ready = bool(
            author is not None
            and author.status == "APPROVED"
            and style is not None
            and style.status == "APPROVED"
            and row["target_characters"]
            and (series is None or series.status == "APPROVED")
        )
        return BookContextView(
            author_profile=author,
            series_profile=series,
            style_profile=style,
            target_characters=cast(int | None, row["target_characters"]),
            min_characters=cast(int | None, row["min_characters"]),
            max_characters=cast(int | None, row["max_characters"]),
            ready_for_planning=ready,
        )

    def save_context(self, book_id: str, request: BookContextUpdateRequest) -> BookContextView:
        author = self.profiles.get_profile(request.author_profile_id)
        self._approved_kind(author, "AUTHOR")
        style = self.profiles.get_profile(request.style_profile_id)
        self._approved_kind(style, "STYLE")
        style_content = StyleProfileContent.model_validate(style.content)
        if style_content.author_profile_id and style_content.author_profile_id != author.profile_id:
            raise BookContextGateError("selected Style Profile belongs to another author")

        series: ProfileView | None = None
        if request.series_profile_id:
            series = self.profiles.get_profile(request.series_profile_id)
            self._approved_kind(series, "SERIES")
            series_content = SeriesProfileContent.model_validate(series.content)
            if series_content.author_profile_id != author.profile_id:
                raise BookContextGateError("selected Series Profile belongs to another author")

        engine = self._engine(book_id)
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO book_context_settings("
                        "book_id,author_profile_id,author_profile_hash,series_profile_id,"
                        "series_profile_hash,style_profile_id,style_profile_hash,target_characters,"
                        "min_characters,max_characters,updated_at) VALUES ("
                        ":book_id,:author_profile_id,:author_profile_hash,:series_profile_id,"
                        ":series_profile_hash,:style_profile_id,:style_profile_hash,:target_characters,"
                        ":min_characters,:max_characters,:updated_at) "
                        "ON CONFLICT(book_id) DO UPDATE SET "
                        "author_profile_id=excluded.author_profile_id,"
                        "author_profile_hash=excluded.author_profile_hash,"
                        "series_profile_id=excluded.series_profile_id,"
                        "series_profile_hash=excluded.series_profile_hash,"
                        "style_profile_id=excluded.style_profile_id,"
                        "style_profile_hash=excluded.style_profile_hash,"
                        "target_characters=excluded.target_characters,"
                        "min_characters=excluded.min_characters,"
                        "max_characters=excluded.max_characters,updated_at=excluded.updated_at"
                    ),
                    {
                        "book_id": book_id,
                        "author_profile_id": author.profile_id,
                        "author_profile_hash": author.content_hash,
                        "series_profile_id": series.profile_id if series else None,
                        "series_profile_hash": series.content_hash if series else None,
                        "style_profile_id": style.profile_id,
                        "style_profile_hash": style.content_hash,
                        "target_characters": request.target_characters,
                        "min_characters": request.min_characters,
                        "max_characters": request.max_characters,
                        "updated_at": utc_now(),
                    },
                )
        finally:
            engine.dispose()
        return self.get_context(book_id)
