from __future__ import annotations

from pathlib import Path
import json
import re
from typing import Annotated, Literal, cast

from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import text
from sqlalchemy.engine import Engine

from .authority import new_ulid
from .authority_types import utc_now
from .db import create_database
from .research_adapters import ResearchCandidate, ResearchGateway, normalize_doi, normalize_url

_BOOK_ID = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")

ClaimType = Literal[
    "QUANTITATIVE",
    "EMPIRICAL",
    "CAUSAL",
    "HISTORICAL",
    "ATTRIBUTION",
    "CASE_ASSERTION",
    "LEGAL_REGULATORY",
    "CONSENSUS",
    "INTERPRETIVE",
    "AUTHORIAL",
]
Materiality = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
VerificationState = Literal[
    "UNREVIEWED",
    "SUPPORTED",
    "PARTIALLY_SUPPORTED",
    "DISPUTED",
    "UNSUPPORTED",
    "REJECTED",
]
EvidenceRelationship = Literal["SUPPORTS", "PARTIALLY_SUPPORTS", "CONTRADICTS", "CONTEXT_ONLY"]
EvidenceStrength = Literal["WEAK", "MODERATE", "STRONG"]

NonEmpty = Annotated[str, Field(min_length=1, max_length=8000)]


class ResearchError(RuntimeError):
    pass


class ResearchNotFound(ResearchError):
    pass


class ResearchGateError(ResearchError):
    pass


class ClaimCreateRequest(BaseModel):
    chapter_id: str
    unit_id: str
    manuscript_revision_id: str
    manuscript_revision_hash: Annotated[str, Field(min_length=64, max_length=64)]
    normalized_text: NonEmpty
    claim_type: ClaimType
    materiality: Materiality = "HIGH"
    required_evidence_level: Annotated[str, Field(min_length=1, max_length=128)] = (
        "TRACEABLE_SOURCE"
    )

    @field_validator("normalized_text", "required_evidence_level")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be blank")
        return value


class ClaimUpdateRequest(BaseModel):
    manuscript_revision_id: str
    manuscript_revision_hash: Annotated[str, Field(min_length=64, max_length=64)]
    normalized_text: NonEmpty
    claim_type: ClaimType
    materiality: Materiality
    required_evidence_level: Annotated[str, Field(min_length=1, max_length=128)]

    @field_validator("normalized_text", "required_evidence_level")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be blank")
        return value


class ClaimReviewRequest(BaseModel):
    state: Literal["UNREVIEWED", "DISPUTED", "UNSUPPORTED", "REJECTED"]
    actor: Annotated[str, Field(min_length=1, max_length=128)] = "OWNER"
    reason: NonEmpty


class ClaimView(BaseModel):
    claim_id: str
    book_id: str
    chapter_id: str
    unit_id: str
    manuscript_revision_id: str
    manuscript_revision_hash: str
    normalized_text: str
    claim_type: str
    materiality: str
    required_evidence_level: str
    verification_state: str
    evidence_count: int = 0
    created_at: str
    updated_at: str


class SourceImportRequest(BaseModel):
    candidate: ResearchCandidate
    primary_secondary: Literal["PRIMARY", "SECONDARY", "UNCLASSIFIED"] = "UNCLASSIFIED"


class SourceAccessRequest(BaseModel):
    access_status: Literal["METADATA_ONLY", "ABSTRACT_AVAILABLE", "FULL_SOURCE_INSPECTED"]
    actor: Annotated[str, Field(min_length=1, max_length=128)] = "OWNER"
    note: str = ""

    @field_validator("actor", "note")
    @classmethod
    def strip_access_fields(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def inspected_requires_note(self) -> SourceAccessRequest:
        if self.access_status == "FULL_SOURCE_INSPECTED" and not self.note:
            raise ValueError("FULL_SOURCE_INSPECTED requires an inspection note")
        return self


class SourceView(BaseModel):
    source_id: str
    canonical_key: str
    source_type: str
    title: str
    authors: list[str]
    organization: str | None
    publication_date: str | None
    publication_year: int | None
    doi: str | None
    canonical_url: str | None
    container_title: str | None
    abstract: str | None
    citation_count: int | None
    primary_secondary: str
    access_status: str
    identifiers: dict[str, list[str]]


class EvidenceCreateRequest(BaseModel):
    source_id: str
    relationship: EvidenceRelationship
    pointer: NonEmpty
    note: str = ""
    strength: EvidenceStrength = "MODERATE"
    limitations: str = ""
    actor: Annotated[str, Field(min_length=1, max_length=128)] = "OWNER"

    @field_validator("pointer", "note", "limitations", "actor")
    @classmethod
    def strip_values(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def partial_requires_limitation(self) -> EvidenceCreateRequest:
        if self.relationship == "PARTIALLY_SUPPORTS" and not self.limitations:
            raise ValueError("PARTIALLY_SUPPORTS evidence requires an explicit limitation")
        return self


class EvidenceView(BaseModel):
    evidence_id: str
    claim_id: str
    source_id: str
    relationship: str
    pointer: str
    note: str
    strength: str
    limitations: str
    actor: str
    status: str
    supersedes_evidence_id: str | None
    created_at: str


class CitationCheckView(BaseModel):
    identifier: str
    resolved: bool
    source_id: str | None = None
    evidence_id: str | None = None
    reason: str


def _default_research_providers() -> list[Literal["openalex", "crossref", "semantic_scholar"]]:
    return ["openalex", "crossref", "semantic_scholar"]


class ResearchSearchRequest(BaseModel):
    query: Annotated[str, Field(min_length=1, max_length=1000)]
    providers: list[Literal["openalex", "crossref", "semantic_scholar"]] = Field(
        default_factory=_default_research_providers
    )
    limit_per_provider: Annotated[int, Field(ge=1, le=10)] = 5

    @field_validator("query")
    @classmethod
    def strip_query(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("research query must not be blank")
        return value


class ResearchService:
    def __init__(self, data_dir: Path, gateway: ResearchGateway) -> None:
        self.projects_dir = data_dir / "projects"
        self.gateway = gateway

    def _database_path(self, book_id: str) -> Path:
        if not _BOOK_ID.fullmatch(book_id):
            raise ResearchNotFound("invalid book project ID")
        path = self.projects_dir / book_id / "project.sqlite"
        if not path.is_file():
            raise ResearchNotFound(f"book project not found: {book_id}")
        return path

    def _engine(self, book_id: str) -> Engine:
        return create_database(self._database_path(book_id))

    def search(self, request: ResearchSearchRequest) -> list[ResearchCandidate]:
        return self.gateway.search(
            request.query,
            providers=[str(provider) for provider in request.providers],
            limit_per_provider=request.limit_per_provider,
        )

    def _current_manuscript_revision(
        self, engine: Engine, chapter_id: str, unit_id: str
    ) -> tuple[str, str]:
        with engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        "SELECT ah.revision_id,ah.revision_hash "
                        "FROM manuscript_units mu JOIN authority_heads ah "
                        "ON ah.entity_id=mu.authority_entity_id "
                        "WHERE mu.chapter_id=:chapter_id AND mu.unit_id=:unit_id"
                    ),
                    {"chapter_id": chapter_id, "unit_id": unit_id},
                )
                .mappings()
                .one_or_none()
            )
        if row is None:
            raise ResearchNotFound("manuscript unit not found in chapter")
        return cast(str, row["revision_id"]), cast(str, row["revision_hash"])

    def _require_current_manuscript_revision(
        self,
        engine: Engine,
        chapter_id: str,
        unit_id: str,
        revision_id: str,
        revision_hash: str,
    ) -> None:
        current_id, current_hash = self._current_manuscript_revision(engine, chapter_id, unit_id)
        if current_id != revision_id or current_hash != revision_hash:
            raise ResearchGateError("claim must target the exact current ManuscriptUnit revision")

    def create_claim(self, book_id: str, request: ClaimCreateRequest) -> ClaimView:
        engine = self._engine(book_id)
        try:
            self._require_current_manuscript_revision(
                engine,
                request.chapter_id,
                request.unit_id,
                request.manuscript_revision_id,
                request.manuscript_revision_hash,
            )
            claim_id = new_ulid()
            now = utc_now()
            with engine.begin() as connection:
                chapter_book = connection.execute(
                    text("SELECT book_id FROM chapters WHERE chapter_id=:chapter_id"),
                    {"chapter_id": request.chapter_id},
                ).scalar_one_or_none()
                if chapter_book != book_id:
                    raise ResearchGateError("chapter does not belong to book project")
                connection.execute(
                    text(
                        "INSERT INTO claims(claim_id,book_id,chapter_id,unit_id,"
                        "manuscript_revision_id,manuscript_revision_hash,normalized_text,claim_type,"
                        "materiality,required_evidence_level,verification_state,created_at,updated_at) "
                        "VALUES (:claim_id,:book_id,:chapter_id,:unit_id,:revision_id,:revision_hash,"
                        ":normalized_text,:claim_type,:materiality,:required_evidence_level,"
                        "'UNREVIEWED',:created_at,:updated_at)"
                    ),
                    {
                        "claim_id": claim_id,
                        "book_id": book_id,
                        "chapter_id": request.chapter_id,
                        "unit_id": request.unit_id,
                        "revision_id": request.manuscript_revision_id,
                        "revision_hash": request.manuscript_revision_hash,
                        "normalized_text": request.normalized_text,
                        "claim_type": request.claim_type,
                        "materiality": request.materiality,
                        "required_evidence_level": request.required_evidence_level,
                        "created_at": now,
                        "updated_at": now,
                    },
                )
                connection.execute(
                    text(
                        "INSERT INTO claim_state_history(state_event_id,claim_id,prior_state,new_state,"
                        "actor,actor_kind,reason,created_at) VALUES (:event_id,:claim_id,NULL,"
                        "'UNREVIEWED','OWNER','HUMAN','Claim registered',:created_at)"
                    ),
                    {"event_id": new_ulid(), "claim_id": claim_id, "created_at": now},
                )
            return self.get_claim(book_id, claim_id)
        finally:
            engine.dispose()

    def update_claim(self, book_id: str, claim_id: str, request: ClaimUpdateRequest) -> ClaimView:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                row = (
                    connection.execute(
                        text(
                            "SELECT chapter_id,unit_id,verification_state FROM claims "
                            "WHERE book_id=:book_id AND claim_id=:claim_id"
                        ),
                        {"book_id": book_id, "claim_id": claim_id},
                    )
                    .mappings()
                    .one_or_none()
                )
            if row is None:
                raise ResearchNotFound("claim not found")
            chapter_id = cast(str, row["chapter_id"])
            unit_id = cast(str, row["unit_id"])
            self._require_current_manuscript_revision(
                engine,
                chapter_id,
                unit_id,
                request.manuscript_revision_id,
                request.manuscript_revision_hash,
            )
            now = utc_now()
            prior_state = cast(str, row["verification_state"])
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "UPDATE claims SET manuscript_revision_id=:revision_id,"
                        "manuscript_revision_hash=:revision_hash,normalized_text=:normalized_text,"
                        "claim_type=:claim_type,materiality=:materiality,"
                        "required_evidence_level=:required_evidence_level,verification_state='UNREVIEWED',"
                        "updated_at=:updated_at WHERE claim_id=:claim_id"
                    ),
                    {
                        "revision_id": request.manuscript_revision_id,
                        "revision_hash": request.manuscript_revision_hash,
                        "normalized_text": request.normalized_text,
                        "claim_type": request.claim_type,
                        "materiality": request.materiality,
                        "required_evidence_level": request.required_evidence_level,
                        "updated_at": now,
                        "claim_id": claim_id,
                    },
                )
                connection.execute(
                    text(
                        "UPDATE evidence SET status='SUPERSEDED' WHERE claim_id=:claim_id AND status='ACTIVE'"
                    ),
                    {"claim_id": claim_id},
                )
                if prior_state != "UNREVIEWED":
                    connection.execute(
                        text(
                            "INSERT INTO claim_state_history(state_event_id,claim_id,prior_state,new_state,"
                            "actor,actor_kind,reason,created_at) VALUES (:event_id,:claim_id,:prior_state,"
                            "'UNREVIEWED','SYSTEM','SYSTEM',"
                            "'Claim edit invalidated prior evidence decision',:created_at)"
                        ),
                        {
                            "event_id": new_ulid(),
                            "claim_id": claim_id,
                            "prior_state": prior_state,
                            "created_at": now,
                        },
                    )
            return self.get_claim(book_id, claim_id)
        finally:
            engine.dispose()

    def get_claim(self, book_id: str, claim_id: str) -> ClaimView:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                row = (
                    connection.execute(
                        text(
                            "SELECT c.*,(SELECT COUNT(*) FROM evidence e WHERE e.claim_id=c.claim_id "
                            "AND e.status='ACTIVE') AS evidence_count FROM claims c "
                            "WHERE c.book_id=:book_id AND c.claim_id=:claim_id"
                        ),
                        {"book_id": book_id, "claim_id": claim_id},
                    )
                    .mappings()
                    .one_or_none()
                )
            if row is None:
                raise ResearchNotFound("claim not found")
            return ClaimView(**dict(row))
        finally:
            engine.dispose()

    def list_claims(
        self,
        book_id: str,
        *,
        chapter_id: str | None = None,
        unit_id: str | None = None,
        verification_state: str | None = None,
    ) -> list[ClaimView]:
        engine = self._engine(book_id)
        try:
            clauses = ["c.book_id=:book_id"]
            params: dict[str, object] = {"book_id": book_id}
            if chapter_id:
                clauses.append("c.chapter_id=:chapter_id")
                params["chapter_id"] = chapter_id
            if unit_id:
                clauses.append("c.unit_id=:unit_id")
                params["unit_id"] = unit_id
            if verification_state:
                clauses.append("c.verification_state=:verification_state")
                params["verification_state"] = verification_state
            statement = (
                "SELECT c.*,(SELECT COUNT(*) FROM evidence e WHERE e.claim_id=c.claim_id "
                "AND e.status='ACTIVE') AS evidence_count FROM claims c WHERE "
                + " AND ".join(clauses)
                + " ORDER BY c.created_at,c.claim_id"
            )
            with engine.connect() as connection:
                rows = connection.execute(text(statement), params).mappings().all()
            return [ClaimView(**dict(row)) for row in rows]
        finally:
            engine.dispose()

    def import_source(self, book_id: str, request: SourceImportRequest) -> SourceView:
        engine = self._engine(book_id)
        candidate = request.candidate
        doi = normalize_doi(candidate.doi)
        canonical_url = normalize_url(candidate.canonical_url)
        try:
            existing_id: str | None = None
            with engine.connect() as connection:
                if doi:
                    existing_id = cast(
                        str | None,
                        connection.execute(
                            text("SELECT source_id FROM sources WHERE doi=:doi"), {"doi": doi}
                        ).scalar_one_or_none(),
                    )
                if existing_id is None:
                    existing_id = cast(
                        str | None,
                        connection.execute(
                            text(
                                "SELECT source_id FROM source_identifiers "
                                "WHERE provider=:provider AND external_id=:external_id"
                            ),
                            {
                                "provider": candidate.provider,
                                "external_id": candidate.external_id,
                            },
                        ).scalar_one_or_none(),
                    )
                if existing_id is None and canonical_url:
                    existing_id = cast(
                        str | None,
                        connection.execute(
                            text("SELECT source_id FROM sources WHERE canonical_url=:url"),
                            {"url": canonical_url},
                        ).scalar_one_or_none(),
                    )
            now = utc_now()
            source_id = existing_id or new_ulid()
            canonical_key = (
                f"doi:{doi}"
                if doi
                else f"provider:{candidate.provider}:{candidate.external_id}"
                if candidate.external_id
                else f"url:{canonical_url}"
            )
            access_status = "ABSTRACT_AVAILABLE" if candidate.abstract else "METADATA_ONLY"
            reliability = {
                "metadata_provider": candidate.provider,
                "metadata_only": access_status != "FULL_SOURCE_INSPECTED",
                "raw_identifiers": candidate.raw_identifiers,
            }
            with engine.begin() as connection:
                if existing_id is None:
                    connection.execute(
                        text(
                            "INSERT INTO sources(source_id,canonical_key,source_type,title,authors_json,"
                            "organization,publication_date,publication_year,doi,canonical_url,"
                            "container_title,abstract,citation_count,primary_secondary,reliability_json,"
                            "access_status,created_at,updated_at) VALUES (:source_id,:canonical_key,"
                            ":source_type,:title,:authors_json,:organization,:publication_date,"
                            ":publication_year,:doi,:canonical_url,:container_title,:abstract,"
                            ":citation_count,:primary_secondary,:reliability_json,:access_status,"
                            ":created_at,:updated_at)"
                        ),
                        {
                            "source_id": source_id,
                            "canonical_key": canonical_key,
                            "source_type": candidate.source_type,
                            "title": candidate.title,
                            "authors_json": json.dumps(candidate.authors, ensure_ascii=False),
                            "organization": candidate.organization,
                            "publication_date": candidate.publication_date,
                            "publication_year": candidate.publication_year,
                            "doi": doi,
                            "canonical_url": canonical_url,
                            "container_title": candidate.container_title,
                            "abstract": candidate.abstract,
                            "citation_count": candidate.citation_count,
                            "primary_secondary": request.primary_secondary,
                            "reliability_json": json.dumps(
                                reliability, ensure_ascii=False, sort_keys=True
                            ),
                            "access_status": access_status,
                            "created_at": now,
                            "updated_at": now,
                        },
                    )
                else:
                    connection.execute(
                        text(
                            "UPDATE sources SET doi=COALESCE(doi,:doi),"
                            "canonical_url=COALESCE(canonical_url,:canonical_url),"
                            "publication_date=COALESCE(publication_date,:publication_date),"
                            "publication_year=COALESCE(publication_year,:publication_year),"
                            "container_title=COALESCE(container_title,:container_title),"
                            "abstract=COALESCE(abstract,:abstract),"
                            "citation_count=COALESCE(citation_count,:citation_count),updated_at=:updated_at "
                            "WHERE source_id=:source_id"
                        ),
                        {
                            "doi": doi,
                            "canonical_url": canonical_url,
                            "publication_date": candidate.publication_date,
                            "publication_year": candidate.publication_year,
                            "container_title": candidate.container_title,
                            "abstract": candidate.abstract,
                            "citation_count": candidate.citation_count,
                            "updated_at": now,
                            "source_id": source_id,
                        },
                    )
                if existing_id is None:
                    connection.execute(
                        text(
                            "INSERT INTO source_access_history(access_event_id,source_id,access_status,"
                            "actor,note,created_at) VALUES (:event_id,:source_id,:access_status,"
                            "'SYSTEM','Imported provider metadata',:created_at)"
                        ),
                        {
                            "event_id": new_ulid(),
                            "source_id": source_id,
                            "access_status": access_status,
                            "created_at": now,
                        },
                    )
                identifiers = [(candidate.provider, candidate.external_id, candidate.provider_url)]
                for key, value in sorted(candidate.raw_identifiers.items()):
                    provider_key = (
                        key
                        if key in {"openalex", "crossref", "semantic_scholar"}
                        else f"{candidate.provider}:{key}"
                    )
                    identifiers.append((provider_key, value, candidate.provider_url))
                for provider, external_id, provider_url in identifiers:
                    if not provider or not external_id:
                        continue
                    connection.execute(
                        text(
                            "INSERT OR IGNORE INTO source_identifiers(source_id,provider,external_id,"
                            "provider_url,created_at) VALUES (:source_id,:provider,:external_id,"
                            ":provider_url,:created_at)"
                        ),
                        {
                            "source_id": source_id,
                            "provider": provider,
                            "external_id": external_id,
                            "provider_url": provider_url,
                            "created_at": now,
                        },
                    )
            return self.get_source(book_id, source_id)
        finally:
            engine.dispose()

    def mark_source_access(
        self, book_id: str, source_id: str, request: SourceAccessRequest
    ) -> SourceView:
        engine = self._engine(book_id)
        try:
            now = utc_now()
            with engine.begin() as connection:
                result = connection.execute(
                    text(
                        "UPDATE sources SET access_status=:status,updated_at=:updated_at WHERE source_id=:source_id"
                    ),
                    {"status": request.access_status, "updated_at": now, "source_id": source_id},
                )
                if result.rowcount != 1:
                    raise ResearchNotFound("source not found")
                connection.execute(
                    text(
                        "INSERT INTO source_access_history(access_event_id,source_id,access_status,"
                        "actor,note,created_at) VALUES (:event_id,:source_id,:status,:actor,:note,:created_at)"
                    ),
                    {
                        "event_id": new_ulid(),
                        "source_id": source_id,
                        "status": request.access_status,
                        "actor": request.actor,
                        "note": request.note,
                        "created_at": now,
                    },
                )
            return self.get_source(book_id, source_id)
        finally:
            engine.dispose()

    def get_source(self, book_id: str, source_id: str) -> SourceView:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                row = (
                    connection.execute(
                        text("SELECT * FROM sources WHERE source_id=:source_id"),
                        {"source_id": source_id},
                    )
                    .mappings()
                    .one_or_none()
                )
                identifiers = (
                    connection.execute(
                        text(
                            "SELECT provider,external_id FROM source_identifiers "
                            "WHERE source_id=:source_id ORDER BY provider,external_id"
                        ),
                        {"source_id": source_id},
                    )
                    .mappings()
                    .all()
                )
            if row is None:
                raise ResearchNotFound("source not found")
            grouped: dict[str, list[str]] = {}
            for item in identifiers:
                grouped.setdefault(cast(str, item["provider"]), []).append(
                    cast(str, item["external_id"])
                )
            values = dict(row)
            values["authors"] = json.loads(cast(str, values.pop("authors_json")))
            values["identifiers"] = grouped
            values.pop("reliability_json", None)
            values.pop("created_at", None)
            values.pop("updated_at", None)
            return SourceView(**values)
        finally:
            engine.dispose()

    def list_sources(self, book_id: str) -> list[SourceView]:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                ids = [
                    cast(str, item)
                    for item in connection.execute(
                        text("SELECT source_id FROM sources ORDER BY title,source_id")
                    ).scalars()
                ]
        finally:
            engine.dispose()
        return [self.get_source(book_id, source_id) for source_id in ids]

    def add_evidence(
        self, book_id: str, claim_id: str, request: EvidenceCreateRequest
    ) -> EvidenceView:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                claim_book = connection.execute(
                    text("SELECT book_id FROM claims WHERE claim_id=:claim_id"),
                    {"claim_id": claim_id},
                ).scalar_one_or_none()
                source_exists = connection.execute(
                    text("SELECT 1 FROM sources WHERE source_id=:source_id"),
                    {"source_id": request.source_id},
                ).scalar_one_or_none()
            if claim_book != book_id:
                raise ResearchNotFound("claim not found")
            if source_exists is None:
                raise ResearchNotFound("source not found")
            evidence_id = new_ulid()
            now = utc_now()
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO evidence(evidence_id,claim_id,source_id,relationship,pointer,note,"
                        "strength,limitations,actor,status,supersedes_evidence_id,created_at) "
                        "VALUES (:evidence_id,:claim_id,:source_id,:relationship,:pointer,:note,"
                        ":strength,:limitations,:actor,'ACTIVE',NULL,:created_at)"
                    ),
                    {
                        "evidence_id": evidence_id,
                        "claim_id": claim_id,
                        "source_id": request.source_id,
                        "relationship": request.relationship,
                        "pointer": request.pointer,
                        "note": request.note,
                        "strength": request.strength,
                        "limitations": request.limitations,
                        "actor": request.actor,
                        "created_at": now,
                    },
                )
            self.recalculate_claim(book_id, claim_id)
            return self.get_evidence(book_id, evidence_id)
        finally:
            engine.dispose()

    def get_evidence(self, book_id: str, evidence_id: str) -> EvidenceView:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                row = (
                    connection.execute(
                        text(
                            "SELECT e.* FROM evidence e JOIN claims c ON c.claim_id=e.claim_id "
                            "WHERE c.book_id=:book_id AND e.evidence_id=:evidence_id"
                        ),
                        {"book_id": book_id, "evidence_id": evidence_id},
                    )
                    .mappings()
                    .one_or_none()
                )
            if row is None:
                raise ResearchNotFound("evidence not found")
            return EvidenceView(**dict(row))
        finally:
            engine.dispose()

    def list_evidence(self, book_id: str, claim_id: str) -> list[EvidenceView]:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                rows = (
                    connection.execute(
                        text(
                            "SELECT e.* FROM evidence e JOIN claims c ON c.claim_id=e.claim_id "
                            "WHERE c.book_id=:book_id AND e.claim_id=:claim_id "
                            "ORDER BY e.created_at,e.evidence_id"
                        ),
                        {"book_id": book_id, "claim_id": claim_id},
                    )
                    .mappings()
                    .all()
                )
            return [EvidenceView(**dict(row)) for row in rows]
        finally:
            engine.dispose()

    def recalculate_claim(self, book_id: str, claim_id: str) -> ClaimView:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                claim = (
                    connection.execute(
                        text(
                            "SELECT verification_state FROM claims "
                            "WHERE book_id=:book_id AND claim_id=:claim_id"
                        ),
                        {"book_id": book_id, "claim_id": claim_id},
                    )
                    .mappings()
                    .one_or_none()
                )
                evidence = (
                    connection.execute(
                        text(
                            "SELECT e.relationship,e.limitations,s.access_status FROM evidence e "
                            "JOIN sources s ON s.source_id=e.source_id "
                            "WHERE e.claim_id=:claim_id AND e.status='ACTIVE'"
                        ),
                        {"claim_id": claim_id},
                    )
                    .mappings()
                    .all()
                )
            if claim is None:
                raise ResearchNotFound("claim not found")
            if claim["verification_state"] == "REJECTED":
                return self.get_claim(book_id, claim_id)
            has_contradiction = any(item["relationship"] == "CONTRADICTS" for item in evidence)
            has_full_support = any(
                item["relationship"] == "SUPPORTS"
                and item["access_status"] == "FULL_SOURCE_INSPECTED"
                for item in evidence
            )
            has_partial = any(
                item["relationship"] == "PARTIALLY_SUPPORTS"
                and bool(cast(str, item["limitations"]).strip())
                for item in evidence
            )
            if has_contradiction:
                state: VerificationState = "DISPUTED"
            elif has_full_support:
                state = "SUPPORTED"
            elif has_partial:
                state = "PARTIALLY_SUPPORTED"
            else:
                state = "UNREVIEWED"
            prior_state = cast(str, claim["verification_state"])
            if prior_state != state:
                now = utc_now()
                with engine.begin() as connection:
                    connection.execute(
                        text(
                            "UPDATE claims SET verification_state=:state,updated_at=:updated_at "
                            "WHERE claim_id=:claim_id"
                        ),
                        {"state": state, "updated_at": now, "claim_id": claim_id},
                    )
                    connection.execute(
                        text(
                            "INSERT INTO claim_state_history(state_event_id,claim_id,prior_state,new_state,"
                            "actor,actor_kind,reason,created_at) VALUES (:event_id,:claim_id,:prior_state,"
                            ":new_state,'SYSTEM','SYSTEM','Deterministic evidence recalculation',:created_at)"
                        ),
                        {
                            "event_id": new_ulid(),
                            "claim_id": claim_id,
                            "prior_state": prior_state,
                            "new_state": state,
                            "created_at": now,
                        },
                    )
            return self.get_claim(book_id, claim_id)
        finally:
            engine.dispose()

    def review_claim(self, book_id: str, claim_id: str, request: ClaimReviewRequest) -> ClaimView:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                prior_state = connection.execute(
                    text(
                        "SELECT verification_state FROM claims WHERE book_id=:book_id AND claim_id=:claim_id"
                    ),
                    {"book_id": book_id, "claim_id": claim_id},
                ).scalar_one_or_none()
            if prior_state is None:
                raise ResearchNotFound("claim not found")
            now = utc_now()
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "UPDATE claims SET verification_state=:state,updated_at=:updated_at "
                        "WHERE book_id=:book_id AND claim_id=:claim_id"
                    ),
                    {
                        "state": request.state,
                        "updated_at": now,
                        "book_id": book_id,
                        "claim_id": claim_id,
                    },
                )
                if prior_state != request.state:
                    connection.execute(
                        text(
                            "INSERT INTO claim_state_history(state_event_id,claim_id,prior_state,new_state,"
                            "actor,actor_kind,reason,created_at) VALUES (:event_id,:claim_id,:prior_state,"
                            ":new_state,:actor,'HUMAN',:reason,:created_at)"
                        ),
                        {
                            "event_id": new_ulid(),
                            "claim_id": claim_id,
                            "prior_state": prior_state,
                            "new_state": request.state,
                            "actor": request.actor,
                            "reason": request.reason,
                            "created_at": now,
                        },
                    )
            return self.get_claim(book_id, claim_id)
        finally:
            engine.dispose()

    def check_citation(self, book_id: str, claim_id: str, identifier: str) -> CitationCheckView:
        engine = self._engine(book_id)
        try:
            identifier = identifier.strip()
            if not identifier:
                raise ResearchGateError("citation identifier must not be blank")
            doi = normalize_doi(identifier)
            with engine.connect() as connection:
                claim_exists = connection.execute(
                    text("SELECT 1 FROM claims WHERE book_id=:book_id AND claim_id=:claim_id"),
                    {"book_id": book_id, "claim_id": claim_id},
                ).scalar_one_or_none()
                if claim_exists is None:
                    raise ResearchNotFound("claim not found")
                source_id: str | None = None
                if doi:
                    source_id = cast(
                        str | None,
                        connection.execute(
                            text("SELECT source_id FROM sources WHERE doi=:doi"), {"doi": doi}
                        ).scalar_one_or_none(),
                    )
                if source_id is None:
                    source_id = cast(
                        str | None,
                        connection.execute(
                            text(
                                "SELECT source_id FROM source_identifiers WHERE external_id=:identifier "
                                "ORDER BY provider LIMIT 1"
                            ),
                            {"identifier": identifier},
                        ).scalar_one_or_none(),
                    )
                if source_id is None:
                    return CitationCheckView(
                        identifier=identifier,
                        resolved=False,
                        reason="UNVERIFIED_CANDIDATE: source identifier is not resolved",
                    )
                evidence_id = cast(
                    str | None,
                    connection.execute(
                        text(
                            "SELECT evidence_id FROM evidence WHERE claim_id=:claim_id "
                            "AND source_id=:source_id AND status='ACTIVE' "
                            "ORDER BY created_at LIMIT 1"
                        ),
                        {"claim_id": claim_id, "source_id": source_id},
                    ).scalar_one_or_none(),
                )
            if evidence_id is None:
                return CitationCheckView(
                    identifier=identifier,
                    resolved=False,
                    source_id=source_id,
                    reason="source metadata exists but no Evidence links it to this Claim",
                )
            return CitationCheckView(
                identifier=identifier,
                resolved=True,
                source_id=source_id,
                evidence_id=evidence_id,
                reason="stored Source and explicit Evidence resolve this citation",
            )
        finally:
            engine.dispose()
