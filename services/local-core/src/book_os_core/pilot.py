from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any, Literal, cast

from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.engine import Engine

from .authority import new_ulid
from .authority_types import utc_now
from .db import create_database
from .projects import ProjectService
from .secrets import SecretStore

PilotStage = Literal[
    "IDEA",
    "BOOK_DEFINITION",
    "RESEARCH",
    "BOOK_CONTRACT",
    "ARCHITECTURE",
    "CHAPTER_CONTRACTS",
    "DRAFTING",
    "BOOK_MEMORY",
    "EDITORIAL",
    "BOOKBENCH",
    "FINAL_REVIEW",
    "LITERARY_MASTER",
]
PilotEventKind = Literal[
    "STARTED",
    "COMPLETED",
    "CHECKPOINT",
    "HUMAN_REVIEW",
    "NOT_APPLICABLE",
    "LITERARY_QUALITY_JUDGMENT",
    "COST_CHECKPOINT",
    "DEFECT_REVIEW",
]
PilotOutcome = Literal["SUCCESS", "ATTENTION", "BLOCKED", "NOT_APPLICABLE"]
ObservationCategory = Literal[
    "PRODUCT_DEFECT",
    "WORKFLOW_FRICTION",
    "MISSED_ERROR",
    "BOOKBENCH_FALSE_POSITIVE",
    "BOOKBENCH_FALSE_NEGATIVE",
    "MODEL_QUALITY_FAILURE",
    "VOICE_FAILURE",
    "RESEARCH_TRACEABILITY_FAILURE",
    "HUMAN_DECISION_REASON",
    "OTHER",
]
ObservationSeverity = Literal["INFO", "ATTENTION", "BLOCKING"]
FinalDecision = Literal["GO", "CONDITIONAL_GO", "NO_GO"]

MANDATORY_STAGES: tuple[PilotStage, ...] = (
    "IDEA",
    "BOOK_DEFINITION",
    "RESEARCH",
    "BOOK_CONTRACT",
    "ARCHITECTURE",
    "CHAPTER_CONTRACTS",
    "DRAFTING",
    "BOOK_MEMORY",
    "EDITORIAL",
    "BOOKBENCH",
    "FINAL_REVIEW",
    "LITERARY_MASTER",
)

STAGE_COMPLETION_EVENT_KINDS = {
    "COMPLETED",
    "HUMAN_REVIEW",
    "NOT_APPLICABLE",
    "LITERARY_QUALITY_JUDGMENT",
    "DEFECT_REVIEW",
}


class PilotError(RuntimeError):
    pass


class PilotNotFound(PilotError):
    pass


class PilotGateError(PilotError):
    pass


class PilotRunView(BaseModel):
    pilot_id: str
    book_id: str
    profile_version: str
    status: str
    human_actor: str
    started_at: str
    completed_at: str | None
    final_decision: str | None
    final_reason: str | None
    decision_actor: str | None


class PilotStageEventRequest(BaseModel):
    stage: PilotStage
    event_kind: PilotEventKind
    actor: str = Field(min_length=1, max_length=255)
    actor_kind: Literal["HUMAN", "AI", "SYSTEM"]
    elapsed_seconds: int | None = Field(default=None, ge=0)
    human_minutes: int | None = Field(default=None, ge=0)
    provider_cost_usd: float | None = Field(default=None, ge=0)
    model_run_count: int | None = Field(default=None, ge=0)
    outcome: PilotOutcome
    metadata: dict[str, Any] = Field(default_factory=dict)


class PilotStageEventView(BaseModel):
    event_id: str
    pilot_id: str
    stage: str
    event_kind: str
    actor: str
    actor_kind: str
    elapsed_seconds: int | None
    human_minutes: int | None
    provider_cost_usd: float | None
    model_run_count: int | None
    outcome: str
    created_at: str


class PilotObservationRequest(BaseModel):
    stage: PilotStage
    category: ObservationCategory
    severity: ObservationSeverity
    actor: str = Field(min_length=1, max_length=255)
    actor_kind: Literal["HUMAN", "AI", "SYSTEM"]
    description: str = Field(min_length=1)
    artifact_ref: str | None = Field(default=None, max_length=255)


class PilotObservationView(BaseModel):
    observation_id: str
    pilot_id: str
    stage: str
    category: str
    severity: str
    actor: str
    actor_kind: str
    description: str
    artifact_ref: str | None
    created_at: str
    resolved_at: str | None
    resolution_actor: str | None
    resolution_actor_kind: str | None
    resolution_reason: str | None


class OpenAIPreflightView(BaseModel):
    provider: str = "openai"
    book_id: str
    pilot_id: str
    credential_state: Literal["AVAILABLE", "NOT_AVAILABLE"]
    writer_model: str
    evaluator_model: str
    editor_lane: str
    max_requests: int
    max_input_tokens: int
    max_output_tokens: int
    max_cost_usd: float | None
    plan_hash: str
    external_calls: int = 0
    paid_calls: int = 0


class GoNoGoReadiness(BaseModel):
    ready: bool
    blockers: list[str]


class PilotSummary(BaseModel):
    pilot: PilotRunView
    stage_event_counts: dict[str, int]
    elapsed_seconds_total: int
    human_minutes_total: int
    stage_recorded_cost_usd: float
    ai_run_count: int
    model_cost_usd: float | Literal["UNKNOWN"]
    model_identities: list[str]
    claims_by_state: dict[str, int]
    material_claims_without_evidence: int
    editorial_by_status: dict[str, int]
    latest_bookbench_snapshot_id: str | None
    bookbench_blocking_count: int
    latest_literary_master_id: str | None
    latest_literary_master_hash: str | None
    open_observations_by_severity: dict[str, int]
    observations_by_category: dict[str, int]
    human_literary_quality_judgment: bool
    bookbench_defect_reviewed_by_human: bool
    go_no_go: GoNoGoReadiness


class PilotService:
    PROFILE_VERSION = "real-business-nonfiction-pilot.v1"

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self._projects = ProjectService(data_dir)

    def _engine(self, book_id: str) -> Engine:
        self._projects.get_project(book_id)
        return create_database(self._projects._database_path(book_id))

    @staticmethod
    def _run_view(row: Any) -> PilotRunView:
        return PilotRunView(
            pilot_id=str(row["pilot_id"]),
            book_id=str(row["book_id"]),
            profile_version=str(row["profile_version"]),
            status=str(row["status"]),
            human_actor=str(row["human_actor"]),
            started_at=str(row["started_at"]),
            completed_at=str(row["completed_at"]) if row["completed_at"] is not None else None,
            final_decision=str(row["final_decision"])
            if row["final_decision"] is not None
            else None,
            final_reason=str(row["final_reason"]) if row["final_reason"] is not None else None,
            decision_actor=str(row["decision_actor"])
            if row["decision_actor"] is not None
            else None,
        )

    @staticmethod
    def _pilot_row(connection: Any, book_id: str, pilot_id: str) -> Any:
        row = (
            connection.execute(
                text("SELECT * FROM pilot_runs WHERE book_id=:book_id AND pilot_id=:pilot_id"),
                {"book_id": book_id, "pilot_id": pilot_id},
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise PilotNotFound(f"pilot not found: {pilot_id}")
        return row

    def start(self, book_id: str, *, human_actor: str) -> PilotRunView:
        actor = human_actor.strip()
        if not actor:
            raise PilotGateError("pilot start requires an explicit human actor")
        engine = self._engine(book_id)
        try:
            with engine.begin() as connection:
                active = connection.execute(
                    text(
                        "SELECT pilot_id FROM pilot_runs WHERE book_id=:book_id AND status='ACTIVE'"
                    ),
                    {"book_id": book_id},
                ).scalar_one_or_none()
                if active is not None:
                    raise PilotGateError(f"book already has an active pilot: {active}")
                pilot_id = new_ulid()
                connection.execute(
                    text(
                        "INSERT INTO pilot_runs(pilot_id,book_id,profile_version,status,human_actor,started_at) "
                        "VALUES (:pilot_id,:book_id,:profile,'ACTIVE',:actor,:started_at)"
                    ),
                    {
                        "pilot_id": pilot_id,
                        "book_id": book_id,
                        "profile": self.PROFILE_VERSION,
                        "actor": actor,
                        "started_at": utc_now(),
                    },
                )
                row = self._pilot_row(connection, book_id, pilot_id)
            return self._run_view(row)
        finally:
            engine.dispose()

    def get(self, book_id: str, pilot_id: str) -> PilotRunView:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                return self._run_view(self._pilot_row(connection, book_id, pilot_id))
        finally:
            engine.dispose()

    def active(self, book_id: str) -> PilotRunView | None:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                row = (
                    connection.execute(
                        text(
                            "SELECT * FROM pilot_runs WHERE book_id=:book_id AND status='ACTIVE' "
                            "ORDER BY started_at DESC LIMIT 1"
                        ),
                        {"book_id": book_id},
                    )
                    .mappings()
                    .one_or_none()
                )
            return self._run_view(row) if row is not None else None
        finally:
            engine.dispose()

    def record_stage_event(
        self, book_id: str, pilot_id: str, payload: PilotStageEventRequest
    ) -> PilotStageEventView:
        if payload.event_kind == "NOT_APPLICABLE" or payload.outcome == "NOT_APPLICABLE":
            reason = payload.metadata.get("reason")
            if not isinstance(reason, str) or not reason.strip():
                raise PilotGateError("NOT_APPLICABLE stage evidence requires a reason")
        human_detail_keys = {
            "HUMAN_REVIEW": "reason",
            "LITERARY_QUALITY_JUDGMENT": "judgment",
            "DEFECT_REVIEW": "reason",
        }
        detail_key = human_detail_keys.get(payload.event_kind)
        if detail_key is not None:
            if payload.actor_kind != "HUMAN":
                raise PilotGateError(f"{payload.event_kind} stage evidence must be HUMAN")
            detail = payload.metadata.get(detail_key)
            if not isinstance(detail, str) or not detail.strip():
                raise PilotGateError(
                    f"{payload.event_kind} stage evidence requires nonblank {detail_key}"
                )
        engine = self._engine(book_id)
        try:
            with engine.begin() as connection:
                pilot = self._pilot_row(connection, book_id, pilot_id)
                if str(pilot["status"]) != "ACTIVE":
                    raise PilotGateError("stage evidence can be added only to an ACTIVE pilot")
                event_id = new_ulid()
                now = utc_now()
                connection.execute(
                    text(
                        "INSERT INTO pilot_stage_events("
                        "event_id,pilot_id,stage,event_kind,actor,actor_kind,elapsed_seconds,human_minutes,"
                        "provider_cost_usd,model_run_count,outcome,metadata_json,created_at) VALUES "
                        "(:event_id,:pilot_id,:stage,:event_kind,:actor,:actor_kind,:elapsed_seconds,"
                        ":human_minutes,:provider_cost_usd,:model_run_count,:outcome,:metadata_json,:created_at)"
                    ),
                    {
                        "event_id": event_id,
                        "pilot_id": pilot_id,
                        "stage": payload.stage,
                        "event_kind": payload.event_kind,
                        "actor": payload.actor,
                        "actor_kind": payload.actor_kind,
                        "elapsed_seconds": payload.elapsed_seconds,
                        "human_minutes": payload.human_minutes,
                        "provider_cost_usd": payload.provider_cost_usd,
                        "model_run_count": payload.model_run_count,
                        "outcome": payload.outcome,
                        "metadata_json": json.dumps(
                            payload.metadata,
                            ensure_ascii=False,
                            sort_keys=True,
                            separators=(",", ":"),
                        ),
                        "created_at": now,
                    },
                )
            return PilotStageEventView(
                event_id=event_id,
                pilot_id=pilot_id,
                stage=payload.stage,
                event_kind=payload.event_kind,
                actor=payload.actor,
                actor_kind=payload.actor_kind,
                elapsed_seconds=payload.elapsed_seconds,
                human_minutes=payload.human_minutes,
                provider_cost_usd=payload.provider_cost_usd,
                model_run_count=payload.model_run_count,
                outcome=payload.outcome,
                created_at=now,
            )
        finally:
            engine.dispose()

    def add_observation(
        self, book_id: str, pilot_id: str, payload: PilotObservationRequest
    ) -> PilotObservationView:
        engine = self._engine(book_id)
        try:
            with engine.begin() as connection:
                pilot = self._pilot_row(connection, book_id, pilot_id)
                if str(pilot["status"]) != "ACTIVE":
                    raise PilotGateError("observations can be added only to an ACTIVE pilot")
                observation_id = new_ulid()
                now = utc_now()
                connection.execute(
                    text(
                        "INSERT INTO pilot_observations("
                        "observation_id,pilot_id,stage,category,severity,actor,actor_kind,description,"
                        "artifact_ref,created_at) VALUES "
                        "(:observation_id,:pilot_id,:stage,:category,:severity,:actor,:actor_kind,"
                        ":description,:artifact_ref,:created_at)"
                    ),
                    {
                        "observation_id": observation_id,
                        "pilot_id": pilot_id,
                        "stage": payload.stage,
                        "category": payload.category,
                        "severity": payload.severity,
                        "actor": payload.actor,
                        "actor_kind": payload.actor_kind,
                        "description": payload.description,
                        "artifact_ref": payload.artifact_ref,
                        "created_at": now,
                    },
                )
            return PilotObservationView(
                observation_id=observation_id,
                pilot_id=pilot_id,
                stage=payload.stage,
                category=payload.category,
                severity=payload.severity,
                actor=payload.actor,
                actor_kind=payload.actor_kind,
                description=payload.description,
                artifact_ref=payload.artifact_ref,
                created_at=now,
                resolved_at=None,
                resolution_actor=None,
                resolution_actor_kind=None,
                resolution_reason=None,
            )
        finally:
            engine.dispose()

    def resolve_observation(
        self,
        book_id: str,
        pilot_id: str,
        observation_id: str,
        *,
        actor: str,
        actor_kind: Literal["HUMAN", "SYSTEM"],
        reason: str,
    ) -> PilotObservationView:
        if not actor.strip() or not reason.strip():
            raise PilotGateError("observation resolution requires actor and reason")
        engine = self._engine(book_id)
        try:
            with engine.begin() as connection:
                pilot = self._pilot_row(connection, book_id, pilot_id)
                if str(pilot["status"]) != "ACTIVE":
                    raise PilotGateError("observations can be resolved only on an ACTIVE pilot")
                row = (
                    connection.execute(
                        text(
                            "SELECT * FROM pilot_observations WHERE pilot_id=:pilot_id "
                            "AND observation_id=:observation_id"
                        ),
                        {"pilot_id": pilot_id, "observation_id": observation_id},
                    )
                    .mappings()
                    .one_or_none()
                )
                if row is None:
                    raise PilotNotFound(f"pilot observation not found: {observation_id}")
                if row["resolved_at"] is not None:
                    raise PilotGateError("pilot observation is already resolved")
                if str(row["severity"]) == "BLOCKING" and actor_kind != "HUMAN":
                    raise PilotGateError("BLOCKING pilot observation requires HUMAN resolution")
                resolved_at = utc_now()
                connection.execute(
                    text(
                        "UPDATE pilot_observations SET resolved_at=:resolved_at,resolution_actor=:actor,"
                        "resolution_actor_kind=:actor_kind,resolution_reason=:reason "
                        "WHERE observation_id=:observation_id"
                    ),
                    {
                        "resolved_at": resolved_at,
                        "actor": actor.strip(),
                        "actor_kind": actor_kind,
                        "reason": reason.strip(),
                        "observation_id": observation_id,
                    },
                )
                updated = (
                    connection.execute(
                        text(
                            "SELECT * FROM pilot_observations WHERE observation_id=:observation_id"
                        ),
                        {"observation_id": observation_id},
                    )
                    .mappings()
                    .one()
                )
            return PilotObservationView(**dict(updated))
        finally:
            engine.dispose()

    @staticmethod
    def openai_preflight(
        secrets: SecretStore,
        *,
        book_id: str,
        pilot_id: str,
        writer_model: str,
        evaluator_model: str,
        editor_lane: str = "deterministic-m6-current",
        max_requests: int,
        max_input_tokens: int,
        max_output_tokens: int,
        max_cost_usd: float,
    ) -> OpenAIPreflightView:
        if not book_id.strip() or not pilot_id.strip():
            raise PilotGateError("OpenAI preflight requires exact book/pilot identity")
        if not writer_model.strip() or not evaluator_model.strip() or not editor_lane.strip():
            raise PilotGateError("OpenAI preflight requires explicit model/config identities")
        if min(max_requests, max_input_tokens, max_output_tokens) <= 0:
            raise PilotGateError("OpenAI preflight requires positive request/token bounds")
        if max_cost_usd <= 0:
            raise PilotGateError("OpenAI preflight requires a positive cost cap")
        try:
            secrets.get_secret("openai_api_key")
        except Exception:
            credential_state: Literal["AVAILABLE", "NOT_AVAILABLE"] = "NOT_AVAILABLE"
        else:
            credential_state = "AVAILABLE"
        plan = {
            "provider": "openai",
            "book_id": book_id.strip(),
            "pilot_id": pilot_id.strip(),
            "writer_model": writer_model.strip(),
            "evaluator_model": evaluator_model.strip(),
            "editor_lane": editor_lane.strip(),
            "max_requests": max_requests,
            "max_input_tokens": max_input_tokens,
            "max_output_tokens": max_output_tokens,
            "max_cost_usd": max_cost_usd,
        }
        plan_hash = hashlib.sha256(
            json.dumps(plan, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return OpenAIPreflightView(
            credential_state=credential_state,
            plan_hash=plan_hash,
            **plan,
        )

    def summary(self, book_id: str, pilot_id: str) -> PilotSummary:
        engine = self._engine(book_id)
        try:
            with engine.connect() as connection:
                pilot_row = self._pilot_row(connection, book_id, pilot_id)
                pilot = self._run_view(pilot_row)

                stage_rows = list(
                    connection.execute(
                        text(
                            "SELECT stage,event_kind,actor_kind,elapsed_seconds,human_minutes,"
                            "provider_cost_usd,outcome FROM pilot_stage_events WHERE pilot_id=:pilot_id"
                        ),
                        {"pilot_id": pilot_id},
                    ).mappings()
                )
                stage_counts = Counter(
                    str(row["stage"])
                    for row in stage_rows
                    if str(row["event_kind"]) in STAGE_COMPLETION_EVENT_KINDS
                )
                elapsed_total = sum(int(row["elapsed_seconds"] or 0) for row in stage_rows)
                human_total = sum(int(row["human_minutes"] or 0) for row in stage_rows)
                stage_cost = sum(float(row["provider_cost_usd"] or 0.0) for row in stage_rows)

                model_rows = list(
                    connection.execute(
                        text(
                            "SELECT mr.provider,mr.model,mr.usage_json FROM model_runs mr "
                            "JOIN bounded_tasks bt ON bt.task_id=mr.task_id "
                            "WHERE bt.book_id=:book_id AND mr.created_at>=:started_at"
                        ),
                        {"book_id": book_id, "started_at": pilot.started_at},
                    ).mappings()
                )
                eval_rows = list(
                    connection.execute(
                        text(
                            "SELECT provider,model,config_id,cost_usd FROM evaluation_runs "
                            "WHERE book_id=:book_id AND created_at>=:started_at AND provider IS NOT NULL"
                        ),
                        {"book_id": book_id, "started_at": pilot.started_at},
                    ).mappings()
                )
                identities: set[str] = set()
                costs: list[float] = []
                cost_unknown = False
                for row in model_rows:
                    identities.add(f"{row['provider']}:{row['model']}")
                    usage = json.loads(str(row["usage_json"]))
                    raw_cost = usage.get("cost_usd") if isinstance(usage, dict) else None
                    if isinstance(raw_cost, (int, float)):
                        costs.append(float(raw_cost))
                    else:
                        cost_unknown = True
                for row in eval_rows:
                    identities.add(
                        f"{row['provider']}:{row['model']}:{row['config_id'] or 'default'}"
                    )
                    if isinstance(row["cost_usd"], (int, float)):
                        costs.append(float(row["cost_usd"]))
                    else:
                        cost_unknown = True
                ai_run_count = len(model_rows) + len(eval_rows)
                if ai_run_count == 0:
                    model_cost: float | Literal["UNKNOWN"] = 0.0
                elif cost_unknown:
                    model_cost = "UNKNOWN"
                else:
                    model_cost = sum(costs)

                claim_rows = list(
                    connection.execute(
                        text(
                            "SELECT verification_state,COUNT(*) AS count FROM claims "
                            "WHERE book_id=:book_id GROUP BY verification_state"
                        ),
                        {"book_id": book_id},
                    ).mappings()
                )
                claims_by_state = {
                    str(row["verification_state"]): int(row["count"]) for row in claim_rows
                }
                material_without_evidence = int(
                    connection.execute(
                        text(
                            "SELECT COUNT(*) FROM claims c WHERE c.book_id=:book_id "
                            "AND c.materiality IN ('HIGH','CRITICAL') AND c.claim_type!='AUTHORIAL' "
                            "AND NOT EXISTS (SELECT 1 FROM evidence e WHERE e.claim_id=c.claim_id "
                            "AND e.status='ACTIVE')"
                        ),
                        {"book_id": book_id},
                    ).scalar_one()
                )

                editorial_rows = list(
                    connection.execute(
                        text(
                            "SELECT status,COUNT(*) AS count FROM editorial_findings "
                            "WHERE book_id=:book_id GROUP BY status"
                        ),
                        {"book_id": book_id},
                    ).mappings()
                )
                editorial_by_status = {
                    str(row["status"]): int(row["count"]) for row in editorial_rows
                }

                snapshot = (
                    connection.execute(
                        text(
                            "SELECT snapshot_id FROM evaluation_snapshots WHERE book_id=:book_id "
                            "AND scope='BOOK' AND created_at>=:started_at "
                            "ORDER BY created_at DESC,snapshot_id DESC LIMIT 1"
                        ),
                        {"book_id": book_id, "started_at": pilot.started_at},
                    )
                    .mappings()
                    .one_or_none()
                )
                snapshot_id = str(snapshot["snapshot_id"]) if snapshot is not None else None
                bookbench_blocking = 0
                if snapshot_id is not None:
                    bookbench_blocking = int(
                        connection.execute(
                            text(
                                "SELECT COUNT(*) FROM evaluation_findings f "
                                "JOIN evaluation_runs r ON r.evaluation_id=f.evaluation_id "
                                "WHERE r.snapshot_id=:snapshot_id AND r.status='SUCCEEDED' "
                                "AND f.severity='BLOCKING'"
                            ),
                            {"snapshot_id": snapshot_id},
                        ).scalar_one()
                    )

                master = (
                    connection.execute(
                        text(
                            "SELECT master_id,manifest_hash,manifest_json FROM literary_masters "
                            "WHERE book_id=:book_id AND status='LOCKED' AND created_at>=:started_at "
                            "ORDER BY created_at DESC,master_id DESC LIMIT 1"
                        ),
                        {"book_id": book_id, "started_at": pilot.started_at},
                    )
                    .mappings()
                    .one_or_none()
                )
                master_id = str(master["master_id"]) if master is not None else None
                master_hash = str(master["manifest_hash"]) if master is not None else None
                master_snapshot_id: str | None = None
                if master is not None:
                    manifest = json.loads(str(master["manifest_json"]))
                    bookbench = manifest.get("bookbench") if isinstance(manifest, dict) else None
                    if isinstance(bookbench, dict) and bookbench.get("snapshot_id") is not None:
                        master_snapshot_id = str(bookbench["snapshot_id"])

                observation_rows = list(
                    connection.execute(
                        text(
                            "SELECT category,severity,resolved_at FROM pilot_observations "
                            "WHERE pilot_id=:pilot_id"
                        ),
                        {"pilot_id": pilot_id},
                    ).mappings()
                )
                open_severity = Counter(
                    str(row["severity"]) for row in observation_rows if row["resolved_at"] is None
                )
                categories = Counter(str(row["category"]) for row in observation_rows)
                open_blocking = int(open_severity.get("BLOCKING", 0))

                human_quality = any(
                    str(row["stage"]) == "FINAL_REVIEW"
                    and str(row["event_kind"]) == "LITERARY_QUALITY_JUDGMENT"
                    and str(row["actor_kind"]) == "HUMAN"
                    for row in stage_rows
                )
                defect_review = any(
                    str(row["stage"]) == "BOOKBENCH"
                    and str(row["event_kind"]) == "DEFECT_REVIEW"
                    and str(row["actor_kind"]) == "HUMAN"
                    for row in stage_rows
                )

                blockers: list[str] = []
                missing_stages = [
                    stage for stage in MANDATORY_STAGES if stage_counts.get(stage, 0) == 0
                ]
                if missing_stages:
                    blockers.append("MISSING_STAGES:" + ",".join(missing_stages))
                if master_id is None:
                    blockers.append("LITERARY_MASTER_MISSING")
                if ai_run_count == 0:
                    blockers.append("AI_RUN_EVIDENCE_MISSING")
                if material_without_evidence:
                    blockers.append(
                        f"MATERIAL_RESEARCH_TRACEABILITY_GAPS:{material_without_evidence}"
                    )
                if snapshot_id is None:
                    blockers.append("BOOKBENCH_SNAPSHOT_MISSING")
                elif bookbench_blocking:
                    blockers.append(f"BOOKBENCH_BLOCKING:{bookbench_blocking}")
                if master_id is not None and master_snapshot_id != snapshot_id:
                    blockers.append("BOOKBENCH_MASTER_MISMATCH")
                if open_blocking:
                    blockers.append(f"PILOT_BLOCKING_OBSERVATIONS:{open_blocking}")
                if not human_quality:
                    blockers.append("HUMAN_LITERARY_QUALITY_JUDGMENT_MISSING")
                if not defect_review:
                    blockers.append("BOOKBENCH_FP_FN_REVIEW_MISSING")

            return PilotSummary(
                pilot=pilot,
                stage_event_counts=dict(stage_counts),
                elapsed_seconds_total=elapsed_total,
                human_minutes_total=human_total,
                stage_recorded_cost_usd=stage_cost,
                ai_run_count=ai_run_count,
                model_cost_usd=model_cost,
                model_identities=sorted(identities),
                claims_by_state=claims_by_state,
                material_claims_without_evidence=material_without_evidence,
                editorial_by_status=editorial_by_status,
                latest_bookbench_snapshot_id=snapshot_id,
                bookbench_blocking_count=bookbench_blocking,
                latest_literary_master_id=master_id,
                latest_literary_master_hash=master_hash,
                open_observations_by_severity=dict(open_severity),
                observations_by_category=dict(categories),
                human_literary_quality_judgment=human_quality,
                bookbench_defect_reviewed_by_human=defect_review,
                go_no_go=GoNoGoReadiness(ready=not blockers, blockers=blockers),
            )
        finally:
            engine.dispose()

    def record_final_decision(
        self,
        book_id: str,
        pilot_id: str,
        *,
        decision: FinalDecision,
        actor: str,
        actor_kind: Literal["HUMAN"],
        reason: str,
    ) -> PilotRunView:
        if actor_kind != "HUMAN":
            raise PilotGateError("final GO/NO-GO decision must be HUMAN")
        if not actor.strip() or not reason.strip():
            raise PilotGateError("final GO/NO-GO decision requires actor and reason")
        summary = self.summary(book_id, pilot_id)
        if not summary.go_no_go.ready:
            raise PilotGateError(
                "GO/NO-GO evidence is not ready: " + "; ".join(summary.go_no_go.blockers)
            )
        engine = self._engine(book_id)
        try:
            with engine.begin() as connection:
                pilot = self._pilot_row(connection, book_id, pilot_id)
                if str(pilot["status"]) != "ACTIVE":
                    raise PilotGateError("final pilot decision is already immutable")
                now = utc_now()
                connection.execute(
                    text(
                        "UPDATE pilot_runs SET status='COMPLETED',completed_at=:completed_at,"
                        "final_decision=:decision,final_reason=:reason,decision_actor=:actor,"
                        "decision_actor_kind='HUMAN' WHERE pilot_id=:pilot_id"
                    ),
                    {
                        "completed_at": now,
                        "decision": decision,
                        "reason": reason.strip(),
                        "actor": actor.strip(),
                        "pilot_id": pilot_id,
                    },
                )
                row = self._pilot_row(connection, book_id, pilot_id)
            return self._run_view(row)
        finally:
            engine.dispose()
