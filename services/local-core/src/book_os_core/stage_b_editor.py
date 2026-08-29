"""Synthetic M8 Stage B EDITOR evidence without granting manuscript authority."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import time
from typing import Any

import httpx

from .bookbench import BookBenchService
from .drafting import DraftSectionRequest, DraftingService
from .editorial import EditorialService, FindingCreateRequest, ProposalCreateRequest
from .model_gateway import (
    AuthorityInputRef,
    ModelAdapterResult,
    ModelGateway,
    ModelTaskRequest,
)
from .prompts import SECTION_DRAFT_V1, PromptTemplate
from .provider_lane import ProviderLaneService
from .secrets import SecretStore
from .stage_b import (
    StageBPlan,
    StageBPreflightService,
    build_provider_runtime,
    require_authorized_execution,
)
from .stage_b_bookbench import STAGE_B_FIXTURE_VERSION, fixture_hash, prepare_synthetic_project

_EDITOR_MARKER_DIAGNOSIS = "DIAGNOSIS:"
_EDITOR_MARKER_PROPOSAL = "PROPOSAL:"


@dataclass(frozen=True)
class StageBEditorEvidence:
    source_book_id: str
    source_unit_id: str
    source_revision_id: str
    source_revision_hash: str
    finding_id: str
    proposal_id: str
    candidate_probe_id: str
    artifact_hash: str
    evaluation_book_id: str
    evaluation_snapshot_id: str
    evaluation_snapshot_hash: str
    deterministic_evaluation_ids: tuple[str, ...]
    provider: str
    configured_model: str
    returned_model_version: str | None
    config_id: str
    provider_run_id: str | None
    plan_hash: str
    budget_usage: dict[str, object]

    def public_dict(self) -> dict[str, object]:
        return {
            "source_book_id": self.source_book_id,
            "source_unit_id": self.source_unit_id,
            "source_revision_id": self.source_revision_id,
            "source_revision_hash": self.source_revision_hash,
            "finding_id": self.finding_id,
            "proposal_id": self.proposal_id,
            "candidate_probe_id": self.candidate_probe_id,
            "artifact_hash": self.artifact_hash,
            "evaluation_book_id": self.evaluation_book_id,
            "evaluation_snapshot_id": self.evaluation_snapshot_id,
            "evaluation_snapshot_hash": self.evaluation_snapshot_hash,
            "deterministic_evaluation_ids": list(self.deterministic_evaluation_ids),
            "provider": self.provider,
            "configured_model": self.configured_model,
            "returned_model_version": self.returned_model_version,
            "config_id": self.config_id,
            "provider_run_id": self.provider_run_id,
            "plan_hash": self.plan_hash,
            "budget_usage": dict(self.budget_usage),
        }


class _ReplayAdapter:
    """Persist the exact editor artifact through normal DraftingService with zero HTTP calls."""

    def __init__(self, provider: str, result: ModelAdapterResult, artifact_text: str) -> None:
        self.provider_name = provider
        self._result = result
        self._artifact_text = artifact_text

    def generate(self, request: ModelTaskRequest, prompt: PromptTemplate) -> ModelAdapterResult:
        _ = (request, prompt)
        return ModelAdapterResult(
            self._result.provider_run_id,
            {"text": self._artifact_text, "notes": ["M8 synthetic EDITOR evaluation artifact"]},
            dict(self._result.usage),
        )


def _parse_editor_artifact(value: str) -> tuple[str, str]:
    if _EDITOR_MARKER_DIAGNOSIS not in value or _EDITOR_MARKER_PROPOSAL not in value:
        raise ValueError("EDITOR fixture output must contain DIAGNOSIS and PROPOSAL markers")
    diagnosis_part, proposal_part = value.split(_EDITOR_MARKER_PROPOSAL, 1)
    diagnosis = diagnosis_part.split(_EDITOR_MARKER_DIAGNOSIS, 1)[1].strip()
    proposal = proposal_part.strip()
    if not diagnosis or not proposal:
        raise ValueError("EDITOR fixture diagnosis and proposal must both be non-empty")
    return diagnosis, proposal


def _artifact_hash(*, diagnosis: str, proposal: str) -> str:
    payload = json.dumps(
        {"diagnosis": diagnosis, "proposal": proposal},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def execute_editor_fixture(
    *,
    data_dir: Path,
    source_book_id: str,
    preflight: StageBPreflightService,
    plan: StageBPlan,
    authorized_plan_hash: str,
    lane: ProviderLaneService,
    secrets: SecretStore,
    transport: httpx.BaseTransport | None = None,
    ca_bundle: str | None = None,
) -> StageBEditorEvidence:
    """Create AI-only M6 finding/proposal and immutable M7 evaluation container."""

    require_authorized_execution(
        preflight,
        plan,
        authorized_plan_hash=authorized_plan_hash,
    )
    if "EDITOR" not in plan.candidate.roles:
        raise ValueError("accepted Stage B plan does not authorize EDITOR")

    source_bench = BookBenchService(data_dir)
    source_snapshot = source_bench.create_snapshot(source_book_id, scope="BOOK")
    source_targets = [
        target for target in source_snapshot.targets if target.target_kind == "MANUSCRIPT_UNIT"
    ]
    if not source_targets:
        raise ValueError("EDITOR fixture requires at least one current source manuscript unit")
    source = source_targets[0]

    runtime = build_provider_runtime(
        plan,
        secrets,
        transport=transport,
        ca_bundle=ca_bundle,
    )
    try:
        request = ModelTaskRequest(
            task_id=f"m8-editor-{source.revision_id}",
            task_type="SECTION_DRAFT",
            role="EDITOR",
            provider=plan.candidate.provider,
            model=plan.candidate.model,
            prompt_id=SECTION_DRAFT_V1.prompt_id,
            prompt_version=SECTION_DRAFT_V1.version,
            prompt_hash=SECTION_DRAFT_V1.prompt_hash,
            section_objective=(
                "Evaluate the supplied synthetic manuscript only. Return text with exactly two "
                "sections: DIAGNOSIS: a bounded evidence-based diagnosis; PROPOSAL: a minimal "
                "revision that preserves the source authority and invents no external facts."
            ),
            authority_inputs=[
                AuthorityInputRef(
                    revision_id=source.revision_id,
                    revision_hash=source.revision_hash,
                    entity_type="manuscript.unit",
                )
            ],
            authoritative_context={
                "fixture_version": STAGE_B_FIXTURE_VERSION,
                "fixture_hash": fixture_hash(),
                "source_revision_id": source.revision_id,
                "source_revision_hash": source.revision_hash,
            },
            untrusted_context=[source.text],
            max_output_tokens=1200,
        )
        started = time.perf_counter()
        result = runtime.generation.generate(request, SECTION_DRAFT_V1)
        latency_ms = max(0, int((time.perf_counter() - started) * 1000))
        raw_text = result.output.get("text")
        if not isinstance(raw_text, str):
            raise ValueError("EDITOR fixture provider output has no text")
        diagnosis, proposal_text = _parse_editor_artifact(raw_text)
        artifact_hash = _artifact_hash(diagnosis=diagnosis, proposal=proposal_text)
        returned_model = result.usage.get("model_version")
        returned_model_version = str(returned_model) if returned_model is not None else None

        editorial = EditorialService(data_dir)
        finding = editorial.create_finding(
            source_book_id,
            FindingCreateRequest(
                role="DEVELOPMENTAL_EDITOR",
                category="M8_STAGE_B_SYNTHETIC_EDITOR",
                target_kind="MANUSCRIPT_UNIT",
                target_id=source.target_id,
                base_revision_id=source.revision_id,
                base_revision_hash=source.revision_hash,
                diagnosis=diagnosis,
                why="Synthetic Stage B EDITOR quality evidence; no authority decision is implied.",
                evidence={
                    "fixture_version": STAGE_B_FIXTURE_VERSION,
                    "fixture_hash": fixture_hash(),
                    "artifact_hash": artifact_hash,
                    "plan_hash": plan.plan_hash,
                    "provider": plan.candidate.provider,
                    "configured_model": plan.candidate.model,
                    "returned_model_version": returned_model_version,
                    "config_id": plan.candidate.config_id,
                    "provider_run_id": result.provider_run_id,
                },
                severity="MAJOR",
                confidence=0.8,
                expected_effect="Bounded diagnosis and minimal proposal for human review.",
                risks="Synthetic fixture only; proposal remains OPEN and must not be auto-accepted.",
                actor=f"model:{plan.candidate.provider}",
                actor_kind="AI",
                run_id=result.provider_run_id,
            ),
        )
        proposal = editorial.create_manuscript_proposal(
            source_book_id,
            finding.finding_id,
            ProposalCreateRequest(
                proposed_text=proposal_text,
                rationale="Synthetic M8 Stage B EDITOR proposal for evaluation only.",
                actor=f"model:{plan.candidate.provider}",
                actor_kind="AI",
            ),
        )
        if finding.status != "OPEN" or proposal.status != "OPEN":
            raise RuntimeError("Stage B EDITOR evidence must remain OPEN for human review")

        usage: dict[str, Any] = dict(result.usage)
        usage.update(
            {
                "fixture_version": STAGE_B_FIXTURE_VERSION,
                "fixture_hash": fixture_hash(),
                "artifact_hash": artifact_hash,
                "finding_id": finding.finding_id,
                "proposal_id": proposal.proposal_id,
                "role": "EDITOR",
            }
        )
        probe_id = lane.record_probe(
            provider=plan.candidate.provider,
            model=plan.candidate.model,
            config_id=plan.candidate.config_id,
            region=plan.candidate.region,
            capability=f"generation:EDITOR:{source.target_id}",
            outcome="SUCCESS",
            probe_type="LIVE",
            latency_ms=latency_ms,
            usage=usage,
            cost={"state": "UNKNOWN"},
            external_request_id=result.provider_run_id,
        )

        evaluation_project = prepare_synthetic_project(data_dir)
        replay = _ReplayAdapter(plan.candidate.provider, result, raw_text)
        replay_gateway = ModelGateway({plan.candidate.provider: replay})
        replay_drafting = DraftingService(data_dir, replay_gateway)
        replay_drafting.generate_section_draft(
            evaluation_project.book_id,
            evaluation_project.chapter_ids[0],
            DraftSectionRequest(
                section_objective="Persist exact synthetic EDITOR artifact for M7 BookBench evaluation",
                provider=plan.candidate.provider,
                model=plan.candidate.model,
                max_output_tokens=1200,
            ),
        )
        evaluation_bench = BookBenchService(data_dir)
        evaluation_snapshot = evaluation_bench.create_snapshot(
            evaluation_project.book_id, scope="BOOK"
        )
        deterministic = evaluation_bench.run_deterministic_suite(
            evaluation_project.book_id, evaluation_snapshot.snapshot_id
        )
        return StageBEditorEvidence(
            source_book_id=source_book_id,
            source_unit_id=source.target_id,
            source_revision_id=source.revision_id,
            source_revision_hash=source.revision_hash,
            finding_id=finding.finding_id,
            proposal_id=proposal.proposal_id,
            candidate_probe_id=probe_id,
            artifact_hash=artifact_hash,
            evaluation_book_id=evaluation_project.book_id,
            evaluation_snapshot_id=evaluation_snapshot.snapshot_id,
            evaluation_snapshot_hash=evaluation_snapshot.snapshot_hash,
            deterministic_evaluation_ids=tuple(run.evaluation_id for run in deterministic),
            provider=plan.candidate.provider,
            configured_model=plan.candidate.model,
            returned_model_version=returned_model_version,
            config_id=plan.candidate.config_id,
            provider_run_id=result.provider_run_id,
            plan_hash=plan.plan_hash,
            budget_usage=runtime.ledger.public_dict(),
        )
    finally:
        runtime.close()
