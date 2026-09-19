from __future__ import annotations

import pytest

from book_os_core.model_gateway import (
    AuthorityInputRef,
    DeterministicFakeAdapter,
    FictionSceneDraftOutput,
    ModelGateway,
    ModelOutputError,
)
from book_os_core.model_routing import RoutingChoice
from book_os_core.mystery_editorial_gate import WritingAdmissionToken
from book_os_core.mystery_fiction_gateway import (
    FictionGatewayExecutionRequest,
    FictionWritingAdmissionError,
    execute_fiction_gateway_task,
)
from book_os_core.mystery_production_routing import (
    ProductionRouteRequest,
    ProductionRouteResult,
)

NOW = 1_800_000_000
AUTHORITY_REFS = (
    "story@rev-story:hash-story",
    "case@rev-case:hash-case",
)
AUTHORITY_INPUTS = (
    AuthorityInputRef(
        revision_id="rev-story",
        revision_hash="hash-story",
        entity_type="STORY_DEFINITION",
    ),
    AuthorityInputRef(
        revision_id="rev-case",
        revision_hash="hash-case",
        entity_type="CASE_SOLUTION",
    ),
)


def _route_request(
    task_type: str,
    *,
    provider: str = "fake",
) -> ProductionRouteRequest:
    return ProductionRouteRequest(
        operation_id=f"op:{task_type.lower()}:1",
        operation_kind=task_type,  # type: ignore[arg-type]
        selected_execution_class="B_STANDARD",
        downstream_blast_radius="LOW",
        provider_execution_requested=True,
        use_editorial_prep_agent=False,
        routing_choice=RoutingChoice(
            provider=provider,
            provider_label="Fake",
            model="fake-model",
            selection_mode="AUTO",
            selection_scope=None,
            operation=task_type,
            rationale="deterministic fiction gateway test route",
        ),
        owner_authorization_ref="owner-auth:v1",
        cost_authorization_ref="cost-auth:v1",
        max_cost_usd=0.10,
        prep_bundle=None,
        agent_lane_available=False,
        agent_capability_enabled=False,
    )


def _route_result() -> ProductionRouteResult:
    return ProductionRouteResult(
        qualified=True,
        execution_route_ref="mystery-production-route:green-v1",
        provider_execution_requested=True,
        execution_authorization_ref="owner-auth:v1",
        cost_authorization_ref="cost-auth:v1",
        agent_dispatch_ready=False,
        findings=(),
    )


def _admission(
    *,
    mode: str,
    not_after_epoch: int | None = None,
) -> WritingAdmissionToken:
    route = _route_result()
    return WritingAdmissionToken(
        admission_id="writing-admission:scene-1:v1",
        book_id="book-1",
        scene_id="scene-1",
        production_mode=mode,  # type: ignore[arg-type]
        scene_revision_ref="scene-contract:book-1:scene-1@rev-1:hash-scene",
        dependency_fingerprint="a" * 64,
        authority_revision_refs=AUTHORITY_REFS,
        evaluation_refs=(
            route.execution_route_ref,
            route.execution_authorization_ref or "",
            route.cost_authorization_ref or "",
            "series-brain:green",
            "anti-cliche:green",
        ),
        not_after_epoch=not_after_epoch,
    )


def _execution(task_type: str) -> FictionGatewayExecutionRequest:
    return FictionGatewayExecutionRequest(
        task_id=f"fiction:{task_type.lower()}:1",
        task_type=task_type,  # type: ignore[arg-type]
        book_id="book-1",
        scene_id="scene-1",
        scene_revision_ref="scene-contract:book-1:scene-1@rev-1:hash-scene",
        section_objective="Write only the admitted synthetic scene.",
        authority_revision_refs=AUTHORITY_REFS,
        authority_inputs=AUTHORITY_INPUTS,
        authoritative_context={
            "scene_contract": {"purpose": "synthetic exact scene"},
            "style_profile_ref": "style-profile:green",
        },
        task_payload={"scene_id": "scene-1"},
    )


def test_representative_sample_executes_through_shared_model_gateway() -> None:
    adapter = DeterministicFakeAdapter()
    gateway = ModelGateway({"fake": adapter})
    route_request = _route_request("REPRESENTATIVE_SAMPLE_DRAFT")

    result = execute_fiction_gateway_task(
        gateway=gateway,
        execution=_execution("REPRESENTATIVE_SAMPLE_DRAFT"),
        admission=_admission(mode="REPRESENTATIVE_SAMPLE"),
        route_request=route_request,
        route_result=_route_result(),
        now_epoch=NOW,
    )

    assert result.output.outcome == "DRAFT"
    assert result.output.text is not None
    assert "Fiction draft for" in result.output.text
    assert result.model_task_request.task_type == "REPRESENTATIVE_SAMPLE_DRAFT"
    assert result.model_task_request.role == "WRITER"
    assert result.model_task_request.prompt_id == "mystery_scene_draft_v1"
    assert adapter.last_request == result.model_task_request


def test_mass_scene_draft_requires_mass_draft_admission() -> None:
    gateway = ModelGateway({"fake": DeterministicFakeAdapter()})

    with pytest.raises(
        FictionWritingAdmissionError,
        match="requires MASS_DRAFT admission",
    ):
        execute_fiction_gateway_task(
            gateway=gateway,
            execution=_execution("SCENE_DRAFT"),
            admission=_admission(mode="REPRESENTATIVE_SAMPLE"),
            route_request=_route_request("SCENE_DRAFT"),
            route_result=_route_result(),
            now_epoch=NOW,
        )


def test_expired_admission_never_reaches_provider() -> None:
    adapter = DeterministicFakeAdapter()
    gateway = ModelGateway({"fake": adapter})

    with pytest.raises(FictionWritingAdmissionError, match="expired"):
        execute_fiction_gateway_task(
            gateway=gateway,
            execution=_execution("SCENE_DRAFT"),
            admission=_admission(mode="MASS_DRAFT", not_after_epoch=NOW),
            route_request=_route_request("SCENE_DRAFT"),
            route_result=_route_result(),
            now_epoch=NOW,
        )

    assert adapter.last_request is None


def test_route_and_authority_snapshot_must_match_exact_admission() -> None:
    gateway = ModelGateway({"fake": DeterministicFakeAdapter()})
    bad_route = ProductionRouteResult(
        qualified=True,
        execution_route_ref="mystery-production-route:other",
        provider_execution_requested=True,
        execution_authorization_ref="owner-auth:v1",
        cost_authorization_ref="cost-auth:v1",
        agent_dispatch_ready=False,
        findings=(),
    )

    with pytest.raises(
        FictionWritingAdmissionError,
        match="production route ref",
    ):
        execute_fiction_gateway_task(
            gateway=gateway,
            execution=_execution("SCENE_DRAFT"),
            admission=_admission(mode="MASS_DRAFT"),
            route_request=_route_request("SCENE_DRAFT"),
            route_result=bad_route,
            now_epoch=NOW,
        )

    bad_execution = FictionGatewayExecutionRequest(
        **{
            **_execution("SCENE_DRAFT").__dict__,
            "authority_revision_refs": (AUTHORITY_REFS[0],),
            "authority_inputs": (AUTHORITY_INPUTS[0],),
        }
    )
    with pytest.raises(
        FictionWritingAdmissionError,
        match="authority snapshot differs",
    ):
        execute_fiction_gateway_task(
            gateway=gateway,
            execution=bad_execution,
            admission=_admission(mode="MASS_DRAFT"),
            route_request=_route_request("SCENE_DRAFT"),
            route_result=_route_result(),
            now_epoch=NOW,
        )


def test_malformed_provider_output_is_rejected_after_gateway_call() -> None:
    adapter = DeterministicFakeAdapter(mode="malformed")
    gateway = ModelGateway({"fake": adapter})

    with pytest.raises(ModelOutputError, match="structured output failed"):
        execute_fiction_gateway_task(
            gateway=gateway,
            execution=_execution("SCENE_DRAFT"),
            admission=_admission(mode="MASS_DRAFT"),
            route_request=_route_request("SCENE_DRAFT"),
            route_result=_route_result(),
            now_epoch=NOW,
        )


def test_architecture_blocker_contract_forbids_mixed_prose() -> None:
    valid = FictionSceneDraftOutput(
        outcome="ARCHITECTURE_BLOCKER",
        text=None,
        blocker_code="CLUE_AUTHORITY_MISSING",
        blocker_detail="Scene cannot proceed without inventing a clue.",
        notes=[],
    )
    assert valid.outcome == "ARCHITECTURE_BLOCKER"

    with pytest.raises(ValueError):
        FictionSceneDraftOutput(
            outcome="ARCHITECTURE_BLOCKER",
            text="I silently wrote the scene anyway.",
            blocker_code="CLUE_AUTHORITY_MISSING",
            blocker_detail="Missing clue.",
            notes=[],
        )


def test_continuity_extraction_uses_evaluator_role_and_no_prose_schema() -> None:
    gateway = ModelGateway({"fake": DeterministicFakeAdapter()})
    result = execute_fiction_gateway_task(
        gateway=gateway,
        execution=_execution("CONTINUITY_EXTRACTION"),
        admission=_admission(mode="MASS_DRAFT"),
        route_request=_route_request("CONTINUITY_EXTRACTION"),
        route_result=_route_result(),
        now_epoch=NOW,
    )

    assert result.model_task_request.role == "EVALUATOR"
    assert result.model_task_request.prompt_id == "mystery_continuity_extract_v1"
    assert result.output.scene_id == "scene-1"  # type: ignore[union-attr]
