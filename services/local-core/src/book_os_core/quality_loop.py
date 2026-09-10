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
FindingDisposition = Literal["OPEN", "RESOLVED", "SUPERSEDED"]


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
    disposition: FindingDisposition = "OPEN"
    resolved_by_kind: Literal["HUMAN", "OWNER", "SYSTEM"] | None = None
    resolved_by: str | None = Field(default=None, max_length=255)
    resolved_at: str | None = None
    resolution_reason: str | None = Field(default=None, max_length=12000)
    resolution_evidence: dict[str, Any] = Field(default_factory=dict)


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
    def _require_actor_kind(actor_kind: object) -> None:
        if actor_kind not in {"HUMAN", "OWNER", "AI", "SYSTEM"}:
            raise QualityLoopGateError(f"unknown quality-loop actor kind: {actor_kind}")

    @staticmethod
    def _touch(run: QualityLoopRun) -> None:
        run.updated_at = utc_now()

    @staticmethod
    def _artifact(
        run: QualityLoopRun,
        artifact_id: object,
        *,
        kind: str,
    ) -> QualityLoopArtifact:
        if not isinstance(artifact_id, str) or not artifact_id:
            raise QualityLoopGateError(f"{kind} transition requires an artifact_id")
        artifact = next((item for item in run.artifacts if item.artifact_id == artifact_id), None)
        if artifact is None:
            raise QualityLoopGateError(f"unknown quality-loop artifact: {artifact_id}")
        if artifact.kind != kind:
            raise QualityLoopGateError(
                f"quality-loop artifact {artifact_id} has kind {artifact.kind}; expected {kind}"
            )
        return artifact

    @staticmethod
    def _stage_event(run: QualityLoopRun, stage: QualityLoopStage) -> QualityLoopEvent:
        event = next((item for item in reversed(run.events) if item.to_stage == stage), None)
        if event is None:
            raise QualityLoopGateError(f"missing provenance event for {stage.value}")
        return event

    def _stage_artifact(
        self,
        run: QualityLoopRun,
        stage: QualityLoopStage,
        *,
        kind: str,
    ) -> QualityLoopArtifact:
        event = self._stage_event(run, stage)
        return self._artifact(run, event.evidence.get("artifact_id"), kind=kind)

    def _validate_stage_evidence(
        self,
        run: QualityLoopRun,
        next_stage: QualityLoopStage,
        evidence: dict[str, Any],
    ) -> None:
        if next_stage == QualityLoopStage.MICRO_PLAN:
            micro_plan = evidence.get("micro_plan")
            if not isinstance(micro_plan, str) or not micro_plan.strip():
                raise QualityLoopGateError("MICRO_PLAN requires a non-empty micro_plan")
            return

        if next_stage == QualityLoopStage.EVIDENCE_PLAN:
            required = evidence.get("evidence_required")
            ready = evidence.get("evidence_ready")
            summary = evidence.get("evidence_summary", "")
            if not isinstance(required, bool) or not isinstance(ready, bool):
                raise QualityLoopGateError(
                    "EVIDENCE_PLAN requires boolean evidence_required and evidence_ready"
                )
            if not isinstance(summary, str):
                raise QualityLoopGateError("EVIDENCE_PLAN evidence_summary must be text")
            if ready and not summary.strip():
                raise QualityLoopGateError(
                    "EVIDENCE_PLAN marked ready requires a non-empty evidence_summary"
                )
            return

        if next_stage == QualityLoopStage.SECTION_INTENT:
            plan = self._stage_event(run, QualityLoopStage.EVIDENCE_PLAN).evidence
            if plan.get("evidence_required") is True and plan.get("evidence_ready") is not True:
                raise QualityLoopGateError(
                    "EVIDENCE_REQUIRED: cannot advance beyond evidence plan until evidence is ready"
                )
            section_intent = evidence.get("section_intent")
            if not isinstance(section_intent, str) or not section_intent.strip():
                raise QualityLoopGateError("SECTION_INTENT requires a non-empty section_intent")
            return

        if next_stage == QualityLoopStage.DRAFT_CANDIDATE:
            artifact = self._artifact(
                run,
                evidence.get("artifact_id"),
                kind="DRAFT_CANDIDATE",
            )
            for field in ("unit_id", "revision_id", "revision_hash", "provider", "model", "run_id"):
                value = artifact.payload.get(field)
                if not isinstance(value, str) or not value:
                    raise QualityLoopGateError(
                        f"DRAFT_CANDIDATE artifact requires non-empty {field} provenance"
                    )
            return

        if next_stage == QualityLoopStage.DETERMINISTIC_CHECKS:
            if evidence.get("result") != "PASS":
                raise QualityLoopGateError("DETERMINISTIC_CHECKS requires result=PASS")
            revision_id = evidence.get("draft_revision_id")
            if not isinstance(revision_id, str) or not revision_id:
                raise QualityLoopGateError(
                    "DETERMINISTIC_CHECKS requires an exact draft_revision_id"
                )
            artifact = self._stage_artifact(
                run,
                QualityLoopStage.DRAFT_CANDIDATE,
                kind="DRAFT_CANDIDATE",
            )
            if artifact.payload.get("revision_id") != revision_id:
                raise QualityLoopGateError(
                    "DETERMINISTIC_CHECKS draft_revision_id does not match draft candidate"
                )
            return

        if next_stage == QualityLoopStage.EVIDENCE_CHECKS:
            if evidence.get("result") != "PASS":
                raise QualityLoopGateError("EVIDENCE_CHECKS requires result=PASS")
            required = evidence.get("required")
            summary = evidence.get("summary", "")
            if not isinstance(required, bool) or not isinstance(summary, str):
                raise QualityLoopGateError(
                    "EVIDENCE_CHECKS requires boolean required and textual summary"
                )
            plan = self._stage_event(run, QualityLoopStage.EVIDENCE_PLAN).evidence
            if required != plan.get("evidence_required"):
                raise QualityLoopGateError(
                    "EVIDENCE_CHECKS required flag does not match evidence plan"
                )
            if required and not summary.strip():
                raise QualityLoopGateError(
                    "EVIDENCE_CHECKS for evidence-required content needs traceable evidence summary"
                )
            return

        if next_stage == QualityLoopStage.NOVELTY_CHECK:
            novelty_evidence = evidence.get("evidence")
            if evidence.get("result") != "PASS":
                raise QualityLoopGateError("NOVELTY_CHECK requires result=PASS")
            if not isinstance(novelty_evidence, str) or not novelty_evidence.strip():
                raise QualityLoopGateError(
                    "NOVELTY_CHECK requires non-empty semantic novelty/repetition evidence"
                )
            return

        if next_stage == QualityLoopStage.INDEPENDENT_CRITIC:
            summary = evidence.get("summary")
            finding_ids = evidence.get("finding_ids")
            if not isinstance(summary, str) or not summary.strip():
                raise QualityLoopGateError("INDEPENDENT_CRITIC requires a non-empty summary")
            if not isinstance(finding_ids, list) or any(
                not isinstance(item, str) or not item for item in finding_ids
            ):
                raise QualityLoopGateError(
                    "INDEPENDENT_CRITIC requires a list of exact finding_ids"
                )
            known = {item.finding_id for item in run.findings}
            unknown = [item for item in finding_ids if item not in known]
            if unknown:
                raise QualityLoopGateError(
                    "INDEPENDENT_CRITIC references unknown findings: " + ", ".join(unknown)
                )
            return

        if next_stage == QualityLoopStage.REVISION_PROPOSAL:
            artifact = self._artifact(
                run,
                evidence.get("artifact_id"),
                kind="TARGETED_REVISION_PROPOSAL",
            )
            for field in ("source_revision_id", "source_revision_hash"):
                value = artifact.payload.get(field)
                if not isinstance(value, str) or not value:
                    raise QualityLoopGateError(
                        f"TARGETED_REVISION_PROPOSAL artifact requires non-empty {field}"
                    )
            draft = self._stage_artifact(
                run,
                QualityLoopStage.DRAFT_CANDIDATE,
                kind="DRAFT_CANDIDATE",
            )
            if (
                artifact.payload.get("source_revision_id") != draft.payload.get("revision_id")
                or artifact.payload.get("source_revision_hash") != draft.payload.get("revision_hash")
            ):
                raise QualityLoopGateError(
                    "TARGETED_REVISION_PROPOSAL must match the exact draft revision baseline"
                )
            return

        if next_stage == QualityLoopStage.POST_REVISION_CHECKS:
            if evidence.get("result") != "PASS" or evidence.get("all_exact_baseline") is not True:
                raise QualityLoopGateError(
                    "POST_REVISION_CHECKS requires PASS against the exact baseline"
                )
            proposal_count = evidence.get("proposal_count")
            if (
                not isinstance(proposal_count, int)
                or isinstance(proposal_count, bool)
                or proposal_count < 0
            ):
                raise QualityLoopGateError(
                    "POST_REVISION_CHECKS requires a non-negative proposal_count"
                )
            revision = self._stage_artifact(
                run,
                QualityLoopStage.REVISION_PROPOSAL,
                kind="TARGETED_REVISION_PROPOSAL",
            )
            proposal_ids = revision.payload.get("proposal_ids")
            if not isinstance(proposal_ids, list) or any(
                not isinstance(item, str) or not item for item in proposal_ids
            ):
                raise QualityLoopGateError(
                    "TARGETED_REVISION_PROPOSAL requires a list of exact proposal_ids"
                )
            if proposal_count != len(proposal_ids):
                raise QualityLoopGateError(
                    "POST_REVISION_CHECKS proposal_count does not match revision proposal"
                )
            return

        if next_stage == QualityLoopStage.HUMAN_REVIEW:
            draft_artifact = self._artifact(
                run,
                evidence.get("draft_artifact_id"),
                kind="DRAFT_CANDIDATE",
            )
            revision_artifact = self._artifact(
                run,
                evidence.get("revision_artifact_id"),
                kind="TARGETED_REVISION_PROPOSAL",
            )
            if evidence.get("material_status") != "PROPOSED":
                raise QualityLoopGateError("HUMAN_REVIEW requires material_status=PROPOSED")
            if draft_artifact.status != "PROPOSED" or revision_artifact.status != "PROPOSED":
                raise QualityLoopGateError(
                    "HUMAN_REVIEW must receive undecided material proposals"
                )
            return

        if next_stage == QualityLoopStage.COMPLETE:
            if evidence.get("decision") != "ACCEPT":
                raise QualityLoopGateError("quality loop completion requires decision=ACCEPT")
            review = self._stage_event(run, QualityLoopStage.HUMAN_REVIEW).evidence
            draft_artifact = self._artifact(
                run,
                review.get("draft_artifact_id"),
                kind="DRAFT_CANDIDATE",
            )
            revision_artifact = self._artifact(
                run,
                review.get("revision_artifact_id"),
                kind="TARGETED_REVISION_PROPOSAL",
            )
            if draft_artifact.status != "ACCEPTED" or revision_artifact.status != "ACCEPTED":
                raise QualityLoopGateError(
                    "quality loop completion requires accepted draft and revision material"
                )

    def start(
        self,
        admission: ChapterAdmissionStatusView,
        *,
        actor_kind: QualityActorKind,
        actor: str,
    ) -> QualityLoopRun:
        self._require_actor_kind(actor_kind)
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
        self._require_actor_kind(actor_kind)
        expected = self._ALLOWED[run.stage]
        if expected != next_stage:
            expected_text = expected.value if expected is not None else "none"
            raise QualityLoopTransitionError(
                f"invalid quality-loop transition {run.stage.value} -> {next_stage.value}; "
                f"expected {expected_text}"
            )
        if not evidence:
            raise QualityLoopTransitionError("stage transition requires provenance evidence")

        self._validate_stage_evidence(run, next_stage, evidence)

        if next_stage == QualityLoopStage.COMPLETE:
            if actor_kind not in {"HUMAN", "OWNER"}:
                raise QualityLoopGateError("quality loop completion requires HUMAN/OWNER authority")
            pending = [item.artifact_id for item in run.artifacts if item.status == "PROPOSED"]
            if pending:
                raise QualityLoopGateError(
                    "quality loop has material proposals awaiting human decision: "
                    + ", ".join(pending)
                )
            blocking = [
                item.finding_id
                for item in run.findings
                if item.severity == "BLOCKING" and item.disposition == "OPEN"
            ]
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
        self._require_actor_kind(actor_kind)
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
        self._require_actor_kind(actor_kind)
        if actor_kind not in {"HUMAN", "OWNER"}:
            raise QualityLoopGateError("material decision requires HUMAN/OWNER authority")
        artifact = next((item for item in run.artifacts if item.artifact_id == artifact_id), None)
        if artifact is None:
            raise QualityLoopGateError(f"unknown quality-loop artifact: {artifact_id}")
        if actor == artifact.created_by:
            raise QualityLoopGateError("material producer cannot approve or reject its own output")
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
        self._require_actor_kind(actor_kind)
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

    def resolve_finding(
        self,
        run: QualityLoopRun,
        finding_id: str,
        *,
        disposition: Literal["RESOLVED", "SUPERSEDED"],
        actor_kind: QualityActorKind,
        actor: str,
        reason: str,
        evidence: dict[str, Any] | None = None,
    ) -> QualityLoopFinding:
        self._require_open(run)
        self._require_actor_kind(actor_kind)
        if actor_kind not in {"HUMAN", "OWNER", "SYSTEM"}:
            raise QualityLoopGateError(
                "quality-loop finding resolution requires HUMAN/OWNER/SYSTEM authority"
            )
        finding = next((item for item in run.findings if item.finding_id == finding_id), None)
        if finding is None:
            raise QualityLoopGateError(f"unknown quality-loop finding: {finding_id}")
        if finding.disposition != "OPEN":
            raise QualityLoopGateError("quality-loop finding is already closed")
        if not reason.strip():
            raise QualityLoopGateError("finding resolution requires a reason")
        finding.disposition = disposition
        finding.resolved_by_kind = cast(Literal["HUMAN", "OWNER", "SYSTEM"], actor_kind)
        finding.resolved_by = actor
        finding.resolved_at = utc_now()
        finding.resolution_reason = reason
        finding.resolution_evidence = evidence or {}
        self._touch(run)
        return finding
