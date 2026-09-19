from __future__ import annotations

from book_os_core.model_gateway import (
    AuthorityInputRef,
    DeterministicFakeAdapter,
    ModelGateway,
)
from book_os_core.model_routing import RoutingChoice
from book_os_core.mystery_anti_cliche_validation import AntiClicheResult
from book_os_core.mystery_authority import (
    MysteryAuthorityGraph,
    MysteryAuthorityRevision,
    create_authority_revision,
    transition_authority_status,
)
from book_os_core.mystery_case_validation import CaseIntegrityResult
from book_os_core.mystery_editorial_gate import (
    ExternalWritingReadiness,
    SceneContract,
    WritingGatePolicy,
    create_scene_contract_revision,
    evaluate_scene_writing_gate,
    readiness_with_anti_cliche,
    readiness_with_production_route,
    readiness_with_sample_qualification,
    readiness_with_series_uniqueness,
    transition_scene_contract_status,
)
from book_os_core.mystery_narrative_validation import (
    NarrativeValidationResult,
    ReaderKnowledgeCheckpoint,
)
from book_os_core.mystery_fiction_gateway import (
    FictionGatewayExecutionRequest,
    execute_fiction_gateway_task,
)
from book_os_core.mystery_production_routing import (
    ProductionRouteRequest,
    ProductionRoutingPolicy,
    VerifiedCostAuthorization,
    VerifiedOwnerExecutionAuthorization,
    evaluate_production_route,
)
from book_os_core.mystery_research_validation import ResearchLedgerResult
from book_os_core.mystery_sample_qualification import SampleQualificationResult
from book_os_core.mystery_series_validation import SeriesUniquenessResult

NOW = 1_800_000_000
OWNER_REF = "owner-auth:synthetic-writing:v1"
COST_REF = "cost-auth:synthetic-writing:v1"


def _approve(
    graph: MysteryAuthorityGraph,
    revision: MysteryAuthorityRevision,
) -> MysteryAuthorityRevision:
    graph.register_head(revision)
    revision = transition_authority_status(
        revision,
        target_status="PROPOSED",
        actor_kind="AI",
    )
    graph.register_head(revision)
    revision = transition_authority_status(
        revision,
        target_status="REVIEWED",
        actor_kind="AI",
    )
    graph.register_head(revision)
    revision = transition_authority_status(
        revision,
        target_status="APPROVED",
        actor_kind="HUMAN",
    )
    graph.register_head(revision)
    return revision


def _build_authority() -> tuple[
    MysteryAuthorityGraph,
    SceneContract,
    MysteryAuthorityRevision,
    tuple[str, ...],
    tuple[AuthorityInputRef, ...],
]:
    graph = MysteryAuthorityGraph()
    story = _approve(
        graph,
        create_authority_revision(
            entity_id="story",
            kind="STORY_DEFINITION",
            payload={"premise": "synthetic mystery premise"},
        ),
    )
    narrative = _approve(
        graph,
        create_authority_revision(
            entity_id="narrative",
            kind="NARRATIVE_CONTRACT",
            payload={"pov": "lead-limited"},
        ),
    )
    case = _approve(
        graph,
        create_authority_revision(
            entity_id="case",
            kind="CASE_SOLUTION",
            payload={"solution": "accepted synthetic case truth"},
        ),
    )
    contract = SceneContract(
        scene_id="scene-01",
        viewpoint_character_id="lead",
        time_ref="case-time:1",
        location_ref="location:dispatch",
        purpose="stress the first case hypothesis",
        entering_state_ref="state:before",
        exiting_state_ref="state:after",
        knowledge_state_ref="knowledge:lead:scene-01",
        state_change_codes=("HYPOTHESIS_CHANGED",),
        mystery_question_refs=("question:primary",),
        clue_operation_refs=("clue:one:observe",),
        tension_source="access to the witness will close",
    )
    scene = create_scene_contract_revision(
        book_id="book-1",
        contract=contract,
    )
    graph.register_head(scene)
    for upstream in (story, narrative, case):
        graph.bind_dependency(
            dependent_entity_id=scene.entity_id,
            upstream_entity_id=upstream.entity_id,
            reason="synthetic pre-writing dependency",
        )
    scene = transition_scene_contract_status(
        scene,
        target_status="PROPOSED",
        actor_kind="AI",
    )
    graph.register_head(scene)
    scene = transition_scene_contract_status(
        scene,
        target_status="REVIEWED",
        actor_kind="AI",
    )
    graph.register_head(scene)
    # Writer packet must mirror the full WritingAdmission authority snapshot,
    # including the exact reviewed SceneContract revision itself.
    authority_revisions = (story, narrative, case, scene)
    return (
        graph,
        contract,
        scene,
        tuple(item.revision_ref for item in authority_revisions),
        tuple(
            AuthorityInputRef(
                revision_id=item.revision_id,
                revision_hash=item.revision_hash,
                entity_type=item.kind,
            )
            for item in authority_revisions
        ),
    )


def _clean_case() -> CaseIntegrityResult:
    return CaseIntegrityResult(findings=())


def _clean_narrative() -> NarrativeValidationResult:
    return NarrativeValidationResult(
        findings=(),
        reader_checkpoints=(
            ReaderKnowledgeCheckpoint(
                scene_id="scene-01",
                reader_order=1,
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


def _route(
    operation_id: str,
    operation_kind: str,
    *,
    authority_refs: tuple[str, ...],
):
    choice = RoutingChoice(
        provider="fake",
        provider_label="Fake",
        model="fake-model",
        selection_mode="AUTO",
        selection_scope=None,
        operation=operation_kind,
        rationale="synthetic shared BOOK OS fiction route",
    )
    request = ProductionRouteRequest(
        operation_id=operation_id,
        operation_kind=operation_kind,  # type: ignore[arg-type]
        selected_execution_class="B_STANDARD",
        downstream_blast_radius="LOW",
        provider_execution_requested=True,
        use_editorial_prep_agent=False,
        routing_choice=choice,
        owner_authorization_ref=OWNER_REF,
        cost_authorization_ref=COST_REF,
        max_cost_usd=0.10,
        prep_bundle=None,
        agent_lane_available=False,
        agent_capability_enabled=False,
    )
    owner = VerifiedOwnerExecutionAuthorization(
        authorization_ref=OWNER_REF,
        operation_id=operation_id,
        operation_kind=operation_kind,  # type: ignore[arg-type]
        provider_execution_allowed=True,
        editorial_prep_agent_allowed=False,
        private_content_allowed=False,
        current=True,
    )
    cost = VerifiedCostAuthorization(
        authorization_ref=COST_REF,
        operation_id=operation_id,
        currency="USD",
        max_cost_usd=0.10,
        current=True,
    )
    result = evaluate_production_route(
        request=request,
        policy=ProductionRoutingPolicy(
            max_operation_cost_usd=0.50,
            allowed_agent_operations=(
                "SERIES_ARCHITECTURE",
                "CASE_SOLUTION_ARCHITECTURE",
                "WRITING_READINESS_AUDIT",
            ),
        ),
        current_authority_refs=authority_refs,
        verified_owner_authorizations={OWNER_REF: owner},
        verified_cost_authorizations={COST_REF: cost},
    )
    assert result.qualified
    return request, result


def _execute_fake_fiction_task(
    *,
    task_type: str,
    token,
    route_request,
    route_result,
    authority_refs: tuple[str, ...],
    authority_inputs: tuple[AuthorityInputRef, ...],
):
    adapter = DeterministicFakeAdapter()
    gateway = ModelGateway({"fake": adapter})
    execution = FictionGatewayExecutionRequest(
        task_id=f"synthetic:{task_type.lower()}:1",
        task_type=task_type,  # type: ignore[arg-type]
        book_id="book-1",
        scene_id="scene-01",
        scene_revision_ref=token.scene_revision_ref,
        section_objective="Write only the admitted synthetic fiction scene.",
        authority_revision_refs=authority_refs,
        authority_inputs=authority_inputs,
        authoritative_context={
            "scene_contract": {"scene_id": "scene-01"},
            "series_brain_ref": "series-brain:synthetic-green",
            "anti_cliche_ref": "anti-cliche:synthetic-green",
        },
        task_payload={"scene_id": "scene-01"},
    )
    return execute_fiction_gateway_task(
        gateway=gateway,
        execution=execution,
        admission=token,
        route_request=route_request,
        route_result=route_result,
        now_epoch=NOW,
    )


def _base_readiness(
    *,
    route,
) -> ExternalWritingReadiness:  # type: ignore[no-untyped-def]
    readiness = ExternalWritingReadiness()
    readiness = readiness_with_anti_cliche(
        readiness,
        AntiClicheResult(
            qualified=True,
            anti_cliche_ref="anti-cliche:synthetic-green",
            rule_pack_ref="anti-cliche-rule-pack:default:v1",
            unresolved_blocking_codes=(),
            findings=(),
        ),
    )
    readiness = readiness_with_series_uniqueness(
        readiness,
        SeriesUniquenessResult(
            qualified=True,
            series_brain_ref="series-brain:synthetic-green",
            current_passport_ref="mystery-book-passport:book-1:green",
            findings=(),
        ),
    )
    return readiness_with_production_route(readiness, route)


def _evaluate(
    graph: MysteryAuthorityGraph,
    policy: WritingGatePolicy,
    contract: SceneContract,
    scene: MysteryAuthorityRevision,
    readiness: ExternalWritingReadiness,
):
    return evaluate_scene_writing_gate(
        graph=graph,
        policy=policy,
        contract=contract,
        scene_revision=scene,
        case_integrity=_clean_case(),
        narrative_validation=_clean_narrative(),
        research_ledger=_clean_research(),
        readiness=readiness,
        now_epoch=NOW,
    )


def _blockers(result) -> set[str]:  # type: ignore[no-untyped-def]
    return {blocker for gate in result.state.gates for blocker in gate.blocking_findings}


def test_full_series_pre_writing_dry_run_reaches_representative_sample_writing_allowed() -> None:
    graph, contract, scene, authority_refs, authority_inputs = _build_authority()
    route_request, route = _route(
        "op:representative-sample:1",
        "REPRESENTATIVE_SAMPLE_DRAFT",
        authority_refs=authority_refs,
    )
    readiness = _base_readiness(route=route)
    policy = WritingGatePolicy(
        book_id="book-1",
        story_definition_entity_id="story",
        narrative_contract_entity_id="narrative",
        case_solution_entity_id="case",
        production_mode="REPRESENTATIVE_SAMPLE",
        series_book=True,
    )

    result = _evaluate(
        graph,
        policy,
        contract,
        scene,
        readiness,
    )

    assert result.state.writing_allowed
    assert result.token is not None
    for exact_ref in (
        "anti-cliche:synthetic-green",
        "series-brain:synthetic-green",
        route.execution_route_ref,
        OWNER_REF,
        COST_REF,
    ):
        assert exact_ref in result.token.evaluation_refs

    gateway_result = _execute_fake_fiction_task(
        task_type="REPRESENTATIVE_SAMPLE_DRAFT",
        token=result.token,
        route_request=route_request,
        route_result=route,
        authority_refs=authority_refs,
        authority_inputs=authority_inputs,
    )
    assert gateway_result.output.outcome == "DRAFT"
    assert gateway_result.output.text is not None


def test_mass_draft_remains_closed_until_sample_and_writer_qualification() -> None:
    graph, contract, scene, authority_refs, authority_inputs = _build_authority()
    route_request, route = _route(
        "op:scene-draft:1",
        "SCENE_DRAFT",
        authority_refs=authority_refs,
    )
    readiness = _base_readiness(route=route)
    mass_policy = WritingGatePolicy(
        book_id="book-1",
        story_definition_entity_id="story",
        narrative_contract_entity_id="narrative",
        case_solution_entity_id="case",
        production_mode="MASS_DRAFT",
        series_book=True,
    )

    blocked = _evaluate(
        graph,
        mass_policy,
        contract,
        scene,
        readiness,
    )
    blockers = _blockers(blocked)

    assert "REPRESENTATIVE_SAMPLE.NOT_QUALIFIED" in blockers
    assert "WRITER.NOT_QUALIFIED" in blockers
    assert not blocked.state.writing_allowed

    qualified = readiness_with_sample_qualification(
        readiness,
        SampleQualificationResult(
            representative_sample_qualified=True,
            representative_sample_ref="representative-sample:synthetic-green",
            writer_qualified=True,
            writer_qualification_ref="writer-qualification:synthetic-green",
            findings=(),
        ),
    )
    admitted = _evaluate(
        graph,
        mass_policy,
        contract,
        scene,
        qualified,
    )

    assert admitted.state.writing_allowed
    assert admitted.token is not None
    assert "representative-sample:synthetic-green" in admitted.token.evaluation_refs
    assert "writer-qualification:synthetic-green" in admitted.token.evaluation_refs

    gateway_result = _execute_fake_fiction_task(
        task_type="SCENE_DRAFT",
        token=admitted.token,
        route_request=route_request,
        route_result=route,
        authority_refs=authority_refs,
        authority_inputs=authority_inputs,
    )
    assert gateway_result.output.outcome == "DRAFT"
    assert gateway_result.output.text is not None


def test_agent_capability_is_not_a_runtime_dependency_for_normal_writing() -> None:
    graph, contract, scene, authority_refs, authority_inputs = _build_authority()
    route_request, route = _route(
        "op:representative-sample:no-agent",
        "REPRESENTATIVE_SAMPLE_DRAFT",
        authority_refs=authority_refs,
    )
    # _route deliberately uses agent_lane_available=False and capability_enabled=False.
    assert route.qualified
    assert not route.agent_dispatch_ready

    result = _evaluate(
        graph,
        WritingGatePolicy(
            book_id="book-1",
            story_definition_entity_id="story",
            narrative_contract_entity_id="narrative",
            case_solution_entity_id="case",
            production_mode="REPRESENTATIVE_SAMPLE",
            series_book=True,
        ),
        contract,
        scene,
        _base_readiness(route=route),
    )

    assert result.state.writing_allowed
    assert result.token is not None
    gateway_result = _execute_fake_fiction_task(
        task_type="REPRESENTATIVE_SAMPLE_DRAFT",
        token=result.token,
        route_request=route_request,
        route_result=route,
        authority_refs=authority_refs,
        authority_inputs=authority_inputs,
    )
    assert gateway_result.output.outcome == "DRAFT"
