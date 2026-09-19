from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, TypeAlias

from pydantic import ValidationError

from .model_gateway import (
    AuthorityInputRef,
    FictionContinuityExtractionOutput,
    FictionSceneDraftOutput,
    ModelAdapterResult,
    ModelGateway,
    ModelOutputError,
    ModelTaskRequest,
)
from .mystery_editorial_gate import WritingAdmissionToken
from .mystery_production_routing import (
    ProductionRouteRequest,
    ProductionRouteResult,
)
from .prompts import get_prompt

FictionGatewayTaskType: TypeAlias = Literal[
    "REPRESENTATIVE_SAMPLE_DRAFT",
    "SCENE_DRAFT",
    "ROUTINE_SCENE_REVISION",
    "CONTINUITY_EXTRACTION",
]


class FictionWritingAdmissionError(RuntimeError):
    pass


@dataclass(frozen=True)
class FictionGatewayExecutionRequest:
    task_id: str
    task_type: FictionGatewayTaskType
    book_id: str
    scene_id: str
    scene_revision_ref: str
    section_objective: str
    authority_revision_refs: tuple[str, ...]
    authority_inputs: tuple[AuthorityInputRef, ...]
    authoritative_context: dict[str, Any]
    untrusted_context: tuple[str, ...] = ()
    task_payload: dict[str, Any] | None = None
    max_output_tokens: int = 5000


@dataclass(frozen=True)
class FictionGatewayExecutionResult:
    provider_run_id: str | None
    task_type: FictionGatewayTaskType
    output: FictionSceneDraftOutput | FictionContinuityExtractionOutput
    usage: dict[str, Any]
    model_task_request: ModelTaskRequest


def _prompt_id(task_type: FictionGatewayTaskType) -> str:
    if task_type in {"REPRESENTATIVE_SAMPLE_DRAFT", "SCENE_DRAFT"}:
        return "mystery_scene_draft_v1"
    if task_type == "ROUTINE_SCENE_REVISION":
        return "mystery_scene_revision_v1"
    return "mystery_continuity_extract_v1"


def _expected_role(task_type: FictionGatewayTaskType) -> str:
    if task_type == "CONTINUITY_EXTRACTION":
        return "EVALUATOR"
    return "WRITER"


def _validate_task_mode(
    task_type: FictionGatewayTaskType,
    admission: WritingAdmissionToken,
) -> None:
    if task_type == "REPRESENTATIVE_SAMPLE_DRAFT":
        if admission.production_mode != "REPRESENTATIVE_SAMPLE":
            raise FictionWritingAdmissionError(
                "representative sample task requires REPRESENTATIVE_SAMPLE admission"
            )
        return
    if task_type == "SCENE_DRAFT":
        if admission.production_mode != "MASS_DRAFT":
            raise FictionWritingAdmissionError(
                "scene draft task requires MASS_DRAFT admission"
            )
        return
    if task_type == "ROUTINE_SCENE_REVISION":
        if admission.production_mode not in {"REPRESENTATIVE_SAMPLE", "MASS_DRAFT"}:
            raise FictionWritingAdmissionError(
                "scene revision requires active writing admission"
            )
        return
    if task_type == "CONTINUITY_EXTRACTION":
        if admission.production_mode not in {"REPRESENTATIVE_SAMPLE", "MASS_DRAFT"}:
            raise FictionWritingAdmissionError(
                "continuity extraction requires admitted scene snapshot"
            )


def _validate_admission(
    *,
    execution: FictionGatewayExecutionRequest,
    admission: WritingAdmissionToken,
    route_request: ProductionRouteRequest,
    route_result: ProductionRouteResult,
    now_epoch: int,
) -> None:
    if not route_result.qualified:
        raise FictionWritingAdmissionError("production route is not qualified")
    if not route_result.provider_execution_requested:
        raise FictionWritingAdmissionError(
            "fiction gateway execution requires provider execution route"
        )
    if route_request.routing_choice is None:
        raise FictionWritingAdmissionError("qualified route has no RoutingChoice")
    if route_request.operation_kind != execution.task_type:
        raise FictionWritingAdmissionError(
            "route operation kind does not match fiction gateway task type"
        )
    if route_result.execution_route_ref not in admission.evaluation_refs:
        raise FictionWritingAdmissionError(
            "WritingAdmissionToken does not contain exact production route ref"
        )
    for label, ref in (
        ("owner authorization", route_result.execution_authorization_ref),
        ("cost authorization", route_result.cost_authorization_ref),
    ):
        if ref is None or ref not in admission.evaluation_refs:
            raise FictionWritingAdmissionError(
                f"WritingAdmissionToken does not contain exact {label} ref"
            )

    if admission.book_id != execution.book_id:
        raise FictionWritingAdmissionError("admission belongs to another book")
    if admission.scene_id != execution.scene_id:
        raise FictionWritingAdmissionError("admission belongs to another scene")
    if admission.scene_revision_ref != execution.scene_revision_ref:
        raise FictionWritingAdmissionError(
            "admission belongs to another SceneContract revision"
        )
    if (
        admission.not_after_epoch is not None
        and now_epoch >= admission.not_after_epoch
    ):
        raise FictionWritingAdmissionError("writing admission token has expired")

    _validate_task_mode(execution.task_type, admission)

    expected_authority = tuple(sorted(set(admission.authority_revision_refs)))
    supplied_authority = tuple(sorted(set(execution.authority_revision_refs)))
    if not supplied_authority:
        raise FictionWritingAdmissionError(
            "fiction Writer request requires exact authority revision refs"
        )
    if supplied_authority != expected_authority:
        raise FictionWritingAdmissionError(
            "fiction Writer authority snapshot differs from WritingAdmissionToken"
        )
    if len(supplied_authority) != len(execution.authority_revision_refs):
        raise FictionWritingAdmissionError(
            "fiction Writer authority revision refs contain duplicates"
        )

    revision_ids = [item.revision_id for item in execution.authority_inputs]
    if len(set(revision_ids)) != len(revision_ids):
        raise FictionWritingAdmissionError(
            "fiction Writer AuthorityInputRef revision_ids contain duplicates"
        )
    if len(execution.authority_inputs) != len(execution.authority_revision_refs):
        raise FictionWritingAdmissionError(
            "AuthorityInputRef count must match exact authority revision ref count"
        )
    if not execution.section_objective.strip():
        raise FictionWritingAdmissionError("fiction scene objective must not be blank")


def _model_request(
    *,
    execution: FictionGatewayExecutionRequest,
    route_request: ProductionRouteRequest,
) -> tuple[ModelTaskRequest, str]:
    choice = route_request.routing_choice
    if choice is None:
        raise FictionWritingAdmissionError("routing choice is missing")
    prompt_id = _prompt_id(execution.task_type)
    prompt = get_prompt(prompt_id)
    task_payload = dict(execution.task_payload or {})
    task_payload.setdefault("book_id", execution.book_id)
    task_payload.setdefault("scene_id", execution.scene_id)
    task_payload.setdefault("scene_revision_ref", execution.scene_revision_ref)
    task_payload.setdefault(
        "authority_revision_refs",
        list(execution.authority_revision_refs),
    )
    request = ModelTaskRequest(
        task_id=execution.task_id,
        task_type=execution.task_type,
        role=_expected_role(execution.task_type),  # type: ignore[arg-type]
        provider=choice.provider,
        model=choice.model,
        prompt_id=prompt.prompt_id,
        prompt_version=prompt.version,
        prompt_hash=prompt.prompt_hash,
        section_objective=execution.section_objective,
        authority_inputs=list(execution.authority_inputs),
        authoritative_context=execution.authoritative_context,
        untrusted_context=list(execution.untrusted_context),
        task_payload=task_payload,
        max_output_tokens=execution.max_output_tokens,
        max_cost_usd=route_request.max_cost_usd,
    )
    return request, prompt_id


def execute_fiction_gateway_task(
    *,
    gateway: ModelGateway,
    execution: FictionGatewayExecutionRequest,
    admission: WritingAdmissionToken,
    route_request: ProductionRouteRequest,
    route_result: ProductionRouteResult,
    now_epoch: int,
) -> FictionGatewayExecutionResult:
    """Execute one admitted fiction task through the shared BOOK OS ModelGateway."""
    _validate_admission(
        execution=execution,
        admission=admission,
        route_request=route_request,
        route_result=route_result,
        now_epoch=now_epoch,
    )
    request, prompt_id = _model_request(
        execution=execution,
        route_request=route_request,
    )
    prompt = get_prompt(prompt_id)
    raw: ModelAdapterResult = gateway.generate(request, prompt)
    try:
        if execution.task_type == "CONTINUITY_EXTRACTION":
            output: FictionSceneDraftOutput | FictionContinuityExtractionOutput
            output = FictionContinuityExtractionOutput.model_validate(raw.output)
        else:
            output = FictionSceneDraftOutput.model_validate(raw.output)
    except ValidationError as exc:
        raise ModelOutputError(
            f"{execution.task_type} structured output failed schema validation"
        ) from exc
    return FictionGatewayExecutionResult(
        provider_run_id=raw.provider_run_id,
        task_type=execution.task_type,
        output=output,
        usage=dict(raw.usage),
        model_task_request=request,
    )
