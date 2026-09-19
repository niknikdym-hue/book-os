from __future__ import annotations

from dataclasses import replace

from book_os_core.model_routing import PROVIDERS, RoutingChoice
from book_os_core.mystery_production_routing import (
    EditorialPrepBundle,
    ProductionRouteRequest,
    ProductionRoutingPolicy,
    VerifiedCostAuthorization,
    VerifiedOwnerExecutionAuthorization,
    editorial_prep_bundle_ref,
    evaluate_production_route,
    verify_production_route,
)

AUTHORITY_REFS = (
    "story@approved:v1",
    "case@approved:v1",
    "series-brain:green:v1",
    "anti-cliche:green:v1",
)

POLICY = ProductionRoutingPolicy(
    max_operation_cost_usd=0.50,
    allowed_agent_operations=(
        "SERIES_ARCHITECTURE",
        "CASE_SOLUTION_ARCHITECTURE",
        "CLUE_REVEAL_ARCHITECTURE",
        "ANTI_CLICHE_STRESS_TEST",
        "SERIES_SEMANTIC_COLLISION",
        "WRITING_READINESS_AUDIT",
        "WHOLE_BOOK_DEVELOPMENTAL",
    ),
)

OWNER_REF = "owner-auth:op:v1"
COST_REF = "cost-auth:op:v1"


def _choice(operation: str, *, model: str = "gpt-5.6-sol") -> RoutingChoice:
    return RoutingChoice(
        provider="openai",
        provider_label="OpenAI",
        model=model,
        selection_mode="AUTO",
        selection_scope=None,
        operation=operation,
        rationale="synthetic verified shared BOOK OS route",
    )


def _owner(
    operation_id: str,
    operation_kind: str,
    *,
    agent_allowed: bool = False,
    private_allowed: bool = False,
    current: bool = True,
) -> VerifiedOwnerExecutionAuthorization:
    return VerifiedOwnerExecutionAuthorization(
        authorization_ref=OWNER_REF,
        operation_id=operation_id,
        operation_kind=operation_kind,  # type: ignore[arg-type]
        provider_execution_allowed=True,
        editorial_prep_agent_allowed=agent_allowed,
        private_content_allowed=private_allowed,
        current=current,
    )


def _cost(
    operation_id: str,
    *,
    cap: float = 0.50,
    current: bool = True,
) -> VerifiedCostAuthorization:
    return VerifiedCostAuthorization(
        authorization_ref=COST_REF,
        operation_id=operation_id,
        currency="USD",
        max_cost_usd=cap,
        current=current,
    )


def _bundle(
    *,
    private_scope: str = "NONE",
    forbidden_actions: tuple[str, ...] | None = None,
    contains_secrets: bool = False,
    repository_write_allowed: bool = False,
    manuscript_prose_allowed: bool = False,
    network_mode: str = "DISABLED",
    source_packet_refs: tuple[str, ...] = (),
) -> EditorialPrepBundle:
    return EditorialPrepBundle(
        task_id="editorial-prep:case:v1",
        project_id="book-os-project",
        series_id="series-112",
        book_id="book-1",
        authority_refs=AUTHORITY_REFS,
        task="Propose and stress-test case architecture; do not write prose.",
        allowed_outputs=(
            "CASE_SOLUTION_PROPOSAL",
            "SUSPECT_MATRIX_PROPOSAL",
            "CLUE_PLAN_PROPOSAL",
            "RISK_REPORT",
        ),
        forbidden_actions=forbidden_actions
        or (
            "UNLOCK_WRITING",
            "APPROVE_STORY_AUTHORITY",
            "APPROVE_ANTI_CLICHE_EXCEPTION",
            "WRITE_MANUSCRIPT_PROSE",
            "REPOSITORY_WRITE",
            "MERGE_DEPLOY_RELEASE",
        ),
        source_packet_refs=source_packet_refs,
        private_content_scope=private_scope,  # type: ignore[arg-type]
        reasoning_mode="high",
        output_schema_ref="schema:editorial-prep-output:v1",
        proposal_only=True,
        repository_write_allowed=repository_write_allowed,
        manuscript_prose_allowed=manuscript_prose_allowed,
        network_mode=network_mode,  # type: ignore[arg-type]
        contains_secrets=contains_secrets,
    )


def _standard_request() -> ProductionRouteRequest:
    return ProductionRouteRequest(
        operation_id="op:scene-draft:1",
        operation_kind="SCENE_DRAFT",
        selected_execution_class="B_STANDARD",
        downstream_blast_radius="LOW",
        provider_execution_requested=True,
        use_editorial_prep_agent=False,
        routing_choice=_choice("SCENE_DRAFT"),
        owner_authorization_ref=OWNER_REF,
        cost_authorization_ref=COST_REF,
        max_cost_usd=0.10,
        prep_bundle=None,
        agent_lane_available=False,
        agent_capability_enabled=False,
    )


def _agent_request(
    *,
    bundle: EditorialPrepBundle | None = None,
) -> ProductionRouteRequest:
    return ProductionRouteRequest(
        operation_id="op:case-architecture:1",
        operation_kind="CASE_SOLUTION_ARCHITECTURE",
        selected_execution_class="C_PREMIUM",
        downstream_blast_radius="HIGH",
        provider_execution_requested=True,
        use_editorial_prep_agent=True,
        routing_choice=_choice(
            "CASE_SOLUTION_ARCHITECTURE",
            model="gpt-6-astra",
        ),
        owner_authorization_ref=OWNER_REF,
        cost_authorization_ref=COST_REF,
        max_cost_usd=0.40,
        prep_bundle=bundle or _bundle(private_scope="MINIMUM_NECESSARY"),
        agent_lane_available=True,
        agent_capability_enabled=True,
    )


def _auth_maps(
    request: ProductionRouteRequest,
    *,
    agent_allowed: bool = False,
    private_allowed: bool = False,
    owner_current: bool = True,
    cost_cap: float = 0.50,
    cost_current: bool = True,
):
    return (
        {
            OWNER_REF: _owner(
                request.operation_id,
                request.operation_kind,
                agent_allowed=agent_allowed,
                private_allowed=private_allowed,
                current=owner_current,
            )
        },
        {
            COST_REF: _cost(
                request.operation_id,
                cap=cost_cap,
                current=cost_current,
            )
        },
    )


def _evaluate(
    request: ProductionRouteRequest,
    *,
    owner=None,  # type: ignore[no-untyped-def]
    cost=None,  # type: ignore[no-untyped-def]
):
    if owner is None or cost is None:
        default_owner, default_cost = _auth_maps(request)
        owner = default_owner if owner is None else owner
        cost = default_cost if cost is None else cost
    return evaluate_production_route(
        request=request,
        policy=POLICY,
        current_authority_refs=AUTHORITY_REFS,
        verified_owner_authorizations=owner,
        verified_cost_authorizations=cost,
    )


def _codes(result) -> set[str]:  # type: ignore[no-untyped-def]
    return {finding.code for finding in result.findings}


def test_shared_auto_routing_keeps_scene_work_standard_and_global_work_premium() -> None:
    openai = PROVIDERS["openai"]

    assert openai.auto["REPRESENTATIVE_SAMPLE_DRAFT"] == "gpt-5.6-sol"
    assert openai.auto["SCENE_DRAFT"] == "gpt-5.6-sol"
    assert openai.auto["ROUTINE_SCENE_REVISION"] == "gpt-5.6-sol"
    assert openai.auto["CASE_SOLUTION_ARCHITECTURE"] == "gpt-6-astra"
    assert openai.auto["SERIES_SEMANTIC_COLLISION"] == "gpt-6-astra"
    assert openai.auto["WRITING_READINESS_AUDIT"] == "gpt-6-astra"


def test_standard_writer_route_does_not_depend_on_agent_lane() -> None:
    request = _standard_request()
    owner, cost = _auth_maps(request)

    result = _evaluate(request, owner=owner, cost=cost)

    assert result.qualified
    assert not result.agent_dispatch_ready
    assert result.provider_execution_requested
    assert result.execution_authorization_ref == OWNER_REF
    assert result.cost_authorization_ref == COST_REF


def test_class_a_local_operation_cannot_secretly_call_provider_or_agent() -> None:
    request = replace(
        _standard_request(),
        operation_id="op:local:1",
        operation_kind="CASE_TIMELINE_VALIDATION",
        selected_execution_class="A_LOCAL",
        provider_execution_requested=True,
        use_editorial_prep_agent=True,
        routing_choice=_choice("CASE_TIMELINE_VALIDATION"),
        prep_bundle=_bundle(),
    )
    owner, cost = _auth_maps(request, agent_allowed=True)

    result = _evaluate(request, owner=owner, cost=cost)
    codes = _codes(result)

    assert "ROUTING.LOCAL.PROVIDER_EXECUTION_FORBIDDEN" in codes
    assert "ROUTING.LOCAL.AGENT_FORBIDDEN" in codes
    assert not result.qualified


def test_operation_cannot_be_routed_below_required_execution_class() -> None:
    request = replace(
        _standard_request(),
        operation_id="op:case-low:1",
        operation_kind="CASE_SOLUTION_ARCHITECTURE",
        selected_execution_class="B_STANDARD",
        routing_choice=_choice(
            "CASE_SOLUTION_ARCHITECTURE",
            model="gpt-5.6-sol",
        ),
    )
    owner, cost = _auth_maps(request)

    result = _evaluate(request, owner=owner, cost=cost)

    assert "ROUTING.EXECUTION_CLASS_TOO_LOW" in _codes(result)


def test_owner_and_cost_authorizations_are_exact_operation_artifacts() -> None:
    request = _standard_request()
    wrong_owner = {
        OWNER_REF: _owner(
            "another-operation",
            "SCENE_DRAFT",
        )
    }
    wrong_cost = {
        COST_REF: _cost("another-operation")
    }

    result = _evaluate(
        request,
        owner=wrong_owner,
        cost=wrong_cost,
    )
    codes = _codes(result)

    assert "ROUTING.PROVIDER.OWNER_AUTH_OPERATION_MISMATCH" in codes
    assert "ROUTING.PROVIDER.COST_AUTH_OPERATION_MISMATCH" in codes
    assert not result.qualified


def test_cost_cap_must_fit_owner_policy_and_exact_cost_authorization() -> None:
    request = replace(_standard_request(), max_cost_usd=0.45)
    owner, cost = _auth_maps(request, cost_cap=0.20)

    authorized = _evaluate(request, owner=owner, cost=cost)
    assert "ROUTING.PROVIDER.COST_CAP_EXCEEDS_AUTHORIZATION" in _codes(
        authorized
    )

    above_policy = replace(request, max_cost_usd=0.75)
    owner2, cost2 = _auth_maps(above_policy, cost_cap=1.00)
    result = _evaluate(above_policy, owner=owner2, cost=cost2)
    assert "ROUTING.PROVIDER.COST_CAP_EXCEEDS_POLICY" in _codes(result)


def test_clean_editorial_prep_agent_bundle_is_dispatch_ready() -> None:
    request = _agent_request()
    owner, cost = _auth_maps(
        request,
        agent_allowed=True,
        private_allowed=True,
    )

    result = _evaluate(request, owner=owner, cost=cost)

    assert result.qualified
    assert result.agent_dispatch_ready
    assert editorial_prep_bundle_ref(request.prep_bundle).startswith(  # type: ignore[arg-type]
        "editorial-prep-bundle:"
    )


def test_agent_requires_lane_kill_switch_owner_and_cost_authority() -> None:
    request = replace(
        _agent_request(),
        agent_lane_available=False,
        agent_capability_enabled=False,
    )

    result = _evaluate(request, owner={}, cost={})
    codes = _codes(result)

    assert "ROUTING.AGENT.LANE_UNAVAILABLE" in codes
    assert "ROUTING.AGENT.CAPABILITY_DISABLED" in codes
    assert "ROUTING.PROVIDER.OWNER_AUTH_UNVERIFIED" in codes
    assert "ROUTING.PROVIDER.COST_AUTH_UNVERIFIED" in codes
    assert not result.agent_dispatch_ready


def test_agent_owner_authorization_must_explicitly_allow_agent_and_private_content() -> None:
    request = _agent_request()
    owner, cost = _auth_maps(
        request,
        agent_allowed=False,
        private_allowed=False,
    )

    result = _evaluate(request, owner=owner, cost=cost)
    codes = _codes(result)

    assert "ROUTING.AGENT.OWNER_AUTH_AGENT_DENIED" in codes
    assert "ROUTING.AGENT.PRIVATE_CONTENT_OWNER_AUTH_MISSING" in codes


def test_agent_bundle_cannot_contain_secrets_or_gain_write_authority() -> None:
    bundle = _bundle(
        private_scope="MINIMUM_NECESSARY",
        contains_secrets=True,
        repository_write_allowed=True,
        manuscript_prose_allowed=True,
    )
    request = _agent_request(bundle=bundle)
    owner, cost = _auth_maps(
        request,
        agent_allowed=True,
        private_allowed=True,
    )

    result = _evaluate(request, owner=owner, cost=cost)
    codes = _codes(result)

    assert "ROUTING.AGENT.BUNDLE.SECRET_MATERIAL_DETECTED" in codes
    assert "ROUTING.AGENT.BUNDLE.REPOSITORY_WRITE_FORBIDDEN" in codes
    assert "ROUTING.AGENT.BUNDLE.MANUSCRIPT_PROSE_FORBIDDEN" in codes


def test_agent_bundle_must_forbid_authority_and_release_actions() -> None:
    bundle = _bundle(
        private_scope="MINIMUM_NECESSARY",
        forbidden_actions=("WRITE_MANUSCRIPT_PROSE",),
    )
    request = _agent_request(bundle=bundle)
    owner, cost = _auth_maps(
        request,
        agent_allowed=True,
        private_allowed=True,
    )

    result = _evaluate(request, owner=owner, cost=cost)

    assert "ROUTING.AGENT.BUNDLE.FORBIDDEN_ACTION_MISSING" in _codes(result)
    assert not result.qualified


def test_source_packet_network_mode_is_explicit_and_bounded() -> None:
    missing_packet = _bundle(
        private_scope="MINIMUM_NECESSARY",
        network_mode="SOURCE_PACKET_ONLY",
        source_packet_refs=(),
    )
    request = _agent_request(bundle=missing_packet)
    owner, cost = _auth_maps(
        request,
        agent_allowed=True,
        private_allowed=True,
    )
    blocked = _evaluate(request, owner=owner, cost=cost)
    assert "ROUTING.AGENT.BUNDLE.SOURCE_PACKET_REQUIRED" in _codes(blocked)

    clean_bundle = replace(
        missing_packet,
        source_packet_refs=("source-packet:current-market:v1",),
    )
    clean_request = _agent_request(bundle=clean_bundle)
    owner2, cost2 = _auth_maps(
        clean_request,
        agent_allowed=True,
        private_allowed=True,
    )
    allowed = _evaluate(clean_request, owner=owner2, cost=cost2)
    assert allowed.qualified


def test_agent_is_optional_for_direct_premium_execution() -> None:
    request = replace(
        _agent_request(),
        use_editorial_prep_agent=False,
        prep_bundle=None,
        agent_lane_available=False,
        agent_capability_enabled=False,
    )
    owner, cost = _auth_maps(request)

    result = _evaluate(request, owner=owner, cost=cost)

    assert result.qualified
    assert not result.agent_dispatch_ready


def test_route_ref_is_version_bound_to_authorized_execution_request() -> None:
    request = _standard_request()
    owner, cost = _auth_maps(request)
    result = _evaluate(request, owner=owner, cost=cost)
    assert result.qualified

    verified = verify_production_route(
        prior_execution_route_ref=result.execution_route_ref,
        request=request,
        policy=POLICY,
        current_authority_refs=AUTHORITY_REFS,
        verified_owner_authorizations=owner,
        verified_cost_authorizations=cost,
    )
    assert verified.valid

    changed = replace(request, max_cost_usd=0.11)
    changed_owner, changed_cost = _auth_maps(changed)
    stale = verify_production_route(
        prior_execution_route_ref=result.execution_route_ref,
        request=changed,
        policy=POLICY,
        current_authority_refs=AUTHORITY_REFS,
        verified_owner_authorizations=changed_owner,
        verified_cost_authorizations=changed_cost,
    )
    assert not stale.valid
    assert stale.reason == "PRODUCTION_ROUTE_SNAPSHOT_CHANGED"
