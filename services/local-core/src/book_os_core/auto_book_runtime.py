from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import StrEnum
import hashlib
import json
from pathlib import Path
from typing import Any, Literal, cast

from pydantic import BaseModel, Field, model_validator
from sqlalchemy import text
from sqlalchemy.engine import Engine

from .authority import canonical_json, new_ulid
from .authority_types import utc_now
from .db import create_database
from .projects import ProjectService


class AutoBookRuntimeError(RuntimeError):
    pass


class AutoBookLeaseError(AutoBookRuntimeError):
    pass


class AutoBookBudgetError(AutoBookRuntimeError):
    pass


class AutoBookStage(StrEnum):
    DEFINITION = "DEFINITION"
    RESEARCH = "RESEARCH"
    ARCHITECTURE = "ARCHITECTURE"
    CHAPTER_CONTEXT = "CHAPTER_CONTEXT"
    WRITING = "WRITING"
    CHAPTER_REVIEW = "CHAPTER_REVIEW"
    MIDBOOK_AUDIT = "MIDBOOK_AUDIT"
    WHOLE_BOOK_EDIT = "WHOLE_BOOK_EDIT"
    FACT_CHECK = "FACT_CHECK"
    LITERARY_EDIT = "LITERARY_EDIT"
    VISUALS = "VISUALS"
    INDEPENDENT_CRITIQUE = "INDEPENDENT_CRITIQUE"
    CORRECTION = "CORRECTION"
    MASTER_AND_EXPORTS = "MASTER_AND_EXPORTS"


AUTO_BOOK_STAGES: tuple[AutoBookStage, ...] = tuple(AutoBookStage)

AutoBookRuntimeStatus = Literal[
    "QUEUED",
    "RUNNING",
    "PAUSED",
    "AWAITING_CLARIFICATION",
    "BUDGET_REACHED",
    "NEEDS_REVISION",
    "UNKNOWN_OUTCOME",
    "MANUSCRIPT_READY",
    "PACKAGE_READY",
    "FAILED",
]
AutoBookOutputKind = Literal[
    "FULL_MANUSCRIPT_DOCX",
    "LITRES_EBOOK_DOCX",
    "READING_PDF",
    "EPUB",
    "AUDIO_READING_DOCX",
    "AUDIO_LITRES_DOCX",
    "VOICE_TEXT_TXT",
    "PRONUNCIATION_DICTIONARY",
    "READER_EXTRAS",
    "PUBLISHER_PACK",
]
AttachmentRole = Literal["SOURCE", "LEGACY_BOOK", "VOICE_REFERENCE"]


class AutoBookAttachment(BaseModel):
    path: str = Field(min_length=1, max_length=4000)
    role: AttachmentRole
    intent: Literal["WRITE_FROM_ZERO", "DEEP_REWRITE", "CONTINUE"] | None = None
    content_hash: str | None = Field(default=None, min_length=64, max_length=64)

    @model_validator(mode="after")
    def legacy_requires_intent(self) -> AutoBookAttachment:
        if self.role == "LEGACY_BOOK" and self.intent is None:
            raise ValueError("legacy book attachment requires an explicit intent")
        return self


class AutoBookOutputSelection(BaseModel):
    full_manuscript_docx: bool = True
    litres_ebook_docx: bool = False
    reading_pdf: bool = False
    epub: bool = False
    audio_reading_docx: bool = False
    audio_litres_docx: bool = False
    voice_text_txt: bool = False
    pronunciation_dictionary: bool = False
    reader_extras: bool = False
    publisher_pack: bool = False

    def selected(self) -> list[AutoBookOutputKind]:
        mapping: tuple[tuple[str, AutoBookOutputKind], ...] = (
            ("full_manuscript_docx", "FULL_MANUSCRIPT_DOCX"),
            ("litres_ebook_docx", "LITRES_EBOOK_DOCX"),
            ("reading_pdf", "READING_PDF"),
            ("epub", "EPUB"),
            ("audio_reading_docx", "AUDIO_READING_DOCX"),
            ("audio_litres_docx", "AUDIO_LITRES_DOCX"),
            ("voice_text_txt", "VOICE_TEXT_TXT"),
            ("pronunciation_dictionary", "PRONUNCIATION_DICTIONARY"),
            ("reader_extras", "READER_EXTRAS"),
            ("publisher_pack", "PUBLISHER_PACK"),
        )
        return [output for field, output in mapping if bool(getattr(self, field))]


class AutoBookVisualPolicy(BaseModel):
    as_needed: bool = True
    allow_generative_illustrations: bool = False
    include_optional_illustrations: bool = True


class AutoBookIntent(BaseModel):
    idea: str = Field(min_length=3, max_length=12000)
    reader_hint: str = Field(default="", max_length=6000)
    author_name: str = Field(min_length=1, max_length=300)
    series_name: str | None = Field(default=None, max_length=500)
    target_characters: int = Field(default=180_000, ge=4_000, le=2_000_000)
    model_choice: str = "AUTO"
    outputs: AutoBookOutputSelection = Field(default_factory=AutoBookOutputSelection)
    visuals: AutoBookVisualPolicy = Field(default_factory=AutoBookVisualPolicy)
    attachments: list[AutoBookAttachment] = Field(default_factory=list, max_length=40)
    max_cost_usd_per_request: float = Field(default=1.0, gt=0, le=20)
    max_total_cost_usd: float = Field(default=25.0, gt=0, le=500)
    max_requests: int = Field(default=40, ge=1, le=500)
    final_human_acceptance_required: bool = True

    @model_validator(mode="after")
    def validate_budget(self) -> AutoBookIntent:
        if self.max_total_cost_usd < self.max_cost_usd_per_request:
            raise ValueError("total cost limit must cover at least one request")
        if not self.outputs.selected():
            raise ValueError("at least one output must be selected")
        return self


class AutoBookRuntimeView(BaseModel):
    run_id: str
    book_id: str
    intent: AutoBookIntent
    status: AutoBookRuntimeStatus
    current_stage: AutoBookStage
    stage_index: int
    progress_completed: int
    progress_total: int
    estimated_cost_usd: float
    reserved_cost_usd: float
    confirmed_cost_usd: float
    unknown_cost_usd: float
    requests_used: int
    last_message: str
    error_code: str | None
    created_at: str
    updated_at: str

    @property
    def progress_percent(self) -> int:
        if self.progress_total <= 0:
            return 0
        return min(100, round(self.progress_completed * 100 / self.progress_total))


class AutoBookOperationView(BaseModel):
    operation_id: str
    run_id: str
    ordinal: int
    stage: AutoBookStage
    operation: str
    idempotency_key: str
    input_hash: str
    state: Literal["PENDING", "RESERVED", "RUNNING", "SUCCEEDED", "FAILED", "UNKNOWN", "STALE"]
    provider: str | None
    model: str | None
    reasoning_effort: str | None
    provider_run_id: str | None
    estimated_cost_usd: float
    reserved_cost_usd: float
    confirmed_cost_usd: float | None
    output: dict[str, Any] | None
    created_at: str
    updated_at: str


class AutoBookArtifactView(BaseModel):
    artifact_id: str
    run_id: str
    output_kind: AutoBookOutputKind
    master_hash: str
    profile_version: str
    exporter_version: str
    relative_path: str
    content_hash: str
    byte_length: int
    status: Literal["READY", "FAILED", "STALE"]
    qa: dict[str, Any]
    created_at: str


def _hash(value: object) -> str:
    return hashlib.sha256(canonical_json(cast(Any, value)).encode("utf-8")).hexdigest()


class DurableAutoBookRuntime:
    """SQLite-backed orchestration ledger used by Local Core, never by the desktop UI.

    The ledger owns leases, idempotency, budget reservation and recovery.  External operations are
    persisted before execution.  An interrupted operation becomes UNKNOWN and is never retried
    automatically unless a provider-specific retrieval path resolves its provider run id.
    """

    LEASE_SECONDS = 90
    RELEASE_RESERVE_RATIO = 0.25

    def __init__(self, data_dir: Path) -> None:
        self.projects = ProjectService(data_dir)

    def _engine(self, book_id: str) -> Engine:
        self.projects.get_project(book_id)
        return create_database(self.projects.projects_dir / book_id / "project.sqlite")

    @staticmethod
    def _row_to_run(row: Any) -> AutoBookRuntimeView:
        return AutoBookRuntimeView(
            run_id=str(row["run_id"]),
            book_id=str(row["book_id"]),
            intent=AutoBookIntent.model_validate_json(str(row["intent_json"])),
            status=cast(AutoBookRuntimeStatus, str(row["status"])),
            current_stage=AutoBookStage(str(row["current_stage"])),
            stage_index=int(row["stage_index"]),
            progress_completed=int(row["progress_completed"]),
            progress_total=int(row["progress_total"]),
            estimated_cost_usd=float(row["estimated_cost_usd"]),
            reserved_cost_usd=float(row["reserved_cost_usd"]),
            confirmed_cost_usd=float(row["confirmed_cost_usd"]),
            unknown_cost_usd=float(row["unknown_cost_usd"]),
            requests_used=int(row["requests_used"]),
            last_message=str(row["last_message"]),
            error_code=str(row["error_code"]) if row["error_code"] is not None else None,
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    def create_run(
        self,
        book_id: str,
        intent: AutoBookIntent,
        *,
        authorized_by: str = "owner",
        run_id: str | None = None,
    ) -> AutoBookRuntimeView:
        engine = self._engine(book_id)
        resolved_run_id = run_id or new_ulid()
        now = utc_now()
        progress_total = len(AUTO_BOOK_STAGES) + len(intent.outputs.selected())
        estimated = round(
            min(intent.max_total_cost_usd, intent.max_cost_usd_per_request * intent.max_requests),
            6,
        )
        release_reserve = round(intent.max_total_cost_usd * self.RELEASE_RESERVE_RATIO, 6)
        scope = {
            "stages": [stage.value for stage in AUTO_BOOK_STAGES],
            "outputs": intent.outputs.selected(),
            "visuals": intent.visuals.model_dump(mode="json"),
            "final_human_acceptance_required": intent.final_human_acceptance_required,
        }
        try:
            with engine.begin() as connection:
                active = connection.execute(
                    text(
                        "SELECT run_id FROM auto_book_runtime_runs WHERE book_id=:book_id AND "
                        "status IN ('QUEUED','RUNNING','PAUSED','AWAITING_CLARIFICATION',"
                        "'BUDGET_REACHED','NEEDS_REVISION','UNKNOWN_OUTCOME','MANUSCRIPT_READY') "
                        "ORDER BY created_at DESC LIMIT 1"
                    ),
                    {"book_id": book_id},
                ).scalar_one_or_none()
                if active is not None:
                    raise AutoBookRuntimeError(f"active Auto Book run already exists: {active}")
                connection.execute(
                    text(
                        "INSERT INTO auto_book_runtime_runs("
                        "run_id,book_id,intent_json,status,current_stage,stage_index,"
                        "progress_completed,progress_total,estimated_cost_usd,reserved_cost_usd,"
                        "confirmed_cost_usd,unknown_cost_usd,requests_used,last_message,created_at,"
                        "updated_at) VALUES (:run_id,:book_id,:intent_json,'QUEUED','DEFINITION',"
                        "0,0,:progress_total,:estimated_cost_usd,:release_reserve,0,0,0,"
                        ":last_message,:created_at,:updated_at)"
                    ),
                    {
                        "run_id": resolved_run_id,
                        "book_id": book_id,
                        "intent_json": intent.model_dump_json(),
                        "progress_total": progress_total,
                        "estimated_cost_usd": estimated,
                        "release_reserve": release_reserve,
                        "last_message": "Запуск сохранён; Local Core готовит определение книги",
                        "created_at": now,
                        "updated_at": now,
                    },
                )
                connection.execute(
                    text(
                        "INSERT INTO auto_book_authorizations(authorization_id,book_id,run_id,"
                        "scope_json,input_revisions_json,max_total_cost_usd,max_requests,"
                        "authorized_by,authorized_by_kind,created_at) VALUES (:authorization_id,"
                        ":book_id,:run_id,:scope_json,:input_revisions_json,:max_total_cost_usd,"
                        ":max_requests,:authorized_by,'OWNER',:created_at)"
                    ),
                    {
                        "authorization_id": new_ulid(),
                        "book_id": book_id,
                        "run_id": resolved_run_id,
                        "scope_json": json.dumps(scope, ensure_ascii=False, sort_keys=True),
                        "input_revisions_json": "[]",
                        "max_total_cost_usd": intent.max_total_cost_usd,
                        "max_requests": intent.max_requests,
                        "authorized_by": authorized_by,
                        "created_at": now,
                    },
                )
        finally:
            engine.dispose()
        return self.get(book_id, resolved_run_id)

    def get(self, book_id: str, run_id: str) -> AutoBookRuntimeView:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                row = (
                    connection.execute(
                        text("SELECT * FROM auto_book_runtime_runs WHERE run_id=:run_id"),
                        {"run_id": run_id},
                    )
                    .mappings()
                    .one_or_none()
                )
        finally:
            engine.dispose()
        if row is None:
            raise AutoBookRuntimeError(f"Auto Book runtime not found: {run_id}")
        return self._row_to_run(row)

    def latest(self, book_id: str) -> AutoBookRuntimeView | None:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                row = (
                    connection.execute(
                        text(
                            "SELECT * FROM auto_book_runtime_runs WHERE book_id=:book_id "
                            "ORDER BY created_at DESC,run_id DESC LIMIT 1"
                        ),
                        {"book_id": book_id},
                    )
                    .mappings()
                    .one_or_none()
                )
        finally:
            engine.dispose()
        return self._row_to_run(row) if row is not None else None

    def claim(self, book_id: str, run_id: str, worker_id: str) -> AutoBookRuntimeView:
        engine = self._engine(book_id)
        now_dt = datetime.now(UTC)
        now = now_dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")
        expires = (
            (now_dt + timedelta(seconds=self.LEASE_SECONDS))
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z")
        )
        try:
            with engine.begin() as connection:
                updated = connection.execute(
                    text(
                        "UPDATE auto_book_runtime_runs SET worker_id=:worker_id,"
                        "lease_expires_at=:expires,status='RUNNING',updated_at=:now "
                        "WHERE run_id=:run_id AND status IN ('QUEUED','RUNNING') AND "
                        "(worker_id IS NULL OR worker_id=:worker_id OR lease_expires_at<:now)"
                    ),
                    {
                        "run_id": run_id,
                        "worker_id": worker_id,
                        "expires": expires,
                        "now": now,
                    },
                )
                if updated.rowcount != 1:
                    raise AutoBookLeaseError("run is paused, terminal, or owned by another worker")
        finally:
            engine.dispose()
        return self.get(book_id, run_id)

    def release(self, book_id: str, run_id: str, worker_id: str) -> None:
        engine = self._engine(book_id)
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "UPDATE auto_book_runtime_runs SET worker_id=NULL,lease_expires_at=NULL,"
                        "updated_at=:updated_at WHERE run_id=:run_id AND worker_id=:worker_id"
                    ),
                    {"run_id": run_id, "worker_id": worker_id, "updated_at": utc_now()},
                )
        finally:
            engine.dispose()

    def ensure_operation(
        self,
        book_id: str,
        run_id: str,
        *,
        ordinal: int,
        stage: AutoBookStage,
        operation: str,
        input_payload: object,
        provider: str | None = None,
        model: str | None = None,
        reasoning_effort: str | None = None,
        estimated_cost_usd: float = 0.0,
    ) -> AutoBookOperationView:
        input_hash = _hash(input_payload)
        idempotency_key = _hash({"run_id": run_id, "operation": operation, "input": input_hash})
        engine = self._engine(book_id)
        now = utc_now()
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT OR IGNORE INTO auto_book_operations(operation_id,run_id,ordinal,"
                        "stage,operation,idempotency_key,input_hash,state,provider,model,"
                        "reasoning_effort,estimated_cost_usd,reserved_cost_usd,created_at,updated_at) "
                        "VALUES (:operation_id,:run_id,:ordinal,:stage,:operation,:idempotency_key,"
                        ":input_hash,'PENDING',:provider,:model,:reasoning_effort,"
                        ":estimated_cost_usd,0,:created_at,:updated_at)"
                    ),
                    {
                        "operation_id": new_ulid(),
                        "run_id": run_id,
                        "ordinal": ordinal,
                        "stage": stage.value,
                        "operation": operation,
                        "idempotency_key": idempotency_key,
                        "input_hash": input_hash,
                        "provider": provider,
                        "model": model,
                        "reasoning_effort": reasoning_effort,
                        "estimated_cost_usd": estimated_cost_usd,
                        "created_at": now,
                        "updated_at": now,
                    },
                )
                row = (
                    connection.execute(
                        text(
                            "SELECT * FROM auto_book_operations WHERE run_id=:run_id AND "
                            "idempotency_key=:idempotency_key"
                        ),
                        {"run_id": run_id, "idempotency_key": idempotency_key},
                    )
                    .mappings()
                    .one()
                )
        finally:
            engine.dispose()
        return self._row_to_operation(row)

    @staticmethod
    def _row_to_operation(row: Any) -> AutoBookOperationView:
        raw_output = row["output_json"]
        return AutoBookOperationView(
            operation_id=str(row["operation_id"]),
            run_id=str(row["run_id"]),
            ordinal=int(row["ordinal"]),
            stage=AutoBookStage(str(row["stage"])),
            operation=str(row["operation"]),
            idempotency_key=str(row["idempotency_key"]),
            input_hash=str(row["input_hash"]),
            state=cast(Any, str(row["state"])),
            provider=str(row["provider"]) if row["provider"] is not None else None,
            model=str(row["model"]) if row["model"] is not None else None,
            reasoning_effort=(
                str(row["reasoning_effort"]) if row["reasoning_effort"] is not None else None
            ),
            provider_run_id=(
                str(row["provider_run_id"]) if row["provider_run_id"] is not None else None
            ),
            estimated_cost_usd=float(row["estimated_cost_usd"]),
            reserved_cost_usd=float(row["reserved_cost_usd"]),
            confirmed_cost_usd=(
                float(row["confirmed_cost_usd"]) if row["confirmed_cost_usd"] is not None else None
            ),
            output=cast(dict[str, Any], json.loads(str(raw_output))) if raw_output else None,
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    def reserve(
        self,
        book_id: str,
        run_id: str,
        operation_id: str,
        amount_usd: float,
    ) -> AutoBookOperationView:
        if amount_usd <= 0:
            raise AutoBookBudgetError("reservation must be positive")
        engine = self._engine(book_id)
        now = utc_now()
        budget_error: str | None = None
        try:
            with engine.begin() as connection:
                run = (
                    connection.execute(
                        text(
                            "SELECT r.*,a.max_total_cost_usd,a.max_requests FROM "
                            "auto_book_runtime_runs r JOIN auto_book_authorizations a "
                            "ON a.run_id=r.run_id WHERE r.run_id=:run_id"
                        ),
                        {"run_id": run_id},
                    )
                    .mappings()
                    .one()
                )
                available = float(run["max_total_cost_usd"]) - (
                    float(run["reserved_cost_usd"])
                    + float(run["confirmed_cost_usd"])
                    + float(run["unknown_cost_usd"])
                )
                if int(run["requests_used"]) >= int(run["max_requests"]):
                    budget_error = "request limit reached"
                elif amount_usd > available + 1e-9:
                    budget_error = "total budget would be exceeded"
                if budget_error is not None:
                    connection.execute(
                        text(
                            "UPDATE auto_book_runtime_runs SET status='BUDGET_REACHED',"
                            "last_message='Бюджет исчерпан; текст и прогресс сохранены',"
                            "updated_at=:updated_at WHERE run_id=:run_id"
                        ),
                        {"run_id": run_id, "updated_at": now},
                    )
                else:
                    updated = connection.execute(
                        text(
                            "UPDATE auto_book_operations SET state='RESERVED',reserved_cost_usd=:amount,"
                            "updated_at=:updated_at WHERE operation_id=:operation_id AND run_id=:run_id "
                            "AND state='PENDING'"
                        ),
                        {
                            "amount": amount_usd,
                            "updated_at": now,
                            "operation_id": operation_id,
                            "run_id": run_id,
                        },
                    )
                    if updated.rowcount != 1:
                        raise AutoBookBudgetError("operation is not available for reservation")
                    connection.execute(
                        text(
                            "UPDATE auto_book_runtime_runs SET reserved_cost_usd=reserved_cost_usd+"
                            ":amount,requests_used=requests_used+1,updated_at=:updated_at "
                            "WHERE run_id=:run_id"
                        ),
                        {"amount": amount_usd, "updated_at": now, "run_id": run_id},
                    )
        finally:
            engine.dispose()
        if budget_error is not None:
            raise AutoBookBudgetError(budget_error)
        return self.operation(book_id, operation_id)

    def operation(self, book_id: str, operation_id: str) -> AutoBookOperationView:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                row = (
                    connection.execute(
                        text("SELECT * FROM auto_book_operations WHERE operation_id=:operation_id"),
                        {"operation_id": operation_id},
                    )
                    .mappings()
                    .one_or_none()
                )
        finally:
            engine.dispose()
        if row is None:
            raise AutoBookRuntimeError(f"operation not found: {operation_id}")
        return self._row_to_operation(row)

    def complete_operation(
        self,
        book_id: str,
        run_id: str,
        operation_id: str,
        *,
        output: dict[str, Any],
        confirmed_cost_usd: float = 0.0,
        provider_run_id: str | None = None,
    ) -> AutoBookRuntimeView:
        engine = self._engine(book_id)
        now = utc_now()
        try:
            with engine.begin() as connection:
                operation = (
                    connection.execute(
                        text(
                            "SELECT * FROM auto_book_operations WHERE operation_id=:operation_id "
                            "AND run_id=:run_id"
                        ),
                        {"operation_id": operation_id, "run_id": run_id},
                    )
                    .mappings()
                    .one()
                )
                if operation["state"] == "SUCCEEDED":
                    return self.get(book_id, run_id)
                if operation["state"] not in {"PENDING", "RESERVED", "RUNNING"}:
                    raise AutoBookRuntimeError(
                        "operation cannot be completed from its current state"
                    )
                reserved = float(operation["reserved_cost_usd"])
                if confirmed_cost_usd < 0 or confirmed_cost_usd > reserved + 1e-9:
                    raise AutoBookBudgetError("confirmed cost exceeds the operation reservation")
                connection.execute(
                    text(
                        "UPDATE auto_book_operations SET state='SUCCEEDED',provider_run_id=:provider_run_id,"
                        "confirmed_cost_usd=:confirmed,output_json=:output_json,updated_at=:updated_at "
                        "WHERE operation_id=:operation_id"
                    ),
                    {
                        "provider_run_id": provider_run_id,
                        "confirmed": confirmed_cost_usd,
                        "output_json": json.dumps(output, ensure_ascii=False, sort_keys=True),
                        "updated_at": now,
                        "operation_id": operation_id,
                    },
                )
                connection.execute(
                    text(
                        "UPDATE auto_book_runtime_runs SET reserved_cost_usd=MAX(0,reserved_cost_usd-"
                        ":reserved),confirmed_cost_usd=confirmed_cost_usd+:confirmed,"
                        "progress_completed=progress_completed+1,last_message=:message,"
                        "updated_at=:updated_at WHERE run_id=:run_id"
                    ),
                    {
                        "reserved": reserved,
                        "confirmed": confirmed_cost_usd,
                        "message": f"Завершён этап: {operation['stage']}",
                        "updated_at": now,
                        "run_id": run_id,
                    },
                )
        finally:
            engine.dispose()
        return self.get(book_id, run_id)

    def mark_unknown(
        self,
        book_id: str,
        run_id: str,
        operation_id: str,
        *,
        provider_run_id: str | None,
    ) -> AutoBookRuntimeView:
        engine = self._engine(book_id)
        now = utc_now()
        try:
            with engine.begin() as connection:
                operation = (
                    connection.execute(
                        text(
                            "SELECT reserved_cost_usd FROM auto_book_operations "
                            "WHERE operation_id=:operation_id AND run_id=:run_id"
                        ),
                        {"operation_id": operation_id, "run_id": run_id},
                    )
                    .mappings()
                    .one()
                )
                reserved = float(operation["reserved_cost_usd"])
                connection.execute(
                    text(
                        "UPDATE auto_book_operations SET state='UNKNOWN',provider_run_id=:provider_run_id,"
                        "updated_at=:updated_at WHERE operation_id=:operation_id"
                    ),
                    {
                        "provider_run_id": provider_run_id,
                        "updated_at": now,
                        "operation_id": operation_id,
                    },
                )
                connection.execute(
                    text(
                        "UPDATE auto_book_runtime_runs SET status='UNKNOWN_OUTCOME',"
                        "reserved_cost_usd=MAX(0,reserved_cost_usd-:reserved),"
                        "unknown_cost_usd=unknown_cost_usd+:reserved,"
                        "last_message='Исход запроса неизвестен; автоматический повтор заблокирован',"
                        "worker_id=NULL,lease_expires_at=NULL,updated_at=:updated_at "
                        "WHERE run_id=:run_id"
                    ),
                    {"reserved": reserved, "updated_at": now, "run_id": run_id},
                )
        finally:
            engine.dispose()
        return self.get(book_id, run_id)

    def set_stage(
        self,
        book_id: str,
        run_id: str,
        stage: AutoBookStage,
        *,
        message: str,
        status: AutoBookRuntimeStatus = "RUNNING",
    ) -> AutoBookRuntimeView:
        index = AUTO_BOOK_STAGES.index(stage)
        engine = self._engine(book_id)
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "UPDATE auto_book_runtime_runs SET current_stage=:stage,stage_index=:stage_index,"
                        "status=:status,last_message=:message,updated_at=:updated_at "
                        "WHERE run_id=:run_id"
                    ),
                    {
                        "stage": stage.value,
                        "stage_index": index,
                        "status": status,
                        "message": message,
                        "updated_at": utc_now(),
                        "run_id": run_id,
                    },
                )
        finally:
            engine.dispose()
        return self.get(book_id, run_id)

    def pause(self, book_id: str, run_id: str) -> AutoBookRuntimeView:
        return self._set_control_status(book_id, run_id, "PAUSED", "Остановлено автором")

    def resume(self, book_id: str, run_id: str) -> AutoBookRuntimeView:
        current = self.get(book_id, run_id)
        if current.status == "UNKNOWN_OUTCOME":
            raise AutoBookRuntimeError(
                "unknown paid outcome must be resolved before the run can continue"
            )
        return self._set_control_status(
            book_id, run_id, "QUEUED", "Продолжение поставлено в очередь"
        )

    def _set_control_status(
        self,
        book_id: str,
        run_id: str,
        status: AutoBookRuntimeStatus,
        message: str,
    ) -> AutoBookRuntimeView:
        engine = self._engine(book_id)
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "UPDATE auto_book_runtime_runs SET status=:status,last_message=:message,"
                        "worker_id=NULL,lease_expires_at=NULL,updated_at=:updated_at "
                        "WHERE run_id=:run_id"
                    ),
                    {
                        "status": status,
                        "message": message,
                        "updated_at": utc_now(),
                        "run_id": run_id,
                    },
                )
        finally:
            engine.dispose()
        return self.get(book_id, run_id)

    def register_artifact(
        self,
        book_id: str,
        run_id: str,
        *,
        output_kind: AutoBookOutputKind,
        master_hash: str,
        profile_version: str,
        exporter_version: str,
        relative_path: str,
        payload: bytes,
        qa: dict[str, Any],
    ) -> AutoBookArtifactView:
        if qa.get("passed") is not True:
            raise AutoBookRuntimeError("a ready output artifact requires passed QA")
        engine = self._engine(book_id)
        now = utc_now()
        artifact_id = new_ulid()
        content_hash = hashlib.sha256(payload).hexdigest()
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "UPDATE auto_book_output_artifacts SET status='STALE' WHERE run_id=:run_id "
                        "AND output_kind=:output_kind AND master_hash!=:master_hash AND status='READY'"
                    ),
                    {
                        "run_id": run_id,
                        "output_kind": output_kind,
                        "master_hash": master_hash,
                    },
                )
                connection.execute(
                    text(
                        "INSERT INTO auto_book_output_artifacts(artifact_id,run_id,output_kind,"
                        "master_hash,profile_version,exporter_version,relative_path,content_hash,"
                        "byte_length,status,qa_json,created_at) VALUES (:artifact_id,:run_id,"
                        ":output_kind,:master_hash,:profile_version,:exporter_version,:relative_path,"
                        ":content_hash,:byte_length,'READY',:qa_json,:created_at)"
                    ),
                    {
                        "artifact_id": artifact_id,
                        "run_id": run_id,
                        "output_kind": output_kind,
                        "master_hash": master_hash,
                        "profile_version": profile_version,
                        "exporter_version": exporter_version,
                        "relative_path": relative_path,
                        "content_hash": content_hash,
                        "byte_length": len(payload),
                        "qa_json": json.dumps(qa, ensure_ascii=False, sort_keys=True),
                        "created_at": now,
                    },
                )
                row = (
                    connection.execute(
                        text(
                            "SELECT * FROM auto_book_output_artifacts WHERE artifact_id=:artifact_id"
                        ),
                        {"artifact_id": artifact_id},
                    )
                    .mappings()
                    .one()
                )
        finally:
            engine.dispose()
        return AutoBookArtifactView(
            artifact_id=str(row["artifact_id"]),
            run_id=str(row["run_id"]),
            output_kind=cast(AutoBookOutputKind, str(row["output_kind"])),
            master_hash=str(row["master_hash"]),
            profile_version=str(row["profile_version"]),
            exporter_version=str(row["exporter_version"]),
            relative_path=str(row["relative_path"]),
            content_hash=str(row["content_hash"]),
            byte_length=int(row["byte_length"]),
            status=cast(Any, str(row["status"])),
            qa=cast(dict[str, Any], json.loads(str(row["qa_json"]))),
            created_at=str(row["created_at"]),
        )

    def list_artifacts(self, book_id: str, run_id: str) -> list[AutoBookArtifactView]:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                rows = list(
                    connection.execute(
                        text(
                            "SELECT * FROM auto_book_output_artifacts WHERE run_id=:run_id "
                            "ORDER BY created_at,artifact_id"
                        ),
                        {"run_id": run_id},
                    ).mappings()
                )
        finally:
            engine.dispose()
        return [
            AutoBookArtifactView(
                artifact_id=str(row["artifact_id"]),
                run_id=str(row["run_id"]),
                output_kind=cast(AutoBookOutputKind, str(row["output_kind"])),
                master_hash=str(row["master_hash"]),
                profile_version=str(row["profile_version"]),
                exporter_version=str(row["exporter_version"]),
                relative_path=str(row["relative_path"]),
                content_hash=str(row["content_hash"]),
                byte_length=int(row["byte_length"]),
                status=cast(Any, str(row["status"])),
                qa=cast(dict[str, Any], json.loads(str(row["qa_json"]))),
                created_at=str(row["created_at"]),
            )
            for row in rows
        ]

    def request_change(self, book_id: str, run_id: str, request_text: str) -> str:
        cleaned = request_text.strip()
        if not cleaned:
            raise AutoBookRuntimeError("change request must not be blank")
        lowered = cleaned.casefold()
        broad = any(word in lowered for word in ("вся книга", "обещание книги", "другая аудитория"))
        affected = ["BOOK_CONTRACT", "ARCHITECTURE", "ALL_CHAPTERS"] if broad else ["TARGETED_TEXT"]
        change_id = new_ulid()
        now = utc_now()
        engine = self._engine(book_id)
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO auto_book_change_requests(change_id,run_id,request_text,"
                        "affected_json,status,created_at,updated_at) VALUES (:change_id,:run_id,"
                        ":request_text,:affected_json,:status,:created_at,:updated_at)"
                    ),
                    {
                        "change_id": change_id,
                        "run_id": run_id,
                        "request_text": cleaned,
                        "affected_json": json.dumps(affected, ensure_ascii=False),
                        "status": "NEEDS_CLARIFICATION" if broad else "PROPOSED",
                        "created_at": now,
                        "updated_at": now,
                    },
                )
        finally:
            engine.dispose()
        return change_id
