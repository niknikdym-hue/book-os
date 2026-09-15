from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import text

from book_os_core.authority import AuthorityService
from book_os_core.db import create_database
from book_os_core.drafting import DraftRunView
from book_os_core.model_gateway import DeterministicFakeAdapter, ModelGateway
from book_os_core.projects import NewBookRequest, ProjectService
from book_os_core.quality_loop import QualityLoopGateError, QualityLoopStage
from book_os_core.quality_orchestrator import (
    CriticFindingProposal,
    CriticReview,
    QualityLoopOrchestrationRequest,
    QualityLoopOrchestrator,
)
from test_drafting import architecture, book_contract, chapter_contract
from test_support_task017 import ensure_writing_allowed_for_test


class DeterministicIndependentCritic:
    executor_identity = "critic:deterministic-v1"

    def review(self, draft: DraftRunView, context: dict[str, Any]) -> CriticReview:
        assert draft.text
        assert context["draft_revision_id"] == draft.revision_id
        return CriticReview(
            executor_identity=self.executor_identity,
            summary="The candidate is usable but needs one targeted specificity revision.",
            findings=[
                CriticFindingProposal(
                    category="specificity",
                    diagnosis="Make the causal mechanism more explicit in the candidate.",
                    why="The deterministic draft states the objective but does not expose the mechanism.",
                    evidence={"signal": "bounded deterministic critic fixture"},
                    severity="MAJOR",
                    confidence=0.9,
                    expected_effect="Increase thought density and contract fulfillment.",
                    risks="Do not broaden beyond the section contract.",
                    proposed_text=draft.text + " Revised with an explicit bounded mechanism.",
                    rationale="Target only the critic finding; preserve the original meaning.",
                )
            ],
        )


def admitted_project(data_dir: Path) -> tuple[str, str]:
    projects = ProjectService(data_dir)
    project = projects.create_project(
        NewBookRequest(working_title="Task 020 Orchestration", primary_subtype="Strategy")
    )
    projects.save_book_contract(project.book_id, book_contract())
    projects.approve_book_contract(project.book_id)
    projects.save_architecture(project.book_id, architecture())
    project = projects.approve_architecture(project.book_id)
    chapter_id = project.chapters[0].chapter_id
    projects.save_chapter_contract(project.book_id, chapter_id, chapter_contract())
    projects.approve_chapter_contract(project.book_id, chapter_id)
    ensure_writing_allowed_for_test(data_dir, project.book_id, chapter_id)
    return project.book_id, chapter_id


def request(
    *, evidence_required: bool = True, evidence_ready: bool = True
) -> QualityLoopOrchestrationRequest:
    return QualityLoopOrchestrationRequest(
        section_objective="Explain one bounded operating mechanism",
        writer_provider="fake",
        writer_model="fake-writer",
        micro_plan="Define the mechanism, show its consequence, close with one operational implication.",
        section_intent="Add one new mechanism without expanding the chapter boundary.",
        evidence_required=evidence_required,
        evidence_ready=evidence_ready,
        evidence_summary="Synthetic rights-clean evidence fixture is ready."
        if evidence_ready
        else "",
        deterministic_checks_pass=True,
        novelty_pass=True,
        novelty_evidence="No overlap in the deterministic fixture.",
    )


def test_fake_quality_loop_reaches_human_review_with_exact_open_revision_proposal(
    tmp_path: Path,
) -> None:
    book_id, chapter_id = admitted_project(tmp_path)
    writer = DeterministicFakeAdapter()
    critic = DeterministicIndependentCritic()
    orchestrator = QualityLoopOrchestrator(
        tmp_path,
        ModelGateway({"fake": writer}),
        critic,
    )

    result = orchestrator.run(book_id, chapter_id, request())

    assert writer.last_request is not None
    assert result.run.stage == QualityLoopStage.HUMAN_REVIEW
    assert result.draft.revision_status == "DRAFT"
    assert result.critic_review.executor_identity != "fake:fake-writer"
    assert len(result.editorial_findings) == 1
    assert len(result.revision_proposals) == 1

    finding = result.editorial_findings[0]
    proposal = result.revision_proposals[0]
    assert finding.actor == critic.executor_identity
    assert finding.actor_kind == "AI"
    assert finding.run_id is None
    assert finding.evidence["quality_loop_run_id"] == result.run.run_id
    assert finding.base_revision_id == result.draft.revision_id
    assert finding.base_revision_hash == result.draft.revision_hash
    assert proposal.status == "OPEN"
    assert proposal.stale is False
    assert proposal.base_revision_id == result.draft.revision_id
    assert proposal.base_revision_hash == result.draft.revision_hash
    assert proposal.diff

    engine = create_database(tmp_path / "projects" / book_id / "project.sqlite")
    try:
        with engine.connect() as connection:
            proposal_status = connection.execute(
                text("SELECT status FROM change_proposals WHERE proposal_id=:proposal_id"),
                {"proposal_id": proposal.proposal_id},
            ).scalar_one()
            unit_entity_id = connection.execute(
                text("SELECT authority_entity_id FROM manuscript_units WHERE unit_id=:unit_id"),
                {"unit_id": result.draft.unit_id},
            ).scalar_one()
        assert proposal_status == "OPEN"
        head = AuthorityService(engine).get_head(unit_entity_id)
        assert head.revision_id == result.draft.revision_id
        assert head.revision_hash == result.draft.revision_hash
    finally:
        engine.dispose()

    assert all(item.status == "PROPOSED" for item in result.run.artifacts)


def test_evidence_required_blocks_before_writer_execution(tmp_path: Path) -> None:
    book_id, chapter_id = admitted_project(tmp_path)
    writer = DeterministicFakeAdapter()
    orchestrator = QualityLoopOrchestrator(
        tmp_path,
        ModelGateway({"fake": writer}),
        DeterministicIndependentCritic(),
    )

    with pytest.raises(QualityLoopGateError, match="EVIDENCE_REQUIRED"):
        orchestrator.run(
            book_id,
            chapter_id,
            request(evidence_required=True, evidence_ready=False),
        )

    assert writer.last_request is None
    engine = create_database(tmp_path / "projects" / book_id / "project.sqlite")
    try:
        with engine.connect() as connection:
            assert connection.execute(text("SELECT COUNT(*) FROM bounded_tasks")).scalar_one() == 0
            assert connection.execute(text("SELECT COUNT(*) FROM model_runs")).scalar_one() == 0
    finally:
        engine.dispose()


def test_same_writer_and_critic_identity_is_rejected_before_writer(tmp_path: Path) -> None:
    book_id, chapter_id = admitted_project(tmp_path)
    writer = DeterministicFakeAdapter()
    critic = DeterministicIndependentCritic()
    critic.executor_identity = "fake:fake-writer"
    orchestrator = QualityLoopOrchestrator(tmp_path, ModelGateway({"fake": writer}), critic)

    with pytest.raises(QualityLoopGateError, match="independent critic"):
        orchestrator.run(book_id, chapter_id, request())

    assert writer.last_request is None
