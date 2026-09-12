from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field, model_validator

from .drafting import DraftRunView, DraftSectionRequest, DraftingService
from .editorial import (
    EditorialService,
    FindingCreateRequest,
    FindingView,
    ProposalCreateRequest,
    ProposalView,
)
from .model_gateway import ModelGateway
from .quality_loop import (
    QualityLoopGateError,
    QualityLoopRun,
    QualityLoopStage,
    QualityLoopStateMachine,
)
from .series_production import SeriesProductionService

CriticSeverity = Literal["INFO", "MINOR", "MAJOR", "CRITICAL"]


class CriticFindingProposal(BaseModel):
    category: str = Field(min_length=1, max_length=96)
    diagnosis: str = Field(min_length=1, max_length=12000)
    why: str = Field(min_length=1, max_length=12000)
    evidence: dict[str, Any] = Field(default_factory=dict)
    severity: CriticSeverity = "MAJOR"
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    expected_effect: str = ""
    risks: str = ""
    proposed_text: str | None = Field(default=None, min_length=1, max_length=120000)
    rationale: str | None = Field(default=None, min_length=1, max_length=12000)


class CriticReview(BaseModel):
    executor_identity: str = Field(min_length=1, max_length=255)
    summary: str = Field(min_length=1, max_length=12000)
    findings: list[CriticFindingProposal] = Field(default_factory=list)


class IndependentCritic(Protocol):
    executor_identity: str

    def review(self, draft: DraftRunView, context: dict[str, Any]) -> CriticReview: ...


class QualityLoopOrchestrationRequest(BaseModel):
    section_objective: str = Field(min_length=1, max_length=12000)
    writer_provider: str = Field(min_length=1, max_length=80)
    writer_model: str = Field(min_length=1, max_length=255)
    micro_plan: str = Field(min_length=1, max_length=12000)
    section_intent: str = Field(min_length=1, max_length=12000)
    evidence_required: bool = False
    evidence_ready: bool = False
    evidence_summary: str = Field(default="", max_length=12000)
    deterministic_checks_pass: bool = True
    novelty_pass: bool = True
    novelty_evidence: str = Field(default="", max_length=12000)
    untrusted_context: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_novelty_evidence(self) -> QualityLoopOrchestrationRequest:
        if self.novelty_pass and not self.novelty_evidence.strip():
            raise ValueError("novelty_evidence is required when novelty_pass is true")
        return self


class QualityLoopOrchestrationResult(BaseModel):
    run: QualityLoopRun
    draft: DraftRunView
    critic_review: CriticReview
    editorial_findings: list[FindingView]
    revision_proposals: list[ProposalView]


class QualityLoopOrchestrator:
    """Bounded manager over accepted BOOK OS services; it never self-approves material output."""

    def __init__(self, data_dir: Path, gateway: ModelGateway, critic: IndependentCritic) -> None:
        self._production = SeriesProductionService(data_dir)
        self._drafting = DraftingService(data_dir, gateway)
        self._editorial = EditorialService(data_dir)
        self._critic = critic
        self._machine = QualityLoopStateMachine()

    @staticmethod
    def _writer_identity(request: QualityLoopOrchestrationRequest) -> str:
        return f"{request.writer_provider}:{request.writer_model}"

    @staticmethod
    def _finding_severity(severity: CriticSeverity) -> Literal["PASS", "ATTENTION", "BLOCKING"]:
        if severity == "INFO":
            return "PASS"
        if severity == "MINOR":
            return "ATTENTION"
        return "BLOCKING"

    def run(
        self,
        book_id: str,
        chapter_id: str,
        request: QualityLoopOrchestrationRequest,
    ) -> QualityLoopOrchestrationResult:
        admission = self._production.admission_status(book_id, chapter_id)
        run = self._machine.start(admission, actor_kind="SYSTEM", actor="quality-loop-manager")

        writer_identity = self._writer_identity(request)
        if self._critic.executor_identity == writer_identity:
            raise QualityLoopGateError("independent critic must not share Writer executor identity")

        self._machine.advance(
            run,
            QualityLoopStage.MICRO_PLAN,
            actor_kind="SYSTEM",
            actor="quality-loop-manager",
            evidence={"micro_plan": request.micro_plan},
        )
        self._machine.advance(
            run,
            QualityLoopStage.EVIDENCE_PLAN,
            actor_kind="SYSTEM",
            actor="quality-loop-manager",
            evidence={
                "evidence_required": request.evidence_required,
                "evidence_ready": request.evidence_ready,
                "evidence_summary": request.evidence_summary,
            },
        )
        if request.evidence_required and not request.evidence_ready:
            self._machine.record_finding(
                run,
                role="EVIDENCE_ANALYST",
                severity="BLOCKING",
                location="chapter evidence plan",
                evidence=request.evidence_summary or "Required evidence is not ready",
                recommended_action="Complete evidence work before Writer execution",
                actor_kind="SYSTEM",
                actor="quality-loop-manager",
            )
            raise QualityLoopGateError(
                "EVIDENCE_REQUIRED: Writer cannot run before evidence is ready"
            )

        self._machine.advance(
            run,
            QualityLoopStage.SECTION_INTENT,
            actor_kind="SYSTEM",
            actor="quality-loop-manager",
            evidence={"section_intent": request.section_intent},
        )

        draft = self._drafting.generate_section_draft(
            book_id,
            chapter_id,
            DraftSectionRequest(
                section_objective=request.section_objective,
                provider=request.writer_provider,
                model=request.writer_model,
                untrusted_context=request.untrusted_context,
            ),
        )
        if not draft.unit_id or not draft.revision_id or not draft.revision_hash or not draft.text:
            raise QualityLoopGateError("Writer did not return an exact persisted draft revision")

        draft_artifact = self._machine.propose_artifact(
            run,
            kind="DRAFT_CANDIDATE",
            role="WRITER",
            payload={
                "unit_id": draft.unit_id,
                "revision_id": draft.revision_id,
                "revision_hash": draft.revision_hash,
                "provider": draft.provider,
                "model": draft.model,
                "run_id": draft.run_id,
            },
            actor_kind="AI",
            actor=writer_identity,
        )
        self._machine.advance(
            run,
            QualityLoopStage.DRAFT_CANDIDATE,
            actor_kind="SYSTEM",
            actor="quality-loop-manager",
            evidence={"artifact_id": draft_artifact.artifact_id},
        )

        deterministic_pass = request.deterministic_checks_pass and bool(draft.text.strip())
        if not deterministic_pass:
            self._machine.record_finding(
                run,
                role="BOOKBENCH_JUDGE",
                severity="BLOCKING",
                location="draft candidate",
                evidence="Deterministic local checks did not pass",
                recommended_action="Repair deterministic blockers before review",
                actor_kind="SYSTEM",
                actor="quality-loop-manager",
            )
            raise QualityLoopGateError("DETERMINISTIC_CHECKS_BLOCKING")
        self._machine.advance(
            run,
            QualityLoopStage.DETERMINISTIC_CHECKS,
            actor_kind="SYSTEM",
            actor="quality-loop-manager",
            evidence={"result": "PASS", "draft_revision_id": draft.revision_id},
        )

        self._machine.advance(
            run,
            QualityLoopStage.EVIDENCE_CHECKS,
            actor_kind="SYSTEM",
            actor="quality-loop-manager",
            evidence={
                "result": "PASS",
                "required": request.evidence_required,
                "summary": request.evidence_summary,
            },
        )

        if not request.novelty_pass:
            self._machine.record_finding(
                run,
                role="BOOKBENCH_JUDGE",
                severity="BLOCKING",
                location="draft candidate",
                evidence=request.novelty_evidence or "Semantic novelty/repetition check failed",
                recommended_action="Remove semantic duplication before independent critique",
                actor_kind="SYSTEM",
                actor="quality-loop-manager",
            )
            raise QualityLoopGateError("NOVELTY_CHECK_BLOCKING")
        self._machine.advance(
            run,
            QualityLoopStage.NOVELTY_CHECK,
            actor_kind="SYSTEM",
            actor="quality-loop-manager",
            evidence={"result": "PASS", "evidence": request.novelty_evidence},
        )

        critic_context = {
            "quality_loop_run_id": run.run_id,
            "book_id": book_id,
            "chapter_id": chapter_id,
            "draft_revision_id": draft.revision_id,
            "draft_revision_hash": draft.revision_hash,
            "section_intent": request.section_intent,
            "evidence_summary": request.evidence_summary,
        }
        review = self._critic.review(draft, critic_context)
        if review.executor_identity != self._critic.executor_identity:
            raise QualityLoopGateError("critic review identity does not match configured critic")
        if review.executor_identity == writer_identity:
            raise QualityLoopGateError("independent critic must not share Writer executor identity")

        findings: list[FindingView] = []
        quality_finding_ids: list[str] = []
        proposals: list[ProposalView] = []
        for proposed in review.findings:
            finding = self._editorial.create_finding(
                book_id,
                FindingCreateRequest(
                    role="DEVELOPMENTAL_EDITOR",
                    category=proposed.category,
                    target_kind="MANUSCRIPT_UNIT",
                    target_id=draft.unit_id,
                    base_revision_id=draft.revision_id,
                    base_revision_hash=draft.revision_hash,
                    diagnosis=proposed.diagnosis,
                    why=proposed.why,
                    evidence={
                        **proposed.evidence,
                        "quality_loop_run_id": run.run_id,
                        "critic_executor_identity": review.executor_identity,
                    },
                    severity=proposed.severity,
                    confidence=proposed.confidence,
                    expected_effect=proposed.expected_effect,
                    risks=proposed.risks,
                    actor=review.executor_identity,
                    actor_kind="AI",
                ),
            )
            findings.append(finding)
            quality_finding = self._machine.record_finding(
                run,
                role="CRITIC",
                severity=self._finding_severity(proposed.severity),
                location=f"manuscript_unit:{draft.unit_id}",
                evidence=proposed.why,
                recommended_action=proposed.diagnosis,
                actor_kind="AI",
                actor=review.executor_identity,
            )
            quality_finding_ids.append(quality_finding.finding_id)
            if proposed.proposed_text:
                proposal = self._editorial.create_manuscript_proposal(
                    book_id,
                    finding.finding_id,
                    ProposalCreateRequest(
                        proposed_text=proposed.proposed_text,
                        rationale=proposed.rationale or proposed.diagnosis,
                        actor=review.executor_identity,
                        actor_kind="AI",
                    ),
                )
                proposals.append(proposal)

        self._machine.advance(
            run,
            QualityLoopStage.INDEPENDENT_CRITIC,
            actor_kind="AI",
            actor=review.executor_identity,
            evidence={
                "summary": review.summary,
                "finding_ids": quality_finding_ids,
                "editorial_finding_ids": [item.finding_id for item in findings],
            },
        )

        proposal_artifact = self._machine.propose_artifact(
            run,
            kind="TARGETED_REVISION_PROPOSAL",
            role="EDITOR",
            payload={
                "source_revision_id": draft.revision_id,
                "source_revision_hash": draft.revision_hash,
                "finding_ids": [item.finding_id for item in findings],
                "quality_finding_ids": quality_finding_ids,
                "proposal_ids": [item.proposal_id for item in proposals],
                "proposal_hashes": [item.proposed_content_hash for item in proposals],
            },
            actor_kind="AI",
            actor=review.executor_identity,
        )
        self._machine.advance(
            run,
            QualityLoopStage.REVISION_PROPOSAL,
            actor_kind="SYSTEM",
            actor="quality-loop-manager",
            evidence={"artifact_id": proposal_artifact.artifact_id},
        )

        if any(item.stale or not item.diff for item in proposals):
            raise QualityLoopGateError(
                "POST_REVISION_CHECKS_BLOCKING: proposal is stale or unchanged"
            )
        self._machine.advance(
            run,
            QualityLoopStage.POST_REVISION_CHECKS,
            actor_kind="SYSTEM",
            actor="quality-loop-manager",
            evidence={
                "result": "PASS",
                "proposal_count": len(proposals),
                "all_exact_baseline": True,
            },
        )
        self._machine.advance(
            run,
            QualityLoopStage.HUMAN_REVIEW,
            actor_kind="SYSTEM",
            actor="quality-loop-manager",
            evidence={
                "draft_artifact_id": draft_artifact.artifact_id,
                "revision_artifact_id": proposal_artifact.artifact_id,
                "material_status": "PROPOSED",
            },
        )

        return QualityLoopOrchestrationResult(
            run=run,
            draft=draft,
            critic_review=review,
            editorial_findings=findings,
            revision_proposals=proposals,
        )
