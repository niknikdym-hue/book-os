"""Independent Stage B BookBench judge execution over immutable snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import httpx

from .bookbench import BookBenchService
from .model_gateway import ModelAdapter, ModelAdapterResult, ModelGateway, ModelTaskRequest
from .prompts import PromptTemplate
from .provider_lane import ProviderLaneService
from .secrets import SecretStore
from .stage_b import (
    StageBGateError,
    StageBPlan,
    StageBPreflightService,
    build_provider_runtime,
    require_authorized_execution,
)


class _RecordingAdapter:
    def __init__(self, inner: ModelAdapter) -> None:
        self._inner = inner
        self.provider_name = inner.provider_name
        self.results: list[ModelAdapterResult] = []

    def generate(self, request: ModelTaskRequest, prompt: PromptTemplate) -> ModelAdapterResult:
        result = self._inner.generate(request, prompt)
        self.results.append(result)
        return result


@dataclass(frozen=True)
class StageBJudgeEvidence:
    book_id: str
    snapshot_id: str
    subject_identity: dict[str, str]
    judge_identity: dict[str, str]
    evaluation_ids: tuple[str, ...]
    provider_probe_ids: tuple[str, ...]
    dimensions: tuple[str, ...]
    independence_state: str
    blocking_dimensions: tuple[str, ...]
    plan_hash: str
    budget_usage: dict[str, object]

    def public_dict(self) -> dict[str, object]:
        return {
            "book_id": self.book_id,
            "snapshot_id": self.snapshot_id,
            "subject_identity": dict(self.subject_identity),
            "judge_identity": dict(self.judge_identity),
            "evaluation_ids": list(self.evaluation_ids),
            "provider_probe_ids": list(self.provider_probe_ids),
            "dimensions": list(self.dimensions),
            "independence_state": self.independence_state,
            "blocking_dimensions": list(self.blocking_dimensions),
            "plan_hash": self.plan_hash,
            "budget_usage": dict(self.budget_usage),
        }


def execute_independent_judges(
    *,
    data_dir: Path,
    book_id: str,
    snapshot_id: str,
    subject_identity: dict[str, str],
    dimensions: tuple[str, ...],
    preflight: StageBPreflightService,
    plan: StageBPlan,
    authorized_plan_hash: str,
    lane: ProviderLaneService,
    secrets: SecretStore,
    transport: httpx.BaseTransport | None = None,
    ca_bundle: str | None = None,
) -> StageBJudgeEvidence:
    """Run release-grade judge dimensions only with an independent exact config."""

    require_authorized_execution(
        preflight,
        plan,
        authorized_plan_hash=authorized_plan_hash,
    )
    if "EVALUATOR" not in plan.candidate.roles:
        raise StageBGateError("accepted Stage B plan does not authorize EVALUATOR")
    if not dimensions or any(not dimension for dimension in dimensions):
        raise ValueError("Stage B judge dimensions must be non-empty")
    if len(set(dimensions)) != len(dimensions):
        raise ValueError("Stage B judge dimensions must be unique")

    judge_identity = {
        "provider": plan.candidate.provider,
        "model": plan.generation_execution_model,
        "config_id": plan.candidate.config_id,
    }
    independence_state, release_grade = BookBenchService.independence(
        subject_identity, judge_identity
    )
    if not release_grade:
        raise StageBGateError(
            f"release-grade Stage B judge requires independent evidence: {independence_state}"
        )

    runtime = build_provider_runtime(
        plan,
        secrets,
        transport=transport,
        ca_bundle=ca_bundle,
    )
    recording = _RecordingAdapter(runtime.generation)
    gateway = ModelGateway({plan.candidate.provider: recording})
    bookbench = BookBenchService(data_dir, model_gateway=gateway)
    evaluation_ids: list[str] = []
    probe_ids: list[str] = []
    try:
        for dimension in dimensions:
            run = bookbench.run_judge(
                book_id,
                snapshot_id,
                dimension=dimension,
                provider=plan.candidate.provider,
                model=plan.generation_execution_model,
                config_id=plan.candidate.config_id,
                writer=subject_identity,
            )
            if run.independence_state != "INDEPENDENT":
                raise StageBGateError("BookBench judge did not persist INDEPENDENT evidence")
            if len(recording.results) != len(evaluation_ids) + 1:
                raise StageBGateError("judge provider evidence cardinality mismatch")
            provider_result = recording.results[-1]
            usage = dict(run.usage)
            usage["evaluation_id"] = run.evaluation_id
            usage["dimension"] = dimension
            if provider_result.usage.get("model_version") is not None:
                usage["model_version"] = str(provider_result.usage["model_version"])
            probe_ids.append(
                lane.record_probe(
                    provider=plan.candidate.provider,
                    model=plan.candidate.model,
                    config_id=plan.candidate.config_id,
                    region=plan.candidate.region,
                    capability=f"evaluation:EVALUATOR:{dimension}",
                    outcome="SUCCESS",
                    probe_type="LIVE",
                    latency_ms=run.latency_ms,
                    usage=usage,
                    cost={"state": "UNKNOWN"},
                    external_request_id=provider_result.provider_run_id,
                )
            )
            evaluation_ids.append(run.evaluation_id)
        report = bookbench.report(book_id, snapshot_id)
        return StageBJudgeEvidence(
            book_id=book_id,
            snapshot_id=snapshot_id,
            subject_identity=dict(subject_identity),
            judge_identity=judge_identity,
            evaluation_ids=tuple(evaluation_ids),
            provider_probe_ids=tuple(probe_ids),
            dimensions=dimensions,
            independence_state=independence_state,
            blocking_dimensions=tuple(report.blocking_dimensions),
            plan_hash=plan.plan_hash,
            budget_usage=runtime.ledger.public_dict(),
        )
    finally:
        runtime.close()
