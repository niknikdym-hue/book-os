from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal, cast

from pydantic import BaseModel, Field

from .authority_types import content_hash, new_ulid, utc_now
from .series_production import ChapterAdmissionStatusView

QualityActorKind = Literal["HUMAN", "OWNER", "AI", "SYSTEM"]
QualityRole = Literal[
    "PLANNER",
    "RESEARCHER",
    "EVIDENCE_ANALYST",
    "WRITER",
    "CRITIC",
    "EDITOR",
    "ADVERSARIAL_REVIEWER",
    "BOOKBENCH_JUDGE",
]
MaterialStatus = Literal["PROPOSED", "ACCEPTED", "REJECTED"]
FindingSeverity = Literal["PASS", "ATTENTION", "BLOCKING"]


class QualityLoopStage(StrEnum):
    ADMISSION_VERIFIED = "ADMISSION_VERIFIED"
    MICRO_PLAN = "MICRO_PLAN"
    EVIDENCE_PLAN = "EVIDENCE_PLAN"
    SECTION_INTENT = "SECTION_INTENT"
    DRAFT_CANDIDATE = "DRAFT_CANDIDATE"
    DETERMINISTIC_CHECKS = "DETERMINISTIC_CHECKS"
    EVIDENCE_CHECKS = "EVIDENCE_CHECKS"
    NOVELTY_CHECK = "NOVELTY_CHECK"
    INDEPENDENT_CRITIC = "INDEPENDENT_CRITIC"
    REVISION_PROPOSAL = "REVISION_PROPOSAL"
    POST_REVISION_CHECKS = "POST_REVISION_CHECKS"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    COMPLETE = "COMPLETE"


class QualityLoopError(RuntimeError):
    pass


class QualityLoopGateError(QualityLoopError):
    pass


class QualityLoopTransitionError(QualityLoopError):
    pass


class QualityLoopArtifact(BaseModel):
    artifact_id: str = Field(min_length=26, max_length=26)
    kind: str = Field(min_length=1, max_length=80)
    role: QualityRole
    status: MaterialStatus = "PROPOSED"
    payload: dict[str, Any] = Field(min_length=1)
    payload_hash: str = Field(min_length=64, max_length=64)
    created_by_kind: QualityActorKind
    created_by: str = Field(min_length=1, max_length=255)
    created_at: str
    decided_by_kind: Literal["HUMAN", "OWNER"] | None = None
    decided_by: str | None = Field(default=None, max_length=255)
    decided_at: str | None = None
    decision_reason: str | None = Field(default=None, max_length=12000)


class QualityLoopFinding(BaseModel):
    finding_id: str = Field(min_length=26, max_length=26)
    role: QualityRole
    severity: FindingSeverity
    location: str = Field(min_length=1, max_length=1000)
    evidence: str = Field(min_length=1, max_length=12000)
    recommended_action: str = Field(min_length=1, max_length=12000)
    created_by_kind: QualityActorKind
    created_by: str = Field(min_length=1, max_length=255)
    created_at: str


class QualityLoopEvent(BaseModel):
    event_id: str = Field(min_length=26, max_length=26)
    from_stage: QualityLoopStage | None
    to_stage: QualityLoopStage
    actor_kind: QualityActorKind
    actor: str = Field(min_length=1, max_length=255)
    evidence: dict[str, Any] = Field(min_length=1)
    created_at: str


class QualityLoopRun(BaseModel):
    run_id: str = Field(min_length=26, max_length=26)
    book_id: str
    chapter_id: str
    admission_id: str
    definition_id: str
    architecture_revision_id: str
    chapter_contract_revision_id: str
    production_contract_id: str
    stage: QualityLoopStage = QualityLoopStage.ADMISSION_VERIFIED
    artifacts: list[QualityLoopArtifact] = Field(default_factory=list)
    findings: list[QualityLoopFinding] = Field(default_factory=list)
    events: list[QualityLoopEvent] = Field(default_factory=list)
    created_at: str
    updated_at: str


class QualityLoopStateMachine:
    """Deterministic quality-loop state machine; it performs no model/provider calls."""

    _ALLOWED: dict[QualityLoopStage, QualityLoopStage | None] = {
        QualityLoopStage.ADMISSION_VERIFIED: QualityLoopStage.MICRO_PLAN,
        QualityLoopStage.MICRO_PLAN: QualityLoopStage.EVIDENCE_PLAN,
        QualityLoopStage.EVIDENCE_PLAN: QualityLoopStage.SECTION_INTENT,
        QualityLoopStage.SECTION_INTENT: QualityLoopStage.DRAFT_CANDIDATE,
        QualityLoopStage.DRAFT_CANDIDATE: QualityLoopStage.DETERMINISTIC_CHECKS,
        QualityLoopStage.DETERMINISTIC_CHECKS: QualityLoopStage.EVIDENCE_CHECKS,
        QualityLoopStage.EVIDENCE_CHECKS: QualityLoopStage.NOVELTY_CHECK,
        QualityLoopStage.NOVELTY_CHECK: QualityLoopStage.INDEPENDENT_CRITIC,
        QualityLoopStage.INDEPENDENT_CRITIC: QualityLoopStage.REVISION_PROPOSAL,
        QualityLoopStage.REVISION_PROPOSAL: QualityLoopStage.POST_REVISION_CHECKS,
        QualityLoopStage.POST_REVISION_CHECKS: QualityLoopStage.HUMAN_REVIEW,
        QualityLoopStage.HUMAN_REVIEW: QualityLoopStage.COMPLETE,
        QualityLoopStage.COMPLETE: None,
    }

    @staticmethod
    def _require_open(run: QualityLoopRun) -> None:
        if run.stage == QualityLoopStage.COMPLETE:
            raise QualityLoopTransitionError("quality loop is already complete")

    @staticmethod
    def _touch(run: QualityLoopRun) -> None:
        run.updated_at = utc_now()

    def start(
        self,
        admission: ChapterAdmissionStatusView,
        *,
        actor_kind: QualityActorKind,
        actor: str,
    ) -> QualityLoopRun:
        if not admission.writing_allowed:
            blockers = ", ".join(admission.blockers) if admission.blockers else "unknown"
            raise QualityLoopGateError(f"WRITING_NOT_ALLOWED: {blockers}")

        required_identity = {
            "admission_id": admission.admission_id,
            "definition_id": admission.definition_id,
            "architecture_revision_id": admission.architecture_revision_id,
            "chapter_contract_revision_id": admission.chapter_contract_revision_id,
            "production_contract_id": admission.production_contract_id,
        }
        missing = [name for name, value in required_identity.items() if value is None]
        if missing:
            raise QualityLoopGateError(
                "current Task 017 admission is incomplete: " + ", ".join(sorted(missing))
            )

        now = utc_now()
        event = QualityLoopEvent(
            event_id=new_ulid(),
            from_stage=None,
            to_stage=QualityLoopStage.ADMISSION_VERIFIED,
            actor_kind=actor_kind,
            actor=actor,
            evidence={"admission_id": cast(str, admission.admission_id)},
            created_at=now,
        )
        return QualityLoopRun(
            run_id=new_ulid(),
            book_id=admission.book_id,
            chapter_id=admission.chapter_id,
            admission_id=cast(str, admission.admission_id),
            definition_id=cast(str, admission.definition_id),
            architecture_revision_id=cast(str, admission.architecture_revision_id),
            chapter_contract_revision_id=cast(str, admission.chapter_contract_revision_id),
            production_contract_id=cast(str, admission.production_contract_id),
            events=[event],
            created_at=now,
            updated_at=now,
        )

    def advance(
        self,
        run: QualityLoopRun,
        next_stage: QualityLoopStage,
        *,
        actor_kind: QualityActorKind,
        actor: str,
        evidence: dict[str, Any],
    ) -> QualityLoopRun:
        self._require_open(run)
        expected = self._ALLOWED[run.stage]
        if expected != next_stage:
            expected_text = expected.value if expected is not None else "none"
            raise QualityLoopTransitionError(
                f"invalid quality-loop transition {run.stage.value} -> {next_stage.value}; "
                f"expected {expected_text}"
            )
        if not evidence:
            raise QualityLoopTransitionError("stage transition requires provenance evidence")

        if next_stage == QualityLoopStage.COMPLETE:
            if actor_kind not in {"HUMAN", "OWNER"}:
                raise QualityLoopGateError("quality loop completion requires HUMAN/OWNER authority")
            pending = [item.artifact_id for item in run.artifacts if item.status == "PROPOSED"]
            if pending:
                raise QualityLoopGateError(
                    "quality loop has material proposals awaiting human decision: "
                    + ", ".join(pending)
                )
            blocking = [item.finding_id for item in run.findings if item.severity == "BLOCKING"]
            if blocking:
                raise QualityLoopGateError(
                    "quality loop has unresolved blocking findings: " + ", ".join(blocking)
                )

        previous = run.stage
        run.stage = next_stage
        now = utc_now()
        run.events.append(
            QualityLoopEvent(
                event_id=new_ulid(),
                from_stage=previous,
                to_stage=next_stage,
                actor_kind=actor_kind,
                actor=actor,
                evidence=evidence,
                created_at=now,
            )
        )
        run.updated_at = now
        return run

    def propose_artifact(
        self,
        run: QualityLoopRun,
        *,
        kind: str,
        role: QualityRole,
        payload: dict[str, Any],
        actor_kind: QualityActorKind,
        actor: str,
    ) -> QualityLoopArtifact:
        self._require_open(run)
        if not payload:
            raise QualityLoopGateError("material proposal payload cannot be empty")
        artifact = QualityLoopArtifact(
            artifact_id=new_ulid(),
            kind=kind,
            role=role,
            payload=payload,
            payload_hash=content_hash(payload),
            created_by_kind=actor_kind,
            created_by=actor,
            created_at=utc_now(),
        )
        run.artifacts.append(artifact)
        self._touch(run)
        return artifact

    def decide_artifact(
        self,
        run: QualityLoopRun,
        artifact_id: str,
        *,
        decision: Literal["ACCEPTED", "REJECTED"],
        actor_kind: QualityActorKind,
        actor: str,
        reason: str,
    ) -> QualityLoopArtifact:
        self._require_open(run)
        if actor_kind not in {"HUMAN", "OWNER"}:
            raise QualityLoopGateError("material decision requires HUMAN/OWNER authority")
        artifact = next((item for item in run.artifacts if item.artifact_id == artifact_id), None)
        if artifact is None:
            raise QualityLoopGateError(f"unknown quality-loop artifact: {artifact_id}")
        if artifact.status != "PROPOSED":
            raise QualityLoopGateError("material proposal already has a human decision")
        if not reason.strip():
            raise QualityLoopGateError("human material decision requires a reason")
        artifact.status = decision
        artifact.decided_by_kind = cast(Literal["HUMAN", "OWNER"], actor_kind)
        artifact.decided_by = actor
        artifact.decided_at = utc_now()
        artifact.decision_reason = reason
        self._touch(run)
        return artifact

    def record_finding(
        self,
        run: QualityLoopRun,
        *,
        role: QualityRole,
        severity: FindingSeverity,
        location: str,
        evidence: str,
        recommended_action: str,
        actor_kind: QualityActorKind,
        actor: str,
    ) -> QualityLoopFinding:
        self._require_open(run)
        finding = QualityLoopFinding(
            finding_id=new_ulid(),
            role=role,
            severity=severity,
            location=location,
            evidence=evidence,
            recommended_action=recommended_action,
            created_by_kind=actor_kind,
            created_by=actor,
            created_at=utc_now(),
        )
        run.findings.append(finding)
        self._touch(run)
        return finding
