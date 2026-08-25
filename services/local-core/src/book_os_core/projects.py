from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
import re
from typing import Annotated, Any, Literal, cast

from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import text
from sqlalchemy.engine import Engine

from .authority import AuthorityService, InvalidAuthorityOperation, new_ulid
from .authority_types import JSONValue, utc_now
from .db import create_database

BUSINESS_SUBTYPES = (
    "Entrepreneurship",
    "Strategy",
    "Leadership",
    "Management",
    "Teams & Culture",
    "Marketing & Brand",
    "Sales & Negotiation",
    "Finance & Investing",
    "Product, Innovation & Technology",
    "Career & Professional Development",
)

_BOOK_ID = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")


class ProjectError(RuntimeError):
    pass


class ProjectNotFound(ProjectError):
    pass


class ProjectGateError(ProjectError):
    pass


NonEmpty = Annotated[str, Field(min_length=1, max_length=4000)]


class NewBookRequest(BaseModel):
    working_title: Annotated[str, Field(min_length=1, max_length=300)]
    mode: Literal["BOOK_FROM_ZERO"] = "BOOK_FROM_ZERO"
    domain: Literal["BUSINESS_NONFICTION"] = "BUSINESS_NONFICTION"
    primary_subtype: str
    secondary_subtype: str | None = None
    profile_version: str = "business-nonfiction-v0.1"

    @field_validator("working_title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("working title must not be blank")
        return value

    @field_validator("primary_subtype")
    @classmethod
    def valid_primary(cls, value: str) -> str:
        if value not in BUSINESS_SUBTYPES:
            raise ValueError("unsupported Business Nonfiction subtype")
        return value

    @field_validator("secondary_subtype")
    @classmethod
    def valid_secondary(cls, value: str | None) -> str | None:
        if value is not None and value not in BUSINESS_SUBTYPES:
            raise ValueError("unsupported secondary Business Nonfiction subtype")
        return value

    @model_validator(mode="after")
    def distinct_subtypes(self) -> NewBookRequest:
        if self.secondary_subtype == self.primary_subtype:
            raise ValueError("secondary subtype must differ from primary subtype")
        return self


class BookContractPayload(BaseModel):
    reader: NonEmpty
    reader_problem: NonEmpty
    central_promise: NonEmpty
    central_thesis: NonEmpty
    unique_angle: NonEmpty
    reader_trajectory: NonEmpty
    explicit_exclusions: list[str] = Field(min_length=1)
    evidence_policy: NonEmpty
    voice_genre_constraints: NonEmpty
    readiness_criteria: list[str] = Field(min_length=1)

    @field_validator("explicit_exclusions", "readiness_criteria")
    @classmethod
    def nonblank_list(cls, value: list[str]) -> list[str]:
        normalized = [item.strip() for item in value if item.strip()]
        if not normalized:
            raise ValueError("at least one non-blank item is required")
        return normalized


class ArchitectureChapter(BaseModel):
    chapter_id: str | None = None
    title: Annotated[str, Field(min_length=1, max_length=300)]
    purpose: NonEmpty
    new_contribution: NonEmpty
    dependencies: list[str] = Field(default_factory=list)
    transition: str = ""


class ArchitecturePart(BaseModel):
    title: Annotated[str, Field(min_length=1, max_length=300)]
    purpose: NonEmpty
    chapters: list[ArchitectureChapter] = Field(min_length=1)


class BookArchitecturePayload(BaseModel):
    parts: list[ArchitecturePart] = Field(min_length=1)
    intellectual_progression: NonEmpty
    concept_allocation: NonEmpty
    promise_thesis_coverage: NonEmpty
    major_transitions: NonEmpty

    @model_validator(mode="after")
    def unique_chapter_ids(self) -> BookArchitecturePayload:
        ids = [
            chapter.chapter_id
            for part in self.parts
            for chapter in part.chapters
            if chapter.chapter_id is not None
        ]
        if len(ids) != len(set(ids)):
            raise ValueError("chapter IDs must be unique")
        return self


class ChapterContractPayload(BaseModel):
    chapter_purpose: NonEmpty
    new_contribution: NonEmpty
    reader_prior_state: NonEmpty
    reader_after_state: NonEmpty
    required_claims: list[str] = Field(min_length=1)
    required_or_permitted_research: list[str] = Field(min_length=1)
    required_scenes_examples: list[str] = Field(min_length=1)
    reserved_elsewhere: list[str] = Field(default_factory=list)
    opening_requirements: NonEmpty
    ending_requirements: NonEmpty
    transition_requirements: NonEmpty

    @field_validator(
        "required_claims",
        "required_or_permitted_research",
        "required_scenes_examples",
        "reserved_elsewhere",
    )
    @classmethod
    def normalize_lists(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]

    @model_validator(mode="after")
    def required_lists_not_empty(self) -> ChapterContractPayload:
        for name in (
            "required_claims",
            "required_or_permitted_research",
            "required_scenes_examples",
        ):
            if not getattr(self, name):
                raise ValueError(f"{name} requires at least one non-blank item")
        return self


class DocumentView(BaseModel):
    entity_id: str
    revision_id: str
    status: str
    authority_revision_id: str
    authority_status: str
    content: dict[str, Any]


class ChapterView(BaseModel):
    chapter_id: str
    ordinal: int
    working_title: str
    architecture_role: str
    workflow_state: str
    chapter_contract: DocumentView | None = None


class ProjectSummary(BaseModel):
    book_id: str
    working_title: str
    primary_subtype: str
    secondary_subtype: str | None
    workflow_stage: str


class ProjectView(ProjectSummary):
    mode: str
    domain: str
    profile_version: str
    book_contract: DocumentView | None
    architecture: DocumentView | None
    chapters: list[ChapterView]


def _json_payload(model: BaseModel) -> dict[str, JSONValue]:
    return cast(dict[str, JSONValue], model.model_dump(mode="json"))


class ProjectService:
    def __init__(self, data_dir: Path):
        self.projects_dir = data_dir / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def _project_dir(self, book_id: str) -> Path:
        if not _BOOK_ID.fullmatch(book_id):
            raise ProjectNotFound("invalid book project ID")
        return self.projects_dir / book_id

    def _database_path(self, book_id: str) -> Path:
        path = self._project_dir(book_id) / "project.sqlite"
        if not path.is_file():
            raise ProjectNotFound(f"book project not found: {book_id}")
        return path

    def _engine(self, book_id: str) -> Engine:
        return create_database(self._database_path(book_id))

    def create_project(self, request: NewBookRequest) -> ProjectView:
        book_id = new_ulid()
        project_dir = self.projects_dir / book_id
        project_dir.mkdir(parents=True, exist_ok=False)
        db_path = project_dir / "project.sqlite"
        engine = create_database(db_path)
        now = utc_now()
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO book_projects("
                        "book_id,working_title,mode,domain,primary_subtype,secondary_subtype,"
                        "profile_version,workflow_stage,created_at,updated_at) "
                        "VALUES (:book_id,:working_title,:mode,:domain,:primary_subtype,"
                        ":secondary_subtype,:profile_version,'BOOK DEFINITION',:created_at,:updated_at)"
                    ),
                    {
                        "book_id": book_id,
                        "working_title": request.working_title,
                        "mode": request.mode,
                        "domain": request.domain,
                        "primary_subtype": request.primary_subtype,
                        "secondary_subtype": request.secondary_subtype,
                        "profile_version": request.profile_version,
                        "created_at": now,
                        "updated_at": now,
                    },
                )
            manifest = {
                "book_id": book_id,
                "working_title": request.working_title,
                "mode": request.mode,
                "domain": request.domain,
                "primary_subtype": request.primary_subtype,
                "secondary_subtype": request.secondary_subtype,
                "profile_version": request.profile_version,
                "created_at": now,
                "database": "project.sqlite",
            }
            (project_dir / "project-manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                encoding="utf-8",
            )
        except Exception:
            engine.dispose()
            for child in project_dir.iterdir():
                child.unlink(missing_ok=True)
            project_dir.rmdir()
            raise
        finally:
            engine.dispose()
        return self.get_project(book_id)

    def list_projects(self) -> list[ProjectSummary]:
        projects: list[ProjectSummary] = []
        for manifest in sorted(self.projects_dir.glob("*/project-manifest.json")):
            try:
                book_id = manifest.parent.name
                project = self.get_project(book_id)
            except (OSError, ValueError, ProjectError):
                continue
            projects.append(ProjectSummary(**project.model_dump()))
        return sorted(projects, key=lambda item: item.working_title.casefold())

    def get_project(self, book_id: str) -> ProjectView:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                project = (
                    connection.execute(
                        text("SELECT * FROM book_projects WHERE book_id=:book_id"),
                        {"book_id": book_id},
                    )
                    .mappings()
                    .one_or_none()
                )
                if project is None:
                    raise ProjectNotFound(f"book project not found: {book_id}")
                chapter_rows = list(
                    connection.execute(
                        text(
                            "SELECT * FROM chapters WHERE book_id=:book_id "
                            "AND workflow_state != 'SUPERSEDED' ORDER BY ordinal"
                        ),
                        {"book_id": book_id},
                    ).mappings()
                )
            authority = AuthorityService(engine)
            book_contract = self._document_view(
                engine, authority, cast(str | None, project["book_contract_entity_id"])
            )
            architecture = self._document_view(
                engine, authority, cast(str | None, project["architecture_entity_id"])
            )
            chapters = [
                ChapterView(
                    chapter_id=cast(str, row["chapter_id"]),
                    ordinal=cast(int, row["ordinal"]),
                    working_title=cast(str, row["working_title"]),
                    architecture_role=cast(str, row["architecture_role"]),
                    workflow_state=cast(str, row["workflow_state"]),
                    chapter_contract=self._document_view(
                        engine,
                        authority,
                        cast(str | None, row["chapter_contract_entity_id"]),
                    ),
                )
                for row in chapter_rows
            ]
            return ProjectView(
                book_id=cast(str, project["book_id"]),
                working_title=cast(str, project["working_title"]),
                mode=cast(str, project["mode"]),
                domain=cast(str, project["domain"]),
                primary_subtype=cast(str, project["primary_subtype"]),
                secondary_subtype=cast(str | None, project["secondary_subtype"]),
                profile_version=cast(str, project["profile_version"]),
                workflow_stage=cast(str, project["workflow_stage"]),
                book_contract=book_contract,
                architecture=architecture,
                chapters=chapters,
            )
        finally:
            engine.dispose()

    def save_book_contract(self, book_id: str, payload: BookContractPayload) -> ProjectView:
        self._save_project_document(
            book_id,
            project_column="book_contract_entity_id",
            entity_type="book.contract",
            schema_name="book.contract.v0.1",
            payload=_json_payload(payload),
        )
        return self.get_project(book_id)

    def approve_book_contract(self, book_id: str) -> ProjectView:
        self._approve_project_document(book_id, "book_contract_entity_id")
        engine = self._engine(book_id)
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "UPDATE book_projects SET workflow_stage='ARCHITECTURE',updated_at=:updated_at "
                        "WHERE book_id=:book_id"
                    ),
                    {"book_id": book_id, "updated_at": utc_now()},
                )
        finally:
            engine.dispose()
        return self.get_project(book_id)

    def save_architecture(self, book_id: str, payload: BookArchitecturePayload) -> ProjectView:
        normalized = payload.model_copy(deep=True)
        for part in normalized.parts:
            for chapter in part.chapters:
                if chapter.chapter_id is None:
                    chapter.chapter_id = new_ulid()
        self._save_project_document(
            book_id,
            project_column="architecture_entity_id",
            entity_type="book.architecture",
            schema_name="book.architecture.v0.1",
            payload=_json_payload(normalized),
        )
        return self.get_project(book_id)

    def approve_architecture(self, book_id: str) -> ProjectView:
        project = self.get_project(book_id)
        if project.book_contract is None or project.book_contract.authority_status not in {
            "APPROVED",
            "LOCKED",
        }:
            raise ProjectGateError("Book Contract must be approved before Architecture approval")
        document = self._approve_project_document(book_id, "architecture_entity_id")
        architecture = BookArchitecturePayload.model_validate(document.content)
        engine = self._engine(book_id)
        now = utc_now()
        current_ids: list[str] = []
        ordinal = 0
        try:
            with engine.begin() as connection:
                for part in architecture.parts:
                    for chapter in part.chapters:
                        if chapter.chapter_id is None:
                            raise ProjectError("approved architecture chapter is missing stable ID")
                        ordinal += 1
                        current_ids.append(chapter.chapter_id)
                        existing = connection.execute(
                            text("SELECT book_id FROM chapters WHERE chapter_id=:chapter_id"),
                            {"chapter_id": chapter.chapter_id},
                        ).scalar_one_or_none()
                        if existing is None:
                            connection.execute(
                                text(
                                    "INSERT INTO chapters(chapter_id,book_id,ordinal,working_title,"
                                    "architecture_role,workflow_state,created_at,updated_at) "
                                    "VALUES (:chapter_id,:book_id,:ordinal,:title,:role,'PLANNED',"
                                    ":created_at,:updated_at)"
                                ),
                                {
                                    "chapter_id": chapter.chapter_id,
                                    "book_id": book_id,
                                    "ordinal": ordinal,
                                    "title": chapter.title,
                                    "role": chapter.purpose,
                                    "created_at": now,
                                    "updated_at": now,
                                },
                            )
                        elif existing == book_id:
                            connection.execute(
                                text(
                                    "UPDATE chapters SET ordinal=:ordinal,working_title=:title,"
                                    "architecture_role=:role,workflow_state=CASE "
                                    "WHEN workflow_state='CONTRACT_APPROVED' THEN workflow_state "
                                    "ELSE 'PLANNED' END,updated_at=:updated_at "
                                    "WHERE chapter_id=:chapter_id"
                                ),
                                {
                                    "chapter_id": chapter.chapter_id,
                                    "ordinal": ordinal,
                                    "title": chapter.title,
                                    "role": chapter.purpose,
                                    "updated_at": now,
                                },
                            )
                        else:
                            raise ProjectError("chapter ID belongs to another project")
                if current_ids:
                    params: dict[str, object] = {"book_id": book_id, "updated_at": now}
                    placeholders = []
                    for index, chapter_id in enumerate(current_ids):
                        key = f"chapter_{index}"
                        params[key] = chapter_id
                        placeholders.append(f":{key}")
                    connection.execute(
                        text(
                            "UPDATE chapters SET workflow_state='SUPERSEDED',updated_at=:updated_at "
                            "WHERE book_id=:book_id AND chapter_id NOT IN ("
                            + ",".join(placeholders)
                            + ")"
                        ),
                        params,
                    )
                connection.execute(
                    text(
                        "UPDATE book_projects SET workflow_stage='ARCHITECTURE',updated_at=:updated_at "
                        "WHERE book_id=:book_id"
                    ),
                    {"book_id": book_id, "updated_at": now},
                )
        finally:
            engine.dispose()
        return self.get_project(book_id)

    def save_chapter_contract(
        self, book_id: str, chapter_id: str, payload: ChapterContractPayload
    ) -> ProjectView:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                row = (
                    connection.execute(
                        text(
                            "SELECT workflow_state,chapter_contract_entity_id FROM chapters "
                            "WHERE book_id=:book_id AND chapter_id=:chapter_id"
                        ),
                        {"book_id": book_id, "chapter_id": chapter_id},
                    )
                    .mappings()
                    .one_or_none()
                )
            if row is None or row["workflow_state"] == "SUPERSEDED":
                raise ProjectGateError("chapter is not in the current project architecture")
            self._save_document_on_engine(
                engine,
                entity_id=cast(str | None, row["chapter_contract_entity_id"]),
                entity_type="chapter.contract",
                schema_name="chapter.contract.v0.1",
                payload=_json_payload(payload),
                reference_update=(
                    "UPDATE chapters SET chapter_contract_entity_id=:entity_id,updated_at=:updated_at "
                    "WHERE book_id=:book_id AND chapter_id=:chapter_id"
                ),
                reference_params={"book_id": book_id, "chapter_id": chapter_id},
            )
        finally:
            engine.dispose()
        return self.get_project(book_id)

    def approve_chapter_contract(self, book_id: str, chapter_id: str) -> ProjectView:
        project = self.get_project(book_id)
        if project.architecture is None or project.architecture.authority_status not in {
            "APPROVED",
            "LOCKED",
        }:
            raise ProjectGateError("Architecture must be approved before Chapter Contract approval")
        architecture = BookArchitecturePayload.model_validate(project.architecture.content)
        current_ids = {
            chapter.chapter_id
            for part in architecture.parts
            for chapter in part.chapters
            if chapter.chapter_id is not None
        }
        if chapter_id not in current_ids:
            raise ProjectGateError("chapter is not in the current approved Architecture")
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                entity_id = connection.execute(
                    text(
                        "SELECT chapter_contract_entity_id FROM chapters "
                        "WHERE book_id=:book_id AND chapter_id=:chapter_id"
                    ),
                    {"book_id": book_id, "chapter_id": chapter_id},
                ).scalar_one_or_none()
            if entity_id is None:
                raise ProjectGateError("Chapter Contract draft must be saved before approval")
            self._approve_entity(engine, cast(str, entity_id))
            with engine.begin() as connection:
                now = utc_now()
                connection.execute(
                    text(
                        "UPDATE chapters SET workflow_state='CONTRACT_APPROVED',updated_at=:updated_at "
                        "WHERE book_id=:book_id AND chapter_id=:chapter_id"
                    ),
                    {"book_id": book_id, "chapter_id": chapter_id, "updated_at": now},
                )
                connection.execute(
                    text(
                        "UPDATE book_projects SET workflow_stage='WRITING',updated_at=:updated_at "
                        "WHERE book_id=:book_id"
                    ),
                    {"book_id": book_id, "updated_at": now},
                )
        finally:
            engine.dispose()
        return self.get_project(book_id)

    def _save_project_document(
        self,
        book_id: str,
        *,
        project_column: str,
        entity_type: str,
        schema_name: str,
        payload: Mapping[str, JSONValue],
    ) -> None:
        if project_column not in {"book_contract_entity_id", "architecture_entity_id"}:
            raise ProjectError("unsupported project document reference")
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                entity_id = connection.execute(
                    text(f"SELECT {project_column} FROM book_projects WHERE book_id=:book_id"),
                    {"book_id": book_id},
                ).scalar_one_or_none()
            self._save_document_on_engine(
                engine,
                entity_id=cast(str | None, entity_id),
                entity_type=entity_type,
                schema_name=schema_name,
                payload=payload,
                reference_update=(
                    f"UPDATE book_projects SET {project_column}=:entity_id,updated_at=:updated_at "
                    "WHERE book_id=:book_id"
                ),
                reference_params={"book_id": book_id},
            )
        finally:
            engine.dispose()

    def _save_document_on_engine(
        self,
        engine: Engine,
        *,
        entity_id: str | None,
        entity_type: str,
        schema_name: str,
        payload: Mapping[str, JSONValue],
        reference_update: str,
        reference_params: dict[str, object],
    ) -> str:
        authority = AuthorityService(engine)
        now = utc_now()
        if entity_id is None:
            head = authority.register_entity(
                entity_type=entity_type,
                payload=payload,
                schema_name=schema_name,
                schema_version="1",
                actor="owner",
                actor_kind="HUMAN",
                origin="HUMAN_WRITTEN",
                initial_status="DRAFT",
            )
            entity_id = head.entity_id
            with engine.begin() as connection:
                connection.execute(
                    text(reference_update),
                    {**reference_params, "entity_id": entity_id, "updated_at": now},
                )
            return entity_id

        with engine.connect() as connection:
            working = connection.execute(
                text("SELECT revision_id FROM working_revisions WHERE entity_id=:entity_id"),
                {"entity_id": entity_id},
            ).scalar_one_or_none()
        parent = (
            cast(str, working) if working is not None else authority.get_head(entity_id).revision_id
        )
        revision_id = authority.create_revision(
            entity_id=entity_id,
            payload=payload,
            schema_name=schema_name,
            schema_version="1",
            actor="owner",
            origin="HUMAN_WRITTEN",
            parent_revision_ids=(parent,),
            input_revision_ids=(parent,),
        )
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO working_revisions(entity_id,revision_id,updated_at) "
                    "VALUES (:entity_id,:revision_id,:updated_at) "
                    "ON CONFLICT(entity_id) DO UPDATE SET revision_id=excluded.revision_id,"
                    "updated_at=excluded.updated_at"
                ),
                {"entity_id": entity_id, "revision_id": revision_id, "updated_at": now},
            )
        return entity_id

    def _approve_project_document(self, book_id: str, project_column: str) -> DocumentView:
        if project_column not in {"book_contract_entity_id", "architecture_entity_id"}:
            raise ProjectError("unsupported project document reference")
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                entity_id = connection.execute(
                    text(f"SELECT {project_column} FROM book_projects WHERE book_id=:book_id"),
                    {"book_id": book_id},
                ).scalar_one_or_none()
            if entity_id is None:
                raise ProjectGateError("document draft must be saved before approval")
            return self._approve_entity(engine, cast(str, entity_id))
        finally:
            engine.dispose()

    def _approve_entity(self, engine: Engine, entity_id: str) -> DocumentView:
        authority = AuthorityService(engine)
        head = authority.get_head(entity_id)
        if head.status == "LOCKED":
            raise InvalidAuthorityOperation("locked authority cannot be replaced in M2")
        with engine.connect() as connection:
            working = connection.execute(
                text("SELECT revision_id FROM working_revisions WHERE entity_id=:entity_id"),
                {"entity_id": entity_id},
            ).scalar_one_or_none()
        source_revision_id = cast(str, working) if working is not None else head.revision_id
        source = authority.get_revision(source_revision_id)
        proposal_id = authority.create_proposal(
            entity_id=entity_id,
            base_revision_id=head.revision_id,
            base_revision_hash=head.revision_hash,
            proposed_payload=cast(dict[str, JSONValue], source["content"]),
            schema_name=cast(str, source["schema_name"]),
            schema_version=cast(str, source["schema_version"]),
            rationale="Owner approval from M2 contract workspace",
            actor="owner",
            origin="HUMAN_WRITTEN",
            task_id="task-003-m2-contract-approval",
            input_revision_ids=(source_revision_id,),
        )
        authority.accept_proposal(
            proposal_id,
            actor="owner",
            actor_kind="HUMAN",
            reason="Owner approved in BOOK OS M2 workspace",
            gates={"human_review": True, "m2_contract_gate": True},
        )
        with engine.begin() as connection:
            connection.execute(
                text("DELETE FROM working_revisions WHERE entity_id=:entity_id"),
                {"entity_id": entity_id},
            )
        view = self._document_view(engine, authority, entity_id)
        if view is None:
            raise ProjectError("approved document disappeared")
        return view

    @staticmethod
    def _document_view(
        engine: Engine, authority: AuthorityService, entity_id: str | None
    ) -> DocumentView | None:
        if entity_id is None:
            return None
        head = authority.get_head(entity_id)
        with engine.connect() as connection:
            working = connection.execute(
                text("SELECT revision_id FROM working_revisions WHERE entity_id=:entity_id"),
                {"entity_id": entity_id},
            ).scalar_one_or_none()
            if working is not None:
                status = connection.execute(
                    text(
                        "SELECT status FROM revision_status_history WHERE revision_id=:revision_id "
                        "ORDER BY created_at DESC,status_event_id DESC LIMIT 1"
                    ),
                    {"revision_id": working},
                ).scalar_one()
        revision_id = cast(str, working) if working is not None else head.revision_id
        revision = authority.get_revision(revision_id)
        return DocumentView(
            entity_id=entity_id,
            revision_id=revision_id,
            status=cast(str, status) if working is not None else head.status,
            authority_revision_id=head.revision_id,
            authority_status=head.status,
            content=cast(dict[str, Any], revision["content"]),
        )
