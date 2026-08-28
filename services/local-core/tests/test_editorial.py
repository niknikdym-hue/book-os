from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest
from sqlalchemy import text

from book_os_core.authority import AuthorityService, HumanApprovalRequired, StaleBaselineError
from book_os_core.db import create_database
from book_os_core.drafting import DraftSectionRequest, DraftingService
from book_os_core.editorial import (
    DecisionRequest,
    EditorialGateError,
    EditorialService,
    FindingCreateRequest,
    ProposalCreateRequest,
)
from book_os_core.editorial_diagnostics import EditorialDiagnostics
from book_os_core.memory import BookMemoryService
from book_os_core.memory_embeddings import DeterministicFakeEmbeddingAdapter, EmbeddingGateway
from book_os_core.model_gateway import DeterministicFakeAdapter, ModelGateway
from book_os_core.projects import (
    BookArchitecturePayload,
    BookContractPayload,
    ChapterContractPayload,
    NewBookRequest,
    ProjectService,
)
from book_os_core.research import (
    ClaimCreateRequest,
    ClaimReviewRequest,
    ResearchService,
)
from book_os_core.research_adapters import ResearchGateway


def book_contract() -> BookContractPayload:
    return BookContractPayload(
        reader="Business leaders",
        reader_problem="Editorial changes can silently drift from book authority",
        central_promise="A controlled editorial decision loop",
        central_thesis="Findings and proposals must remain separate from authority",
        unique_angle="Treat every material edit as an exact-base decision",
        reader_trajectory="From invisible edits to inspectable editorial decisions",
        explicit_exclusions=["No autonomous whole-book rewrite"],
        evidence_policy="Material claims require traceable evidence",
        voice_genre_constraints="Precise business nonfiction",
        readiness_criteria=["Every material edit has a human decision"],
    )


def architecture() -> BookArchitecturePayload:
    return BookArchitecturePayload.model_validate(
        {
            "parts": [
                {
                    "title": "Part I",
                    "purpose": "Exercise editorial control",
                    "chapters": [
                        {
                            "chapter_id": None,
                            "title": "First",
                            "purpose": "Introduce the editorial loop",
                            "new_contribution": "Exact-base decisions",
                            "dependencies": [],
                            "transition": "Move to whole-book control",
                        },
                        {
                            "chapter_id": None,
                            "title": "Second",
                            "purpose": "Test cross-book audit",
                            "new_contribution": "Whole-book consistency",
                            "dependencies": [],
                            "transition": "Move to BookBench",
                        },
                    ],
                }
            ],
            "intellectual_progression": "finding → proposal → decision",
            "concept_allocation": "One editorial concept per chapter",
            "promise_thesis_coverage": "Both chapters enforce material edit control",
            "major_transitions": "Local edit → whole-book consequence",
        }
    )


def chapter_contract(label: str) -> ChapterContractPayload:
    return ChapterContractPayload(
        chapter_purpose=f"Explain {label} editorial control",
        new_contribution=f"One distinct {label} mechanism",
        reader_prior_state="Reader sees edits as text replacement",
        reader_after_state="Reader sees edits as governed decisions",
        required_claims=["human decision protects material editorial authority"],
        required_or_permitted_research=["Use verified Claim Ledger evidence only"],
        required_scenes_examples=["One concrete editorial example"],
        reserved_elsewhere=["BookBench scoring belongs later"],
        opening_requirements="Open with an invisible-edit failure",
        ending_requirements="End with a visible decision",
        transition_requirements="Hand off the next governance question",
    )


def ready_editorial_book(data_dir: Path) -> dict[str, str]:
    projects = ProjectService(data_dir)
    project = projects.create_project(
        NewBookRequest(working_title="Editorial Test Book", primary_subtype="Strategy")
    )
    projects.save_book_contract(project.book_id, book_contract())
    projects.approve_book_contract(project.book_id)
    projects.save_architecture(project.book_id, architecture())
    project = projects.approve_architecture(project.book_id)
    first_chapter = project.chapters[0]
    second_chapter = project.chapters[1]
    projects.save_chapter_contract(
        project.book_id, first_chapter.chapter_id, chapter_contract("first")
    )
    projects.approve_chapter_contract(project.book_id, first_chapter.chapter_id)
    projects.save_chapter_contract(
        project.book_id, second_chapter.chapter_id, chapter_contract("second")
    )
    projects.approve_chapter_contract(project.book_id, second_chapter.chapter_id)

    duplicate_objective = (
        "Repeat this bounded editorial passage with enough shared words to prove current repetition"
    )
    drafting = DraftingService(data_dir, ModelGateway({"fake": DeterministicFakeAdapter()}))
    first = drafting.generate_section_draft(
        project.book_id,
        first_chapter.chapter_id,
        DraftSectionRequest(
            section_objective=duplicate_objective,
            provider="fake",
            model="fake-writer",
        ),
    )
    second = drafting.generate_section_draft(
        project.book_id,
        second_chapter.chapter_id,
        DraftSectionRequest(
            section_objective=duplicate_objective,
            provider="fake",
            model="fake-writer",
        ),
    )
    assert first.unit_id and first.revision_id and first.revision_hash and first.text
    assert second.unit_id and second.revision_id and second.revision_hash and second.text

    research = ResearchService(data_dir, ResearchGateway({}))
    claims = []
    for suffix in ("unreviewed", "disputed", "unsupported"):
        claims.append(
            research.create_claim(
                project.book_id,
                ClaimCreateRequest(
                    chapter_id=first_chapter.chapter_id,
                    unit_id=first.unit_id,
                    manuscript_revision_id=first.revision_id,
                    manuscript_revision_hash=first.revision_hash,
                    normalized_text=f"Material editorial claim {suffix} requires evidence.",
                    claim_type="EMPIRICAL",
                    materiality="HIGH",
                    required_evidence_level="TRACEABLE_SOURCE",
                ),
            )
        )
    research.review_claim(
        project.book_id,
        claims[1].claim_id,
        ClaimReviewRequest(state="DISPUTED", actor="OWNER", reason="fixture dispute"),
    )
    research.review_claim(
        project.book_id,
        claims[2].claim_id,
        ClaimReviewRequest(state="UNSUPPORTED", actor="OWNER", reason="fixture unsupported"),
    )

    return {
        "book_id": project.book_id,
        "chapter_1": first_chapter.chapter_id,
        "chapter_2": second_chapter.chapter_id,
        "unit_1": first.unit_id,
        "unit_2": second.unit_id,
        "revision_1": first.revision_id,
        "revision_hash_1": first.revision_hash,
        "revision_2": second.revision_id,
        "revision_hash_2": second.revision_hash,
        "text_1": first.text,
        "text_2": second.text,
        "claim_1": claims[0].claim_id,
        "claim_2": claims[1].claim_id,
        "claim_3": claims[2].claim_id,
    }


def current_unit_head(data_dir: Path, book_id: str, unit_id: str):
    engine = create_database(data_dir / "projects" / book_id / "project.sqlite")
    with engine.connect() as connection:
        entity_id = cast(
            str,
            connection.execute(
                text("SELECT authority_entity_id FROM manuscript_units WHERE unit_id=:unit_id"),
                {"unit_id": unit_id},
            ).scalar_one(),
        )
    return entity_id, AuthorityService(engine).get_head(entity_id)


def manual_finding(
    data_dir: Path,
    state: dict[str, str],
    *,
    unit_key: str = "unit_1",
    role: str = "LITERARY_EDITOR",
):
    unit_id = state[unit_key]
    _, head = current_unit_head(data_dir, state["book_id"], unit_id)
    service = EditorialService(data_dir)
    return service.create_finding(
        state["book_id"],
        FindingCreateRequest(
            role=cast(object, role),
            category="MANUAL_EDITORIAL_FINDING",
            target_kind="MANUSCRIPT_UNIT",
            target_id=unit_id,
            base_revision_id=head.revision_id,
            base_revision_hash=head.revision_hash,
            diagnosis="The passage needs a bounded material editorial revision.",
            why="The proposed change should be reviewed as an exact-base decision.",
            evidence={"source": "human editorial review"},
            severity="MAJOR",
            confidence=0.9,
            expected_effect="Improve the passage without silent authority mutation.",
            risks="Meaning could drift if accepted without review.",
            actor="OWNER",
            actor_kind="HUMAN",
        ),
    )


def test_m6_schema_and_finding_exact_baseline_do_not_mutate_authority(tmp_path: Path) -> None:
    state = ready_editorial_book(tmp_path)
    service = EditorialService(tmp_path)
    entity_id, before = current_unit_head(tmp_path, state["book_id"], state["unit_1"])
    engine = create_database(tmp_path / "projects" / state["book_id"] / "project.sqlite")
    with engine.connect() as connection:
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            == "0009"
        )
        tables = {
            row[0]
            for row in connection.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        }
    assert {"editorial_runs", "editorial_findings", "editorial_finding_proposals"} <= tables

    finding = manual_finding(tmp_path, state)
    assert finding.base_revision_id == before.revision_id
    assert finding.base_revision_hash == before.revision_hash
    assert AuthorityService(engine).get_head(entity_id) == before

    with pytest.raises(EditorialGateError, match="exact current"):
        service.create_finding(
            state["book_id"],
            FindingCreateRequest(
                role="STYLE_GUARDIAN",
                category="STALE_FIXTURE",
                target_kind="MANUSCRIPT_UNIT",
                target_id=state["unit_1"],
                base_revision_id=state["revision_2"],
                base_revision_hash=state["revision_hash_2"],
                diagnosis="Stale baseline should fail.",
                why="Exact current baseline is mandatory.",
            ),
        )
    assert AuthorityService(engine).get_head(entity_id) == before


def test_deterministic_developmental_cross_book_and_fact_runs_only_create_findings(
    tmp_path: Path,
) -> None:
    state = ready_editorial_book(tmp_path)
    diagnostics = EditorialDiagnostics(tmp_path)
    research = ResearchService(tmp_path, ResearchGateway({}))
    before_claim_states = {
        claim_id: research.get_claim(state["book_id"], claim_id).verification_state
        for claim_id in (state["claim_1"], state["claim_2"], state["claim_3"])
    }
    _, first_head = current_unit_head(tmp_path, state["book_id"], state["unit_1"])
    _, second_head = current_unit_head(tmp_path, state["book_id"], state["unit_2"])

    developmental = diagnostics.run_developmental(state["book_id"], state["chapter_1"])
    assert developmental.role == "DEVELOPMENTAL_EDITOR"
    assert any(item.category == "REQUIRED_CLAIM_LEXICAL_GAP" for item in developmental.findings)
    assert all(
        "Lexical" in item.risks or "lexical" in item.diagnosis.lower()
        for item in developmental.findings
    )

    cross_book = diagnostics.run_cross_book(state["book_id"])
    assert cross_book.role == "CROSS_BOOK_AUDITOR"
    assert any(item.category == "NEAR_DUPLICATE_CURRENT_UNITS" for item in cross_book.findings)

    fact = diagnostics.run_fact_checker(state["book_id"])
    assert fact.role == "FACT_CHECKER"
    categories = {item.category for item in fact.findings}
    assert "MATERIAL_CLAIM_UNREVIEWED" in categories
    assert "MATERIAL_CLAIM_DISPUTED" in categories
    assert "MATERIAL_CLAIM_UNSUPPORTED" in categories

    after_claim_states = {
        claim_id: research.get_claim(state["book_id"], claim_id).verification_state
        for claim_id in (state["claim_1"], state["claim_2"], state["claim_3"])
    }
    assert after_claim_states == before_claim_states
    assert current_unit_head(tmp_path, state["book_id"], state["unit_1"])[1] == first_head
    assert current_unit_head(tmp_path, state["book_id"], state["unit_2"])[1] == second_head


def test_literary_and_style_roles_share_typed_finding_workflow(tmp_path: Path) -> None:
    state = ready_editorial_book(tmp_path)
    literary = manual_finding(tmp_path, state, role="LITERARY_EDITOR")
    style = manual_finding(tmp_path, state, unit_key="unit_2", role="STYLE_GUARDIAN")
    assert literary.role == "LITERARY_EDITOR"
    assert style.role == "STYLE_GUARDIAN"
    assert literary.status == style.status == "OPEN"


def test_proposal_diff_is_exact_base_and_does_not_change_head(tmp_path: Path) -> None:
    state = ready_editorial_book(tmp_path)
    service = EditorialService(tmp_path)
    finding = manual_finding(tmp_path, state)
    entity_id, before = current_unit_head(tmp_path, state["book_id"], state["unit_1"])

    proposed_text = "A human-readable revised passage with one controlled editorial decision."
    proposal = service.create_manuscript_proposal(
        state["book_id"],
        finding.finding_id,
        ProposalCreateRequest(
            proposed_text=proposed_text,
            rationale="Replace the duplicated wording with a bounded revision.",
            actor="editor",
            actor_kind="AI",
        ),
    )
    assert proposal.status == "OPEN"
    assert proposal.stale is False
    assert proposal.base_revision_id == before.revision_id
    assert proposal.proposed_text == proposed_text
    assert "--- current" in proposal.diff
    assert "+++ proposed" in proposal.diff
    assert state["text_1"] in proposal.diff
    assert proposed_text in proposal.diff

    engine = create_database(tmp_path / "projects" / state["book_id"] / "project.sqlite")
    assert AuthorityService(engine).get_head(entity_id) == before


def test_human_accept_changes_authority_resolves_finding_and_preserves_claim_binding(
    tmp_path: Path,
) -> None:
    state = ready_editorial_book(tmp_path)
    service = EditorialService(tmp_path)
    finding = manual_finding(tmp_path, state)
    entity_id, before = current_unit_head(tmp_path, state["book_id"], state["unit_1"])
    proposal = service.create_manuscript_proposal(
        state["book_id"],
        finding.finding_id,
        ProposalCreateRequest(
            proposed_text="Accepted editorial revision with a unique current memory phrase.",
            rationale="Human review candidate",
        ),
    )

    with pytest.raises(HumanApprovalRequired):
        service.accept(
            state["book_id"],
            finding.finding_id,
            proposal.proposal_id,
            DecisionRequest(actor="editor-model", actor_kind="AI", reason="self approval"),
        )

    accepted = service.accept(
        state["book_id"],
        finding.finding_id,
        proposal.proposal_id,
        DecisionRequest(actor="OWNER", actor_kind="HUMAN", reason="material edit approved"),
    )
    assert accepted.finding.status == "RESOLVED"
    assert accepted.accepted_revision_id
    assert accepted.approval_id
    engine = create_database(tmp_path / "projects" / state["book_id"] / "project.sqlite")
    head = AuthorityService(engine).get_head(entity_id)
    assert head.revision_id == accepted.accepted_revision_id
    assert head.status == "APPROVED"
    assert head.revision_id != before.revision_id

    research = ResearchService(tmp_path, ResearchGateway({}))
    claim = research.get_claim(state["book_id"], state["claim_1"])
    assert claim.manuscript_revision_id == state["revision_1"]
    assert claim.manuscript_revision_hash == state["revision_hash_1"]

    corpus = service.decision_corpus(state["book_id"], finding.finding_id)
    assert corpus["original_revision"]["revision_id"] == before.revision_id
    assert corpus["proposals"][0]["proposal_id"] == proposal.proposal_id
    assert corpus["decisions"][0]["decision"] == "ACCEPT"
    assert corpus["approvals"][0]["approved_revision_id"] == head.revision_id
    assert corpus["current_final_revision"]["revision_id"] == head.revision_id


def test_reject_request_revision_and_waive_preserve_current_authority(tmp_path: Path) -> None:
    state = ready_editorial_book(tmp_path)
    service = EditorialService(tmp_path)

    reject_finding = manual_finding(tmp_path, state)
    _, before = current_unit_head(tmp_path, state["book_id"], state["unit_1"])
    rejected_proposal = service.create_manuscript_proposal(
        state["book_id"],
        reject_finding.finding_id,
        ProposalCreateRequest(proposed_text="Rejected revision.", rationale="reject fixture"),
    )
    rejected = service.reject(
        state["book_id"],
        reject_finding.finding_id,
        rejected_proposal.proposal_id,
        DecisionRequest(actor="OWNER", actor_kind="HUMAN", reason="not the right edit"),
    )
    assert rejected.decision == "REJECT"
    assert rejected.finding.status == "OPEN"
    assert rejected.proposal is not None and rejected.proposal.status == "REJECTED"
    assert current_unit_head(tmp_path, state["book_id"], state["unit_1"])[1] == before

    revise_finding = manual_finding(tmp_path, state)
    revise_proposal = service.create_manuscript_proposal(
        state["book_id"],
        revise_finding.finding_id,
        ProposalCreateRequest(proposed_text="Needs another revision.", rationale="revise fixture"),
    )
    revised = service.request_revision(
        state["book_id"],
        revise_finding.finding_id,
        revise_proposal.proposal_id,
        DecisionRequest(actor="OWNER", actor_kind="HUMAN", reason="revise the ending"),
    )
    assert revised.decision == "REQUEST_REVISION"
    assert revised.finding.status == "OPEN"
    assert revised.proposal is not None and revised.proposal.status == "SUPERSEDED"
    assert current_unit_head(tmp_path, state["book_id"], state["unit_1"])[1] == before

    waive_finding = manual_finding(tmp_path, state)
    waive_proposal = service.create_manuscript_proposal(
        state["book_id"],
        waive_finding.finding_id,
        ProposalCreateRequest(proposed_text="Waived revision.", rationale="waive fixture"),
    )
    waived = service.waive(
        state["book_id"],
        waive_finding.finding_id,
        DecisionRequest(actor="OWNER", actor_kind="HUMAN", reason="intentional repetition"),
        proposal_id=waive_proposal.proposal_id,
    )
    assert waived.decision == "WAIVE"
    assert waived.finding.status == "WAIVED"
    assert waived.proposal is not None and waived.proposal.status == "SUPERSEDED"
    assert current_unit_head(tmp_path, state["book_id"], state["unit_1"])[1] == before


def test_stale_proposal_cannot_be_accepted(tmp_path: Path) -> None:
    state = ready_editorial_book(tmp_path)
    service = EditorialService(tmp_path)
    stale_finding = manual_finding(tmp_path, state)
    stale_proposal = service.create_manuscript_proposal(
        state["book_id"],
        stale_finding.finding_id,
        ProposalCreateRequest(proposed_text="Stale proposal text.", rationale="stale candidate"),
    )

    winning_finding = manual_finding(tmp_path, state)
    winning_proposal = service.create_manuscript_proposal(
        state["book_id"],
        winning_finding.finding_id,
        ProposalCreateRequest(
            proposed_text="Winning current revision.", rationale="winning candidate"
        ),
    )
    service.accept(
        state["book_id"],
        winning_finding.finding_id,
        winning_proposal.proposal_id,
        DecisionRequest(actor="OWNER", actor_kind="HUMAN", reason="accept competing edit"),
    )

    refreshed = service.get_proposal(
        state["book_id"], stale_finding.finding_id, stale_proposal.proposal_id
    )
    assert refreshed.stale is True
    with pytest.raises(StaleBaselineError):
        service.accept(
            state["book_id"],
            stale_finding.finding_id,
            stale_proposal.proposal_id,
            DecisionRequest(actor="OWNER", actor_kind="HUMAN", reason="should fail stale"),
        )


def test_cross_book_audit_ignores_historical_duplicate_after_accepted_edit(tmp_path: Path) -> None:
    state = ready_editorial_book(tmp_path)
    service = EditorialService(tmp_path)
    diagnostics = EditorialDiagnostics(tmp_path)
    assert diagnostics.run_cross_book(state["book_id"]).findings

    finding = manual_finding(tmp_path, state, unit_key="unit_2")
    proposal = service.create_manuscript_proposal(
        state["book_id"],
        finding.finding_id,
        ProposalCreateRequest(
            proposed_text="A completely distinct current passage about a different mechanism and outcome.",
            rationale="Remove accidental duplication",
        ),
    )
    service.accept(
        state["book_id"],
        finding.finding_id,
        proposal.proposal_id,
        DecisionRequest(actor="OWNER", actor_kind="HUMAN", reason="make current passage distinct"),
    )
    assert diagnostics.run_cross_book(state["book_id"]).findings == []


def test_book_memory_sync_after_accept_uses_new_current_revision_and_keeps_old_in_history(
    tmp_path: Path,
) -> None:
    state = ready_editorial_book(tmp_path)
    editorial = EditorialService(tmp_path)
    memory = BookMemoryService(
        tmp_path,
        EmbeddingGateway({"fake": DeterministicFakeEmbeddingAdapter(dimension=8)}),
    )
    memory.synchronize(state["book_id"])
    assert memory.lexical_search(
        state["book_id"], "Repeat this bounded editorial passage", object_kinds=["MANUSCRIPT_UNIT"]
    )

    finding = manual_finding(tmp_path, state)
    proposal = editorial.create_manuscript_proposal(
        state["book_id"],
        finding.finding_id,
        ProposalCreateRequest(
            proposed_text="Unique accepted editorial memory phrase for current retrieval.",
            rationale="Replace old current phrase",
        ),
    )
    accepted = editorial.accept(
        state["book_id"],
        finding.finding_id,
        proposal.proposal_id,
        DecisionRequest(actor="OWNER", actor_kind="HUMAN", reason="approve memory fixture"),
    )
    memory.synchronize(state["book_id"])

    current = memory.lexical_search(
        state["book_id"],
        "Unique accepted editorial memory phrase",
        object_kinds=["MANUSCRIPT_UNIT"],
    )
    assert current[0].revision_id == accepted.accepted_revision_id
    assert current[0].currentness == "CURRENT"
    current_old = memory.lexical_search(
        state["book_id"],
        "Repeat this bounded editorial passage",
        object_kinds=["MANUSCRIPT_UNIT"],
    )
    assert all(item.revision_id != state["revision_1"] for item in current_old)
    history_old = memory.lexical_search(
        state["book_id"],
        "Repeat this bounded editorial passage",
        scope="HISTORY",
        object_kinds=["MANUSCRIPT_UNIT"],
    )
    assert any(item.revision_id == state["revision_1"] for item in history_old)
