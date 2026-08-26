from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Literal, cast

import numpy as np
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError

from .authority import AuthorityService, new_ulid
from .authority_types import utc_now
from .db import create_database
from .memory_embeddings import EmbeddingGateway, EmbeddingOutputError, embedding_config_hash

MemoryScope = Literal["CURRENT", "HISTORY"]
MemoryObjectKind = Literal["MANUSCRIPT_UNIT", "BOOK_CONTRACT", "CHAPTER_CONTRACT", "CLAIM"]
MemorySearchMode = Literal["LEXICAL", "SEMANTIC", "HYBRID"]

_BOOK_ID = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")


class MemoryError(RuntimeError):
    pass


class MemoryNotFound(MemoryError):
    pass


class MemoryGateError(MemoryError):
    pass


class MemoryQueryError(MemoryError):
    pass


class MemoryIndexStatus(BaseModel):
    book_id: str
    status: str
    document_count: int
    embedding_count: int
    provider: str | None = None
    model: str | None = None
    model_version: str | None = None
    config_hash: str | None = None
    dimension: int | None = None
    updated_at: str | None = None


class MemorySearchResult(BaseModel):
    memory_id: str
    object_kind: str
    object_id: str
    chapter_id: str | None
    revision_id: str
    revision_hash: str
    content_hash: str
    source_status: str
    currentness: str
    text: str
    lexical_score: float | None = None
    semantic_score: float | None = None
    fused_score: float | None = None
    lexical_rank: int | None = None
    semantic_rank: int | None = None
    fused_rank: int | None = None


class MemorySearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    mode: MemorySearchMode = "HYBRID"
    scope: MemoryScope = "CURRENT"
    chapter_id: str | None = None
    object_kinds: list[MemoryObjectKind] = Field(default_factory=list)
    limit: int = Field(default=12, ge=1, le=100)
    exact_phrase: bool = False
    provider: str | None = None
    model: str | None = None


class MemoryRebuildRequest(BaseModel):
    provider: str = "openai"
    model: str = Field(min_length=1, max_length=128)


@dataclass(frozen=True)
class _CanonicalDocument:
    object_kind: MemoryObjectKind
    object_id: str
    chapter_id: str | None
    revision_id: str
    revision_hash: str
    content_hash: str
    text: str
    source_status: str

    @property
    def key(self) -> tuple[str, str]:
        return self.object_kind, self.object_id

    @property
    def identity(self) -> tuple[str, str, str]:
        return self.revision_id, self.revision_hash, self.content_hash


def _flatten_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        parts: list[str] = []
        for key in sorted(value):
            nested = _flatten_text(value[key])
            if nested:
                parts.append(f"{key}: {nested}")
        return "\n".join(parts)
    if isinstance(value, (list, tuple)):
        return "\n".join(part for item in value if (part := _flatten_text(item)))
    return str(value)


def _content_hash(payload: object) -> str:
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _fts_expression(query: str, *, exact_phrase: bool) -> str:
    query = query.strip()
    if not query:
        raise MemoryQueryError("memory query must not be blank")
    if exact_phrase:
        escaped = query.replace('"', '""')
        return f'"{escaped}"'
    tokens = re.findall(r"[\w-]+", query, flags=re.UNICODE)
    if not tokens:
        raise MemoryQueryError("memory query has no searchable terms")
    return " AND ".join(f'"{token.replace(chr(34), chr(34) * 2)}"' for token in tokens)


def _vector_blob(vector: list[float]) -> bytes:
    return np.asarray(vector, dtype=np.float32).tobytes(order="C")


def _vector_from_blob(blob: bytes, dimension: int) -> np.ndarray[Any, np.dtype[np.float32]]:
    vector = np.frombuffer(blob, dtype=np.float32)
    if vector.size != dimension:
        raise MemoryGateError("stored embedding dimension does not match vector bytes")
    return vector


def exact_cosine_scores(
    query_vector: np.ndarray[Any, np.dtype[np.float32]],
    matrix: np.ndarray[Any, np.dtype[np.float32]],
) -> np.ndarray[Any, np.dtype[np.float32]]:
    if matrix.ndim != 2 or query_vector.ndim != 1:
        raise MemoryGateError("cosine inputs have invalid shape")
    if matrix.shape[1] != query_vector.shape[0]:
        raise MemoryGateError("cosine vector dimensions do not match")
    query_norm = float(np.linalg.norm(query_vector))
    if query_norm == 0.0:
        raise MemoryGateError("query embedding has zero norm")
    row_norms = np.linalg.norm(matrix, axis=1)
    denominators = row_norms * query_norm
    dots = matrix @ query_vector
    scores = np.divide(
        dots,
        denominators,
        out=np.full_like(dots, -1.0, dtype=np.float32),
        where=denominators != 0.0,
    )
    return cast(np.ndarray[Any, np.dtype[np.float32]], scores)


class BookMemoryService:
    def __init__(self, data_dir: Path, embedding_gateway: EmbeddingGateway):
        self.projects_dir = data_dir / "projects"
        self.embedding_gateway = embedding_gateway

    def _database_path(self, book_id: str) -> Path:
        if not _BOOK_ID.fullmatch(book_id):
            raise MemoryNotFound("invalid book project ID")
        path = self.projects_dir / book_id / "project.sqlite"
        if not path.is_file():
            raise MemoryNotFound(f"book project not found: {book_id}")
        return path

    def _engine(self, book_id: str) -> Engine:
        return create_database(self._database_path(book_id))

    def _canonical_documents(self, engine: Engine, book_id: str) -> list[_CanonicalDocument]:
        authority = AuthorityService(engine)
        documents: list[_CanonicalDocument] = []
        with engine.connect() as connection:
            project = (
                connection.execute(
                    text(
                        "SELECT book_contract_entity_id FROM book_projects WHERE book_id=:book_id"
                    ),
                    {"book_id": book_id},
                )
                .mappings()
                .one_or_none()
            )
            if project is None:
                raise MemoryNotFound(f"book project not found: {book_id}")
            units = list(
                connection.execute(
                    text(
                        "SELECT unit_id,chapter_id,authority_entity_id FROM manuscript_units "
                        "WHERE book_id=:book_id ORDER BY chapter_id,ordinal,unit_id"
                    ),
                    {"book_id": book_id},
                ).mappings()
            )
            chapters = list(
                connection.execute(
                    text(
                        "SELECT chapter_id,chapter_contract_entity_id FROM chapters "
                        "WHERE book_id=:book_id AND workflow_state!='SUPERSEDED' "
                        "ORDER BY ordinal,chapter_id"
                    ),
                    {"book_id": book_id},
                ).mappings()
            )
            claims = list(
                connection.execute(
                    text(
                        "SELECT claim_id,chapter_id,manuscript_revision_id,manuscript_revision_hash,"
                        "normalized_text,claim_type,materiality,required_evidence_level,"
                        "verification_state,updated_at FROM claims WHERE book_id=:book_id "
                        "ORDER BY claim_id"
                    ),
                    {"book_id": book_id},
                ).mappings()
            )

        for row in units:
            entity_id = cast(str, row["authority_entity_id"])
            head = authority.get_head(entity_id)
            revision = authority.get_revision(head.revision_id)
            payload = cast(dict[str, Any], revision["content"])
            unit_text = str(payload.get("text") or _flatten_text(payload)).strip()
            if not unit_text:
                continue
            documents.append(
                _CanonicalDocument(
                    object_kind="MANUSCRIPT_UNIT",
                    object_id=cast(str, row["unit_id"]),
                    chapter_id=cast(str, row["chapter_id"]),
                    revision_id=head.revision_id,
                    revision_hash=head.revision_hash,
                    content_hash=cast(str, revision["content_hash"]),
                    text=unit_text,
                    source_status=head.status,
                )
            )

        book_contract_entity = cast(str | None, project["book_contract_entity_id"])
        if book_contract_entity:
            head = authority.get_head(book_contract_entity)
            revision = authority.get_revision(head.revision_id)
            payload = cast(dict[str, Any], revision["content"])
            documents.append(
                _CanonicalDocument(
                    object_kind="BOOK_CONTRACT",
                    object_id=book_contract_entity,
                    chapter_id=None,
                    revision_id=head.revision_id,
                    revision_hash=head.revision_hash,
                    content_hash=cast(str, revision["content_hash"]),
                    text=_flatten_text(payload),
                    source_status=head.status,
                )
            )

        for row in chapters:
            entity_id = cast(str | None, row["chapter_contract_entity_id"])
            if not entity_id:
                continue
            head = authority.get_head(entity_id)
            revision = authority.get_revision(head.revision_id)
            payload = cast(dict[str, Any], revision["content"])
            documents.append(
                _CanonicalDocument(
                    object_kind="CHAPTER_CONTRACT",
                    object_id=entity_id,
                    chapter_id=cast(str, row["chapter_id"]),
                    revision_id=head.revision_id,
                    revision_hash=head.revision_hash,
                    content_hash=cast(str, revision["content_hash"]),
                    text=_flatten_text(payload),
                    source_status=head.status,
                )
            )

        for row in claims:
            claim_payload = {
                "normalized_text": cast(str, row["normalized_text"]),
                "claim_type": cast(str, row["claim_type"]),
                "materiality": cast(str, row["materiality"]),
                "required_evidence_level": cast(str, row["required_evidence_level"]),
                "verification_state": cast(str, row["verification_state"]),
                "updated_at": cast(str, row["updated_at"]),
            }
            documents.append(
                _CanonicalDocument(
                    object_kind="CLAIM",
                    object_id=cast(str, row["claim_id"]),
                    chapter_id=cast(str, row["chapter_id"]),
                    revision_id=cast(str, row["manuscript_revision_id"]),
                    revision_hash=cast(str, row["manuscript_revision_hash"]),
                    content_hash=_content_hash(claim_payload),
                    text=cast(str, row["normalized_text"]),
                    source_status=cast(str, row["verification_state"]),
                )
            )
        return documents

    def _canonical_map(
        self, engine: Engine, book_id: str
    ) -> dict[tuple[str, str], _CanonicalDocument]:
        return {document.key: document for document in self._canonical_documents(engine, book_id)}

    @staticmethod
    def _row_is_current(
        row: dict[str, Any], canonical: dict[tuple[str, str], _CanonicalDocument]
    ) -> bool:
        current = canonical.get((cast(str, row["object_kind"]), cast(str, row["object_id"])))
        if current is None:
            return False
        return current.identity == (
            cast(str, row["revision_id"]),
            cast(str, row["revision_hash"]),
            cast(str, row["content_hash"]),
        )

    def synchronize(self, book_id: str) -> MemoryIndexStatus:
        engine = self._engine(book_id)
        try:
            canonical_documents = self._canonical_documents(engine, book_id)
            canonical_identities = {
                (doc.object_kind, doc.object_id, doc.revision_id, doc.content_hash)
                for doc in canonical_documents
            }
            with engine.connect() as connection:
                prior_current = {
                    (
                        cast(str, row["object_kind"]),
                        cast(str, row["object_id"]),
                        cast(str, row["revision_id"]),
                        cast(str, row["content_hash"]),
                    )
                    for row in connection.execute(
                        text(
                            "SELECT object_kind,object_id,revision_id,content_hash "
                            "FROM memory_documents WHERE book_id=:book_id AND currentness='CURRENT'"
                        ),
                        {"book_id": book_id},
                    ).mappings()
                }
            changed = prior_current != canonical_identities
            now = utc_now()
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "UPDATE memory_documents SET currentness='HISTORY',indexed_at=:indexed_at "
                        "WHERE book_id=:book_id AND currentness='CURRENT'"
                    ),
                    {"book_id": book_id, "indexed_at": now},
                )
                for document in canonical_documents:
                    existing = connection.execute(
                        text(
                            "SELECT memory_id FROM memory_documents WHERE book_id=:book_id "
                            "AND object_kind=:object_kind AND object_id=:object_id "
                            "AND revision_id=:revision_id AND content_hash=:content_hash"
                        ),
                        {
                            "book_id": book_id,
                            "object_kind": document.object_kind,
                            "object_id": document.object_id,
                            "revision_id": document.revision_id,
                            "content_hash": document.content_hash,
                        },
                    ).scalar_one_or_none()
                    memory_id = cast(str | None, existing) or new_ulid()
                    if existing is None:
                        connection.execute(
                            text(
                                "INSERT INTO memory_documents(memory_id,book_id,object_kind,object_id,"
                                "chapter_id,revision_id,revision_hash,content_hash,text,source_status,"
                                "currentness,created_at,indexed_at) VALUES (:memory_id,:book_id,"
                                ":object_kind,:object_id,:chapter_id,:revision_id,:revision_hash,"
                                ":content_hash,:text,:source_status,'CURRENT',:created_at,:indexed_at)"
                            ),
                            {
                                "memory_id": memory_id,
                                "book_id": book_id,
                                "object_kind": document.object_kind,
                                "object_id": document.object_id,
                                "chapter_id": document.chapter_id,
                                "revision_id": document.revision_id,
                                "revision_hash": document.revision_hash,
                                "content_hash": document.content_hash,
                                "text": document.text,
                                "source_status": document.source_status,
                                "created_at": now,
                                "indexed_at": now,
                            },
                        )
                    else:
                        connection.execute(
                            text(
                                "UPDATE memory_documents SET chapter_id=:chapter_id,"
                                "revision_hash=:revision_hash,text=:text,source_status=:source_status,"
                                "currentness='CURRENT',indexed_at=:indexed_at WHERE memory_id=:memory_id"
                            ),
                            {
                                "chapter_id": document.chapter_id,
                                "revision_hash": document.revision_hash,
                                "text": document.text,
                                "source_status": document.source_status,
                                "indexed_at": now,
                                "memory_id": memory_id,
                            },
                        )
                    connection.execute(
                        text("DELETE FROM memory_fts WHERE memory_id=:memory_id"),
                        {"memory_id": memory_id},
                    )
                    connection.execute(
                        text(
                            "INSERT INTO memory_fts(memory_id,text,object_kind,chapter_id) "
                            "VALUES (:memory_id,:text,:object_kind,:chapter_id)"
                        ),
                        {
                            "memory_id": memory_id,
                            "text": document.text,
                            "object_kind": document.object_kind,
                            "chapter_id": document.chapter_id or "",
                        },
                    )

                prior_state = (
                    connection.execute(
                        text(
                            "SELECT status,provider,model,model_version,config_hash,dimension "
                            "FROM memory_index_state WHERE book_id=:book_id"
                        ),
                        {"book_id": book_id},
                    )
                    .mappings()
                    .one_or_none()
                )
                if not canonical_documents:
                    status = "EMPTY"
                elif changed or prior_state is None:
                    status = "LEXICAL_READY"
                else:
                    status = cast(str, prior_state["status"])
                    if status == "FAILED":
                        status = "LEXICAL_READY"
                connection.execute(
                    text(
                        "INSERT INTO memory_index_state(book_id,provider,model,model_version,"
                        "config_hash,dimension,document_count,status,last_error,updated_at) VALUES "
                        "(:book_id,:provider,:model,:model_version,:config_hash,:dimension,"
                        ":document_count,:status,NULL,:updated_at) ON CONFLICT(book_id) DO UPDATE SET "
                        "document_count=excluded.document_count,status=excluded.status,last_error=NULL,"
                        "updated_at=excluded.updated_at"
                    ),
                    {
                        "book_id": book_id,
                        "provider": cast(str | None, prior_state["provider"])
                        if prior_state
                        else None,
                        "model": cast(str | None, prior_state["model"]) if prior_state else None,
                        "model_version": (
                            cast(str | None, prior_state["model_version"]) if prior_state else None
                        ),
                        "config_hash": (
                            cast(str | None, prior_state["config_hash"]) if prior_state else None
                        ),
                        "dimension": cast(int | None, prior_state["dimension"])
                        if prior_state
                        else None,
                        "document_count": len(canonical_documents),
                        "status": status,
                        "updated_at": now,
                    },
                )
            return self.status(book_id, synchronize=False)
        finally:
            engine.dispose()

    def status(self, book_id: str, *, synchronize: bool = True) -> MemoryIndexStatus:
        if synchronize:
            return self.synchronize(book_id)
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                state = (
                    connection.execute(
                        text("SELECT * FROM memory_index_state WHERE book_id=:book_id"),
                        {"book_id": book_id},
                    )
                    .mappings()
                    .one_or_none()
                )
                embedding_count = cast(
                    int,
                    connection.execute(
                        text(
                            "SELECT COUNT(*) FROM memory_embeddings me JOIN memory_documents md "
                            "ON md.memory_id=me.memory_id WHERE md.book_id=:book_id "
                            "AND md.currentness='CURRENT'"
                        ),
                        {"book_id": book_id},
                    ).scalar_one(),
                )
            if state is None:
                return MemoryIndexStatus(
                    book_id=book_id,
                    status="EMPTY",
                    document_count=0,
                    embedding_count=0,
                )
            return MemoryIndexStatus(
                book_id=book_id,
                status=cast(str, state["status"]),
                document_count=cast(int, state["document_count"]),
                embedding_count=embedding_count,
                provider=cast(str | None, state["provider"]),
                model=cast(str | None, state["model"]),
                model_version=cast(str | None, state["model_version"]),
                config_hash=cast(str | None, state["config_hash"]),
                dimension=cast(int | None, state["dimension"]),
                updated_at=cast(str | None, state["updated_at"]),
            )
        finally:
            engine.dispose()

    def rebuild_embeddings(self, book_id: str, *, provider: str, model: str) -> MemoryIndexStatus:
        self.synchronize(book_id)
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                rows = list(
                    connection.execute(
                        text(
                            "SELECT * FROM memory_documents WHERE book_id=:book_id "
                            "AND currentness='CURRENT' ORDER BY object_kind,chapter_id,object_id,memory_id"
                        ),
                        {"book_id": book_id},
                    ).mappings()
                )
            if not rows:
                return self.status(book_id, synchronize=False)
            texts = [cast(str, row["text"]) for row in rows]
            batch_size = 128
            all_vectors: list[list[float]] = []
            model_version: str | None = None
            dimension: int | None = None
            for offset in range(0, len(texts), batch_size):
                result = self.embedding_gateway.embed(
                    texts[offset : offset + batch_size], provider=provider, model=model
                )
                if result.provider != provider or result.model != model:
                    raise EmbeddingOutputError(
                        "embedding adapter returned unexpected provider/model"
                    )
                if model_version is None:
                    model_version = result.model_version
                elif model_version != result.model_version:
                    raise EmbeddingOutputError("embedding model version changed during rebuild")
                for vector in result.vectors:
                    if dimension is None:
                        dimension = len(vector)
                    elif dimension != len(vector):
                        raise EmbeddingOutputError("embedding dimension changed during rebuild")
                    all_vectors.append(vector)
            if model_version is None or dimension is None or len(all_vectors) != len(rows):
                raise EmbeddingOutputError("embedding rebuild returned incomplete output")
            config_hash = embedding_config_hash(provider, model, model_version, dimension)
            now = utc_now()
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "DELETE FROM memory_embeddings WHERE memory_id IN "
                        "(SELECT memory_id FROM memory_documents WHERE book_id=:book_id "
                        "AND currentness='CURRENT')"
                    ),
                    {"book_id": book_id},
                )
                for row, vector in zip(rows, all_vectors, strict=True):
                    connection.execute(
                        text(
                            "INSERT INTO memory_embeddings(embedding_id,memory_id,provider,model,"
                            "model_version,config_hash,dimension,vector_blob,created_at) VALUES "
                            "(:embedding_id,:memory_id,:provider,:model,:model_version,:config_hash,"
                            ":dimension,:vector_blob,:created_at)"
                        ),
                        {
                            "embedding_id": new_ulid(),
                            "memory_id": cast(str, row["memory_id"]),
                            "provider": provider,
                            "model": model,
                            "model_version": model_version,
                            "config_hash": config_hash,
                            "dimension": dimension,
                            "vector_blob": _vector_blob(vector),
                            "created_at": now,
                        },
                    )
                connection.execute(
                    text(
                        "UPDATE memory_index_state SET provider=:provider,model=:model,"
                        "model_version=:model_version,config_hash=:config_hash,dimension=:dimension,"
                        "status='SEMANTIC_READY',last_error=NULL,updated_at=:updated_at "
                        "WHERE book_id=:book_id"
                    ),
                    {
                        "provider": provider,
                        "model": model,
                        "model_version": model_version,
                        "config_hash": config_hash,
                        "dimension": dimension,
                        "updated_at": now,
                        "book_id": book_id,
                    },
                )
            return self.status(book_id, synchronize=False)
        except Exception as exc:
            try:
                now = utc_now()
                with engine.begin() as connection:
                    connection.execute(
                        text(
                            "UPDATE memory_index_state SET status='FAILED',last_error=:error,"
                            "updated_at=:updated_at WHERE book_id=:book_id"
                        ),
                        {"error": str(exc)[:1000], "updated_at": now, "book_id": book_id},
                    )
            except Exception:
                pass
            raise
        finally:
            engine.dispose()

    def rebuild(self, book_id: str, *, provider: str, model: str) -> MemoryIndexStatus:
        self.synchronize(book_id)
        return self.rebuild_embeddings(book_id, provider=provider, model=model)

    @staticmethod
    def _row_to_result(
        row: dict[str, Any],
        *,
        currentness: str,
        lexical_score: float | None = None,
        semantic_score: float | None = None,
        lexical_rank: int | None = None,
        semantic_rank: int | None = None,
    ) -> MemorySearchResult:
        return MemorySearchResult(
            memory_id=cast(str, row["memory_id"]),
            object_kind=cast(str, row["object_kind"]),
            object_id=cast(str, row["object_id"]),
            chapter_id=cast(str | None, row["chapter_id"]),
            revision_id=cast(str, row["revision_id"]),
            revision_hash=cast(str, row["revision_hash"]),
            content_hash=cast(str, row["content_hash"]),
            source_status=cast(str, row["source_status"]),
            currentness=currentness,
            text=cast(str, row["text"]),
            lexical_score=lexical_score,
            semantic_score=semantic_score,
            lexical_rank=lexical_rank,
            semantic_rank=semantic_rank,
        )

    @staticmethod
    def _filters_sql(
        *, chapter_id: str | None, object_kinds: list[str]
    ) -> tuple[str, dict[str, object]]:
        clauses: list[str] = []
        params: dict[str, object] = {}
        if chapter_id:
            clauses.append("md.chapter_id=:chapter_id")
            params["chapter_id"] = chapter_id
        if object_kinds:
            placeholders: list[str] = []
            for index, kind in enumerate(object_kinds):
                key = f"kind_{index}"
                placeholders.append(f":{key}")
                params[key] = kind
            clauses.append(f"md.object_kind IN ({','.join(placeholders)})")
        return (" AND " + " AND ".join(clauses) if clauses else ""), params

    def lexical_search(
        self,
        book_id: str,
        query: str,
        *,
        scope: MemoryScope = "CURRENT",
        chapter_id: str | None = None,
        object_kinds: list[str] | None = None,
        limit: int = 12,
        exact_phrase: bool = False,
    ) -> list[MemorySearchResult]:
        self.synchronize(book_id)
        engine = self._engine(book_id)
        try:
            filter_sql, params = self._filters_sql(
                chapter_id=chapter_id, object_kinds=object_kinds or []
            )
            params.update(
                {
                    "book_id": book_id,
                    "query": _fts_expression(query, exact_phrase=exact_phrase),
                    "scope": scope,
                    "limit": limit,
                }
            )
            statement = text(
                "SELECT md.*,bm25(memory_fts) AS lexical_rank_value FROM memory_fts "
                "JOIN memory_documents md ON md.memory_id=memory_fts.memory_id "
                "WHERE memory_fts MATCH :query AND md.book_id=:book_id "
                "AND md.currentness=:scope"
                + filter_sql
                + " ORDER BY lexical_rank_value,md.memory_id LIMIT :limit"
            )
            try:
                with engine.connect() as connection:
                    rows = list(connection.execute(statement, params).mappings())
            except OperationalError as exc:
                raise MemoryQueryError("invalid FTS5 query") from exc
            canonical = self._canonical_map(engine, book_id) if scope == "CURRENT" else {}
            results: list[MemorySearchResult] = []
            for rank, row in enumerate(rows, start=1):
                row_dict = dict(row)
                if scope == "CURRENT" and not self._row_is_current(row_dict, canonical):
                    continue
                raw_rank = abs(float(row["lexical_rank_value"]))
                results.append(
                    self._row_to_result(
                        row_dict,
                        currentness=scope,
                        lexical_score=1.0 / (1.0 + raw_rank),
                        lexical_rank=rank,
                    )
                )
            return results[:limit]
        finally:
            engine.dispose()

    def semantic_search(
        self,
        book_id: str,
        query: str,
        *,
        scope: MemoryScope = "CURRENT",
        chapter_id: str | None = None,
        object_kinds: list[str] | None = None,
        limit: int = 12,
        provider: str | None = None,
        model: str | None = None,
    ) -> list[MemorySearchResult]:
        self.synchronize(book_id)
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                state = (
                    connection.execute(
                        text("SELECT * FROM memory_index_state WHERE book_id=:book_id"),
                        {"book_id": book_id},
                    )
                    .mappings()
                    .one_or_none()
                )
            if state is None or state["status"] != "SEMANTIC_READY":
                raise MemoryGateError("semantic index is stale or not built; rebuild required")
            if state["config_hash"] is None or state["dimension"] is None:
                raise MemoryGateError("semantic index configuration is incomplete")
            active_provider = provider or cast(str | None, state["provider"])
            active_model = model or cast(str | None, state["model"])
            if not active_provider or not active_model:
                raise MemoryGateError("semantic provider/model is not configured")
            if active_provider != state["provider"] or active_model != state["model"]:
                raise MemoryGateError("requested embedding configuration requires rebuild")
            query_result = self.embedding_gateway.embed(
                [query.strip()], provider=active_provider, model=active_model
            )
            query_vector_list = query_result.vectors[0]
            dimension = cast(int, state["dimension"])
            if len(query_vector_list) != dimension:
                raise MemoryGateError("query embedding dimension differs from stored index")
            query_config = embedding_config_hash(
                active_provider, active_model, query_result.model_version, dimension
            )
            if query_config != state["config_hash"]:
                raise MemoryGateError("embedding model/config changed; rebuild required")

            filter_sql, params = self._filters_sql(
                chapter_id=chapter_id, object_kinds=object_kinds or []
            )
            params.update(
                {
                    "book_id": book_id,
                    "scope": scope,
                    "config_hash": cast(str, state["config_hash"]),
                }
            )
            with engine.connect() as connection:
                rows = list(
                    connection.execute(
                        text(
                            "SELECT md.*,me.vector_blob,me.dimension FROM memory_embeddings me "
                            "JOIN memory_documents md ON md.memory_id=me.memory_id "
                            "WHERE md.book_id=:book_id AND md.currentness=:scope "
                            "AND me.config_hash=:config_hash"
                            + filter_sql
                            + " ORDER BY md.memory_id"
                        ),
                        params,
                    ).mappings()
                )
            canonical = self._canonical_map(engine, book_id) if scope == "CURRENT" else {}
            eligible: list[dict[str, Any]] = []
            vectors: list[np.ndarray[Any, np.dtype[np.float32]]] = []
            for row in rows:
                row_dict = dict(row)
                if scope == "CURRENT" and not self._row_is_current(row_dict, canonical):
                    continue
                eligible.append(row_dict)
                vectors.append(
                    _vector_from_blob(cast(bytes, row["vector_blob"]), cast(int, row["dimension"]))
                )
            if not eligible:
                return []
            matrix = np.stack(vectors).astype(np.float32, copy=False)
            query_vector = np.asarray(query_vector_list, dtype=np.float32)
            scores = exact_cosine_scores(query_vector, matrix)
            order = sorted(
                range(len(eligible)),
                key=lambda index: (-float(scores[index]), eligible[index]["memory_id"]),
            )
            results: list[MemorySearchResult] = []
            for rank, index in enumerate(order[:limit], start=1):
                results.append(
                    self._row_to_result(
                        eligible[index],
                        currentness=scope,
                        semantic_score=float(scores[index]),
                        semantic_rank=rank,
                    )
                )
            return results
        finally:
            engine.dispose()

    def hybrid_search(
        self,
        book_id: str,
        query: str,
        *,
        scope: MemoryScope = "CURRENT",
        chapter_id: str | None = None,
        object_kinds: list[str] | None = None,
        limit: int = 12,
        exact_phrase: bool = False,
        provider: str | None = None,
        model: str | None = None,
    ) -> list[MemorySearchResult]:
        candidate_limit = max(limit * 4, 24)
        lexical = self.lexical_search(
            book_id,
            query,
            scope=scope,
            chapter_id=chapter_id,
            object_kinds=object_kinds,
            limit=candidate_limit,
            exact_phrase=exact_phrase,
        )
        semantic = self.semantic_search(
            book_id,
            query,
            scope=scope,
            chapter_id=chapter_id,
            object_kinds=object_kinds,
            limit=candidate_limit,
            provider=provider,
            model=model,
        )
        combined: dict[str, MemorySearchResult] = {}
        scores: dict[str, float] = {}
        rrf_k = 60.0
        for result in lexical:
            combined[result.memory_id] = result.model_copy(deep=True)
            rank = result.lexical_rank or candidate_limit
            scores[result.memory_id] = scores.get(result.memory_id, 0.0) + 1.0 / (rrf_k + rank)
        for result in semantic:
            existing = combined.get(result.memory_id)
            if existing is None:
                existing = result.model_copy(deep=True)
                combined[result.memory_id] = existing
            else:
                existing.semantic_score = result.semantic_score
                existing.semantic_rank = result.semantic_rank
            rank = result.semantic_rank or candidate_limit
            scores[result.memory_id] = scores.get(result.memory_id, 0.0) + 1.0 / (rrf_k + rank)
        ordered_ids = sorted(combined, key=lambda memory_id: (-scores[memory_id], memory_id))[
            :limit
        ]
        output: list[MemorySearchResult] = []
        for rank, memory_id in enumerate(ordered_ids, start=1):
            result = combined[memory_id]
            result.fused_score = scores[memory_id]
            result.fused_rank = rank
            output.append(result)
        return output

    def search(self, book_id: str, request: MemorySearchRequest) -> list[MemorySearchResult]:
        object_kinds = [str(kind) for kind in request.object_kinds]
        if request.mode == "LEXICAL":
            return self.lexical_search(
                book_id,
                request.query,
                scope=request.scope,
                chapter_id=request.chapter_id,
                object_kinds=object_kinds,
                limit=request.limit,
                exact_phrase=request.exact_phrase,
            )
        if request.mode == "SEMANTIC":
            return self.semantic_search(
                book_id,
                request.query,
                scope=request.scope,
                chapter_id=request.chapter_id,
                object_kinds=object_kinds,
                limit=request.limit,
                provider=request.provider,
                model=request.model,
            )
        return self.hybrid_search(
            book_id,
            request.query,
            scope=request.scope,
            chapter_id=request.chapter_id,
            object_kinds=object_kinds,
            limit=request.limit,
            exact_phrase=request.exact_phrase,
            provider=request.provider,
            model=request.model,
        )
