from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, TypeAlias

from .authority_types import JSONValue, content_hash
from .model_routing import RoutingChoice

ExecutionClass: TypeAlias = Literal["A_LOCAL", "B_STANDARD", "C_PREMIUM"]
OperationKind: TypeAlias = Literal[
    "SCHEMA_VALIDATION",
    "CASE_TIMELINE_VALIDATION",
    "EXACT_SERIES_COLLISION",
    "REPRESENTATIVE_SAMPLE_DRAFT",
    "SCENE_DRAFT",
    "ROUTINE_SCENE_REVISION",
    "CONTINUITY_EXTRACTION",
    "SERIES_ARCHITECTURE",
    "CASE_SOLUTION_ARCHITECTURE",
    "CLUE_REVEAL_ARCHITECTURE",
    "ANTI_CLICHE_STRESS_TEST",
    "SERIES_SEMANTIC_COLLISION",
    "WRITING_READINESS_AUDIT",
    "WHOLE_BOOK_DEVELOPMENTAL",
]
BlastRadius: TypeAlias = Literal["LOW", "MEDIUM", "HIGH"]
PrivateContentScope: TypeAlias = Literal[
    "NONE",
    "MINIMUM_NECESSARY",
    "OWNER_SELECTED",
]
NetworkMode: TypeAlias = Literal["DISABLED", "SOURCE_PACKET_ONLY"]
ReasoningMode: TypeAlias = Literal["auto", "medium", "high", "xhigh"]

_VALID_BLAST_RADIUS = frozenset({"LOW", "MEDIUM", "HIGH"})
_VALID_PRIVATE_SCOPES = frozenset({"NONE", "MINIMUM_NECESSARY", "OWNER_SELECTED"})
_VALID_NETWORK_MODES = frozenset({"DISABLED", "SOURCE_PACKET_ONLY"})
_VALID_REASONING_MODES = frozenset({"auto", "medium", "high", "xhigh"})

_CLASS_ORDER: dict[str, int] = {
    "A_LOCAL": 0,
    "B_STANDARD": 1,
    "C_PREMIUM": 2,
}
_OPERATION_MINIMUM: dict[str, ExecutionClass] = {
    "SCHEMA_VALIDATION": "A_LOCAL",
    "CASE_TIMELINE_VALIDATION": "A_LOCAL",
    "EXACT_SERIES_COLLISION": "A_LOCAL",
    "REPRESENTATIVE_SAMPLE_DRAFT": "B_STANDARD",
    "SCENE_DRAFT": "B_STANDARD",
    "ROUTINE_SCENE_REVISION": "B_STANDARD",
    "CONTINUITY_EXTRACTION": "B_STANDARD",
    "SERIES_ARCHITECTURE": "C_PREMIUM",
    "CASE_SOLUTION_ARCHITECTURE": "C_PREMIUM",
    "CLUE_REVEAL_ARCHITECTURE": "C_PREMIUM",
    "ANTI_CLICHE_STRESS_TEST": "C_PREMIUM",
    "SERIES_SEMANTIC_COLLISION": "C_PREMIUM",
    "WRITING_READINESS_AUDIT": "C_PREMIUM",
    "WHOLE_BOOK_DEVELOPMENTAL": "C_PREMIUM",
}
_REQUIRED_AGENT_FORBIDDEN_ACTIONS = frozenset(
    {
        "UNLOCK_WRITING",
        "APPROVE_STORY_AUTHORITY",
        "APPROVE_ANTI_CLICHE_EXCEPTION",
        "WRITE_MANUSCRIPT_PROSE",
        "REPOSITORY_WRITE",
        "MERGE_DEPLOY_RELEASE",
    }
)


@dataclass(frozen=True)
class ProductionRoutingPolicy:
    max_operation_cost_usd: float
    allowed_agent_operations: tuple[OperationKind, ...]
    require_owner_authorization_for_provider: bool = True
    require_cost_authorization_for_provider: bool = True
    require_owner_authorization_for_private_content: bool = True


@dataclass(frozen=True)
class EditorialPrepBundle:
    task_id: str
    project_id: str
    series_id: str | None
    book_id: str | None
    authority_refs: tuple[str, ...]
    task: str
    allowed_outputs: tuple[str, ...]
    forbidden_actions: tuple[str, ...]
    source_packet_refs: tuple[str, ...]
    private_content_scope: PrivateContentScope
    reasoning_mode: ReasoningMode
    output_schema_ref: str
    proposal_only: bool
    repository_write_allowed: bool
    manuscript_prose_allowed: bool
    network_mode: NetworkMode
    contains_secrets: bool


@dataclass(frozen=True)
class VerifiedOwnerExecutionAuthorization:
    authorization_ref: str
    operation_id: str
    operation_kind: OperationKind
    provider_execution_allowed: bool
    editorial_prep_agent_allowed: bool
    private_content_allowed: bool
    current: bool = True


@dataclass(frozen=True)
class VerifiedCostAuthorization:
    authorization_ref: str
    operation_id: str
    currency: str
    max_cost_usd: float
    current: bool = True


@dataclass(frozen=True)
class ProductionRouteRequest:
    operation_id: str
    operation_kind: OperationKind
    selected_execution_class: ExecutionClass
    downstream_blast_radius: BlastRadius
    provider_execution_requested: bool
    use_editorial_prep_agent: bool
    routing_choice: RoutingChoice | None
    owner_authorization_ref: str | None
    cost_authorization_ref: str | None
    max_cost_usd: float | None
    prep_bundle: EditorialPrepBundle | None
    agent_lane_available: bool
    agent_capability_enabled: bool


@dataclass(frozen=True)
class ProductionRoutingFinding:
    code: str
    message: str
    object_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProductionRouteResult:
    qualified: bool
    operation_id: str
    operation_kind: OperationKind
    provider: str | None
    model: str | None
    execution_route_ref: str
    provider_execution_requested: bool
    execution_authorization_ref: str | None
    cost_authorization_ref: str | None
    agent_dispatch_ready: bool
    findings: tuple[ProductionRoutingFinding, ...]


@dataclass(frozen=True)
class ProductionRouteVerification:
    valid: bool
    reason: str | None
    current_result: ProductionRouteResult


def _finding(
    code: str,
    message: str,
    *object_refs: str,
) -> ProductionRoutingFinding:
    return ProductionRoutingFinding(
        code=code,
        message=message,
        object_refs=tuple(object_refs),
    )


def _json_strings(values: tuple[str, ...]) -> list[JSONValue]:
    result: list[JSONValue] = []
    for value in sorted(values):
        result.append(value)
    return result


def _bundle_payload(bundle: EditorialPrepBundle) -> dict[str, JSONValue]:
    return {
        "task_id": bundle.task_id,
        "project_id": bundle.project_id,
        "series_id": bundle.series_id,
        "book_id": bundle.book_id,
        "authority_refs": _json_strings(bundle.authority_refs),
        "task": bundle.task,
        "allowed_outputs": _json_strings(bundle.allowed_outputs),
        "forbidden_actions": _json_strings(bundle.forbidden_actions),
        "source_packet_refs": _json_strings(bundle.source_packet_refs),
        "private_content_scope": bundle.private_content_scope,
        "reasoning_mode": bundle.reasoning_mode,
        "output_schema_ref": bundle.output_schema_ref,
        "proposal_only": bundle.proposal_only,
        "repository_write_allowed": bundle.repository_write_allowed,
        "manuscript_prose_allowed": bundle.manuscript_prose_allowed,
        "network_mode": bundle.network_mode,
        "contains_secrets": bundle.contains_secrets,
    }


def editorial_prep_bundle_ref(bundle: EditorialPrepBundle) -> str:
    return f"editorial-prep-bundle:{content_hash(_bundle_payload(bundle))}"


def _routing_choice_payload(choice: RoutingChoice | None) -> JSONValue:
    if choice is None:
        return None
    return {
        "provider": choice.provider,
        "provider_label": choice.provider_label,
        "model": choice.model,
        "selection_mode": choice.selection_mode,
        "selection_scope": choice.selection_scope,
        "operation": choice.operation,
        "rationale": choice.rationale,
    }


def _owner_authorization_payload(
    authorization: VerifiedOwnerExecutionAuthorization | None,
) -> JSONValue:
    if authorization is None:
        return None
    return {
        "authorization_ref": authorization.authorization_ref,
        "operation_id": authorization.operation_id,
        "operation_kind": authorization.operation_kind,
        "provider_execution_allowed": authorization.provider_execution_allowed,
        "editorial_prep_agent_allowed": authorization.editorial_prep_agent_allowed,
        "private_content_allowed": authorization.private_content_allowed,
        "current": authorization.current,
    }


def _cost_authorization_payload(
    authorization: VerifiedCostAuthorization | None,
) -> JSONValue:
    if authorization is None:
        return None
    return {
        "authorization_ref": authorization.authorization_ref,
        "operation_id": authorization.operation_id,
        "currency": authorization.currency,
        "max_cost_usd": authorization.max_cost_usd,
        "current": authorization.current,
    }


def _policy_payload(policy: ProductionRoutingPolicy) -> dict[str, JSONValue]:
    return {
        "max_operation_cost_usd": policy.max_operation_cost_usd,
        "allowed_agent_operations": _json_strings(tuple(policy.allowed_agent_operations)),
        "require_owner_authorization_for_provider": (
            policy.require_owner_authorization_for_provider
        ),
        "require_cost_authorization_for_provider": (policy.require_cost_authorization_for_provider),
        "require_owner_authorization_for_private_content": (
            policy.require_owner_authorization_for_private_content
        ),
    }


def _request_payload(
    request: ProductionRouteRequest,
    policy: ProductionRoutingPolicy,
    owner_authorization: VerifiedOwnerExecutionAuthorization | None,
    cost_authorization: VerifiedCostAuthorization | None,
) -> dict[str, JSONValue]:
    return {
        "operation_id": request.operation_id,
        "operation_kind": request.operation_kind,
        "selected_execution_class": request.selected_execution_class,
        "downstream_blast_radius": request.downstream_blast_radius,
        "provider_execution_requested": request.provider_execution_requested,
        "use_editorial_prep_agent": request.use_editorial_prep_agent,
        "routing_choice": _routing_choice_payload(request.routing_choice),
        "owner_authorization_ref": request.owner_authorization_ref,
        "cost_authorization_ref": request.cost_authorization_ref,
        "owner_authorization": _owner_authorization_payload(owner_authorization),
        "cost_authorization": _cost_authorization_payload(cost_authorization),
        "max_cost_usd": request.max_cost_usd,
        "prep_bundle_ref": (
            editorial_prep_bundle_ref(request.prep_bundle)
            if request.prep_bundle is not None
            else None
        ),
        "agent_lane_available": request.agent_lane_available,
        "agent_capability_enabled": request.agent_capability_enabled,
        "policy": _policy_payload(policy),
    }


def _validate_unique_nonempty(
    values: tuple[str, ...],
    *,
    code_prefix: str,
    findings: list[ProductionRoutingFinding],
) -> None:
    if any(not value.strip() for value in values):
        findings.append(
            _finding(
                f"{code_prefix}.EMPTY",
                "list contains a blank value",
            )
        )
    if len(set(values)) != len(values):
        findings.append(
            _finding(
                f"{code_prefix}.DUPLICATE",
                "list contains duplicate values",
            )
        )


def _validate_prep_bundle(
    *,
    bundle: EditorialPrepBundle,
    current_authority_refs: tuple[str, ...],
    request: ProductionRouteRequest,
    policy: ProductionRoutingPolicy,
    verified_owner_authorizations: Mapping[str, VerifiedOwnerExecutionAuthorization],
    findings: list[ProductionRoutingFinding],
) -> None:
    if bundle.private_content_scope not in _VALID_PRIVATE_SCOPES:
        findings.append(
            _finding(
                "ROUTING.AGENT.BUNDLE.PRIVATE_SCOPE_UNKNOWN",
                f"unknown private content scope {bundle.private_content_scope}",
            )
        )
    if bundle.network_mode not in _VALID_NETWORK_MODES:
        findings.append(
            _finding(
                "ROUTING.AGENT.BUNDLE.NETWORK_MODE_UNKNOWN",
                f"unknown network mode {bundle.network_mode}",
            )
        )
    if bundle.reasoning_mode not in _VALID_REASONING_MODES:
        findings.append(
            _finding(
                "ROUTING.AGENT.BUNDLE.REASONING_MODE_UNKNOWN",
                f"unknown reasoning mode {bundle.reasoning_mode}",
            )
        )

    for field_name, value in (
        ("TASK_ID", bundle.task_id),
        ("PROJECT_ID", bundle.project_id),
        ("TASK", bundle.task),
        ("OUTPUT_SCHEMA_REF", bundle.output_schema_ref),
    ):
        if not value.strip():
            findings.append(
                _finding(
                    f"ROUTING.AGENT.BUNDLE.{field_name}_MISSING",
                    f"editorial-prep bundle {field_name.lower()} must not be blank",
                )
            )

    _validate_unique_nonempty(
        bundle.authority_refs,
        code_prefix="ROUTING.AGENT.BUNDLE.AUTHORITY_REFS",
        findings=findings,
    )
    _validate_unique_nonempty(
        bundle.allowed_outputs,
        code_prefix="ROUTING.AGENT.BUNDLE.ALLOWED_OUTPUTS",
        findings=findings,
    )
    _validate_unique_nonempty(
        bundle.forbidden_actions,
        code_prefix="ROUTING.AGENT.BUNDLE.FORBIDDEN_ACTIONS",
        findings=findings,
    )
    _validate_unique_nonempty(
        bundle.source_packet_refs,
        code_prefix="ROUTING.AGENT.BUNDLE.SOURCE_PACKET_REFS",
        findings=findings,
    )

    if tuple(sorted(set(bundle.authority_refs))) != tuple(sorted(set(current_authority_refs))):
        findings.append(
            _finding(
                "ROUTING.AGENT.BUNDLE.AUTHORITY_STALE",
                "editorial-prep bundle does not bind the exact current authority set",
            )
        )
    if not bundle.allowed_outputs:
        findings.append(
            _finding(
                "ROUTING.AGENT.BUNDLE.ALLOWED_OUTPUTS_MISSING",
                "editorial-prep agent requires an explicit output allowlist",
            )
        )
    missing_forbidden = sorted(_REQUIRED_AGENT_FORBIDDEN_ACTIONS - set(bundle.forbidden_actions))
    for action in missing_forbidden:
        findings.append(
            _finding(
                "ROUTING.AGENT.BUNDLE.FORBIDDEN_ACTION_MISSING",
                f"editorial-prep bundle must forbid {action}",
                action,
            )
        )
    if not bundle.proposal_only:
        findings.append(
            _finding(
                "ROUTING.AGENT.BUNDLE.NOT_PROPOSAL_ONLY",
                "editorial-prep outputs must import as proposals only",
            )
        )
    if bundle.repository_write_allowed:
        findings.append(
            _finding(
                "ROUTING.AGENT.BUNDLE.REPOSITORY_WRITE_FORBIDDEN",
                "editorial-prep agent may not write repository state",
            )
        )
    if bundle.manuscript_prose_allowed:
        findings.append(
            _finding(
                "ROUTING.AGENT.BUNDLE.MANUSCRIPT_PROSE_FORBIDDEN",
                "editorial-prep agent may not draft manuscript prose",
            )
        )
    if bundle.contains_secrets:
        findings.append(
            _finding(
                "ROUTING.AGENT.BUNDLE.SECRET_MATERIAL_DETECTED",
                "secrets/credentials may not enter editorial-prep input",
            )
        )
    if bundle.network_mode == "SOURCE_PACKET_ONLY" and not bundle.source_packet_refs:
        findings.append(
            _finding(
                "ROUTING.AGENT.BUNDLE.SOURCE_PACKET_REQUIRED",
                "SOURCE_PACKET_ONLY mode requires explicit source packet refs",
            )
        )
    if bundle.network_mode == "DISABLED" and bundle.source_packet_refs:
        findings.append(
            _finding(
                "ROUTING.AGENT.BUNDLE.SOURCE_PACKET_WITH_DISABLED_NETWORK",
                ("source packets may be supplied only under SOURCE_PACKET_ONLY network mode"),
            )
        )
    if (
        policy.require_owner_authorization_for_private_content
        and bundle.private_content_scope != "NONE"
    ):
        owner_ref = request.owner_authorization_ref
        owner_authorization = (
            verified_owner_authorizations.get(owner_ref) if owner_ref is not None else None
        )
        if (
            owner_authorization is None
            or not owner_authorization.current
            or not owner_authorization.private_content_allowed
        ):
            findings.append(
                _finding(
                    "ROUTING.AGENT.PRIVATE_CONTENT_OWNER_AUTH_MISSING",
                    "private editorial content requires current Owner authorization",
                )
            )


def evaluate_production_route(
    *,
    request: ProductionRouteRequest,
    policy: ProductionRoutingPolicy,
    current_authority_refs: tuple[str, ...],
    verified_owner_authorizations: Mapping[str, VerifiedOwnerExecutionAuthorization],
    verified_cost_authorizations: Mapping[str, VerifiedCostAuthorization],
) -> ProductionRouteResult:
    findings: list[ProductionRoutingFinding] = []
    owner_authorization = (
        verified_owner_authorizations.get(request.owner_authorization_ref)
        if request.owner_authorization_ref is not None
        else None
    )
    cost_authorization = (
        verified_cost_authorizations.get(request.cost_authorization_ref)
        if request.cost_authorization_ref is not None
        else None
    )

    if request.downstream_blast_radius not in _VALID_BLAST_RADIUS:
        findings.append(
            _finding(
                "ROUTING.BLAST_RADIUS_UNKNOWN",
                f"unknown downstream blast radius {request.downstream_blast_radius}",
            )
        )

    if not request.operation_id.strip():
        findings.append(
            _finding(
                "ROUTING.OPERATION_ID_MISSING",
                "operation_id must not be blank",
            )
        )
    minimum_class = _OPERATION_MINIMUM.get(request.operation_kind)
    if minimum_class is None:
        findings.append(
            _finding(
                "ROUTING.OPERATION_KIND_UNKNOWN",
                f"unknown operation kind {request.operation_kind}",
            )
        )
    if request.selected_execution_class not in _CLASS_ORDER:
        findings.append(
            _finding(
                "ROUTING.EXECUTION_CLASS_UNKNOWN",
                f"unknown execution class {request.selected_execution_class}",
            )
        )
    elif minimum_class is not None and (
        _CLASS_ORDER[request.selected_execution_class] < _CLASS_ORDER[minimum_class]
    ):
        findings.append(
            _finding(
                "ROUTING.EXECUTION_CLASS_TOO_LOW",
                (
                    f"{request.operation_kind} requires at least {minimum_class}, "
                    f"got {request.selected_execution_class}"
                ),
            )
        )

    if policy.max_operation_cost_usd < 0:
        findings.append(
            _finding(
                "ROUTING.POLICY.COST_CAP_INVALID",
                "max_operation_cost_usd cannot be negative",
            )
        )
    if len(set(policy.allowed_agent_operations)) != len(policy.allowed_agent_operations):
        findings.append(
            _finding(
                "ROUTING.POLICY.DUPLICATE_AGENT_OPERATION",
                "allowed agent operation list contains duplicates",
            )
        )
    for operation in policy.allowed_agent_operations:
        if operation not in _OPERATION_MINIMUM:
            findings.append(
                _finding(
                    "ROUTING.POLICY.AGENT_OPERATION_UNKNOWN",
                    f"unknown allowed agent operation {operation}",
                )
            )

    if request.selected_execution_class == "A_LOCAL":
        if request.provider_execution_requested:
            findings.append(
                _finding(
                    "ROUTING.LOCAL.PROVIDER_EXECUTION_FORBIDDEN",
                    "Class A local operation must not call a provider",
                )
            )
        if request.routing_choice is not None:
            findings.append(
                _finding(
                    "ROUTING.LOCAL.ROUTING_CHOICE_UNEXPECTED",
                    "Class A local operation must not carry provider routing choice",
                )
            )
        if request.use_editorial_prep_agent:
            findings.append(
                _finding(
                    "ROUTING.LOCAL.AGENT_FORBIDDEN",
                    "Class A local operation must not use editorial agent",
                )
            )

    if request.provider_execution_requested:
        choice = request.routing_choice
        if choice is None:
            findings.append(
                _finding(
                    "ROUTING.PROVIDER.ROUTING_CHOICE_MISSING",
                    "provider execution requires existing BOOK OS RoutingChoice",
                )
            )
        else:
            if choice.operation != request.operation_kind:
                findings.append(
                    _finding(
                        "ROUTING.PROVIDER.OPERATION_MISMATCH",
                        (
                            f"RoutingChoice operation {choice.operation} differs "
                            f"from {request.operation_kind}"
                        ),
                    )
                )
            if not choice.provider.strip() or not choice.model.strip():
                findings.append(
                    _finding(
                        "ROUTING.PROVIDER.MODEL_ROUTE_INCOMPLETE",
                        "RoutingChoice provider/model must be non-empty",
                    )
                )
        if policy.require_owner_authorization_for_provider:
            if owner_authorization is None:
                findings.append(
                    _finding(
                        "ROUTING.PROVIDER.OWNER_AUTH_UNVERIFIED",
                        "provider execution requires verified Owner authorization",
                    )
                )
            else:
                if owner_authorization.authorization_ref != request.owner_authorization_ref:
                    findings.append(
                        _finding(
                            "ROUTING.PROVIDER.OWNER_AUTH_REF_MISMATCH",
                            "Owner authorization catalog identity mismatch",
                            owner_authorization.authorization_ref,
                        )
                    )
                if not owner_authorization.current:
                    findings.append(
                        _finding(
                            "ROUTING.PROVIDER.OWNER_AUTH_STALE",
                            "Owner execution authorization is not current",
                            owner_authorization.authorization_ref,
                        )
                    )
                if (
                    owner_authorization.operation_id != request.operation_id
                    or owner_authorization.operation_kind != request.operation_kind
                ):
                    findings.append(
                        _finding(
                            "ROUTING.PROVIDER.OWNER_AUTH_OPERATION_MISMATCH",
                            "Owner authorization belongs to another operation",
                            owner_authorization.authorization_ref,
                        )
                    )
                if not owner_authorization.provider_execution_allowed:
                    findings.append(
                        _finding(
                            "ROUTING.PROVIDER.OWNER_AUTH_PROVIDER_DENIED",
                            "Owner authorization does not permit provider execution",
                            owner_authorization.authorization_ref,
                        )
                    )
                if (
                    request.use_editorial_prep_agent
                    and not owner_authorization.editorial_prep_agent_allowed
                ):
                    findings.append(
                        _finding(
                            "ROUTING.AGENT.OWNER_AUTH_AGENT_DENIED",
                            "Owner authorization does not permit EDITORIAL_PREP agent",
                            owner_authorization.authorization_ref,
                        )
                    )
        if policy.require_cost_authorization_for_provider:
            if cost_authorization is None:
                findings.append(
                    _finding(
                        "ROUTING.PROVIDER.COST_AUTH_UNVERIFIED",
                        "provider execution requires verified bounded cost authorization",
                    )
                )
            else:
                if cost_authorization.authorization_ref != request.cost_authorization_ref:
                    findings.append(
                        _finding(
                            "ROUTING.PROVIDER.COST_AUTH_REF_MISMATCH",
                            "cost authorization catalog identity mismatch",
                            cost_authorization.authorization_ref,
                        )
                    )
                if cost_authorization.max_cost_usd < 0:
                    findings.append(
                        _finding(
                            "ROUTING.PROVIDER.COST_AUTH_CAP_INVALID",
                            "authorized max_cost_usd cannot be negative",
                            cost_authorization.authorization_ref,
                        )
                    )
                if not cost_authorization.current:
                    findings.append(
                        _finding(
                            "ROUTING.PROVIDER.COST_AUTH_STALE",
                            "cost authorization is not current",
                            cost_authorization.authorization_ref,
                        )
                    )
                if cost_authorization.operation_id != request.operation_id:
                    findings.append(
                        _finding(
                            "ROUTING.PROVIDER.COST_AUTH_OPERATION_MISMATCH",
                            "cost authorization belongs to another operation",
                            cost_authorization.authorization_ref,
                        )
                    )
                if cost_authorization.currency != "USD":
                    findings.append(
                        _finding(
                            "ROUTING.PROVIDER.COST_AUTH_CURRENCY_INVALID",
                            "cost authorization currency must be USD",
                            cost_authorization.authorization_ref,
                        )
                    )
        if request.max_cost_usd is None:
            findings.append(
                _finding(
                    "ROUTING.PROVIDER.COST_CAP_MISSING",
                    "provider execution requires explicit max_cost_usd",
                )
            )
        elif request.max_cost_usd < 0:
            findings.append(
                _finding(
                    "ROUTING.PROVIDER.COST_CAP_INVALID",
                    "max_cost_usd cannot be negative",
                )
            )
        elif request.max_cost_usd > policy.max_operation_cost_usd:
            findings.append(
                _finding(
                    "ROUTING.PROVIDER.COST_CAP_EXCEEDS_POLICY",
                    (
                        f"requested cap {request.max_cost_usd} exceeds policy "
                        f"{policy.max_operation_cost_usd}"
                    ),
                )
            )
        if (
            request.max_cost_usd is not None
            and cost_authorization is not None
            and request.max_cost_usd > cost_authorization.max_cost_usd
        ):
            findings.append(
                _finding(
                    "ROUTING.PROVIDER.COST_CAP_EXCEEDS_AUTHORIZATION",
                    (
                        f"requested cap {request.max_cost_usd} exceeds authorized "
                        f"{cost_authorization.max_cost_usd}"
                    ),
                    cost_authorization.authorization_ref,
                )
            )
    else:
        if request.routing_choice is not None:
            findings.append(
                _finding(
                    "ROUTING.NO_PROVIDER.ROUTING_CHOICE_UNEXPECTED",
                    "no-provider operation should not carry RoutingChoice",
                )
            )
        if request.max_cost_usd not in {None, 0}:
            findings.append(
                _finding(
                    "ROUTING.NO_PROVIDER.COST_UNEXPECTED",
                    "no-provider operation must not reserve provider spend",
                )
            )

    agent_dispatch_ready = False
    if request.use_editorial_prep_agent:
        if minimum_class != "C_PREMIUM":
            findings.append(
                _finding(
                    "ROUTING.AGENT.OPERATION_CLASS_INVALID",
                    (
                        "EDITORIAL_PREP agent may only execute operations whose "
                        "minimum class is C_PREMIUM"
                    ),
                )
            )
        if request.selected_execution_class != "C_PREMIUM":
            findings.append(
                _finding(
                    "ROUTING.AGENT.CLASS_INVALID",
                    "EDITORIAL_PREP agent is reserved for Class C operations",
                )
            )
        if request.operation_kind not in set(policy.allowed_agent_operations):
            findings.append(
                _finding(
                    "ROUTING.AGENT.OPERATION_NOT_ALLOWED",
                    (f"operation {request.operation_kind} is not in the editorial agent allowlist"),
                )
            )
        if (
            owner_authorization is None
            or not owner_authorization.current
            or owner_authorization.operation_id != request.operation_id
            or owner_authorization.operation_kind != request.operation_kind
        ):
            findings.append(
                _finding(
                    "ROUTING.AGENT.EXPLICIT_OWNER_AUTH_INVALID",
                    "EDITORIAL_PREP agent requires exact current Owner authorization",
                )
            )
        elif not owner_authorization.editorial_prep_agent_allowed:
            findings.append(
                _finding(
                    "ROUTING.AGENT.EXPLICIT_OWNER_AUTH_DENIED",
                    "Owner authorization does not permit EDITORIAL_PREP agent",
                    owner_authorization.authorization_ref,
                )
            )

        if not request.agent_lane_available:
            findings.append(
                _finding(
                    "ROUTING.AGENT.LANE_UNAVAILABLE",
                    "BOOK OS Agents API lane is not currently available",
                )
            )
        if not request.agent_capability_enabled:
            findings.append(
                _finding(
                    "ROUTING.AGENT.CAPABILITY_DISABLED",
                    "editorial-prep agent kill switch/capability is disabled",
                )
            )
        if not request.provider_execution_requested:
            findings.append(
                _finding(
                    "ROUTING.AGENT.PROVIDER_EXECUTION_REQUIRED",
                    "agent dispatch requires an explicitly authorized provider execution",
                )
            )
        if request.prep_bundle is None:
            findings.append(
                _finding(
                    "ROUTING.AGENT.BUNDLE_MISSING",
                    "agent dispatch requires EditorialPrepBundle",
                )
            )
        else:
            _validate_prep_bundle(
                bundle=request.prep_bundle,
                current_authority_refs=current_authority_refs,
                request=request,
                policy=policy,
                verified_owner_authorizations=verified_owner_authorizations,
                findings=findings,
            )
    elif request.prep_bundle is not None:
        findings.append(
            _finding(
                "ROUTING.AGENT.BUNDLE_WITHOUT_AGENT",
                "EditorialPrepBundle must not be attached to a non-agent operation",
            )
        )

    payload = _request_payload(
        request,
        policy,
        owner_authorization,
        cost_authorization,
    )
    route_ref = f"mystery-production-route:{content_hash(payload)}"
    qualified = not findings
    if request.use_editorial_prep_agent and qualified:
        agent_dispatch_ready = True
    choice = request.routing_choice
    return ProductionRouteResult(
        qualified=qualified,
        operation_id=request.operation_id,
        operation_kind=request.operation_kind,
        provider=choice.provider if choice is not None else None,
        model=choice.model if choice is not None else None,
        execution_route_ref=route_ref,
        provider_execution_requested=request.provider_execution_requested,
        execution_authorization_ref=(
            request.owner_authorization_ref
            if qualified and request.provider_execution_requested
            else None
        ),
        cost_authorization_ref=(
            request.cost_authorization_ref
            if qualified and request.provider_execution_requested
            else None
        ),
        agent_dispatch_ready=agent_dispatch_ready,
        findings=tuple(findings),
    )


def verify_production_route(
    *,
    prior_execution_route_ref: str,
    request: ProductionRouteRequest,
    policy: ProductionRoutingPolicy,
    current_authority_refs: tuple[str, ...],
    verified_owner_authorizations: Mapping[str, VerifiedOwnerExecutionAuthorization],
    verified_cost_authorizations: Mapping[str, VerifiedCostAuthorization],
) -> ProductionRouteVerification:
    current = evaluate_production_route(
        request=request,
        policy=policy,
        current_authority_refs=current_authority_refs,
        verified_owner_authorizations=verified_owner_authorizations,
        verified_cost_authorizations=verified_cost_authorizations,
    )
    if not current.qualified:
        return ProductionRouteVerification(
            valid=False,
            reason="CURRENT_PRODUCTION_ROUTE_BLOCKED",
            current_result=current,
        )
    if current.execution_route_ref != prior_execution_route_ref:
        return ProductionRouteVerification(
            valid=False,
            reason="PRODUCTION_ROUTE_SNAPSHOT_CHANGED",
            current_result=current,
        )
    return ProductionRouteVerification(
        valid=True,
        reason=None,
        current_result=current,
    )
