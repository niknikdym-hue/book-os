from __future__ import annotations

import pytest

from book_os_core.authority_types import InvalidAuthorityOperation
from book_os_core.mystery_authority import (
    MysteryAuthorityGraph,
    MysteryAuthorityRevision,
    create_authority_revision,
    transition_authority_status,
)
from book_os_core.mystery_research_validation import (
    FictionResearchItem,
    SharedResearchEvidence,
    bind_research_dependency,
    create_fiction_research_revision,
    evaluate_research_ledger,
    research_entity_id,
    revise_fiction_research_revision,
    transition_fiction_research_status,
    validate_fiction_research_item,
)

NOW = 1_800_000_000


def _primary_strong(
    *,
    evidence_ref: str = "ev-1",
    source_ref: str = "src-1",
    active: bool = True,
) -> SharedResearchEvidence:
    return SharedResearchEvidence(
        evidence_ref=evidence_ref,
        source_ref=source_ref,
        relationship="SUPPORTS",
        strength="STRONG",
        source_access_status="FULL_SOURCE_INSPECTED",
        primary_secondary="PRIMARY",
        active=active,
    )


def _good_r3_item(
    *,
    research_id: str = "dispatch-rule",
    assumed_answer: str = "verified answer v1",
    freshness_mode: str = "STABLE",
    fresh_until_epoch: int | None = None,
) -> FictionResearchItem:
    return FictionResearchItem(
        research_id=research_id,
        question="What rule governs this plot-critical procedure?",
        risk_class="R3",
        domain="emergency-dispatch",
        disposition="VERIFIED",
        confidence="HIGH",
        context_scope="JURISDICTION_AND_TIME",
        jurisdiction="Test jurisdiction",
        time_period="2026",
        assumed_answer=assumed_answer,
        source_refs=("src-1",),
        evidence_refs=("ev-1",),
        freshness_mode=freshness_mode,  # type: ignore[arg-type]
        fresh_until_epoch=fresh_until_epoch,
    )


def _approve_generic_in_graph(
    graph: MysteryAuthorityGraph, revision: MysteryAuthorityRevision
) -> MysteryAuthorityRevision:
    graph.register_head(revision)
    revision = transition_authority_status(
        revision, target_status="PROPOSED", actor_kind="AI"
    )
    graph.register_head(revision)
    revision = transition_authority_status(
        revision, target_status="REVIEWED", actor_kind="AI"
    )
    graph.register_head(revision)
    revision = transition_authority_status(
        revision, target_status="APPROVED", actor_kind="HUMAN"
    )
    graph.register_head(revision)
    return revision


def _approve_research_in_graph(
    graph: MysteryAuthorityGraph,
    revision: MysteryAuthorityRevision,
    item: FictionResearchItem,
    *,
    evidence_catalog: dict[str, SharedResearchEvidence],
    now_epoch: int = NOW,
) -> MysteryAuthorityRevision:
    graph.register_head(revision)
    revision = transition_fiction_research_status(
        revision,
        item,
        target_status="PROPOSED",
        actor_kind="AI",
        evidence_catalog=evidence_catalog,
        now_epoch=now_epoch,
    )
    graph.register_head(revision)
    revision = transition_fiction_research_status(
        revision,
        item,
        target_status="REVIEWED",
        actor_kind="AI",
        evidence_catalog=evidence_catalog,
        now_epoch=now_epoch,
    )
    graph.register_head(revision)
    revision = transition_fiction_research_status(
        revision,
        item,
        target_status="APPROVED",
        actor_kind="HUMAN",
        evidence_catalog=evidence_catalog,
        now_epoch=now_epoch,
    )
    graph.register_head(revision)
    return revision


def _codes(result) -> set[str]:  # type: ignore[no-untyped-def]
    return {finding.code for finding in result.findings}


def test_plot_critical_verified_research_passes_with_inspected_strong_primary_evidence() -> None:
    item = _good_r3_item()
    result = validate_fiction_research_item(
        item,
        evidence_catalog={"ev-1": _primary_strong()},
        available_source_refs=frozenset({"src-1"}),
        now_epoch=NOW,
    )

    assert result.passed
    assert result.findings == ()


def test_r3_cannot_be_verified_from_weak_or_uninspected_evidence() -> None:
    item = _good_r3_item()
    weak = SharedResearchEvidence(
        evidence_ref="ev-1",
        source_ref="src-1",
        relationship="SUPPORTS",
        strength="WEAK",
        source_access_status="METADATA_ONLY",
        primary_secondary="PRIMARY",
    )
    result = validate_fiction_research_item(
        item,
        evidence_catalog={"ev-1": weak},
        now_epoch=NOW,
    )

    codes = _codes(result)
    assert "RESEARCH.EVIDENCE.FULL_SOURCE_NOT_INSPECTED" in codes
    assert "RESEARCH.EVIDENCE.PLOT_CRITICAL_STRENGTH_INSUFFICIENT" in codes
    assert not result.passed


def test_two_independent_inspected_material_sources_can_support_r3() -> None:
    item = FictionResearchItem(
        research_id="medical-window",
        question="What is the bounded window?",
        risk_class="R3",
        domain="forensic-medicine",
        disposition="VERIFIED",
        confidence="HIGH",
        context_scope="TIME_PERIOD",
        time_period="2026",
        assumed_answer="bounded answer",
        source_refs=("src-a", "src-b"),
        evidence_refs=("ev-a", "ev-b"),
    )
    catalog = {
        "ev-a": SharedResearchEvidence(
            evidence_ref="ev-a",
            source_ref="src-a",
            relationship="SUPPORTS",
            strength="MODERATE",
            source_access_status="FULL_SOURCE_INSPECTED",
            primary_secondary="SECONDARY",
        ),
        "ev-b": SharedResearchEvidence(
            evidence_ref="ev-b",
            source_ref="src-b",
            relationship="PARTIALLY_SUPPORTS",
            strength="STRONG",
            source_access_status="FULL_SOURCE_INSPECTED",
            primary_secondary="SECONDARY",
        ),
    }

    result = validate_fiction_research_item(item, evidence_catalog=catalog, now_epoch=NOW)

    assert result.passed


def test_r2_qualified_uncertainty_is_allowed_only_when_logic_is_explicitly_safe() -> None:
    evidence = SharedResearchEvidence(
        evidence_ref="ev",
        source_ref="src",
        relationship="PARTIALLY_SUPPORTS",
        strength="MODERATE",
        source_access_status="FULL_SOURCE_INSPECTED",
        primary_secondary="SECONDARY",
    )
    unsafe = FictionResearchItem(
        research_id="travel",
        question="How long does the route take?",
        risk_class="R2",
        domain="geography",
        disposition="QUALIFIED",
        confidence="MEDIUM",
        assumed_answer="roughly 20-30 minutes",
        source_refs=("src",),
        evidence_refs=("ev",),
        logic_safe_under_qualification=False,
    )
    safe = FictionResearchItem(
        **{
            **unsafe.__dict__,
            "logic_safe_under_qualification": True,
        }
    )

    blocked = validate_fiction_research_item(
        unsafe, evidence_catalog={"ev": evidence}, now_epoch=NOW
    )
    allowed = validate_fiction_research_item(
        safe, evidence_catalog={"ev": evidence}, now_epoch=NOW
    )

    assert "RESEARCH.DISPOSITION.R2_UNSAFE_QUALIFICATION" in _codes(blocked)
    assert not blocked.passed
    assert allowed.passed


def test_r3_or_r4_qualified_answer_cannot_govern_plot_critical_writing() -> None:
    evidence = _primary_strong()
    item = FictionResearchItem(
        **{
            **_good_r3_item().__dict__,
            "disposition": "QUALIFIED",
        }
    )
    result = validate_fiction_research_item(
        item, evidence_catalog={"ev-1": evidence}, now_epoch=NOW
    )

    assert "RESEARCH.DISPOSITION.QUALIFIED_PLOT_CRITICAL" in _codes(result)
    assert not result.passed


def test_jurisdiction_and_time_scope_fail_closed_when_context_is_missing() -> None:
    item = FictionResearchItem(
        **{
            **_good_r3_item().__dict__,
            "jurisdiction": None,
            "time_period": None,
        }
    )
    result = validate_fiction_research_item(
        item, evidence_catalog={"ev-1": _primary_strong()}, now_epoch=NOW
    )

    codes = _codes(result)
    assert "RESEARCH.CONTEXT.JURISDICTION_MISSING" in codes
    assert "RESEARCH.CONTEXT.TIME_PERIOD_MISSING" in codes


def test_fictionalization_requires_prior_decision_baseline_and_rationale() -> None:
    item = FictionResearchItem(
        research_id="fictional-procedure",
        question="What real procedure are we changing?",
        risk_class="R2",
        domain="police-procedure",
        disposition="FICTIONALIZED",
        confidence="HIGH",
        source_refs=("src-1",),
        evidence_refs=("ev-1",),
        intentional_fictionalization=False,
    )
    result = validate_fiction_research_item(
        item, evidence_catalog={"ev-1": _primary_strong()}, now_epoch=NOW
    )

    codes = _codes(result)
    assert "RESEARCH.FICTIONALIZATION.FLAG_MISSING" in codes
    assert "RESEARCH.FICTIONALIZATION.RATIONALE_MISSING" in codes
    assert "RESEARCH.FICTIONALIZATION.DECISION_MISSING" in codes
    assert "RESEARCH.FICTIONALIZATION.BASELINE_MISSING" in codes

    accepted = FictionResearchItem(
        **{
            **item.__dict__,
            "intentional_fictionalization": True,
            "real_world_baseline": "documented real baseline",
            "fictionalization_rationale": "fictional analogue avoids false real-agency claim",
            "fictionalization_decision_ref": "decision-1",
        }
    )
    accepted_result = validate_fiction_research_item(
        accepted, evidence_catalog={"ev-1": _primary_strong()}, now_epoch=NOW
    )
    assert accepted_result.passed


def test_r4_requires_completed_expert_and_explicit_risk_review() -> None:
    base = FictionResearchItem(
        **{
            **_good_r3_item(research_id="sensitive").__dict__,
            "risk_class": "R4",
        }
    )
    blocked = validate_fiction_research_item(
        base, evidence_catalog={"ev-1": _primary_strong()}, now_epoch=NOW
    )
    codes = _codes(blocked)
    assert "RESEARCH.R4.RISK_REVIEW_MISSING" in codes
    assert "RESEARCH.R4.EXPERT_REVIEW_INCOMPLETE" in codes

    allowed = FictionResearchItem(
        **{
            **base.__dict__,
            "expert_review": "COMPLETED",
            "risk_review_ref": "risk-review-1",
        }
    )
    allowed_result = validate_fiction_research_item(
        allowed, evidence_catalog={"ev-1": _primary_strong()}, now_epoch=NOW
    )
    assert allowed_result.passed


def test_freshness_expiry_invalidates_research_and_all_effective_dependents() -> None:
    graph = MysteryAuthorityGraph()
    evidence = {"ev-1": _primary_strong()}
    item = _good_r3_item(
        freshness_mode="VALID_UNTIL",
        fresh_until_epoch=NOW + 100,
    )
    research_revision = _approve_research_in_graph(
        graph,
        create_fiction_research_revision(item),
        item,
        evidence_catalog=evidence,
        now_epoch=NOW,
    )

    case = create_authority_revision(
        entity_id="case",
        kind="CASE_SOLUTION",
        payload={"culprit": "A"},
    )
    graph.register_head(case)
    bind_research_dependency(
        graph,
        dependent_entity_id="case",
        research_id=item.research_id,
        reason="case mechanism depends on dispatch rule",
    )
    _approve_generic_in_graph(graph, case)

    assert graph.effective(research_revision.entity_id) == research_revision
    before = evaluate_research_ledger(
        graph,
        items_by_revision_id={research_revision.revision_id: item},
        evidence_catalog=evidence,
        now_epoch=NOW,
    )
    assert before.passed

    after = evaluate_research_ledger(
        graph,
        items_by_revision_id={research_revision.revision_id: item},
        evidence_catalog=evidence,
        now_epoch=NOW + 101,
    )
    assert research_revision.entity_id in after.invalid_research_entity_ids
    assert "case" in after.affected_authority_entity_ids
    assert "RESEARCH.FRESHNESS.EXPIRED" in _codes(after)


def test_superseded_shared_evidence_invalidates_dependents_without_changing_story_text() -> None:
    graph = MysteryAuthorityGraph()
    item = _good_r3_item()
    active_catalog = {"ev-1": _primary_strong(active=True)}
    research_revision = _approve_research_in_graph(
        graph,
        create_fiction_research_revision(item),
        item,
        evidence_catalog=active_catalog,
    )

    case = create_authority_revision(
        entity_id="case",
        kind="CASE_SOLUTION",
        payload={"mechanism": "depends-on-research"},
    )
    graph.register_head(case)
    bind_research_dependency(
        graph,
        dependent_entity_id="case",
        research_id=item.research_id,
        reason="plot-critical realism dependency",
    )
    _approve_generic_in_graph(graph, case)

    inactive_catalog = {"ev-1": _primary_strong(active=False)}
    result = evaluate_research_ledger(
        graph,
        items_by_revision_id={research_revision.revision_id: item},
        evidence_catalog=inactive_catalog,
        now_epoch=NOW,
    )

    assert "RESEARCH.EVIDENCE.INACTIVE" in _codes(result)
    assert research_revision.entity_id in result.invalid_research_entity_ids
    assert "case" in result.affected_authority_entity_ids


def test_new_accepted_research_revision_triggers_structural_authority_staleness() -> None:
    graph = MysteryAuthorityGraph()
    evidence = {"ev-1": _primary_strong()}
    item_v1 = _good_r3_item(assumed_answer="answer v1")
    revision_v1 = _approve_research_in_graph(
        graph,
        create_fiction_research_revision(item_v1),
        item_v1,
        evidence_catalog=evidence,
    )

    case = create_authority_revision(
        entity_id="case",
        kind="CASE_SOLUTION",
        payload={"mechanism": "v1"},
    )
    graph.register_head(case)
    bind_research_dependency(
        graph,
        dependent_entity_id="case",
        research_id=item_v1.research_id,
        reason="case consumes exact research conclusion",
    )
    _approve_generic_in_graph(graph, case)
    assert "case" not in graph.stale_entities()

    item_v2 = _good_r3_item(assumed_answer="answer v2")
    revision_v2 = revise_fiction_research_revision(revision_v1, item_v2)
    _approve_research_in_graph(
        graph,
        revision_v2,
        item_v2,
        evidence_catalog=evidence,
    )

    assert graph.effective(research_entity_id(item_v1.research_id)) is not None
    assert "case" in graph.stale_entities()


def test_research_approval_is_fail_closed_and_bound_to_exact_item_hash() -> None:
    graph = MysteryAuthorityGraph()
    invalid_item = FictionResearchItem(
        research_id="critical",
        question="critical unresolved question",
        risk_class="R3",
        domain="forensics",
        disposition="VERIFIED",
        confidence="HIGH",
        assumed_answer="unsupported answer",
    )
    revision = create_fiction_research_revision(invalid_item)
    graph.register_head(revision)
    revision = transition_fiction_research_status(
        revision,
        invalid_item,
        target_status="PROPOSED",
        actor_kind="AI",
        now_epoch=NOW,
    )
    graph.register_head(revision)
    revision = transition_fiction_research_status(
        revision,
        invalid_item,
        target_status="REVIEWED",
        actor_kind="AI",
        now_epoch=NOW,
    )
    graph.register_head(revision)

    with pytest.raises(InvalidAuthorityOperation, match="research authority cannot become APPROVED"):
        transition_fiction_research_status(
            revision,
            invalid_item,
            target_status="APPROVED",
            actor_kind="HUMAN",
            now_epoch=NOW,
        )

    different_item = FictionResearchItem(
        **{
            **invalid_item.__dict__,
            "assumed_answer": "silently swapped answer",
        }
    )
    with pytest.raises(InvalidAuthorityOperation, match="exact authority revision hash"):
        transition_fiction_research_status(
            revision,
            different_item,
            target_status="APPROVED",
            actor_kind="HUMAN",
            now_epoch=NOW,
        )


def test_working_research_draft_does_not_replace_effective_ledger_projection() -> None:
    graph = MysteryAuthorityGraph()
    evidence = {"ev-1": _primary_strong()}
    item_v1 = _good_r3_item(assumed_answer="accepted v1")
    revision_v1 = _approve_research_in_graph(
        graph,
        create_fiction_research_revision(item_v1),
        item_v1,
        evidence_catalog=evidence,
    )

    item_v2 = _good_r3_item(assumed_answer="working draft v2")
    draft_v2 = revise_fiction_research_revision(revision_v1, item_v2)
    graph.register_head(draft_v2)

    result = evaluate_research_ledger(
        graph,
        items_by_revision_id={revision_v1.revision_id: item_v1},
        evidence_catalog=evidence,
        now_epoch=NOW,
    )

    assert result.passed
    assert graph.effective(revision_v1.entity_id) == revision_v1
    assert graph.latest(revision_v1.entity_id) == draft_v2


def test_evidence_catalog_key_must_match_snapshot_identity() -> None:
    item = _good_r3_item()
    mismatched = _primary_strong(evidence_ref="ev-other")
    result = validate_fiction_research_item(
        item,
        evidence_catalog={"ev-1": mismatched},
        now_epoch=NOW,
    )

    assert "RESEARCH.EVIDENCE.CATALOG_ID_MISMATCH" in _codes(result)
    assert not result.passed
