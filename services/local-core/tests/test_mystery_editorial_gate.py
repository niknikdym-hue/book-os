from __future__ import annotations

from dataclasses import replace

from book_os_core.mystery_anti_cliche_validation import AntiClicheResult
from book_os_core.mystery_authority import (
    MysteryAuthorityGraph,
    MysteryAuthorityRevision,
    create_authority_revision,
    revise_authority,
    transition_authority_status,
)
from book_os_core.mystery_case_validation import (
    CaseIntegrityResult,
    ValidationFinding as CaseFinding,
)
from book_os_core.mystery_editorial_gate import (
    ExternalWritingReadiness,
    SceneContract,
    readiness_with_anti_cliche,
    WritingGatePolicy,
    create_scene_contract_revision,
    evaluate_scene_writing_gate,
    readiness_with_series_uniqueness,
    scene_contract_entity_id,
    transition_scene_contract_status,
    verify_writing_admission_token,
)
from book_os_core.mystery_narrative_validation import (
    NarrativeFinding,
    NarrativeValidationResult,
    ReaderKnowledgeCheckpoint,
)
from book_os_core.mystery_research_validation import (
    ResearchLedgerResult,
    research_entity_id,
)
from book_os_core.mystery_series_validation import SeriesUniquenessResult

NOW = 1_800_000_000


def _approve_in_graph(
    graph: MysteryAuthorityGraph, revision: MysteryAuthorityRevision
) -> MysteryAuthorityRevision:
    graph.register_head(revision)
    revision = transition_authority_status(revision, target_status="PROPOSED", actor_kind="AI")
    graph.register_head(revision)
    revision = transition_authority_status(revision, target_status="REVIEWED", actor_kind="AI")
    graph.register_head(revision)
    revision = transition_authority_status(revision, target_status="APPROVED", actor_kind="HUMAN")
    graph.register_head(revision)
    return revision


def _review_scene_in_graph(
    graph: MysteryAuthorityGraph, revision: MysteryAuthorityRevision
) -> MysteryAuthorityRevision:
    graph.register_head(revision)
    revision = transition_scene_contract_status(revision, target_status="PROPOSED", actor_kind="AI")
    graph.register_head(revision)
    revision = transition_scene_contract_status(revision, target_status="REVIEWED", actor_kind="AI")
    graph.register_head(revision)
    return revision


def _clean_case() -> CaseIntegrityResult:
    return CaseIntegrityResult(findings=())


def _clean_narrative() -> NarrativeValidationResult:
    return NarrativeValidationResult(
        findings=(),
        reader_checkpoints=(
            ReaderKnowledgeCheckpoint(
                scene_id="scene-01",
                reader_order=10,
                known_fact_ids=frozenset(),
            ),
        ),
    )


def _clean_research() -> ResearchLedgerResult:
    return ResearchLedgerResult(
        findings=(),
        invalid_research_entity_ids=frozenset(),
        affected_authority_entity_ids=frozenset(),
    )


def _clean_readiness(**kwargs: object) -> ExternalWritingReadiness:
    values: dict[str, object] = {
        "anti_cliche_qualified": True,
        "anti_cliche_evaluation_ref": "anti-cliche-eval:v1",
    }
    values.update(kwargs)
    return ExternalWritingReadiness(**values)  # type: ignore[arg-type]


def _scene_contract(
    *,
    required_research_ids: tuple[str, ...] = (),
    required_authority_entity_ids: tuple[str, ...] = (),
    state_change_codes: tuple[str, ...] = ("CLUE_MODEL_CHANGED",),
) -> SceneContract:
    return SceneContract(
        scene_id="scene-01",
        viewpoint_character_id="lead",
        time_ref="timeline:event-10",
        location_ref="location:dispatch-room",
        purpose="test the current suspect hypothesis under pressure",
        entering_state_ref="state:before",
        exiting_state_ref="state:after",
        knowledge_state_ref="knowledge:lead@scene-01",
        state_change_codes=state_change_codes,
        mystery_question_refs=("question:who-called",),
        clue_operation_refs=("clue:c1:observe",),
        tension_source="a deadline closes access to the witness",
        required_authority_entity_ids=required_authority_entity_ids,
        required_research_ids=required_research_ids,
    )


def _setup(
    *,
    production_mode: str = "REPRESENTATIVE_SAMPLE",
    required_research_ids: tuple[str, ...] = (),
    omit_dependency_ids: frozenset[str] = frozenset(),
) -> tuple[
    MysteryAuthorityGraph,
    WritingGatePolicy,
    SceneContract,
    MysteryAuthorityRevision,
    MysteryAuthorityRevision,
]:
    graph = MysteryAuthorityGraph()
    story = _approve_in_graph(
        graph,
        create_authority_revision(
            entity_id="story",
            kind="STORY_DEFINITION",
            payload={"marker": "story-v1"},
        ),
    )
    narrative = _approve_in_graph(
        graph,
        create_authority_revision(
            entity_id="narrative",
            kind="NARRATIVE_CONTRACT",
            payload={"marker": "narrative-v1"},
        ),
    )
    case = _approve_in_graph(
        graph,
        create_authority_revision(
            entity_id="case",
            kind="CASE_SOLUTION",
            payload={"marker": "case-v1"},
        ),
    )

    research_entities: list[str] = []
    for research_id in required_research_ids:
        entity_id = research_entity_id(research_id)
        _approve_in_graph(
            graph,
            create_authority_revision(
                entity_id=entity_id,
                kind="FICTION_RESEARCH_ITEM",
                payload={"research_id": research_id, "marker": "effective"},
            ),
        )
        research_entities.append(entity_id)

    contract = _scene_contract(required_research_ids=required_research_ids)
    scene_revision = create_scene_contract_revision(
        book_id="book-1",
        contract=contract,
    )
    graph.register_head(scene_revision)

    dependency_ids = ("story", "narrative", "case", *research_entities)
    for entity_id in dependency_ids:
        if entity_id in omit_dependency_ids:
            continue
        graph.bind_dependency(
            dependent_entity_id=scene_revision.entity_id,
            upstream_entity_id=entity_id,
            reason=f"scene consumes {entity_id}",
        )
    scene_revision = transition_scene_contract_status(
        scene_revision, target_status="PROPOSED", actor_kind="AI"
    )
    graph.register_head(scene_revision)
    scene_revision = transition_scene_contract_status(
        scene_revision, target_status="REVIEWED", actor_kind="AI"
    )
    graph.register_head(scene_revision)

    policy = WritingGatePolicy(
        book_id="book-1",
        story_definition_entity_id=story.entity_id,
        narrative_contract_entity_id=narrative.entity_id,
        case_solution_entity_id=case.entity_id,
        production_mode=production_mode,  # type: ignore[arg-type]
    )
    return graph, policy, contract, scene_revision, case


def _evaluate(
    graph: MysteryAuthorityGraph,
    policy: WritingGatePolicy,
    contract: SceneContract,
    scene_revision: MysteryAuthorityRevision,
    *,
    case_integrity: CaseIntegrityResult | None = None,
    narrative: NarrativeValidationResult | None = None,
    research: ResearchLedgerResult | None = None,
    readiness: ExternalWritingReadiness | None = None,
    now_epoch: int = NOW,
):
    return evaluate_scene_writing_gate(
        graph=graph,
        policy=policy,
        contract=contract,
        scene_revision=scene_revision,
        case_integrity=case_integrity or _clean_case(),
        narrative_validation=narrative or _clean_narrative(),
        research_ledger=research or _clean_research(),
        readiness=readiness or _clean_readiness(),
        now_epoch=now_epoch,
    )


def _blockers(result) -> set[str]:  # type: ignore[no-untyped-def]
    return {blocker for gate in result.state.gates for blocker in gate.blocking_findings}


def test_reviewed_scene_can_receive_representative_sample_admission_without_human_scene_approval() -> (
    None
):
    graph, policy, contract, scene_revision, _ = _setup()

    result = _evaluate(graph, policy, contract, scene_revision)

    assert result.state.writing_allowed
    assert result.state.writing_allowed_scope == ("scene-01",)
    assert result.token is not None
    assert result.token.scene_revision_ref == scene_revision.revision_ref
    assert result.token.production_mode == "REPRESENTATIVE_SAMPLE"


def test_scene_requires_state_change_and_core_contract_fields() -> None:
    graph, policy, contract, scene_revision, _ = _setup()
    invalid_contract = replace(
        contract,
        purpose="",
        knowledge_state_ref="",
        state_change_codes=(),
    )

    result = _evaluate(graph, policy, invalid_contract, scene_revision)

    blockers = _blockers(result)
    assert "SCENE_CONTRACT.PURPOSE_MISSING" in blockers
    assert "SCENE_CONTRACT.KNOWLEDGE_STATE_MISSING" in blockers
    assert "SCENE_CONTRACT.STATE_CHANGE_MISSING" in blockers
    assert "SCENE_REVISION.HASH_MISMATCH" in blockers
    assert not result.state.writing_allowed


def test_scene_revision_must_be_reviewed_or_accepted() -> None:
    graph = MysteryAuthorityGraph()
    story = _approve_in_graph(
        graph,
        create_authority_revision(entity_id="story", kind="STORY_DEFINITION", payload={"v": 1}),
    )
    narrative = _approve_in_graph(
        graph,
        create_authority_revision(
            entity_id="narrative", kind="NARRATIVE_CONTRACT", payload={"v": 1}
        ),
    )
    case = _approve_in_graph(
        graph,
        create_authority_revision(entity_id="case", kind="CASE_SOLUTION", payload={"v": 1}),
    )
    contract = _scene_contract()
    revision = create_scene_contract_revision(book_id="book-1", contract=contract)
    graph.register_head(revision)
    for upstream in (story, narrative, case):
        graph.bind_dependency(
            dependent_entity_id=revision.entity_id,
            upstream_entity_id=upstream.entity_id,
            reason="required",
        )
    policy = WritingGatePolicy(
        book_id="book-1",
        story_definition_entity_id="story",
        narrative_contract_entity_id="narrative",
        case_solution_entity_id="case",
        production_mode="REPRESENTATIVE_SAMPLE",
    )

    result = _evaluate(graph, policy, contract, revision)

    assert "SCENE_REVISION.STATUS_NOT_ADMISSIBLE:DRAFT" in _blockers(result)
    assert not result.state.writing_allowed


def test_missing_exact_scene_dependency_blocks_before_writer_access() -> None:
    graph, policy, contract, scene_revision, _ = _setup(
        omit_dependency_ids=frozenset({"narrative"})
    )

    result = _evaluate(graph, policy, contract, scene_revision)

    assert "SCENE_DEPENDENCY.MISSING:narrative" in _blockers(result)
    assert not result.state.writing_allowed


def test_unaccepted_upstream_draft_does_not_invalidate_existing_token_but_accepted_change_does() -> (
    None
):
    graph, policy, contract, scene_revision, case_v1 = _setup()
    initial = _evaluate(graph, policy, contract, scene_revision)
    assert initial.token is not None

    case_v2 = revise_authority(case_v1, {"marker": "case-v2"})
    graph.register_head(case_v2)

    while_draft = verify_writing_admission_token(
        initial.token,
        graph=graph,
        policy=policy,
        contract=contract,
        scene_revision=scene_revision,
        case_integrity=_clean_case(),
        narrative_validation=_clean_narrative(),
        research_ledger=_clean_research(),
        readiness=_clean_readiness(),
        now_epoch=NOW,
    )
    assert while_draft.valid

    case_v2 = transition_authority_status(case_v2, target_status="PROPOSED", actor_kind="AI")
    graph.register_head(case_v2)
    case_v2 = transition_authority_status(case_v2, target_status="REVIEWED", actor_kind="AI")
    graph.register_head(case_v2)
    case_v2 = transition_authority_status(case_v2, target_status="APPROVED", actor_kind="HUMAN")
    graph.register_head(case_v2)

    after_acceptance = verify_writing_admission_token(
        initial.token,
        graph=graph,
        policy=policy,
        contract=contract,
        scene_revision=scene_revision,
        case_integrity=_clean_case(),
        narrative_validation=_clean_narrative(),
        research_ledger=_clean_research(),
        readiness=_clean_readiness(),
        now_epoch=NOW,
    )
    assert not after_acceptance.valid
    assert after_acceptance.reason == "CURRENT_GATE_BLOCKED"
    assert "SCENE_DEPENDENCY.STALE:case" in _blockers(after_acceptance.current_result)


def test_case_or_narrative_blocker_prevents_admission() -> None:
    graph, policy, contract, scene_revision, _ = _setup()
    bad_case = CaseIntegrityResult(
        findings=(
            CaseFinding(
                code="CASE.TRAVEL.IMPOSSIBLE",
                severity="BLOCKING",
                message="impossible travel",
            ),
        )
    )
    bad_narrative = NarrativeValidationResult(
        findings=(
            NarrativeFinding(
                code="NARRATIVE.WITHHOLDING.CONSCIOUS_DECISIVE_FACT",
                severity="BLOCKING",
                message="unfair withholding",
            ),
        ),
        reader_checkpoints=(),
    )

    case_result = _evaluate(
        graph,
        policy,
        contract,
        scene_revision,
        case_integrity=bad_case,
    )
    narrative_result = _evaluate(
        graph,
        policy,
        contract,
        scene_revision,
        narrative=bad_narrative,
    )

    assert "CASE:CASE.TRAVEL.IMPOSSIBLE" in _blockers(case_result)
    assert "NARRATIVE:NARRATIVE.WITHHOLDING.CONSCIOUS_DECISIVE_FACT" in _blockers(narrative_result)


def test_required_invalid_research_and_research_affected_case_block_scene() -> None:
    graph, policy, contract, scene_revision, _ = _setup(required_research_ids=("dispatch-rule",))
    research_entity = research_entity_id("dispatch-rule")
    invalid_required = ResearchLedgerResult(
        findings=(),
        invalid_research_entity_ids=frozenset({research_entity}),
        affected_authority_entity_ids=frozenset(),
    )
    invalid_result = _evaluate(
        graph,
        policy,
        contract,
        scene_revision,
        research=invalid_required,
    )
    assert f"RESEARCH.INVALID:{research_entity}" in _blockers(invalid_result)

    affected_case = ResearchLedgerResult(
        findings=(),
        invalid_research_entity_ids=frozenset(),
        affected_authority_entity_ids=frozenset({"case"}),
    )
    affected_result = _evaluate(
        graph,
        policy,
        contract,
        scene_revision,
        research=affected_case,
    )
    assert "RESEARCH.AFFECTS_AUTHORITY:case" in _blockers(affected_result)


def test_anti_cliche_evaluation_is_mandatory_and_unresolved_blocked_device_blocks() -> None:
    graph, policy, contract, scene_revision, _ = _setup()

    missing_eval = _evaluate(
        graph,
        policy,
        contract,
        scene_revision,
        readiness=ExternalWritingReadiness(),
    )
    assert "ANTI_CLICHE.EVALUATION_REF_MISSING" in _blockers(missing_eval)

    unresolved = _evaluate(
        graph,
        policy,
        contract,
        scene_revision,
        readiness=_clean_readiness(unresolved_blocked_cliche_codes=("CHEAP_TWIST.UNKNOWN_TWIN",)),
    )
    assert "ANTI_CLICHE.UNRESOLVED:CHEAP_TWIST.UNKNOWN_TWIN" in _blockers(unresolved)


def test_mass_draft_requires_representative_sample_and_writer_qualification() -> None:
    graph, policy, contract, scene_revision, _ = _setup(production_mode="MASS_DRAFT")

    blocked = _evaluate(graph, policy, contract, scene_revision)
    blockers = _blockers(blocked)
    assert "REPRESENTATIVE_SAMPLE.NOT_QUALIFIED" in blockers
    assert "REPRESENTATIVE_SAMPLE.REF_MISSING" in blockers
    assert "WRITER.NOT_QUALIFIED" in blockers
    assert "WRITER.QUALIFICATION_REF_MISSING" in blockers

    admitted = _evaluate(
        graph,
        policy,
        contract,
        scene_revision,
        readiness=_clean_readiness(
            representative_sample_qualified=True,
            representative_sample_ref="sample-eval:v1",
            writer_qualified=True,
            writer_qualification_ref="writer-qualification:v1",
        ),
    )
    assert admitted.state.writing_allowed
    assert admitted.token is not None


def test_provider_execution_requires_route_execution_and_cost_authorization() -> None:
    graph, policy, contract, scene_revision, _ = _setup()
    blocked = _evaluate(
        graph,
        policy,
        contract,
        scene_revision,
        readiness=_clean_readiness(provider_execution_requested=True),
    )
    blockers = _blockers(blocked)
    assert "EXECUTION.ROUTE_REF_MISSING" in blockers
    assert "EXECUTION.AUTHORIZATION_REF_MISSING" in blockers
    assert "EXECUTION.COST_AUTHORIZATION_REF_MISSING" in blockers

    admitted = _evaluate(
        graph,
        policy,
        contract,
        scene_revision,
        readiness=_clean_readiness(
            provider_execution_requested=True,
            execution_route_ref="route:writer-standard",
            execution_authorization_ref="execution-auth:1",
            cost_authorization_ref="cost-auth:1",
        ),
    )
    assert admitted.state.writing_allowed


def test_dependency_change_after_review_invalidates_old_token_even_if_new_dependency_is_valid() -> (
    None
):
    graph, policy, contract, scene_revision, _ = _setup()
    initial = _evaluate(graph, policy, contract, scene_revision)
    assert initial.token is not None

    extra = _approve_in_graph(
        graph,
        create_authority_revision(
            entity_id="character-bible",
            kind="CHARACTER_BIBLE",
            payload={"v": 1},
        ),
    )
    graph.bind_dependency(
        dependent_entity_id=scene_revision.entity_id,
        upstream_entity_id=extra.entity_id,
        reason="late-added but valid dependency",
    )

    verification = verify_writing_admission_token(
        initial.token,
        graph=graph,
        policy=policy,
        contract=contract,
        scene_revision=scene_revision,
        case_integrity=_clean_case(),
        narrative_validation=_clean_narrative(),
        research_ledger=_clean_research(),
        readiness=_clean_readiness(),
        now_epoch=NOW,
    )

    assert not verification.valid
    assert verification.reason == "ADMISSION_SNAPSHOT_CHANGED"
    assert verification.current_result.state.writing_allowed
    assert verification.current_result.token is not None
    assert (
        verification.current_result.token.dependency_fingerprint
        != initial.token.dependency_fingerprint
    )


def test_nonblocking_evaluation_change_invalidates_old_admission_snapshot() -> None:
    graph, policy, contract, scene_revision, _ = _setup()
    initial = _evaluate(graph, policy, contract, scene_revision)
    assert initial.token is not None

    changed_narrative = NarrativeValidationResult(
        findings=(
            NarrativeFinding(
                code="NARRATIVE.NOTE.READER_STATE_UPDATED",
                severity="NOTE",
                message="reader model changed without blocker",
                object_refs=("scene-01",),
            ),
        ),
        reader_checkpoints=(
            ReaderKnowledgeCheckpoint(
                scene_id="scene-01",
                reader_order=10,
                known_fact_ids=frozenset({"updated-reader-state"}),
            ),
        ),
    )
    verification = verify_writing_admission_token(
        initial.token,
        graph=graph,
        policy=policy,
        contract=contract,
        scene_revision=scene_revision,
        case_integrity=_clean_case(),
        narrative_validation=changed_narrative,
        research_ledger=_clean_research(),
        readiness=_clean_readiness(),
        now_epoch=NOW,
    )

    assert not verification.valid
    assert verification.reason == "ADMISSION_SNAPSHOT_CHANGED"
    assert verification.current_result.state.writing_allowed


def test_scene_entity_identity_is_bound_to_book_and_scene() -> None:
    graph, policy, contract, scene_revision, _ = _setup()
    assert scene_revision.entity_id == scene_contract_entity_id("book-1", "scene-01")

    other_contract = replace(contract, scene_id="scene-02")
    result = _evaluate(graph, policy, other_contract, scene_revision)

    blockers = _blockers(result)
    assert "SCENE_REVISION.WRONG_ENTITY" in blockers
    assert "SCENE_REVISION.HASH_MISMATCH" in blockers


def test_invalid_research_bound_as_extra_scene_dependency_blocks_even_if_not_declared_required() -> (
    None
):
    graph, policy, contract, scene_revision, _ = _setup()
    research_entity = research_entity_id("late-realism")
    _approve_in_graph(
        graph,
        create_authority_revision(
            entity_id=research_entity,
            kind="FICTION_RESEARCH_ITEM",
            payload={"research_id": "late-realism", "marker": "effective"},
        ),
    )
    graph.bind_dependency(
        dependent_entity_id=scene_revision.entity_id,
        upstream_entity_id=research_entity,
        reason="scene acquired an additional factual dependency",
    )
    research = ResearchLedgerResult(
        findings=(),
        invalid_research_entity_ids=frozenset({research_entity}),
        affected_authority_entity_ids=frozenset(),
    )

    result = _evaluate(
        graph,
        policy,
        contract,
        scene_revision,
        research=research,
    )

    assert f"RESEARCH.INVALID:{research_entity}" in _blockers(result)
    assert not result.state.writing_allowed


def test_narrative_evaluation_must_cover_the_exact_scene_scope() -> None:
    graph, policy, contract, scene_revision, _ = _setup()
    wrong_scope = NarrativeValidationResult(
        findings=(),
        reader_checkpoints=(
            ReaderKnowledgeCheckpoint(
                scene_id="scene-02",
                reader_order=10,
                known_fact_ids=frozenset(),
            ),
        ),
    )

    result = _evaluate(
        graph,
        policy,
        contract,
        scene_revision,
        narrative=wrong_scope,
    )

    assert "NARRATIVE.SCENE_NOT_EVALUATED:scene-01" in _blockers(result)
    assert not result.state.writing_allowed


def test_relevant_research_snapshot_change_invalidates_existing_token() -> None:
    graph, policy, contract, scene_revision, _ = _setup(required_research_ids=("dispatch-rule",))
    entity_id = research_entity_id("dispatch-rule")
    research_v1 = ResearchLedgerResult(
        findings=(),
        invalid_research_entity_ids=frozenset(),
        affected_authority_entity_ids=frozenset(),
        evaluation_snapshot_refs_by_entity=((entity_id, "research-snapshot:v1"),),
    )
    initial = _evaluate(
        graph,
        policy,
        contract,
        scene_revision,
        research=research_v1,
    )
    assert initial.state.writing_allowed
    assert initial.token is not None

    research_v2 = ResearchLedgerResult(
        findings=(),
        invalid_research_entity_ids=frozenset(),
        affected_authority_entity_ids=frozenset(),
        evaluation_snapshot_refs_by_entity=((entity_id, "research-snapshot:v2"),),
    )
    verification = verify_writing_admission_token(
        initial.token,
        graph=graph,
        policy=policy,
        contract=contract,
        scene_revision=scene_revision,
        case_integrity=_clean_case(),
        narrative_validation=_clean_narrative(),
        research_ledger=research_v2,
        readiness=_clean_readiness(),
        now_epoch=NOW,
    )

    assert not verification.valid
    assert verification.reason == "ADMISSION_SNAPSHOT_CHANGED"
    assert verification.current_result.state.writing_allowed


def test_research_recheck_deadline_bounds_admission_even_with_cached_green_ledger() -> None:
    graph, policy, contract, scene_revision, _ = _setup(required_research_ids=("dispatch-rule",))
    entity_id = research_entity_id("dispatch-rule")
    cached_green = ResearchLedgerResult(
        findings=(),
        invalid_research_entity_ids=frozenset(),
        affected_authority_entity_ids=frozenset(),
        research_recheck_epochs=((entity_id, NOW + 10),),
        next_recheck_epoch=NOW + 10,
        evaluation_snapshot_refs_by_entity=((entity_id, "research-snapshot:v1"),),
    )

    initial = _evaluate(
        graph,
        policy,
        contract,
        scene_revision,
        research=cached_green,
        now_epoch=NOW,
    )
    assert initial.state.writing_allowed
    assert initial.token is not None
    assert initial.token.not_after_epoch == NOW + 10

    verification = verify_writing_admission_token(
        initial.token,
        graph=graph,
        policy=policy,
        contract=contract,
        scene_revision=scene_revision,
        case_integrity=_clean_case(),
        narrative_validation=_clean_narrative(),
        research_ledger=cached_green,
        readiness=_clean_readiness(),
        now_epoch=NOW + 10,
    )

    assert not verification.valid
    assert verification.reason == "CURRENT_GATE_BLOCKED"
    assert f"RESEARCH.RECHECK_DUE:{entity_id}:{NOW + 10}" in _blockers(verification.current_result)
    research_gate = next(
        gate
        for gate in verification.current_result.state.gates
        if gate.gate_id == "REALISM_RESEARCH"
    )
    assert research_gate.status == "STALE"


def test_series_book_cannot_receive_writing_admission_without_current_series_brain() -> None:
    graph, policy, contract, scene_revision, _ = _setup()
    series_policy = replace(policy, series_book=True)

    blocked = _evaluate(
        graph,
        series_policy,
        contract,
        scene_revision,
    )

    blockers = _blockers(blocked)
    assert "SERIES_UNIQUENESS.NOT_QUALIFIED" in blockers
    assert "SERIES_UNIQUENESS.REF_MISSING" in blockers
    assert not blocked.state.writing_allowed


def test_series_uniqueness_result_populates_writing_readiness_and_token() -> None:
    graph, policy, contract, scene_revision, _ = _setup()
    series_policy = replace(policy, series_book=True)
    uniqueness = SeriesUniquenessResult(
        qualified=True,
        series_brain_ref="series-brain:qualified-v1",
        current_passport_ref="mystery-book-passport:book-1:v1",
        findings=(),
    )
    readiness = readiness_with_series_uniqueness(
        _clean_readiness(),
        uniqueness,
    )

    result = _evaluate(
        graph,
        series_policy,
        contract,
        scene_revision,
        readiness=readiness,
    )

    assert result.state.writing_allowed
    assert result.token is not None
    assert "series-brain:qualified-v1" in result.token.evaluation_refs


def test_failed_series_uniqueness_never_sets_manual_series_ready_flag() -> None:
    readiness = readiness_with_series_uniqueness(
        _clean_readiness(
            series_uniqueness_qualified=True,
            series_brain_ref="series-brain:stale-manual-value",
        ),
        SeriesUniquenessResult(
            qualified=False,
            series_brain_ref="series-brain:blocked",
            current_passport_ref="passport:blocked",
            findings=(),
        ),
    )

    assert not readiness.series_uniqueness_qualified
    assert readiness.series_brain_ref is None


def test_manual_anti_cliche_ref_without_qualified_result_does_not_unlock_writing() -> None:
    graph, policy, contract, scene_revision, _ = _setup()
    readiness = _clean_readiness(
        anti_cliche_qualified=False,
        anti_cliche_evaluation_ref="anti-cliche:invented-ref",
    )

    result = _evaluate(
        graph,
        policy,
        contract,
        scene_revision,
        readiness=readiness,
    )

    assert "ANTI_CLICHE.NOT_QUALIFIED" in _blockers(result)
    assert not result.state.writing_allowed


def test_anti_cliche_bridge_binds_exact_qualified_result_into_token() -> None:
    graph, policy, contract, scene_revision, _ = _setup()
    result = AntiClicheResult(
        qualified=True,
        anti_cliche_ref="anti-cliche:qualified-v1",
        rule_pack_ref="anti-cliche-rule-pack:default:v1",
        unresolved_blocking_codes=(),
        findings=(),
    )
    readiness = readiness_with_anti_cliche(
        ExternalWritingReadiness(),
        result,
    )

    admitted = _evaluate(
        graph,
        policy,
        contract,
        scene_revision,
        readiness=readiness,
    )

    assert admitted.state.writing_allowed
    assert admitted.token is not None
    assert "anti-cliche:qualified-v1" in admitted.token.evaluation_refs


def test_failed_anti_cliche_result_clears_stale_manual_readiness() -> None:
    readiness = readiness_with_anti_cliche(
        _clean_readiness(
            anti_cliche_qualified=True,
            anti_cliche_evaluation_ref="anti-cliche:stale-green",
        ),
        AntiClicheResult(
            qualified=False,
            anti_cliche_ref="anti-cliche:blocked",
            rule_pack_ref="anti-cliche-rule-pack:default:v1",
            unresolved_blocking_codes=("ANTI_CLICHE.BLOCKED_RULE.EXCEPTION_MISSING",),
            findings=(),
        ),
    )

    assert not readiness.anti_cliche_qualified
    assert readiness.anti_cliche_evaluation_ref is None
    assert readiness.unresolved_blocked_cliche_codes
