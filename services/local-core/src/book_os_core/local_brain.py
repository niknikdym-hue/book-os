from __future__ import annotations

from dataclasses import dataclass
import os
import platform
from typing import Any, Literal, Protocol, cast

from pydantic import BaseModel, Field, ValidationError, model_validator

from .model_gateway import (
    BookArchitectureProposalOutput,
    BookBenchJudgeOutput,
    BookBenchPairwiseOutput,
    BookContractProposalOutput,
    ChapterContractProposalOutput,
    ModelAdapterResult,
    ModelOutputError,
    ModelProviderError,
    ModelTaskRequest,
    SectionDraftOutput,
)
from .prompts import PromptTemplate

LocalTaskClass = Literal[
    "BOOK_CONTRACT_PROPOSAL",
    "ARCHITECTURE_PROPOSAL",
    "CHAPTER_CONTRACT_PROPOSAL",
    "SECTION_DRAFT",
    "BOOKBENCH_JUDGE",
    "BOOKBENCH_PAIRWISE",
    "RESEARCH_SYNTHESIS",
    "DEVELOPMENTAL_CRITIQUE",
    "TARGETED_REWRITE",
    "CONTRADICTION_REPETITION",
]
PromotionState = Literal["EXPERIMENTAL", "SHADOW", "ELIGIBLE", "PREFERRED", "SUSPENDED"]
BenchmarkStatus = Literal["NOT_RUN", "PASS", "ATTENTION", "FAIL"]


class LocalModelManifest(BaseModel):
    provider_id: Literal["local"] = "local"
    runtime_id: str = Field(min_length=1, max_length=120)
    model_id: str = Field(min_length=1, max_length=255)
    model_version: str = Field(min_length=1, max_length=120)
    source_identifier: str = Field(min_length=1, max_length=1000)
    license_identifier: str = Field(min_length=1, max_length=1000)
    weights_hash: str | None = Field(default=None, min_length=8, max_length=128)
    config_hash: str | None = Field(default=None, min_length=8, max_length=128)
    quantization: str | None = Field(default=None, max_length=120)
    context_limit: int = Field(ge=1024)
    supported_task_classes: list[LocalTaskClass] = Field(min_length=1)
    supports_structured_output: bool
    supports_tools: bool = False
    memory_required_bytes: int | None = Field(default=None, ge=0)
    requires_apple_silicon: bool = True
    benchmark_status_by_operation: dict[LocalTaskClass, BenchmarkStatus] = Field(
        default_factory=dict
    )
    promotion_state_by_operation: dict[LocalTaskClass, PromotionState] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_operation_metadata(self) -> LocalModelManifest:
        supported = set(self.supported_task_classes)
        for field_name, mapping in (
            ("benchmark_status_by_operation", self.benchmark_status_by_operation),
            ("promotion_state_by_operation", self.promotion_state_by_operation),
        ):
            unknown = set(mapping) - supported
            if unknown:
                raise ValueError(
                    f"{field_name} contains unsupported task classes: {sorted(unknown)}"
                )
        return self

    def promotion_state(self, task_class: LocalTaskClass) -> PromotionState:
        return self.promotion_state_by_operation.get(task_class, "EXPERIMENTAL")


class LocalHardwareFacts(BaseModel):
    system: str = Field(min_length=1)
    architecture: str = Field(min_length=1)
    apple_silicon: bool
    memory_bytes: int | None = Field(default=None, ge=0)


class HardwareProbe(Protocol):
    def probe(self) -> LocalHardwareFacts: ...


class SystemHardwareProbe:
    def probe(self) -> LocalHardwareFacts:
        system = platform.system() or "unknown"
        architecture = platform.machine() or "unknown"
        normalized_arch = architecture.casefold()
        apple_silicon = system == "Darwin" and normalized_arch in {"arm64", "aarch64"}

        memory_bytes: int | None = None
        try:
            page_size = int(os.sysconf("SC_PAGE_SIZE"))
            physical_pages = int(os.sysconf("SC_PHYS_PAGES"))
            if page_size > 0 and physical_pages > 0:
                memory_bytes = page_size * physical_pages
        except (AttributeError, KeyError, OSError, ValueError):
            memory_bytes = None

        return LocalHardwareFacts(
            system=system,
            architecture=architecture,
            apple_silicon=apple_silicon,
            memory_bytes=memory_bytes,
        )


@dataclass(frozen=True)
class LocalRuntimeResult:
    provider_run_id: str | None
    output: dict[str, Any]
    usage: dict[str, Any]


class LocalRuntime(Protocol):
    runtime_id: str
    network_required: bool

    def is_available(self) -> bool: ...

    def configured_model_ids(self) -> set[str]: ...

    def generate(
        self,
        request: ModelTaskRequest,
        prompt: PromptTemplate,
        manifest: LocalModelManifest,
    ) -> LocalRuntimeResult: ...


class LocalReadinessReport(BaseModel):
    provider_id: Literal["local"] = "local"
    runtime_id: str
    model_id: str
    hardware: LocalHardwareFacts
    runtime_id_matches: bool
    runtime_available: bool
    model_configured: bool
    memory_sufficient: bool | None
    apple_silicon_sufficient: bool
    network_local: bool
    ready: bool
    reasons: list[str] = Field(default_factory=list)


class LocalReadinessService:
    def __init__(self, runtime: LocalRuntime, hardware_probe: HardwareProbe | None = None) -> None:
        self._runtime = runtime
        self._hardware_probe = hardware_probe or SystemHardwareProbe()

    def check(self, manifest: LocalModelManifest) -> LocalReadinessReport:
        hardware = self._hardware_probe.probe()
        reasons: list[str] = []

        runtime_id_matches = self._runtime.runtime_id == manifest.runtime_id
        if not runtime_id_matches:
            reasons.append("RUNTIME_ID_MISMATCH")

        network_local = not self._runtime.network_required
        if not network_local:
            reasons.append("LOCAL_RUNTIME_REQUIRES_NETWORK")

        runtime_available = self._runtime.is_available()
        if not runtime_available:
            reasons.append("RUNTIME_UNAVAILABLE")

        configured_models = self._runtime.configured_model_ids() if runtime_available else set()
        model_configured = manifest.model_id in configured_models
        if not model_configured:
            reasons.append("MODEL_NOT_CONFIGURED")

        apple_silicon_sufficient = not manifest.requires_apple_silicon or hardware.apple_silicon
        if not apple_silicon_sufficient:
            reasons.append("APPLE_SILICON_REQUIRED")

        memory_sufficient: bool | None = True
        if manifest.memory_required_bytes is not None:
            if hardware.memory_bytes is None:
                memory_sufficient = None
                reasons.append("MEMORY_SIGNAL_UNAVAILABLE")
            elif hardware.memory_bytes < manifest.memory_required_bytes:
                memory_sufficient = False
                reasons.append("INSUFFICIENT_MEMORY")

        ready = (
            runtime_id_matches
            and network_local
            and runtime_available
            and model_configured
            and apple_silicon_sufficient
            and memory_sufficient is True
        )
        return LocalReadinessReport(
            runtime_id=manifest.runtime_id,
            model_id=manifest.model_id,
            hardware=hardware,
            runtime_id_matches=runtime_id_matches,
            runtime_available=runtime_available,
            model_configured=model_configured,
            memory_sufficient=memory_sufficient,
            apple_silicon_sufficient=apple_silicon_sufficient,
            network_local=network_local,
            ready=ready,
            reasons=reasons,
        )


_OUTPUT_TYPES: dict[str, type[BaseModel]] = {
    "SECTION_DRAFT": SectionDraftOutput,
    "BOOK_CONTRACT_PROPOSAL": BookContractProposalOutput,
    "ARCHITECTURE_PROPOSAL": BookArchitectureProposalOutput,
    "CHAPTER_CONTRACT_PROPOSAL": ChapterContractProposalOutput,
    "BOOKBENCH_JUDGE": BookBenchJudgeOutput,
    "BOOKBENCH_PAIRWISE": BookBenchPairwiseOutput,
}


class LocalModelAdapter:
    """Provider-neutral local adapter compatible with ModelGateway."""

    provider_name = "local"

    def __init__(
        self,
        manifest: LocalModelManifest,
        runtime: LocalRuntime,
        *,
        hardware_probe: HardwareProbe | None = None,
    ) -> None:
        self.manifest = manifest
        self._runtime = runtime
        self._readiness = LocalReadinessService(runtime, hardware_probe)

    @staticmethod
    def _validate_output(task_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        output_type = _OUTPUT_TYPES.get(task_type)
        if output_type is None:
            raise ModelOutputError(f"local structured output schema is unknown: {task_type}")
        try:
            validated = output_type.model_validate(payload)
        except ValidationError as exc:
            raise ModelOutputError("local structured output failed schema validation") from exc
        return validated.model_dump(mode="json")

    def generate(self, request: ModelTaskRequest, prompt: PromptTemplate) -> ModelAdapterResult:
        if request.provider != self.provider_name:
            raise ModelProviderError(
                f"local adapter cannot execute provider request: {request.provider}"
            )
        if request.model != self.manifest.model_id:
            raise ModelProviderError(
                f"local model request {request.model} does not match manifest {self.manifest.model_id}"
            )

        task_class = cast(LocalTaskClass, request.task_type)
        if task_class not in self.manifest.supported_task_classes:
            raise ModelProviderError(
                f"local model does not support task class: {request.task_type}"
            )
        if not self.manifest.supports_structured_output:
            raise ModelProviderError("local model manifest does not support structured output")

        readiness = self._readiness.check(self.manifest)
        if not readiness.ready:
            reasons = ",".join(readiness.reasons) or "UNKNOWN"
            raise ModelProviderError(f"local executor is not ready: {reasons}")

        try:
            runtime_result = self._runtime.generate(request, prompt, self.manifest)
        except RuntimeError as exc:
            raise ModelProviderError(f"local runtime failure: {exc}") from exc

        validated_output = self._validate_output(request.task_type, runtime_result.output)
        usage = dict(runtime_result.usage)
        usage.update(
            {
                "provider": "local",
                "runtime_id": self.manifest.runtime_id,
                "model_id": self.manifest.model_id,
                "model_version": self.manifest.model_version,
                "network_required": False,
                "external_calls": 0,
                "paid_calls": 0,
            }
        )
        return ModelAdapterResult(
            provider_run_id=runtime_result.provider_run_id,
            output=validated_output,
            usage=usage,
        )
