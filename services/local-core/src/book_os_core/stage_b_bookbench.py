"""Synthetic M8 Stage B BookBench harness.

The fixture is public, deterministic and contains no owner manuscript. A future
Owner-authorized live run can draft against approved synthetic contracts using
the accepted provider adapter, persist DRAFT manuscript revisions, snapshot
those exact revisions with M7 BookBench and emit reproducible evidence.
"""

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
from .memory_embeddings import EmbeddingGateway
from .model_gateway import ModelGateway
from .projects import (
    BookArchitecturePayload,
    BookContractPayload,
    ChapterContractPayload,
    NewBookRequest,
    ProjectService,
)
from .provider_lane import ProviderLaneService
from .secrets import SecretStore
from .stage_b import (
    StageBPlan,
    StageBPreflightService,
    build_provider_runtime,
    require_authorized_execution,
)

STAGE_B_FIXTURE_VERSION = "m8-stage-b-synthetic-v1"

_STAGE_B_FIXTURE = {
    "version": STAGE_B_FIXTURE_VERSION,
    "working_title": "BOOK OS M8 Synthetic Provider Evaluation",
    "primary_subtype": "Strategy",
    "book_contract": {
        "reader": "Business leaders building a repeatable decision system",
        "reader_problem": "Teams collect advice but cannot distinguish a repeatable operating mechanism from generic prose",
        "central_promise": "A concrete decision loop that can be inspected, tested and improved",
        "central_thesis": "Explicit decision rules and feedback evidence outperform disconnected best-practice lists",
        "unique_angle": "Treat management guidance as a falsifiable operating mechanism rather than inspiration",
        "reader_trajectory": "From generic recommendations to an explicit decision loop with observable evidence",
        "explicit_exclusions": [
            "No bestseller prediction",
            "No invented research claims",
            "No motivational filler",
        ],
        "evidence_policy": "Do not invent external facts; label assumptions and use only supplied synthetic facts",
        "voice_genre_constraints": "Precise Russian-language business nonfiction; concrete, calm, non-promotional",
        "readiness_criteria": [
            "Each chapter advances the central mechanism",
            "Claims are bounded by supplied evidence",
            "No hidden authority approval",
        ],
    },
    "chapters": [
        {
            "title": "Decision Loop",
            "purpose": "Explain how a team turns an ambiguous operational signal into one bounded decision",
            "new_contribution": "A four-step signal-to-decision mechanism",
            "objective": "Write a bounded section explaining a four-step signal-to-decision loop. Use one concrete synthetic example: a software team sees support tickets rise from 20 to 35 per day after a release. Do not invent outside statistics. End with one measurable next decision.",
        },
        {
            "title": "Feedback Evidence",
            "purpose": "Show how the team tests whether the chosen decision improved the operating system",
            "new_contribution": "A feedback rule that separates observation from interpretation",
            "objective": "Write a bounded section showing how the same synthetic team evaluates the decision one week later. Distinguish observed ticket counts from interpretation, avoid invented causes, and specify what evidence would trigger a revision of the decision.",
        },
    ],
}


def fixture_payload() -> dict[str, Any]:
    return json.loads(json.dumps(_STAGE_B_FIXTURE, ensure_ascii=False))


def fixture_hash() -> str:
    raw = json.dumps(
        _STAGE_B_FIXTURE,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class StageBSyntheticProject:
    book_id: str
    chapter_ids: tuple[str, ...]
    fixture_version: str
    fixture_hash: str


@dataclass(frozen=True)
class StageBBookBenchEvidence:
    book_id: str
    fixture_version: str
    fixture_hash: str
    snapshot_id: str
    snapshot_hash: str
    evaluation_ids: tuple[str, ...]
    semantic_evaluation_ids: tuple[str, ...]
    semantic_config_hash: str | None
    blocking_dimensions: tuple[str, ...]
    provider_probe_ids: tuple[str, ...]
    provider: str
    configured_model: str
    config_id: str
    plan_hash: str
    budget_usage: dict[str, object]

    def public_dict(self) -> dict[str, object]:
        return {
            "book_id": self.book_id,
            "fixture_version": self.fixture_version,
            "fixture_hash": self.fixture_hash,
            "snapshot_id": self.snapshot_id,
            "snapshot_hash": self.snapshot_hash,
            "evaluation_ids": list(self.evaluation_ids),
            "semantic_evaluation_ids": list(self.semantic_evaluation_ids),
            "semantic_config_hash": self.semantic_config_hash,
            "blocking_dimensions": list(self.blocking_dimensions),
            "provider_probe_ids": list(self.provider_probe_ids),
            "provider": self.provider,
            "configured_model": self.configured_model,
            "config_id": self.config_id,
            "plan_hash": self.plan_hash,
            "budget_usage": dict(self.budget_usage),
        }


def _book_contract() -> BookContractPayload:
    return BookContractPayload.model_validate(_STAGE_B_FIXTURE["book_contract"])


def _architecture() -> BookArchitecturePayload:
    chapters = [
        {
            "chapter_id": None,
            "title": str(item["title"]),
            "purpose": str(item["purpose"]),
            "new_contribution": str(item["new_contribution"]),
            "dependencies": [],
            "transition": "Carry the decision mechanism into the next evidence question",
        }
        for item in _STAGE_B_FIXTURE["chapters"]
    ]
    return BookArchitecturePayload.model_validate(
        {
            "parts": [
                {
                    "title": "Synthetic Evaluation",
                    "purpose": "Exercise bounded provider quality on a reproducible business-nonfiction case",
                    "chapters": chapters,
                }
            ],
            "intellectual_progression": "signal → decision → feedback evidence",
            "concept_allocation": "One distinct operating mechanism per chapter",
            "promise_thesis_coverage": "Both chapters test the explicit decision-loop thesis",
            "major_transitions": "Decision evidence hands off to feedback evidence",
        }
    )


def _chapter_contract(item: dict[str, object]) -> ChapterContractPayload:
    return ChapterContractPayload(
        chapter_purpose=str(item["purpose"]),
        new_contribution=str(item["new_contribution"]),
        reader_prior_state="Reader has generic advice but no inspectable decision rule",
        reader_after_state="Reader can execute and test one bounded operating rule",
        required_claims=["Separate observed synthetic facts from interpretation"],
        required_or_permitted_research=["Use only the synthetic facts supplied in the objective"],
        required_scenes_examples=["Use the supplied support-ticket example"],
        reserved_elsewhere=["Do not introduce provider, billing or BOOK OS implementation details"],
        opening_requirements="Open with the concrete operational signal, not an abstract definition",
        ending_requirements="End with one explicit measurable decision or revision trigger",
        transition_requirements="Hand off one unresolved evidence question",
    )


def prepare_synthetic_project(data_dir: Path) -> StageBSyntheticProject:
    projects = ProjectService(data_dir)
    project = projects.create_project(
        NewBookRequest(
            working_title=str(_STAGE_B_FIXTURE["working_title"]),
            primary_subtype=str(_STAGE_B_FIXTURE["primary_subtype"]),
        )
    )
    projects.save_book_contract(project.book_id, _book_contract())
    projects.approve_book_contract(project.book_id)
    projects.save_architecture(project.book_id, _architecture())
    project = projects.approve_architecture(project.book_id)
    chapter_ids: list[str] = []
    for chapter, item in zip(project.chapters, _STAGE_B_FIXTURE["chapters"], strict=True):
        projects.save_chapter_contract(
            project.book_id,
            chapter.chapter_id,
            _chapter_contract(item),
        )
        projects.approve_chapter_contract(project.book_id, chapter.chapter_id)
        chapter_ids.append(chapter.chapter_id)
    return StageBSyntheticProject(
        book_id=project.book_id,
        chapter_ids=tuple(chapter_ids),
        fixture_version=STAGE_B_FIXTURE_VERSION,
        fixture_hash=fixture_hash(),
    )


def execute_writer_bookbench_fixture(
    *,
    data_dir: Path,
    preflight: StageBPreflightService,
    plan: StageBPlan,
    authorized_plan_hash: str,
    lane: ProviderLaneService,
    secrets: SecretStore,
    transport: httpx.BaseTransport | None = None,
    ca_bundle: str | None = None,
    run_semantic: bool = False,
) -> StageBBookBenchEvidence:
    """Run the exact synthetic WRITER fixture and snapshot it through M7 BookBench."""

    require_authorized_execution(
        preflight,
        plan,
        authorized_plan_hash=authorized_plan_hash,
    )
    if "WRITER" not in plan.candidate.roles:
        raise ValueError("accepted Stage B plan does not authorize WRITER")
    project = prepare_synthetic_project(data_dir)
    runtime = build_provider_runtime(
        plan,
        secrets,
        transport=transport,
        ca_bundle=ca_bundle,
    )
    probe_ids: list[str] = []
    try:
        gateway = ModelGateway({plan.candidate.provider: runtime.generation})
        drafting = DraftingService(data_dir, gateway)
        for chapter_id, item in zip(
            project.chapter_ids,
            _STAGE_B_FIXTURE["chapters"],
            strict=True,
        ):
            started = time.perf_counter()
            draft = drafting.generate_section_draft(
                project.book_id,
                chapter_id,
                DraftSectionRequest(
                    section_objective=str(item["objective"]),
                    provider=plan.candidate.provider,
                    model=plan.candidate.model,
                    max_output_tokens=1200,
                ),
            )
            latency_ms = max(0, int((time.perf_counter() - started) * 1000))
            usage = dict(draft.usage)
            usage["fixture_version"] = project.fixture_version
            usage["fixture_hash"] = project.fixture_hash
            usage["chapter_id"] = chapter_id
            probe_ids.append(
                lane.record_probe(
                    provider=plan.candidate.provider,
                    model=plan.candidate.model,
                    config_id=plan.candidate.config_id,
                    region=plan.candidate.region,
                    capability=f"generation:WRITER:{chapter_id}",
                    outcome="SUCCESS",
                    probe_type="LIVE",
                    latency_ms=latency_ms,
                    usage=usage,
                    cost={"state": "UNKNOWN"},
                    external_request_id=draft.provider_run_id,
                )
            )

        embedding_gateway = (
            EmbeddingGateway({plan.candidate.provider: runtime.embedding}) if run_semantic else None
        )
        bookbench = BookBenchService(data_dir, embedding_gateway=embedding_gateway)
        snapshot = bookbench.create_snapshot(project.book_id, scope="BOOK")
        deterministic = bookbench.run_deterministic_suite(project.book_id, snapshot.snapshot_id)
        semantic_ids: tuple[str, ...] = ()
        semantic_config_hash: str | None = None
        if run_semantic:
            semantic = bookbench.run_semantic(
                project.book_id,
                snapshot.snapshot_id,
                provider=plan.candidate.provider,
                model=plan.candidate.model,
            )
            semantic_ids = tuple(semantic.evaluation_ids)
            semantic_config_hash = semantic.config_hash
        report = bookbench.report(project.book_id, snapshot.snapshot_id)
        return StageBBookBenchEvidence(
            book_id=project.book_id,
            fixture_version=project.fixture_version,
            fixture_hash=project.fixture_hash,
            snapshot_id=snapshot.snapshot_id,
            snapshot_hash=snapshot.snapshot_hash,
            evaluation_ids=tuple(run.evaluation_id for run in deterministic),
            semantic_evaluation_ids=semantic_ids,
            semantic_config_hash=semantic_config_hash,
            blocking_dimensions=tuple(report.blocking_dimensions),
            provider_probe_ids=tuple(probe_ids),
            provider=plan.candidate.provider,
            configured_model=plan.candidate.model,
            config_id=plan.candidate.config_id,
            plan_hash=plan.plan_hash,
            budget_usage=runtime.ledger.public_dict(),
        )
    finally:
        runtime.close()
