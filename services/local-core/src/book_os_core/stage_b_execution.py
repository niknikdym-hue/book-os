"""Bounded Stage B execution using the accepted M8 provider adapters.

Real provider execution remains Owner-gated. Tests inject MockTransport while
exercising the same adapters, budget transport, persistence, and plan binding.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import time
from typing import Any, Literal

import httpx

from .model_gateway import ModelOutputError, ModelProviderError, ModelTaskRequest
from .prompts import PromptTemplate
from .provider_lane import ProviderLaneService
from .secrets import SecretStore
from .stage_b import (
    StageBPlan,
    StageBPreflightService,
    StageBProviderRuntime,
    build_provider_runtime,
    require_authorized_execution,
)

ProbeOutcome = Literal["SUCCESS", "REFUSAL", "UNAVAILABLE", "ERROR"]


@dataclass(frozen=True)
class StageBGenerationCase:
    case_id: str
    role: str
    request: ModelTaskRequest
    prompt: PromptTemplate


@dataclass(frozen=True)
class StageBCaseEvidence:
    case_id: str
    role: str
    probe_id: str
    external_request_id: str | None
    configured_model: str
    returned_model_version: str | None
    latency_ms: int
    usage: dict[str, Any]
    cost: dict[str, Any]

    def public_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "role": self.role,
            "probe_id": self.probe_id,
            "external_request_id": self.external_request_id,
            "configured_model": self.configured_model,
            "returned_model_version": self.returned_model_version,
            "latency_ms": self.latency_ms,
            "usage": dict(self.usage),
            "cost": dict(self.cost),
        }


@dataclass(frozen=True)
class StageBExecutionResult:
    state: str
    plan_hash: str
    provider: str
    model: str
    config_id: str
    cases: tuple[StageBCaseEvidence, ...]
    budget_usage: dict[str, object]

    def public_dict(self) -> dict[str, object]:
        return {
            "state": self.state,
            "plan_hash": self.plan_hash,
            "provider": self.provider,
            "model": self.model,
            "config_id": self.config_id,
            "cases": [item.public_dict() for item in self.cases],
            "budget_usage": dict(self.budget_usage),
        }


def _normalize_failure(exc: Exception) -> ProbeOutcome:
    message = str(exc).casefold()
    if any(token in message for token in ("refusal", "blacklist", "content_filter")):
        return "REFUSAL"
    if any(token in message for token in ("429", "503", "unavailable", "timeout")):
        return "UNAVAILABLE"
    return "ERROR"


def _cost_metadata(usage: dict[str, Any], runtime: StageBProviderRuntime) -> dict[str, Any]:
    raw = usage.get("cost_usd")
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        value = float(raw)
        runtime.ledger.record_actual_cost(value)
        return {"state": "KNOWN", "currency": "USD", "amount": value}
    return {"state": "UNKNOWN"}


def execute_generation_cases(
    *,
    preflight: StageBPreflightService,
    plan: StageBPlan,
    authorized_plan_hash: str,
    lane: ProviderLaneService,
    secrets: SecretStore,
    cases: tuple[StageBGenerationCase, ...],
    transport: httpx.BaseTransport | None = None,
    ca_bundle: str | None = None,
) -> StageBExecutionResult:
    """Execute exact bounded role cases and persist LIVE evidence without promotion."""

    require_authorized_execution(
        preflight,
        plan,
        authorized_plan_hash=authorized_plan_hash,
    )
    if not cases:
        raise ValueError("Stage B execution requires at least one bounded generation case")

    allowed_roles = set(plan.candidate.roles)
    seen_ids: set[str] = set()
    for case in cases:
        if not case.case_id or case.case_id in seen_ids:
            raise ValueError("Stage B case IDs must be non-empty and unique")
        seen_ids.add(case.case_id)
        if case.role not in allowed_roles or case.request.role != case.role:
            raise ValueError("Stage B case role is not authorized by the accepted plan")

    runtime = build_provider_runtime(
        plan,
        secrets,
        transport=transport,
        ca_bundle=ca_bundle,
    )
    evidence: list[StageBCaseEvidence] = []
    try:
        for case in cases:
            request = case.request.model_copy(
                update={
                    "provider": plan.candidate.provider,
                    "model": plan.generation_execution_model,
                }
            )
            started = time.perf_counter()
            try:
                result = runtime.generation.generate(request, case.prompt)
            except (ModelProviderError, ModelOutputError) as exc:
                latency_ms = max(0, int((time.perf_counter() - started) * 1000))
                lane.record_probe(
                    provider=plan.candidate.provider,
                    model=plan.candidate.model,
                    config_id=plan.candidate.config_id,
                    region=plan.candidate.region,
                    capability=f"generation:{case.role}:{case.case_id}",
                    outcome=_normalize_failure(exc),
                    probe_type="LIVE",
                    latency_ms=latency_ms,
                    usage={},
                    cost={"state": "UNKNOWN"},
                )
                raise

            latency_ms = max(0, int((time.perf_counter() - started) * 1000))
            usage = dict(result.usage)
            returned_model = usage.get("model_version")
            if returned_model is not None:
                returned_model = str(returned_model)
            usage.setdefault("policy_model", plan.candidate.model)
            usage.setdefault("configured_model", plan.generation_execution_model)
            usage["case_id"] = case.case_id
            usage["role"] = case.role
            cost = _cost_metadata(usage, runtime)
            probe_id = lane.record_probe(
                provider=plan.candidate.provider,
                model=plan.candidate.model,
                config_id=plan.candidate.config_id,
                region=plan.candidate.region,
                capability=f"generation:{case.role}:{case.case_id}",
                outcome="SUCCESS",
                probe_type="LIVE",
                latency_ms=latency_ms,
                usage=usage,
                cost=cost,
                external_request_id=result.provider_run_id,
            )
            evidence.append(
                StageBCaseEvidence(
                    case_id=case.case_id,
                    role=case.role,
                    probe_id=probe_id,
                    external_request_id=result.provider_run_id,
                    configured_model=plan.generation_execution_model,
                    returned_model_version=returned_model,
                    latency_ms=latency_ms,
                    usage=usage,
                    cost=cost,
                )
            )
    finally:
        runtime.close()

    return StageBExecutionResult(
        state="EVIDENCE_AWAITING_OWNER_DECISION",
        plan_hash=plan.plan_hash,
        provider=plan.candidate.provider,
        model=plan.candidate.model,
        config_id=plan.candidate.config_id,
        cases=tuple(evidence),
        budget_usage=runtime.ledger.public_dict(),
    )


def assert_secret_safe_execution(
    result: StageBExecutionResult, secret_values: tuple[str, ...]
) -> None:
    serialized = json.dumps(result.public_dict(), sort_keys=True, ensure_ascii=True)
    for value in secret_values:
        if value and value in serialized:
            raise RuntimeError("Stage B public evidence contains a provider secret")
