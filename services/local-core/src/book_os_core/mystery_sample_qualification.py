from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, TypeAlias

from .authority_types import JSONValue, content_hash

SampleFunction: TypeAlias = Literal[
    "OPENING",
    "INVESTIGATION_DIALOGUE",
    "TENSION_MYSTIC",
    "QUIET_CHARACTER",
]
SampleDimension: TypeAlias = Literal[
    "NARRATIVE_CONTRACT",
    "POV_INTEGRITY",
    "VOICE_STYLE",
    "DIALOGUE",
    "SCENE_CAUSALITY",
    "SUSPENSE_INFORMATION_CONTROL",
    "ANTI_CLICHE",
    "FACTUAL_REALISM",
    "AUDIO_LISTENABILITY",
]
EvaluationStatus: TypeAlias = Literal[
    "PASS",
    "MAJOR_GAP",
    "BLOCKING_GAP",
    "NOT_EVALUATED",
]
ProfileStatus: TypeAlias = Literal["DRAFT", "APPROVED"]
PostWriterRevisionClass: TypeAlias = Literal["NONE", "MECHANICAL", "MATERIAL"]

_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class StyleProfileSnapshot:
    profile_id: str
    content_hash: str
    status: ProfileStatus


@dataclass(frozen=True)
class WriterCandidate:
    writer_candidate_id: str
    executor_identity: str
    provider: str
    model: str
    route_ref: str
    prompt_ref: str


@dataclass(frozen=True)
class SampleArtifact:
    sample_id: str
    scene_id: str
    scene_revision_ref: str
    writing_admission_id: str
    writer_candidate_id: str
    writer_output_hash: str
    final_text_hash: str
    final_character_count: int
    function_codes: tuple[SampleFunction, ...]
    post_writer_revision_class: PostWriterRevisionClass = "NONE"


@dataclass(frozen=True)
class SampleEvaluationEvidence:
    sample_id: str
    status: EvaluationStatus
    coverage_dimensions: tuple[SampleDimension, ...]
    evaluation_ref: str
    evaluator_identity: str


@dataclass(frozen=True)
class ProfessionalBenchmarkEvidence:
    status: EvaluationStatus
    benchmark_ref: str
    benchmark_set_ref: str
    evaluator_identity: str


@dataclass(frozen=True)
class RepresentativeSamplePack:
    book_id: str
    style_profile: StyleProfileSnapshot
    writer_candidate: WriterCandidate
    authority_revision_refs: tuple[str, ...]
    samples: tuple[SampleArtifact, ...]
    evaluations: tuple[SampleEvaluationEvidence, ...]
    professional_benchmark: ProfessionalBenchmarkEvidence


@dataclass(frozen=True)
class RepresentativeSamplePolicy:
    min_distinct_samples: int
    min_characters_per_sample: int
    require_tension_mystic: bool = False
    require_quiet_character: bool = False
    audio_selected: bool = False


@dataclass(frozen=True)
class SampleQualificationFinding:
    code: str
    message: str
    object_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class SampleQualificationResult:
    representative_sample_qualified: bool
    representative_sample_ref: str
    writer_qualified: bool
    writer_qualification_ref: str | None
    findings: tuple[SampleQualificationFinding, ...]


@dataclass(frozen=True)
class WriterQualificationVerification:
    valid: bool
    reason: str | None
    current_result: SampleQualificationResult


def _finding(
    code: str,
    message: str,
    *object_refs: str,
) -> SampleQualificationFinding:
    return SampleQualificationFinding(
        code=code,
        message=message,
        object_refs=tuple(object_refs),
    )


def _json_strings(values: tuple[str, ...]) -> list[JSONValue]:
    result: list[JSONValue] = []
    for value in sorted(values):
        result.append(value)
    return result


def _json_objects(values: tuple[dict[str, JSONValue], ...]) -> list[JSONValue]:
    result: list[JSONValue] = []
    for value in values:
        result.append(value)
    return result


def _valid_hash(value: str) -> bool:
    return bool(_SHA256.fullmatch(value))


def _style_ref(snapshot: StyleProfileSnapshot) -> str:
    return f"style-profile:{snapshot.profile_id}:{snapshot.content_hash}"


def _writer_payload(candidate: WriterCandidate) -> dict[str, JSONValue]:
    return {
        "writer_candidate_id": candidate.writer_candidate_id,
        "executor_identity": candidate.executor_identity,
        "provider": candidate.provider,
        "model": candidate.model,
        "route_ref": candidate.route_ref,
        "prompt_ref": candidate.prompt_ref,
    }


def _sample_payload(sample: SampleArtifact) -> dict[str, JSONValue]:
    return {
        "sample_id": sample.sample_id,
        "scene_id": sample.scene_id,
        "scene_revision_ref": sample.scene_revision_ref,
        "writing_admission_id": sample.writing_admission_id,
        "writer_candidate_id": sample.writer_candidate_id,
        "writer_output_hash": sample.writer_output_hash,
        "final_text_hash": sample.final_text_hash,
        "final_character_count": sample.final_character_count,
        "function_codes": _json_strings(tuple(sample.function_codes)),
        "post_writer_revision_class": sample.post_writer_revision_class,
    }


def _evaluation_payload(evaluation: SampleEvaluationEvidence) -> dict[str, JSONValue]:
    return {
        "sample_id": evaluation.sample_id,
        "status": evaluation.status,
        "coverage_dimensions": _json_strings(tuple(evaluation.coverage_dimensions)),
        "evaluation_ref": evaluation.evaluation_ref,
        "evaluator_identity": evaluation.evaluator_identity,
    }


def _benchmark_payload(benchmark: ProfessionalBenchmarkEvidence) -> dict[str, JSONValue]:
    return {
        "status": benchmark.status,
        "benchmark_ref": benchmark.benchmark_ref,
        "benchmark_set_ref": benchmark.benchmark_set_ref,
        "evaluator_identity": benchmark.evaluator_identity,
    }


def _representative_sample_ref(pack: RepresentativeSamplePack) -> str:
    payload: dict[str, JSONValue] = {
        "book_id": pack.book_id,
        "style_profile_ref": _style_ref(pack.style_profile),
        "writer": _writer_payload(pack.writer_candidate),
        "authority_revision_refs": _json_strings(pack.authority_revision_refs),
        "samples": _json_objects(
            tuple(
                _sample_payload(sample)
                for sample in sorted(pack.samples, key=lambda x: x.sample_id)
            )
        ),
        "evaluations": _json_objects(
            tuple(
                _evaluation_payload(evaluation)
                for evaluation in sorted(pack.evaluations, key=lambda x: x.sample_id)
            )
        ),
        "professional_benchmark": _benchmark_payload(pack.professional_benchmark),
    }
    return f"representative-sample:{content_hash(payload)}"


def _writer_qualification_ref(
    *,
    pack: RepresentativeSamplePack,
    representative_sample_ref: str,
) -> str:
    payload: dict[str, JSONValue] = {
        "book_id": pack.book_id,
        "representative_sample_ref": representative_sample_ref,
        "style_profile_ref": _style_ref(pack.style_profile),
        "writer": _writer_payload(pack.writer_candidate),
        "authority_revision_refs": _json_strings(pack.authority_revision_refs),
        "sample_writer_output_hashes": _json_strings(
            tuple(sample.writer_output_hash for sample in pack.samples)
        ),
    }
    return f"writer-qualification:{content_hash(payload)}"


def _required_functions(policy: RepresentativeSamplePolicy) -> frozenset[SampleFunction]:
    required: set[SampleFunction] = {"OPENING", "INVESTIGATION_DIALOGUE"}
    if policy.require_tension_mystic:
        required.add("TENSION_MYSTIC")
    if policy.require_quiet_character:
        required.add("QUIET_CHARACTER")
    return frozenset(required)


def _core_dimensions(policy: RepresentativeSamplePolicy) -> frozenset[SampleDimension]:
    result: set[SampleDimension] = {
        "NARRATIVE_CONTRACT",
        "POV_INTEGRITY",
        "VOICE_STYLE",
        "SCENE_CAUSALITY",
        "ANTI_CLICHE",
        "FACTUAL_REALISM",
    }
    if policy.audio_selected:
        result.add("AUDIO_LISTENABILITY")
    return frozenset(result)


def _sample_required_dimensions(
    sample: SampleArtifact,
    policy: RepresentativeSamplePolicy,
) -> frozenset[SampleDimension]:
    result = set(_core_dimensions(policy))
    if "INVESTIGATION_DIALOGUE" in sample.function_codes:
        result.add("DIALOGUE")
    if "TENSION_MYSTIC" in sample.function_codes:
        result.add("SUSPENSE_INFORMATION_CONTROL")
    return frozenset(result)


def qualify_representative_sample(
    *,
    pack: RepresentativeSamplePack,
    policy: RepresentativeSamplePolicy,
    current_style_profile: StyleProfileSnapshot,
    current_authority_revision_refs: tuple[str, ...],
    valid_admission_scene_refs: Mapping[str, str],
) -> SampleQualificationResult:
    """Qualify final representative prose and separately qualify its Writer.

    This function never generates prose and never judges prose semantics. It validates
    provenance, exact context and the presence/outcome of independent evaluation.
    """
    findings: list[SampleQualificationFinding] = []
    writer_findings: list[SampleQualificationFinding] = []

    if policy.min_distinct_samples < 1:
        findings.append(
            _finding(
                "SAMPLE.POLICY.MIN_SAMPLE_COUNT_INVALID",
                "min_distinct_samples must be positive",
            )
        )
    if policy.min_characters_per_sample < 1:
        findings.append(
            _finding(
                "SAMPLE.POLICY.MIN_CHARACTERS_INVALID",
                "min_characters_per_sample must be positive",
            )
        )

    if not pack.book_id.strip():
        findings.append(_finding("SAMPLE.BOOK_ID_MISSING", "book_id must not be blank"))

    style = pack.style_profile
    if not style.profile_id.strip():
        findings.append(
            _finding("SAMPLE.STYLE.PROFILE_ID_MISSING", "StyleProfile id must not be blank")
        )
    if not _valid_hash(style.content_hash):
        findings.append(
            _finding(
                "SAMPLE.STYLE.HASH_INVALID",
                "StyleProfile content hash must be lowercase SHA-256",
                style.profile_id,
            )
        )
    if style.status != "APPROVED":
        findings.append(
            _finding(
                "SAMPLE.STYLE.NOT_APPROVED",
                f"StyleProfile {style.profile_id} is {style.status}",
                style.profile_id,
            )
        )
    if current_style_profile != style:
        findings.append(
            _finding(
                "SAMPLE.STYLE.STALE",
                "representative sample is not bound to the current exact StyleProfile",
                style.profile_id,
            )
        )

    authority_refs = tuple(sorted(set(pack.authority_revision_refs)))
    if not authority_refs or any(not value.strip() for value in authority_refs):
        findings.append(
            _finding(
                "SAMPLE.AUTHORITY.REFS_MISSING",
                "representative sample requires exact non-empty authority revision refs",
            )
        )
    if len(authority_refs) != len(pack.authority_revision_refs):
        findings.append(
            _finding(
                "SAMPLE.AUTHORITY.DUPLICATE_REF",
                "representative sample contains duplicate authority revision refs",
            )
        )
    if authority_refs != tuple(sorted(set(current_authority_revision_refs))):
        findings.append(
            _finding(
                "SAMPLE.AUTHORITY.STALE",
                "representative sample authority snapshot differs from current context",
            )
        )

    candidate = pack.writer_candidate
    for field_name, value in (
        ("WRITER_CANDIDATE_ID", candidate.writer_candidate_id),
        ("EXECUTOR_IDENTITY", candidate.executor_identity),
        ("PROVIDER", candidate.provider),
        ("MODEL", candidate.model),
        ("ROUTE_REF", candidate.route_ref),
        ("PROMPT_REF", candidate.prompt_ref),
    ):
        if not value.strip():
            findings.append(
                _finding(
                    f"SAMPLE.WRITER.{field_name}_MISSING",
                    f"writer candidate {field_name.lower()} must not be blank",
                )
            )

    samples_by_id: dict[str, SampleArtifact] = {}
    scene_ids: set[str] = set()
    functions_seen: set[SampleFunction] = set()
    for sample in pack.samples:
        if not sample.sample_id.strip():
            findings.append(_finding("SAMPLE.ARTIFACT.ID_MISSING", "sample_id must not be blank"))
            continue
        if sample.sample_id in samples_by_id:
            findings.append(
                _finding(
                    "SAMPLE.ARTIFACT.DUPLICATE_ID",
                    f"duplicate sample id {sample.sample_id}",
                    sample.sample_id,
                )
            )
            continue
        samples_by_id[sample.sample_id] = sample

        if not sample.scene_id.strip():
            findings.append(
                _finding(
                    "SAMPLE.ARTIFACT.SCENE_ID_MISSING",
                    f"sample {sample.sample_id} has no scene_id",
                    sample.sample_id,
                )
            )
        elif sample.scene_id in scene_ids:
            findings.append(
                _finding(
                    "SAMPLE.ARTIFACT.DUPLICATE_SCENE",
                    f"scene {sample.scene_id} appears in more than one sample artifact",
                    sample.sample_id,
                    sample.scene_id,
                )
            )
        else:
            scene_ids.add(sample.scene_id)

        if not sample.scene_revision_ref.strip():
            findings.append(
                _finding(
                    "SAMPLE.ARTIFACT.SCENE_REVISION_REF_MISSING",
                    f"sample {sample.sample_id} has no scene revision ref",
                    sample.sample_id,
                )
            )
        if not sample.writing_admission_id.strip():
            findings.append(
                _finding(
                    "SAMPLE.ARTIFACT.ADMISSION_ID_MISSING",
                    f"sample {sample.sample_id} has no MYS-05 admission id",
                    sample.sample_id,
                )
            )
        else:
            admitted_scene_ref = valid_admission_scene_refs.get(sample.writing_admission_id)
            if admitted_scene_ref is None:
                findings.append(
                    _finding(
                        "SAMPLE.ARTIFACT.ADMISSION_UNKNOWN",
                        (
                            f"sample {sample.sample_id} references an unverified "
                            "writing admission"
                        ),
                        sample.sample_id,
                        sample.writing_admission_id,
                    )
                )
            elif admitted_scene_ref != sample.scene_revision_ref:
                findings.append(
                    _finding(
                        "SAMPLE.ARTIFACT.ADMISSION_SCENE_MISMATCH",
                        (
                            f"sample {sample.sample_id} scene revision does not match "
                            "its verified writing admission"
                        ),
                        sample.sample_id,
                        sample.scene_revision_ref,
                    )
                )

        if not _valid_hash(sample.writer_output_hash):
            findings.append(
                _finding(
                    "SAMPLE.ARTIFACT.WRITER_OUTPUT_HASH_INVALID",
                    f"sample {sample.sample_id} has invalid writer output hash",
                    sample.sample_id,
                )
            )
        if not _valid_hash(sample.final_text_hash):
            findings.append(
                _finding(
                    "SAMPLE.ARTIFACT.FINAL_TEXT_HASH_INVALID",
                    f"sample {sample.sample_id} has invalid final text hash",
                    sample.sample_id,
                )
            )
        if sample.final_character_count < policy.min_characters_per_sample:
            findings.append(
                _finding(
                    "SAMPLE.ARTIFACT.TOO_SHORT",
                    (
                        f"sample {sample.sample_id} has {sample.final_character_count} "
                        f"characters; minimum is {policy.min_characters_per_sample}"
                    ),
                    sample.sample_id,
                )
            )
        if not sample.function_codes:
            findings.append(
                _finding(
                    "SAMPLE.ARTIFACT.FUNCTION_MISSING",
                    f"sample {sample.sample_id} has no representative function",
                    sample.sample_id,
                )
            )
        if len(set(sample.function_codes)) != len(sample.function_codes):
            findings.append(
                _finding(
                    "SAMPLE.ARTIFACT.DUPLICATE_FUNCTION",
                    f"sample {sample.sample_id} contains duplicate function codes",
                    sample.sample_id,
                )
            )
        functions_seen.update(sample.function_codes)

        if sample.writer_candidate_id != candidate.writer_candidate_id:
            writer_findings.append(
                _finding(
                    "WRITER_QUALIFICATION.CANDIDATE_MISMATCH",
                    (
                        f"sample {sample.sample_id} was not produced by writer candidate "
                        f"{candidate.writer_candidate_id}"
                    ),
                    sample.sample_id,
                )
            )
        if sample.post_writer_revision_class == "MATERIAL":
            writer_findings.append(
                _finding(
                    "WRITER_QUALIFICATION.MATERIAL_REWRITE",
                    (
                        f"sample {sample.sample_id} required material post-Writer rewrite; "
                        "final prose cannot qualify the original Writer"
                    ),
                    sample.sample_id,
                )
            )
        elif (
            sample.post_writer_revision_class == "NONE"
            and sample.writer_output_hash != sample.final_text_hash
        ):
            writer_findings.append(
                _finding(
                    "WRITER_QUALIFICATION.UNDECLARED_REWRITE",
                    (
                        f"sample {sample.sample_id} final hash differs from Writer output "
                        "while revision class is NONE"
                    ),
                    sample.sample_id,
                )
            )

    if len(samples_by_id) < policy.min_distinct_samples:
        findings.append(
            _finding(
                "SAMPLE.COVERAGE.TOO_FEW_SAMPLES",
                (
                    f"representative sample has {len(samples_by_id)} distinct samples; "
                    f"minimum is {policy.min_distinct_samples}"
                ),
            )
        )

    for function_code in sorted(_required_functions(policy)):
        if function_code not in functions_seen:
            findings.append(
                _finding(
                    "SAMPLE.COVERAGE.FUNCTION_MISSING",
                    f"required representative function {function_code} is missing",
                    function_code,
                )
            )

    evaluations_by_sample: dict[str, SampleEvaluationEvidence] = {}
    for evaluation in pack.evaluations:
        if evaluation.sample_id in evaluations_by_sample:
            findings.append(
                _finding(
                    "SAMPLE.EVALUATION.DUPLICATE_SAMPLE",
                    f"sample {evaluation.sample_id} has multiple evaluation records",
                    evaluation.sample_id,
                )
            )
            continue
        evaluations_by_sample[evaluation.sample_id] = evaluation
        if evaluation.sample_id not in samples_by_id:
            findings.append(
                _finding(
                    "SAMPLE.EVALUATION.UNKNOWN_SAMPLE",
                    f"evaluation references unknown sample {evaluation.sample_id}",
                    evaluation.sample_id,
                )
            )
        if not evaluation.evaluation_ref.strip():
            findings.append(
                _finding(
                    "SAMPLE.EVALUATION.REF_MISSING",
                    f"sample {evaluation.sample_id} evaluation has no ref",
                    evaluation.sample_id,
                )
            )
        if not evaluation.evaluator_identity.strip():
            findings.append(
                _finding(
                    "SAMPLE.EVALUATION.EVALUATOR_MISSING",
                    f"sample {evaluation.sample_id} evaluation has no evaluator identity",
                    evaluation.sample_id,
                )
            )
        elif evaluation.evaluator_identity == candidate.executor_identity:
            findings.append(
                _finding(
                    "SAMPLE.EVALUATION.NOT_INDEPENDENT",
                    (
                        f"sample {evaluation.sample_id} is judged only by the same "
                        "executor identity that wrote it"
                    ),
                    evaluation.sample_id,
                )
            )
        if evaluation.status != "PASS":
            findings.append(
                _finding(
                    f"SAMPLE.EVALUATION.{evaluation.status}",
                    (
                        f"sample {evaluation.sample_id} evaluation status is "
                        f"{evaluation.status}"
                    ),
                    evaluation.sample_id,
                )
            )

    for sample_id, sample in samples_by_id.items():
        evaluation = evaluations_by_sample.get(sample_id)
        if evaluation is None:
            findings.append(
                _finding(
                    "SAMPLE.EVALUATION.MISSING",
                    f"sample {sample_id} has no evaluation evidence",
                    sample_id,
                )
            )
            continue
        coverage = frozenset(evaluation.coverage_dimensions)
        if len(coverage) != len(evaluation.coverage_dimensions):
            findings.append(
                _finding(
                    "SAMPLE.EVALUATION.DUPLICATE_DIMENSION",
                    f"sample {sample_id} repeats evaluation dimensions",
                    sample_id,
                )
            )
        missing_dimensions = _sample_required_dimensions(sample, policy) - coverage
        for dimension in sorted(missing_dimensions):
            findings.append(
                _finding(
                    "SAMPLE.EVALUATION.DIMENSION_MISSING",
                    f"sample {sample_id} lacks required evaluation dimension {dimension}",
                    sample_id,
                    dimension,
                )
            )

    benchmark = pack.professional_benchmark
    if benchmark.status != "PASS":
        findings.append(
            _finding(
                f"SAMPLE.BENCHMARK.{benchmark.status}",
                f"professional sample benchmark status is {benchmark.status}",
            )
        )
    if not benchmark.benchmark_ref.strip():
        findings.append(
            _finding(
                "SAMPLE.BENCHMARK.REF_MISSING",
                "professional benchmark evidence ref is missing",
            )
        )
    if not benchmark.benchmark_set_ref.strip():
        findings.append(
            _finding(
                "SAMPLE.BENCHMARK.SET_REF_MISSING",
                "professional benchmark set ref is missing",
            )
        )
    if not benchmark.evaluator_identity.strip():
        findings.append(
            _finding(
                "SAMPLE.BENCHMARK.EVALUATOR_MISSING",
                "professional benchmark evaluator identity is missing",
            )
        )
    elif benchmark.evaluator_identity == candidate.executor_identity:
        findings.append(
            _finding(
                "SAMPLE.BENCHMARK.NOT_INDEPENDENT",
                "professional benchmark cannot rely solely on the Writer executor identity",
            )
        )

    representative_ref = _representative_sample_ref(pack)
    sample_qualified = not findings
    writer_qualified = sample_qualified and not writer_findings
    writer_ref = (
        _writer_qualification_ref(
            pack=pack,
            representative_sample_ref=representative_ref,
        )
        if writer_qualified
        else None
    )
    return SampleQualificationResult(
        representative_sample_qualified=sample_qualified,
        representative_sample_ref=representative_ref,
        writer_qualified=writer_qualified,
        writer_qualification_ref=writer_ref,
        findings=tuple((*findings, *writer_findings)),
    )


def verify_writer_qualification(
    *,
    prior_writer_qualification_ref: str,
    pack: RepresentativeSamplePack,
    policy: RepresentativeSamplePolicy,
    current_style_profile: StyleProfileSnapshot,
    current_authority_revision_refs: tuple[str, ...],
    valid_admission_scene_refs: Mapping[str, str],
) -> WriterQualificationVerification:
    current = qualify_representative_sample(
        pack=pack,
        policy=policy,
        current_style_profile=current_style_profile,
        current_authority_revision_refs=current_authority_revision_refs,
        valid_admission_scene_refs=valid_admission_scene_refs,
    )
    if not current.writer_qualified or current.writer_qualification_ref is None:
        return WriterQualificationVerification(
            valid=False,
            reason="CURRENT_QUALIFICATION_BLOCKED",
            current_result=current,
        )
    if current.writer_qualification_ref != prior_writer_qualification_ref:
        return WriterQualificationVerification(
            valid=False,
            reason="QUALIFICATION_SNAPSHOT_CHANGED",
            current_result=current,
        )
    return WriterQualificationVerification(
        valid=True,
        reason=None,
        current_result=current,
    )
