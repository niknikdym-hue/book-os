from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DatabaseError

from book_os_core.authority import AuthorityService
from book_os_core.bookbench import BookBenchService
from book_os_core.db import create_database
from book_os_core.drafting import DraftSectionRequest, DraftingService
from book_os_core.editorial import (
    DecisionRequest,
    EditorialService,
    FindingCreateRequest,
    ProposalCreateRequest,
)
from book_os_core.model_gateway import DeterministicFakeAdapter, ModelGateway
from book_os_core.projects import (
    BookArchitecturePayload,
    BookContractPayload,
    ChapterContractPayload,
    NewBookRequest,
    ProjectService,
)
from book_os_core.research import ClaimCreateRequest, ClaimReviewRequest, ResearchService
from book_os_core.research_adapters import ResearchGateway


def book_contract() -> BookContractPayload:
    return BookContractPayload(
        reader="Business leaders",
        reader_problem="The whole book can pass local edits while accumulating invisible quality risks",
        central_promise="A reproducible internal quality evaluation system",
        central_thesis="Exact revision evaluation beats impressionistic scoring",
        unique_angle="BookBench reports dimensions and evidence, never a magic overall score",
        reader_trajectory="From intuition-only review to versioned evaluation evidence",
        explicit_exclusions=["No bestseller prediction", "No one-number quality score"],
        evidence_policy="Material claims require traceable evidence",
        voice_genre_constraints="Precise business nonfiction",
        readiness_criteria=["Blocking quality dimensions are visible and reviewable"],
    )


def architecture() -> BookArchitecturePayload:
    return BookArchitecturePayload.model_validate(
        {
            "parts": [
                {
                    "title": "Part I",
                    "purpose": "Exercise BookBench checks",
                    "chapters": [
                        {
                            "chapter_id": None,
                            "title": "Quality Signals",
                            "purpose": "Explain deterministic checks",
                            "new_contribution": "Measured quality evidence",
                            "dependencies": [],
                            "transition": "Move from signals to comparison",
                        },
                        {
                            "chapter_id": None,
                            "title": "Regression",
                            "purpose": "Exercise cross-book checks",
                            "new_contribution": "Reproducible comparisons",
                            "dependencies": [],
                            "transition": "Move toward provider evaluation",
                        },
                    ],
                }
            ],
            "intellectual_progression": "signals → evidence → regression",
            "concept_allocation": "One BookBench concept per chapter",
            "promise_thesis_coverage": "Both chapters advance reproducible evaluation",
            "major_transitions": "Local checks feed whole-book evaluation",
        }
    )


def chapter_contract(label: str) -> ChapterContractPayload:
    return ChapterContractPayload(
        chapter_purpose=f"Explain {label} quality evaluation",
        new_contribution=f"One distinct {label} BookBench mechanism",
        reader_prior_state="Reader relies on impressionistic review",
        reader_after_state="Reader can inspect measured evidence",
        required_claims=["exact revision evaluation prevents hidden quality drift"],
        required_or_permitted_research=["Use explicit Claim Ledger evidence"],
        required_scenes_examples=["One concrete evaluation example"],
        reserved_elsewhere=["Russia provider promotion belongs to M8"],
        opening_requirements="Open with a hidden quality failure",
        ending_requirements="End with a measurable evaluation decision",
        transition_requirements="Hand off the next quality question",
    )


def ready_book(data_dir: Path) -> dict[str, str]:
    projects = ProjectService(data_dir)
    project = projects.create_project(
        NewBookRequest(working_title="BookBench Test Book", primary_subtype="Strategy")
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
        "Это не про скорость, а про ясность? Важно понимать этот точный повторяемый фрагмент "
        "для проверки BookBench и качества редакционного решения"
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
                    normalized_text=f"Material BookBench claim {suffix} needs evidence.",
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
        "claim_1": claims[0].claim_id,
    }


def test_m7_schema_snapshot_exactness_and_currentness(tmp_path: Path) -> None:
    state = ready_book(tmp_path)
    service = BookBenchService(tmp_path)
    snapshot = service.create_snapshot(state["book_id"], scope="BOOK")
    assert snapshot.current is True
    assert snapshot.snapshot_hash
    assert {target.target_kind for target in snapshot.targets} >= {
        "BOOK_CONTRACT",
        "CHAPTER_CONTRACT",
        "MANUSCRIPT_UNIT",
        "CLAIM",
    }
    unit_target = next(target for target in snapshot.targets if target.target_id == state["unit_1"])
    assert unit_target.revision_id == state["revision_1"]
    assert unit_target.revision_hash == state["revision_hash_1"]

    engine = create_database(tmp_path / "projects" / state["book_id"] / "project.sqlite")
    with engine.connect() as connection:
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            == "0009"
        )
        assert connection.execute(
            text("SELECT COUNT(*) FROM evaluation_snapshot_targets WHERE snapshot_id=:snapshot_id"),
            {"snapshot_id": snapshot.snapshot_id},
        ).scalar_one() == len(snapshot.targets)

    editorial = EditorialService(tmp_path)
    entity_id = (
        engine.connect()
        .execute(
            text("SELECT authority_entity_id FROM manuscript_units WHERE unit_id=:unit_id"),
            {"unit_id": state["unit_1"]},
        )
        .scalar_one()
    )
    head = AuthorityService(engine).get_head(str(entity_id))
    finding = editorial.create_finding(
        state["book_id"],
        FindingCreateRequest(
            role="LITERARY_EDITOR",
            category="BOOKBENCH_CURRENTNESS_FIXTURE",
            target_kind="MANUSCRIPT_UNIT",
            target_id=state["unit_1"],
            base_revision_id=head.revision_id,
            base_revision_hash=head.revision_hash,
            diagnosis="Create a later current revision after the BookBench snapshot.",
            why="The old snapshot must remain reproducible but become visibly non-current.",
            actor="OWNER",
            actor_kind="HUMAN",
        ),
    )
    proposal = editorial.create_manuscript_proposal(
        state["book_id"],
        finding.finding_id,
        ProposalCreateRequest(
            proposed_text="A unique later revision that invalidates only currentness, not old evaluation evidence.",
            rationale="currentness fixture",
        ),
    )
    editorial.accept(
        state["book_id"],
        finding.finding_id,
        proposal.proposal_id,
        DecisionRequest(actor="OWNER", actor_kind="HUMAN", reason="accept currentness fixture"),
    )

    old = service.get_snapshot(state["book_id"], snapshot.snapshot_id)
    assert old.current is False
    new = service.create_snapshot(state["book_id"], scope="BOOK")
    assert new.current is True
    assert new.snapshot_hash != snapshot.snapshot_hash
    assert old.snapshot_hash == snapshot.snapshot_hash


def test_voice_fingerprint_uses_exact_references_and_is_diagnostic(tmp_path: Path) -> None:
    state = ready_book(tmp_path)
    service = BookBenchService(tmp_path)
    reference = service.create_snapshot(state["book_id"], scope="BOOK")
    fingerprint = service.create_voice_fingerprint(
        state["book_id"], reference.snapshot_id, name="Explicit synthetic references"
    )
    assert fingerprint.extractor_version == "1.0.0"
    assert fingerprint.reference_revisions
    assert fingerprint.reference_revisions[0]["revision_hash"]
    assert "rhetorical_question_rate" in fingerprint.features
    listed = service.list_voice_fingerprints(state["book_id"])
    assert [item.fingerprint_id for item in listed] == [fingerprint.fingerprint_id]
    assert listed[0].reference_revisions == fingerprint.reference_revisions

    comparison = service.compare_voice(
        state["book_id"], fingerprint.fingerprint_id, reference.snapshot_id
    )
    assert comparison.diagnostic_only is True
    assert set(comparison.feature_deltas) == {
        "sentence_length_mean",
        "paragraph_length_mean",
        "first_person_rate",
        "rhetorical_question_rate",
        "concrete_number_density",
    }
    assert all(delta == 0 for delta in comparison.feature_deltas.values())
    assert comparison.target_revisions == fingerprint.reference_revisions


def test_deterministic_suite_is_actionable_reproducible_and_has_no_magic_score(
    tmp_path: Path,
) -> None:
    state = ready_book(tmp_path)
    service = BookBenchService(tmp_path)
    snapshot = service.create_snapshot(state["book_id"], scope="BOOK")
    runs = service.run_deterministic_suite(state["book_id"], snapshot.snapshot_id)
    assert len(runs) == 7
    assert all(run.status == "SUCCEEDED" for run in runs)

    repetition = next(run for run in runs if run.check_id == "deterministic.repetition")
    assert repetition.findings
    assert repetition.findings[0].category == "REPEATED_NORMALIZED_SENTENCE"
    assert repetition.findings[0].revision_id
    assert repetition.findings[0].revision_hash
    assert repetition.findings[0].location.startswith("sentence:")
    assert repetition.findings[0].evidence["occurrences"]
    assert repetition.findings[0].recommended_action

    evidence = next(run for run in runs if run.check_id == "deterministic.evidence")
    categories = {finding.category for finding in evidence.findings}
    assert "MATERIAL_CLAIM_UNREVIEWED" in categories
    assert "MATERIAL_CLAIM_DISPUTED" in categories
    assert "MATERIAL_CLAIM_UNSUPPORTED" in categories
    assert any(finding.severity == "BLOCKING" for finding in evidence.findings)

    pathology = next(run for run in runs if run.check_id == "deterministic.ai_prose_pathology")
    pathology_categories = {finding.category for finding in pathology.findings}
    assert "FALSE_CONTRAST_TEMPLATE" in pathology_categories
    assert "NOT_ABOUT_TEMPLATE" in pathology_categories
    assert pathology.metrics["ai_authorship_probability"] is None
    assert pathology.output["claim"].startswith("measured prose patterns")

    statistics_run = next(run for run in runs if run.check_id == "deterministic.statistics")
    assert statistics_run.metrics["sentence_count"] > 0
    assert statistics_run.metrics["sentence_length_mean_tokens"] > 0
    assert statistics_run.metrics["lexical_diversity"] > 0

    second_statistics = service.run_check(
        state["book_id"], snapshot.snapshot_id, "deterministic.statistics"
    )
    assert second_statistics.metrics == statistics_run.metrics

    report = service.report(state["book_id"], snapshot.snapshot_id)
    dumped = report.model_dump(mode="json")
    assert "overall_score" not in dumped
    assert "score" not in dumped
    assert report.dimensions
    assert any(dimension.state == "BLOCKING" for dimension in report.dimensions)
    assert "EVIDENCE_UNSUPPORTED_CLAIMS" in report.blocking_dimensions
    assert report.current is True


def test_evaluation_findings_and_runs_are_immutable_and_authority_is_unchanged(
    tmp_path: Path,
) -> None:
    state = ready_book(tmp_path)
    service = BookBenchService(tmp_path)
    snapshot = service.create_snapshot(state["book_id"], scope="BOOK")
    engine = create_database(tmp_path / "projects" / state["book_id"] / "project.sqlite")
    with engine.connect() as connection:
        entity_id = connection.execute(
            text("SELECT authority_entity_id FROM manuscript_units WHERE unit_id=:unit_id"),
            {"unit_id": state["unit_1"]},
        ).scalar_one()
    before = AuthorityService(engine).get_head(str(entity_id))

    run = service.run_check(state["book_id"], snapshot.snapshot_id, "deterministic.repetition")
    assert run.findings
    finding_id = run.findings[0].finding_id
    with engine.begin() as connection:
        with pytest.raises(DatabaseError):
            connection.execute(
                text("UPDATE evaluation_findings SET category='rewritten' WHERE finding_id=:id"),
                {"id": finding_id},
            )
    with engine.begin() as connection:
        with pytest.raises(DatabaseError):
            connection.execute(
                text("UPDATE evaluation_runs SET status='FAILED' WHERE evaluation_id=:id"),
                {"id": run.evaluation_id},
            )
    assert AuthorityService(engine).get_head(str(entity_id)) == before


def test_semantic_candidates_config_gate_and_fake_only(tmp_path: Path) -> None:
    from book_os_core.memory_embeddings import DeterministicFakeEmbeddingAdapter, EmbeddingGateway

    state = ready_book(tmp_path)
    fake = DeterministicFakeEmbeddingAdapter(dimension=4)
    service = BookBenchService(tmp_path, EmbeddingGateway({"fake": fake}))
    snapshot = service.create_snapshot(state["book_id"], scope="BOOK")
    result = service.run_semantic(
        state["book_id"], snapshot.snapshot_id, provider="fake", model="fake-v1"
    )
    assert result.candidates_only and result.embedding_config["provider"] == "fake"
    assert result.evaluation_ids and fake.calls
    with pytest.raises(Exception, match="incompatible embedding config"):
        service.run_semantic(
            state["book_id"],
            snapshot.snapshot_id,
            provider="fake",
            model="fake-v1",
            expected_config_hash="0" * 64,
        )


def test_judge_independence_blind_pairwise_and_persistence(tmp_path: Path) -> None:
    state = ready_book(tmp_path)
    gateway = ModelGateway({"fake": DeterministicFakeAdapter()})
    service = BookBenchService(tmp_path, model_gateway=gateway)
    snapshot = service.create_snapshot(state["book_id"], scope="BOOK")
    run = service.run_judge(
        state["book_id"],
        snapshot.snapshot_id,
        dimension="AUTHOR_VOICE",
        provider="fake",
        model="same",
        config_id="same",
        writer={"provider": "fake", "model": "same", "config_id": "same"},
    )
    assert run.independence_state == "SAME_CONFIG" and run.output["release_grade"] is False
    assert run.cost_usd is None
    first = service.run_pairwise(
        state["book_id"],
        snapshot.snapshot_id,
        dimension="AUTHOR_VOICE",
        candidates={"candidate-one": "one", "candidate-two": "two"},
        seed=42,
        provider="fake",
        model="judge",
        config_id="judge",
    )
    second = service.run_pairwise(
        state["book_id"],
        snapshot.snapshot_id,
        dimension="AUTHOR_VOICE",
        candidates={"candidate-one": "one", "candidate-two": "two"},
        seed=42,
        provider="fake",
        model="judge",
        config_id="judge",
    )
    assert first.labels == second.labels and first.winner_candidate_id == first.labels["A"]


def test_dataset_scorecards_and_current_safe_handoff(tmp_path: Path) -> None:
    state = ready_book(tmp_path)
    editorial = EditorialService(tmp_path)
    finding = editorial.create_finding(
        state["book_id"],
        FindingCreateRequest(
            role="LITERARY_EDITOR",
            category="SYNTHETIC_CASE",
            target_kind="MANUSCRIPT_UNIT",
            target_id=state["unit_1"],
            base_revision_id=state["revision_1"],
            base_revision_hash=state["revision_hash_1"],
            diagnosis="Synthetic diagnostic",
            why="Synthetic acceptance fixture",
            actor="OWNER",
            actor_kind="HUMAN",
        ),
    )
    proposal = editorial.create_manuscript_proposal(
        state["book_id"],
        finding.finding_id,
        ProposalCreateRequest(proposed_text="Synthetic improved revision.", rationale="fixture"),
    )
    editorial.reject(
        state["book_id"],
        finding.finding_id,
        proposal.proposal_id,
        DecisionRequest(actor="OWNER", actor_kind="HUMAN", reason="labelled synthetic rejection"),
    )
    service = BookBenchService(tmp_path)
    dataset = service.create_dataset(state["book_id"], name="synthetic")
    assert dataset.version == 1 and dataset.case_count == 1 and dataset.dataset_hash
    again = service.create_dataset(state["book_id"], name="synthetic")
    assert again.dataset_snapshot_id == dataset.dataset_snapshot_id
    cards = service.compare_configs(
        state["book_id"],
        dataset.dataset_snapshot_id,
        configs=[{"config_id": "fake-a"}, {"config_id": "fake-b"}],
    )
    assert len(cards) == 2 and all(c.dimensions and c.cost_usd == 0 for c in cards)
    snapshot = service.create_snapshot(state["book_id"], scope="BOOK")
    runs = service.run_deterministic_suite(state["book_id"], snapshot.snapshot_id)
    eval_finding = next(f for r in runs for f in r.findings if f.target_kind == "MANUSCRIPT_UNIT")
    handed = service.handoff(state["book_id"], eval_finding.finding_id)
    assert (
        handed.evidence["bookbench_provenance"]["evaluation_finding_id"] == eval_finding.finding_id
    )
    assert editorial.list_proposals(state["book_id"], handed.finding_id) == []
