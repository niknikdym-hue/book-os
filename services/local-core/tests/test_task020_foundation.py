from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from book_os_core.local_brain import (
    LocalHardwareFacts,
    LocalModelAdapter,
    LocalModelManifest,
    LocalReadinessService,
    LocalRuntimeResult,
)
from book_os_core.model_gateway import (
    AuthorityInputRef,
    ModelGateway,
    ModelOutputError,
    ModelProviderError,
    ModelTaskRequest,
)
from book_os_core.prompts import SECTION_DRAFT_V1, PromptTemplate
from book_os_core.quality_loop import (
    QualityLoopGateError,
    QualityLoopStage,
    QualityLoopStateMachine,
    QualityLoopTransitionError,
)
from book_os_core.series_production import ChapterAdmissionStatusView


class FakeHardwareProbe:
    def __init__(self, facts: LocalHardwareFacts) -> None:
        self._facts = facts

    def probe(self) -> LocalHardwareFacts:
        return self._facts


class FakeLocalRuntime:
    runtime_id = "mlx-lm"
    network_required = False

    def __init__(
        self,
        *,
        available: bool = True,
        models: set[str] | None = None,
        output: dict[str, Any] | None = None,
    ) -> None:
        self.available = available
        self.models = models or {"local-test-model"}
        self.output = output or {
            "text": "Deterministic local draft",
            "notes": ["fake local runtime"],
        }
        self.calls = 0

    def is_available(self) -> bool:
        return self.available

    def configured_model_ids(self) -> set[str]:
        return set(self.models)

    def generate(
        self,
        request: ModelTaskRequest,
        prompt: PromptTemplate,
        manifest: LocalModelManifest,
    ) -> LocalRuntimeResult:
        self.calls += 1
        assert request.provider == "local"
        assert manifest.model_id == request.model
        assert prompt.prompt_hash == request.prompt_hash
        return LocalRuntimeResult(
            provider_run_id="local-run-1",
            output=self.output,
            usage={"input_tokens": 12, "output_tokens": 8},
        )


def apple_hardware(memory_bytes: int = 32 * 1024**3) -> FakeHardwareProbe:
    return FakeHardwareProbe(
        LocalHardwareFacts(
            system="Darwin",
            architecture="arm64",
            apple_silicon=True,
            memory_bytes=memory_bytes,
        )
    )


def local_manifest() -> LocalModelManifest:
    return LocalModelManifest(
        runtime_id="mlx-lm",
        model_id="local-test-model",
        model_version="1",
        source_identifier="rights-clean:test-fixture",
        license_identifier="test-license",
        weights_hash="a" * 64,
        config_hash="b" * 64,
        quantization="4bit",
        context_limit=32_768,
        supported_task_classes=["SECTION_DRAFT"],
        supports_structured_output=True,
        memory_required_bytes=8 * 1024**3,
        promotion_state_by_operation={"SECTION_DRAFT": "SHADOW"},
    )


def local_request() -> ModelTaskRequest:
    return ModelTaskRequest(
        task_id="01JTASK0000000000000000000",
        task_type="SECTION_DRAFT",
        role="WRITER",
        provider="local",
        model="local-test-model",
        prompt_id=SECTION_DRAFT_V1.prompt_id,
        prompt_version=SECTION_DRAFT_V1.version,
        prompt_hash=SECTION_DRAFT_V1.prompt_hash,
        section_objective="Draft the bounded section",
        authority_inputs=[
            AuthorityInputRef(
                revision_id="01JREV00000000000000000000",
                revision_hash="a" * 64,
                entity_type="chapter.contract",
            )
        ],
        authoritative_context={"chapter_contract": {"purpose": "test"}},
    )


def admitted_chapter(*, writing_allowed: bool = True) -> ChapterAdmissionStatusView:
    return ChapterAdmissionStatusView(
        book_id="01JBOOK0000000000000000000",
        chapter_id="01JCHAP0000000000000000000",
        writing_allowed=writing_allowed,
        blockers=[] if writing_allowed else ["definition_pack"],
        admission_id="01JADMIT000000000000000000",
        definition_id="01JDEFIN000000000000000000",
        architecture_revision_id="01JARCH0000000000000000000",
        chapter_contract_revision_id="01JCONTR000000000000000000",
        production_contract_id="01JPRODC000000000000000000",
    )


def advance_to_human_review(machine: QualityLoopStateMachine):
    run = machine.start(admitted_chapter(), actor_kind="SYSTEM", actor="test")
    machine.advance(
        run,
        QualityLoopStage.MICRO_PLAN,
        actor_kind="SYSTEM",
        actor="manager",
        evidence={"micro_plan": "One bounded deterministic micro-plan."},
    )
    machine.advance(
        run,
        QualityLoopStage.EVIDENCE_PLAN,
        actor_kind="SYSTEM",
        actor="manager",
        evidence={
            "evidence_required": True,
            "evidence_ready": True,
            "evidence_summary": "Rights-clean deterministic evidence fixture.",
        },
    )
    machine.advance(
        run,
        QualityLoopStage.SECTION_INTENT,
        actor_kind="SYSTEM",
        actor="manager",
        evidence={"section_intent": "Add one bounded mechanism."},
    )
    draft = machine.propose_artifact(
        run,
        kind="DRAFT_CANDIDATE",
        role="WRITER",
        payload={
            "unit_id": "unit-1",
            "revision_id": "revision-1",
            "revision_hash": "a" * 64,
            "provider": "fake",
            "model": "fake-writer",
            "run_id": "writer-run-1",
        },
        actor_kind="AI",
        actor="fake:fake-writer",
    )
    machine.advance(
        run,
        QualityLoopStage.DRAFT_CANDIDATE,
        actor_kind="SYSTEM",
        actor="manager",
        evidence={"artifact_id": draft.artifact_id},
    )
    machine.advance(
        run,
        QualityLoopStage.DETERMINISTIC_CHECKS,
        actor_kind="SYSTEM",
        actor="manager",
        evidence={"result": "PASS", "draft_revision_id": "revision-1"},
    )
    machine.advance(
        run,
        QualityLoopStage.EVIDENCE_CHECKS,
        actor_kind="SYSTEM",
        actor="manager",
        evidence={
            "result": "PASS",
            "required": True,
            "summary": "Rights-clean deterministic evidence fixture.",
        },
    )
    machine.advance(
        run,
        QualityLoopStage.NOVELTY_CHECK,
        actor_kind="SYSTEM",
        actor="manager",
        evidence={"result": "PASS", "evidence": "No semantic overlap in deterministic fixture."},
    )
    machine.advance(
        run,
        QualityLoopStage.INDEPENDENT_CRITIC,
        actor_kind="AI",
        actor="critic:deterministic-v1",
        evidence={"summary": "Independent deterministic review complete.", "finding_ids": []},
    )
    revision = machine.propose_artifact(
        run,
        kind="TARGETED_REVISION_PROPOSAL",
        role="EDITOR",
        payload={
            "source_revision_id": "revision-1",
            "source_revision_hash": "a" * 64,
            "finding_ids": [],
            "proposal_ids": [],
            "proposal_hashes": [],
        },
        actor_kind="AI",
        actor="critic:deterministic-v1",
    )
    machine.advance(
        run,
        QualityLoopStage.REVISION_PROPOSAL,
        actor_kind="SYSTEM",
        actor="manager",
        evidence={"artifact_id": revision.artifact_id},
    )
    machine.advance(
        run,
        QualityLoopStage.POST_REVISION_CHECKS,
        actor_kind="SYSTEM",
        actor="manager",
        evidence={"result": "PASS", "proposal_count": 0, "all_exact_baseline": True},
    )
    machine.advance(
        run,
        QualityLoopStage.HUMAN_REVIEW,
        actor_kind="SYSTEM",
        actor="manager",
        evidence={
            "draft_artifact_id": draft.artifact_id,
            "revision_artifact_id": revision.artifact_id,
            "material_status": "PROPOSED",
        },
    )
    return run, draft, revision


def accept_material(machine: QualityLoopStateMachine, run, *artifacts) -> None:
    for artifact in artifacts:
        machine.decide_artifact(
            run,
            artifact.artifact_id,
            decision="ACCEPTED",
            actor_kind="OWNER",
            actor="owner",
            reason="Reviewed against exact deterministic provenance.",
        )


def test_quality_loop_reuses_task017_admission_and_fails_closed() -> None:
    machine = QualityLoopStateMachine()

    with pytest.raises(QualityLoopGateError, match="WRITING_NOT_ALLOWED"):
        machine.start(admitted_chapter(writing_allowed=False), actor_kind="SYSTEM", actor="test")

    run = machine.start(admitted_chapter(), actor_kind="SYSTEM", actor="test")
    assert run.stage == QualityLoopStage.ADMISSION_VERIFIED
    assert run.admission_id == "01JADMIT000000000000000000"
    assert run.events[0].evidence == {"admission_id": run.admission_id}


def test_quality_loop_rejects_generic_stage_evidence_bypass() -> None:
    machine = QualityLoopStateMachine()
    run = machine.start(admitted_chapter(), actor_kind="SYSTEM", actor="test")

    with pytest.raises(QualityLoopGateError, match="MICRO_PLAN"):
        machine.advance(
            run,
            QualityLoopStage.MICRO_PLAN,
            actor_kind="SYSTEM",
            actor="state-machine-test",
            evidence={"completed": QualityLoopStage.MICRO_PLAN.value},
        )

    assert run.stage == QualityLoopStage.ADMISSION_VERIFIED


def test_quality_loop_is_ordered_and_material_output_cannot_self_approve() -> None:
    machine = QualityLoopStateMachine()
    run, draft, revision = advance_to_human_review(machine)

    with pytest.raises(QualityLoopGateError, match="HUMAN/OWNER"):
        machine.decide_artifact(
            run,
            draft.artifact_id,
            decision="ACCEPTED",
            actor_kind="AI",  # type: ignore[arg-type]
            actor="fake:fake-writer",
            reason="self approval must fail",
        )

    accept_material(machine, run, draft, revision)

    with pytest.raises(QualityLoopGateError, match="HUMAN/OWNER"):
        machine.advance(
            run,
            QualityLoopStage.COMPLETE,
            actor_kind="AI",
            actor="fake-judge",
            evidence={"decision": "ACCEPT"},
        )

    machine.advance(
        run,
        QualityLoopStage.COMPLETE,
        actor_kind="OWNER",
        actor="owner",
        evidence={"decision": "ACCEPT"},
    )
    assert run.stage == QualityLoopStage.COMPLETE

    with pytest.raises(QualityLoopTransitionError, match="already complete"):
        machine.propose_artifact(
            run,
            kind="AFTER_COMPLETE",
            role="WRITER",
            payload={"text": "forbidden"},
            actor_kind="AI",
            actor="fake-writer",
        )


def test_blocking_finding_requires_explicit_non_ai_resolution_before_completion() -> None:
    machine = QualityLoopStateMachine()
    run, draft, revision = advance_to_human_review(machine)
    blocking = machine.record_finding(
        run,
        role="BOOKBENCH_JUDGE",
        severity="BLOCKING",
        location="draft candidate",
        evidence="Deterministic contradiction fixture.",
        recommended_action="Repair the contradiction and rerun checks.",
        actor_kind="SYSTEM",
        actor="bookbench",
    )
    accept_material(machine, run, draft, revision)

    with pytest.raises(QualityLoopGateError, match="unresolved blocking findings"):
        machine.advance(
            run,
            QualityLoopStage.COMPLETE,
            actor_kind="OWNER",
            actor="owner",
            evidence={"decision": "ACCEPT"},
        )

    with pytest.raises(QualityLoopGateError, match="AI cannot resolve"):
        machine.resolve_finding(
            run,
            blocking.finding_id,
            disposition="RESOLVED",
            actor_kind="AI",
            actor="same-model",
            reason="model self-clear must fail",
        )

    resolved = machine.resolve_finding(
        run,
        blocking.finding_id,
        disposition="RESOLVED",
        actor_kind="SYSTEM",
        actor="deterministic-checker",
        reason="Exact rerun passed after the bounded repair.",
        evidence={"check": "contradiction", "result": "PASS"},
    )
    assert resolved.disposition == "RESOLVED"
    assert resolved.resolved_by_kind == "SYSTEM"
    assert resolved.resolution_evidence == {"check": "contradiction", "result": "PASS"}

    machine.advance(
        run,
        QualityLoopStage.COMPLETE,
        actor_kind="OWNER",
        actor="owner",
        evidence={"decision": "ACCEPT"},
    )
    assert run.stage == QualityLoopStage.COMPLETE


def test_local_readiness_is_explicit_and_operation_promotion_is_not_global() -> None:
    runtime = FakeLocalRuntime()
    manifest = local_manifest()
    report = LocalReadinessService(runtime, apple_hardware()).check(manifest)

    assert report.ready is True
    assert report.reasons == []
    assert manifest.promotion_state("SECTION_DRAFT") == "SHADOW"
    assert manifest.promotion_state("DEVELOPMENTAL_CRITIQUE") == "EXPERIMENTAL"

    low_memory = LocalReadinessService(runtime, apple_hardware(4 * 1024**3)).check(manifest)
    assert low_memory.ready is False
    assert "INSUFFICIENT_MEMORY" in low_memory.reasons


def test_local_manifest_cannot_advertise_task_without_gateway_execution_seam() -> None:
    with pytest.raises(ValidationError, match="supported_task_classes"):
        LocalModelManifest(
            runtime_id="mlx-lm",
            model_id="local-test-model",
            model_version="1",
            source_identifier="rights-clean:test-fixture",
            license_identifier="test-license",
            context_limit=32_768,
            supported_task_classes=["TARGETED_REWRITE"],  # type: ignore[list-item]
            supports_structured_output=True,
        )


def test_local_adapter_runs_through_model_gateway_with_zero_external_calls() -> None:
    runtime = FakeLocalRuntime()
    adapter = LocalModelAdapter(local_manifest(), runtime, hardware_probe=apple_hardware())
    gateway = ModelGateway({"local": adapter})

    result = gateway.generate(local_request(), SECTION_DRAFT_V1)

    assert runtime.calls == 1
    assert result.provider_run_id == "local-run-1"
    assert result.output == {
        "text": "Deterministic local draft",
        "notes": ["fake local runtime"],
    }
    assert result.usage["provider"] == "local"
    assert result.usage["runtime_id"] == "mlx-lm"
    assert result.usage["external_calls"] == 0
    assert result.usage["paid_calls"] == 0
    assert result.usage["network_required"] is False


def test_local_adapter_fails_explicitly_for_malformed_or_unready_runtime() -> None:
    malformed = FakeLocalRuntime(output={"notes": ["missing text"]})
    adapter = LocalModelAdapter(local_manifest(), malformed, hardware_probe=apple_hardware())
    with pytest.raises(ModelOutputError, match="schema validation"):
        adapter.generate(local_request(), SECTION_DRAFT_V1)

    offline = FakeLocalRuntime(available=False)
    unavailable = LocalModelAdapter(local_manifest(), offline, hardware_probe=apple_hardware())
    with pytest.raises(ModelProviderError, match="RUNTIME_UNAVAILABLE"):
        unavailable.generate(local_request(), SECTION_DRAFT_V1)
    assert offline.calls == 0
