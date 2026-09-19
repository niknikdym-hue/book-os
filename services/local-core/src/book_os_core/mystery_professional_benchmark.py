from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, TypeAlias

from .authority_types import JSONValue, content_hash
from .mystery_bench_validation import (
    EvaluatorClass,
    VerifiedEvaluationArtifact,
)
from .mystery_sample_qualification import ProfessionalBenchmarkEvidence

BenchmarkCheckpoint: TypeAlias = Literal[
    "PRE_DRAFT",
    "REPRESENTATIVE_SAMPLE",
    "MIDBOOK",
    "WHOLE_BOOK",
    "FINAL",
]
BenchmarkDimension: TypeAlias = Literal[
    "PREMISE_IDENTITY",
    "NARRATIVE_ENGINE",
    "CHARACTERS",
    "SCENES",
    "DIALOGUE",
    "MYSTERY_CONSTRUCTION",
    "SUSPENSE",
    "PROSE_VOICE",
    "SETTING",
    "EMOTIONAL_ARCHITECTURE",
    "WHOLE_BOOK_STRUCTURE",
    "ORIGINALITY",
    "AUDIO_READINESS",
]
BenchmarkSeverity: TypeAlias = Literal["BLOCKING", "MAJOR", "MINOR", "NOTE"]
BenchmarkDimensionStatus: TypeAlias = Literal["PASS", "MAJOR_GAP", "BLOCKING_GAP"]
ReadinessBand: TypeAlias = Literal[
    "BELOW_PROFESSIONAL_FLOOR",
    "PROFESSIONAL_GAPS_REMAIN",
    "PROFESSIONAL_RANGE_CANDIDATE",
    "STRONG_PROFESSIONAL_CANDIDATE",
]
ReferenceCategory: TypeAlias = Literal[
    "COMMERCIAL_SUCCESS",
    "CRITICAL_RESPECT",
    "DURABLE_BACKLIST",
    "RECENT_EXPECTATION",
    "AUDIO_REFERENCE",
]
PublisherClass: TypeAlias = Literal[
    "ESTABLISHED_PUBLISHER",
    "SMALL_PRESS",
    "INDEPENDENT",
    "OTHER",
]
BenchmarkAccessLevel: TypeAlias = Literal[
    "METADATA_ONLY",
    "DERIVED_NON_RECONSTRUCTIVE",
    "LAWFUL_BOUNDED_TEXT",
    "LICENSED_FULL_ACCESS",
    "PUBLIC_DOMAIN_FULL_ACCESS",
]
RightsBasis: TypeAlias = Literal[
    "PUBLIC_METADATA",
    "PUBLIC_DOMAIN",
    "USER_OWNED",
    "LICENSED",
    "OTHER_DOCUMENTED",
]
ComparisonMode: TypeAlias = Literal["CRITERION", "BLIND_PAIRWISE", "CORPUS_DIAGNOSTIC"]

_BAND_ORDER: dict[str, int] = {
    "BELOW_PROFESSIONAL_FLOOR": 0,
    "PROFESSIONAL_GAPS_REMAIN": 1,
    "PROFESSIONAL_RANGE_CANDIDATE": 2,
    "STRONG_PROFESSIONAL_CANDIDATE": 3,
}
_VALID_DIMENSIONS = frozenset(
    {
        "PREMISE_IDENTITY",
        "NARRATIVE_ENGINE",
        "CHARACTERS",
        "SCENES",
        "DIALOGUE",
        "MYSTERY_CONSTRUCTION",
        "SUSPENSE",
        "PROSE_VOICE",
        "SETTING",
        "EMOTIONAL_ARCHITECTURE",
        "WHOLE_BOOK_STRUCTURE",
        "ORIGINALITY",
        "AUDIO_READINESS",
    }
)


@dataclass(frozen=True)
class BenchmarkReference:
    reference_id: str
    work_ref: str
    author_ref: str
    publication_year: int
    publisher_class: PublisherClass
    publisher_ref: str | None
    format_codes: tuple[str, ...]
    selection_categories: tuple[ReferenceCategory, ...]
    selection_reason: str
    prohibited_inference: str
    access_level: BenchmarkAccessLevel
    rights_basis: RightsBasis
    rights_ref: str
    source_metadata_ref: str
    craft_observation_refs: tuple[str, ...] = ()
    raw_protected_text_embedded: bool = False


@dataclass(frozen=True)
class FictionBenchmarkSet:
    benchmark_set_id: str
    version: int
    subgenre: str
    target_market: str
    language: str
    audience_ref: str
    publication_window: str
    last_review_epoch: int
    references: tuple[BenchmarkReference, ...]


@dataclass(frozen=True)
class BenchmarkSetPolicy:
    min_references: int
    min_distinct_authors: int
    min_publication_span_years: int
    max_single_author_fraction: float
    min_text_access_references: int
    required_categories: tuple[ReferenceCategory, ...]
    min_established_publisher_references: int = 0
    max_review_age_seconds: int | None = None


@dataclass(frozen=True)
class BenchmarkDimensionEvaluation:
    dimension: BenchmarkDimension
    status: BenchmarkDimensionStatus
    evaluation_ref: str
    rubric_ref: str
    evaluator_identity: str
    evaluator_class: EvaluatorClass
    comparison_mode: ComparisonMode


@dataclass(frozen=True)
class FictionBenchmarkFinding:
    dimension: BenchmarkDimension
    severity: BenchmarkSeverity
    observation: str
    recommended_action: str
    manuscript_evidence_refs: tuple[str, ...]
    benchmark_observation_refs: tuple[str, ...]
    evaluation_ref: str
    scope: str | None = None
    non_infringing_comparison: str | None = None
    human_disposition_ref: str | None = None


@dataclass(frozen=True)
class ProfessionalFictionBenchmarkRun:
    book_id: str
    checkpoint: BenchmarkCheckpoint
    manuscript_snapshot_ref: str
    manuscript_snapshot_hash: str
    evaluated_revision_refs: tuple[str, ...]
    benchmark_set_ref: str
    benchmark_set_hash: str
    writer_executor_identity: str
    dimension_evaluations: tuple[BenchmarkDimensionEvaluation, ...]
    findings: tuple[FictionBenchmarkFinding, ...]
    readiness_band: ReadinessBand
    mimicry_request_detected: bool = False
    protected_expression_reproduction_detected: bool = False
    strong_candidate_human_ref: str | None = None


@dataclass(frozen=True)
class ProfessionalBenchmarkPolicy:
    checkpoint: BenchmarkCheckpoint
    audio_selected: bool
    minimum_readiness_band: ReadinessBand
    require_independent_semantic_evaluation: bool = True


@dataclass(frozen=True)
class ProfessionalBenchmarkFinding:
    code: str
    message: str
    object_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class BenchmarkSetValidationResult:
    qualified: bool
    benchmark_set_ref: str
    benchmark_set_hash: str
    findings: tuple[ProfessionalBenchmarkFinding, ...]


@dataclass(frozen=True)
class ProfessionalBenchmarkResult:
    qualified: bool
    professional_benchmark_ref: str
    benchmark_set_ref: str
    readiness_band: ReadinessBand
    findings: tuple[ProfessionalBenchmarkFinding, ...]


@dataclass(frozen=True)
class ProfessionalBenchmarkVerification:
    valid: bool
    reason: str | None
    current_result: ProfessionalBenchmarkResult


def _finding(
    code: str,
    message: str,
    *object_refs: str,
) -> ProfessionalBenchmarkFinding:
    return ProfessionalBenchmarkFinding(
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


def _reference_payload(reference: BenchmarkReference) -> dict[str, JSONValue]:
    return {
        "reference_id": reference.reference_id,
        "work_ref": reference.work_ref,
        "author_ref": reference.author_ref,
        "publication_year": reference.publication_year,
        "publisher_class": reference.publisher_class,
        "publisher_ref": reference.publisher_ref,
        "format_codes": _json_strings(reference.format_codes),
        "selection_categories": _json_strings(
            tuple(reference.selection_categories)
        ),
        "selection_reason": reference.selection_reason,
        "prohibited_inference": reference.prohibited_inference,
        "access_level": reference.access_level,
        "rights_basis": reference.rights_basis,
        "rights_ref": reference.rights_ref,
        "source_metadata_ref": reference.source_metadata_ref,
        "craft_observation_refs": _json_strings(reference.craft_observation_refs),
        "raw_protected_text_embedded": reference.raw_protected_text_embedded,
    }


def _benchmark_set_payload(
    benchmark_set: FictionBenchmarkSet,
) -> dict[str, JSONValue]:
    return {
        "benchmark_set_id": benchmark_set.benchmark_set_id,
        "version": benchmark_set.version,
        "subgenre": benchmark_set.subgenre,
        "target_market": benchmark_set.target_market,
        "language": benchmark_set.language,
        "audience_ref": benchmark_set.audience_ref,
        "publication_window": benchmark_set.publication_window,
        "last_review_epoch": benchmark_set.last_review_epoch,
        "references": _json_objects(
            tuple(
                _reference_payload(reference)
                for reference in sorted(
                    benchmark_set.references,
                    key=lambda item: item.reference_id,
                )
            )
        ),
    }


def benchmark_set_hash(benchmark_set: FictionBenchmarkSet) -> str:
    return content_hash(_benchmark_set_payload(benchmark_set))


def benchmark_set_ref(benchmark_set: FictionBenchmarkSet) -> str:
    return (
        f"fiction-benchmark-set:{benchmark_set.benchmark_set_id}:"
        f"v{benchmark_set.version}:{benchmark_set_hash(benchmark_set)}"
    )


def _dimension_payload(
    evaluation: BenchmarkDimensionEvaluation,
) -> dict[str, JSONValue]:
    return {
        "dimension": evaluation.dimension,
        "status": evaluation.status,
        "evaluation_ref": evaluation.evaluation_ref,
        "rubric_ref": evaluation.rubric_ref,
        "evaluator_identity": evaluation.evaluator_identity,
        "evaluator_class": evaluation.evaluator_class,
        "comparison_mode": evaluation.comparison_mode,
    }


def _finding_payload(finding: FictionBenchmarkFinding) -> dict[str, JSONValue]:
    return {
        "dimension": finding.dimension,
        "severity": finding.severity,
        "observation": finding.observation,
        "recommended_action": finding.recommended_action,
        "manuscript_evidence_refs": _json_strings(
            finding.manuscript_evidence_refs
        ),
        "benchmark_observation_refs": _json_strings(
            finding.benchmark_observation_refs
        ),
        "evaluation_ref": finding.evaluation_ref,
        "scope": finding.scope,
        "non_infringing_comparison": finding.non_infringing_comparison,
        "human_disposition_ref": finding.human_disposition_ref,
    }


def _policy_payload(policy: ProfessionalBenchmarkPolicy) -> dict[str, JSONValue]:
    return {
        "checkpoint": policy.checkpoint,
        "audio_selected": policy.audio_selected,
        "minimum_readiness_band": policy.minimum_readiness_band,
        "require_independent_semantic_evaluation": (
            policy.require_independent_semantic_evaluation
        ),
    }


def _run_ref(
    *,
    run: ProfessionalFictionBenchmarkRun,
    policy: ProfessionalBenchmarkPolicy,
) -> str:
    payload: dict[str, JSONValue] = {
        "book_id": run.book_id,
        "policy": _policy_payload(policy),
        "checkpoint": run.checkpoint,
        "manuscript_snapshot_ref": run.manuscript_snapshot_ref,
        "manuscript_snapshot_hash": run.manuscript_snapshot_hash,
        "evaluated_revision_refs": _json_strings(run.evaluated_revision_refs),
        "benchmark_set_ref": run.benchmark_set_ref,
        "benchmark_set_hash": run.benchmark_set_hash,
        "writer_executor_identity": run.writer_executor_identity,
        "dimension_evaluations": _json_objects(
            tuple(
                _dimension_payload(evaluation)
                for evaluation in sorted(
                    run.dimension_evaluations,
                    key=lambda item: item.dimension,
                )
            )
        ),
        "findings": _json_objects(
            tuple(
                _finding_payload(finding)
                for finding in sorted(
                    run.findings,
                    key=lambda item: (
                        item.dimension,
                        item.severity,
                        item.evaluation_ref,
                        item.scope or "",
                    ),
                )
            )
        ),
        "readiness_band": run.readiness_band,
        "mimicry_request_detected": run.mimicry_request_detected,
        "protected_expression_reproduction_detected": (
            run.protected_expression_reproduction_detected
        ),
        "strong_candidate_human_ref": run.strong_candidate_human_ref,
    }
    return f"professional-fiction-benchmark:{content_hash(payload)}"


def _required_dimensions(
    policy: ProfessionalBenchmarkPolicy,
) -> frozenset[str]:
    checkpoint = policy.checkpoint
    if checkpoint == "PRE_DRAFT":
        required = {
            "PREMISE_IDENTITY",
            "NARRATIVE_ENGINE",
            "CHARACTERS",
            "MYSTERY_CONSTRUCTION",
            "ORIGINALITY",
        }
    elif checkpoint == "REPRESENTATIVE_SAMPLE":
        required = {
            "SCENES",
            "DIALOGUE",
            "SUSPENSE",
            "PROSE_VOICE",
            "SETTING",
            "EMOTIONAL_ARCHITECTURE",
            "ORIGINALITY",
        }
    elif checkpoint == "MIDBOOK":
        required = {
            "NARRATIVE_ENGINE",
            "CHARACTERS",
            "SCENES",
            "MYSTERY_CONSTRUCTION",
            "SUSPENSE",
            "SETTING",
            "EMOTIONAL_ARCHITECTURE",
            "WHOLE_BOOK_STRUCTURE",
            "ORIGINALITY",
        }
    else:
        required = set(_VALID_DIMENSIONS) - {"AUDIO_READINESS"}
    if policy.audio_selected:
        required.add("AUDIO_READINESS")
    return frozenset(required)


def _text_access(reference: BenchmarkReference) -> bool:
    return reference.access_level in {
        "LAWFUL_BOUNDED_TEXT",
        "LICENSED_FULL_ACCESS",
        "PUBLIC_DOMAIN_FULL_ACCESS",
    }


def validate_benchmark_set(
    *,
    benchmark_set: FictionBenchmarkSet,
    policy: BenchmarkSetPolicy,
    now_epoch: int,
) -> BenchmarkSetValidationResult:
    findings: list[ProfessionalBenchmarkFinding] = []

    if not benchmark_set.benchmark_set_id.strip():
        findings.append(
            _finding(
                "PRO_BENCH.SET.ID_MISSING",
                "benchmark_set_id must not be blank",
            )
        )
    if benchmark_set.version < 1:
        findings.append(
            _finding(
                "PRO_BENCH.SET.VERSION_INVALID",
                "benchmark set version must be positive",
            )
        )
    for field_name, value in (
        ("SUBGENRE", benchmark_set.subgenre),
        ("TARGET_MARKET", benchmark_set.target_market),
        ("LANGUAGE", benchmark_set.language),
        ("AUDIENCE_REF", benchmark_set.audience_ref),
        ("PUBLICATION_WINDOW", benchmark_set.publication_window),
    ):
        if not value.strip():
            findings.append(
                _finding(
                    f"PRO_BENCH.SET.{field_name}_MISSING",
                    f"benchmark set {field_name.lower()} must not be blank",
                )
            )

    if policy.min_references < 1:
        findings.append(
            _finding(
                "PRO_BENCH.POLICY.MIN_REFERENCES_INVALID",
                "min_references must be positive",
            )
        )
    if policy.min_distinct_authors < 1:
        findings.append(
            _finding(
                "PRO_BENCH.POLICY.MIN_AUTHORS_INVALID",
                "min_distinct_authors must be positive",
            )
        )
    if policy.min_publication_span_years < 0:
        findings.append(
            _finding(
                "PRO_BENCH.POLICY.PUBLICATION_SPAN_INVALID",
                "min_publication_span_years cannot be negative",
            )
        )
    if not 0 < policy.max_single_author_fraction <= 1:
        findings.append(
            _finding(
                "PRO_BENCH.POLICY.AUTHOR_FRACTION_INVALID",
                "max_single_author_fraction must be in (0, 1]",
            )
        )
    if policy.min_text_access_references < 0:
        findings.append(
            _finding(
                "PRO_BENCH.POLICY.TEXT_ACCESS_MIN_INVALID",
                "min_text_access_references cannot be negative",
            )
        )

    references_by_id: dict[str, BenchmarkReference] = {}
    work_refs: set[str] = set()
    author_counts: Counter[str] = Counter()
    categories_seen: set[str] = set()
    years: list[int] = []
    established_count = 0
    text_access_count = 0

    for reference in benchmark_set.references:
        if not reference.reference_id.strip():
            findings.append(
                _finding(
                    "PRO_BENCH.REFERENCE.ID_MISSING",
                    "benchmark reference id must not be blank",
                )
            )
            continue
        if reference.reference_id in references_by_id:
            findings.append(
                _finding(
                    "PRO_BENCH.REFERENCE.DUPLICATE_ID",
                    f"duplicate benchmark reference {reference.reference_id}",
                    reference.reference_id,
                )
            )
            continue
        references_by_id[reference.reference_id] = reference

        if not reference.work_ref.strip():
            findings.append(
                _finding(
                    "PRO_BENCH.REFERENCE.WORK_REF_MISSING",
                    f"reference {reference.reference_id} has no work_ref",
                    reference.reference_id,
                )
            )
        elif reference.work_ref in work_refs:
            findings.append(
                _finding(
                    "PRO_BENCH.REFERENCE.DUPLICATE_WORK",
                    f"work {reference.work_ref} appears more than once",
                    reference.reference_id,
                    reference.work_ref,
                )
            )
        else:
            work_refs.add(reference.work_ref)

        if not reference.author_ref.strip():
            findings.append(
                _finding(
                    "PRO_BENCH.REFERENCE.AUTHOR_REF_MISSING",
                    f"reference {reference.reference_id} has no author_ref",
                    reference.reference_id,
                )
            )
        else:
            author_counts[reference.author_ref] += 1

        if reference.publication_year < 1400 or reference.publication_year > 3000:
            findings.append(
                _finding(
                    "PRO_BENCH.REFERENCE.PUBLICATION_YEAR_INVALID",
                    (
                        f"reference {reference.reference_id} has implausible "
                        f"publication year {reference.publication_year}"
                    ),
                    reference.reference_id,
                )
            )
        else:
            years.append(reference.publication_year)

        if not reference.selection_categories:
            findings.append(
                _finding(
                    "PRO_BENCH.REFERENCE.CATEGORIES_MISSING",
                    f"reference {reference.reference_id} has no selection categories",
                    reference.reference_id,
                )
            )
        if len(set(reference.selection_categories)) != len(
            reference.selection_categories
        ):
            findings.append(
                _finding(
                    "PRO_BENCH.REFERENCE.DUPLICATE_CATEGORY",
                    f"reference {reference.reference_id} repeats selection categories",
                    reference.reference_id,
                )
            )
        categories_seen.update(reference.selection_categories)

        for field_name, value in (
            ("SELECTION_REASON", reference.selection_reason),
            ("PROHIBITED_INFERENCE", reference.prohibited_inference),
            ("RIGHTS_REF", reference.rights_ref),
            ("SOURCE_METADATA_REF", reference.source_metadata_ref),
        ):
            if not value.strip():
                findings.append(
                    _finding(
                        f"PRO_BENCH.REFERENCE.{field_name}_MISSING",
                        (
                            f"reference {reference.reference_id} "
                            f"{field_name.lower()} must not be blank"
                        ),
                        reference.reference_id,
                    )
                )

        if reference.raw_protected_text_embedded:
            findings.append(
                _finding(
                    "PRO_BENCH.RIGHTS.PROTECTED_TEXT_EMBEDDED",
                    (
                        f"reference {reference.reference_id} embeds protected text; "
                        "benchmark sets may store metadata/derived observations only"
                    ),
                    reference.reference_id,
                )
            )

        if reference.access_level == "METADATA_ONLY" and (
            reference.craft_observation_refs
        ):
            findings.append(
                _finding(
                    "PRO_BENCH.RIGHTS.CRAFT_OBSERVATION_WITH_METADATA_ONLY",
                    (
                        f"reference {reference.reference_id} has craft observations "
                        "without declared craft-access rights"
                    ),
                    reference.reference_id,
                )
            )
        if reference.access_level in {
            "LAWFUL_BOUNDED_TEXT",
            "LICENSED_FULL_ACCESS",
            "PUBLIC_DOMAIN_FULL_ACCESS",
        } and reference.rights_basis == "PUBLIC_METADATA":
            findings.append(
                _finding(
                    "PRO_BENCH.RIGHTS.TEXT_ACCESS_BASIS_INVALID",
                    (
                        f"reference {reference.reference_id} claims text access "
                        "with metadata-only rights basis"
                    ),
                    reference.reference_id,
                )
            )

        if reference.publisher_class == "ESTABLISHED_PUBLISHER":
            established_count += 1
        if _text_access(reference):
            text_access_count += 1

    reference_count = len(references_by_id)
    if reference_count < policy.min_references:
        findings.append(
            _finding(
                "PRO_BENCH.SET.TOO_FEW_REFERENCES",
                (
                    f"benchmark set has {reference_count} references; "
                    f"minimum is {policy.min_references}"
                ),
            )
        )
    distinct_authors = len(author_counts)
    if distinct_authors < policy.min_distinct_authors:
        findings.append(
            _finding(
                "PRO_BENCH.SET.TOO_FEW_AUTHORS",
                (
                    f"benchmark set has {distinct_authors} distinct authors; "
                    f"minimum is {policy.min_distinct_authors}"
                ),
            )
        )
    if reference_count and author_counts:
        largest_author_count = max(author_counts.values())
        fraction = largest_author_count / reference_count
        if fraction > policy.max_single_author_fraction:
            findings.append(
                _finding(
                    "PRO_BENCH.SET.AUTHOR_MONOCULTURE",
                    (
                        f"single-author share {fraction:.3f} exceeds "
                        f"{policy.max_single_author_fraction:.3f}"
                    ),
                )
            )
    if years and max(years) - min(years) < policy.min_publication_span_years:
        findings.append(
            _finding(
                "PRO_BENCH.SET.PUBLICATION_SPAN_TOO_NARROW",
                (
                    f"publication span is {max(years) - min(years)} years; "
                    f"minimum is {policy.min_publication_span_years}"
                ),
            )
        )
    for category in policy.required_categories:
        if category not in categories_seen:
            findings.append(
                _finding(
                    "PRO_BENCH.SET.REQUIRED_CATEGORY_MISSING",
                    f"benchmark set lacks required category {category}",
                    category,
                )
            )
    if established_count < policy.min_established_publisher_references:
        findings.append(
            _finding(
                "PRO_BENCH.SET.ESTABLISHED_PUBLISHER_COVERAGE_LOW",
                (
                    f"benchmark set has {established_count} established-publisher "
                    f"references; minimum is "
                    f"{policy.min_established_publisher_references}"
                ),
            )
        )
    if text_access_count < policy.min_text_access_references:
        findings.append(
            _finding(
                "PRO_BENCH.SET.TEXT_ACCESS_COVERAGE_LOW",
                (
                    f"benchmark set has {text_access_count} lawful text-access "
                    f"references; minimum is {policy.min_text_access_references}"
                ),
            )
        )

    if (
        policy.max_review_age_seconds is not None
        and policy.max_review_age_seconds >= 0
        and now_epoch - benchmark_set.last_review_epoch
        > policy.max_review_age_seconds
    ):
        findings.append(
            _finding(
                "PRO_BENCH.SET.REVIEW_STALE",
                "benchmark set requires a current review before use",
            )
        )
    if policy.max_review_age_seconds is not None and (
        policy.max_review_age_seconds < 0
    ):
        findings.append(
            _finding(
                "PRO_BENCH.POLICY.REVIEW_AGE_INVALID",
                "max_review_age_seconds cannot be negative",
            )
        )

    set_hash = benchmark_set_hash(benchmark_set)
    set_ref = benchmark_set_ref(benchmark_set)
    return BenchmarkSetValidationResult(
        qualified=not findings,
        benchmark_set_ref=set_ref,
        benchmark_set_hash=set_hash,
        findings=tuple(findings),
    )


def _verified_artifact_matches(
    *,
    evaluation: BenchmarkDimensionEvaluation,
    run: ProfessionalFictionBenchmarkRun,
    verified_evaluations: Mapping[str, VerifiedEvaluationArtifact],
    findings: list[ProfessionalBenchmarkFinding],
) -> None:
    artifact = verified_evaluations.get(evaluation.evaluation_ref)
    if artifact is None:
        findings.append(
            _finding(
                "PRO_BENCH.EVALUATION.ARTIFACT_MISSING",
                (
                    f"benchmark dimension {evaluation.dimension} evaluation artifact "
                    "is missing"
                ),
                evaluation.dimension,
                evaluation.evaluation_ref,
            )
        )
        return
    if artifact.evaluation_ref != evaluation.evaluation_ref:
        findings.append(
            _finding(
                "PRO_BENCH.EVALUATION.ARTIFACT_ID_MISMATCH",
                (
                    f"catalog key {evaluation.evaluation_ref} resolves to "
                    f"{artifact.evaluation_ref}"
                ),
                evaluation.dimension,
            )
        )
    if artifact.manuscript_snapshot_ref != run.manuscript_snapshot_ref:
        findings.append(
            _finding(
                "PRO_BENCH.EVALUATION.SNAPSHOT_MISMATCH",
                f"dimension {evaluation.dimension} uses another manuscript snapshot",
                evaluation.dimension,
            )
        )
    if artifact.evaluator_identity != evaluation.evaluator_identity:
        findings.append(
            _finding(
                "PRO_BENCH.EVALUATION.EVALUATOR_MISMATCH",
                f"dimension {evaluation.dimension} evaluator identity mismatch",
                evaluation.dimension,
            )
        )
    if artifact.evaluator_class != evaluation.evaluator_class:
        findings.append(
            _finding(
                "PRO_BENCH.EVALUATION.CLASS_MISMATCH",
                f"dimension {evaluation.dimension} evaluator class mismatch",
                evaluation.dimension,
            )
        )
    if artifact.rubric_ref != evaluation.rubric_ref:
        findings.append(
            _finding(
                "PRO_BENCH.EVALUATION.RUBRIC_MISMATCH",
                f"dimension {evaluation.dimension} rubric mismatch",
                evaluation.dimension,
            )
        )
    expected_purpose = (
        f"PROFESSIONAL_BENCHMARK:{run.checkpoint}:{evaluation.dimension}"
    )
    if artifact.purpose != expected_purpose:
        findings.append(
            _finding(
                "PRO_BENCH.EVALUATION.PURPOSE_MISMATCH",
                (
                    f"dimension {evaluation.dimension} purpose "
                    f"{artifact.purpose} does not match {expected_purpose}"
                ),
                evaluation.dimension,
            )
        )
    if artifact.status != "SUCCEEDED" or not artifact.current:
        findings.append(
            _finding(
                "PRO_BENCH.EVALUATION.NOT_CURRENT_SUCCESS",
                (
                    f"dimension {evaluation.dimension} evaluation must be "
                    "SUCCEEDED and current"
                ),
                evaluation.dimension,
            )
        )


def evaluate_professional_benchmark(
    *,
    run: ProfessionalFictionBenchmarkRun,
    policy: ProfessionalBenchmarkPolicy,
    benchmark_set: FictionBenchmarkSet,
    benchmark_set_validation: BenchmarkSetValidationResult,
    current_manuscript_snapshot_ref: str,
    current_manuscript_snapshot_hash: str,
    current_evaluated_revision_refs: tuple[str, ...],
    verified_evaluations: Mapping[str, VerifiedEvaluationArtifact],
    verified_human_disposition_refs: frozenset[str] = frozenset(),
) -> ProfessionalBenchmarkResult:
    findings: list[ProfessionalBenchmarkFinding] = []

    if policy.checkpoint != run.checkpoint:
        findings.append(
            _finding(
                "PRO_BENCH.RUN.CHECKPOINT_POLICY_MISMATCH",
                (
                    f"run checkpoint {run.checkpoint} differs from policy "
                    f"{policy.checkpoint}"
                ),
            )
        )
    if not run.book_id.strip():
        findings.append(
            _finding("PRO_BENCH.RUN.BOOK_ID_MISSING", "book_id must not be blank")
        )
    if (
        run.manuscript_snapshot_ref != current_manuscript_snapshot_ref
        or run.manuscript_snapshot_hash != current_manuscript_snapshot_hash
    ):
        findings.append(
            _finding(
                "PRO_BENCH.RUN.MANUSCRIPT_STALE",
                "professional benchmark is not bound to current manuscript snapshot",
            )
        )
    if tuple(sorted(set(run.evaluated_revision_refs))) != tuple(
        sorted(set(current_evaluated_revision_refs))
    ):
        findings.append(
            _finding(
                "PRO_BENCH.RUN.REVISIONS_STALE",
                "evaluated revision snapshot differs from current required revisions",
            )
        )
    if not run.evaluated_revision_refs:
        findings.append(
            _finding(
                "PRO_BENCH.RUN.REVISIONS_MISSING",
                "professional benchmark requires evaluated revision refs",
            )
        )
    if len(set(run.evaluated_revision_refs)) != len(run.evaluated_revision_refs):
        findings.append(
            _finding(
                "PRO_BENCH.RUN.DUPLICATE_REVISION_REF",
                "evaluated revision refs contain duplicates",
            )
        )

    current_set_ref = benchmark_set_ref(benchmark_set)
    current_set_hash = benchmark_set_hash(benchmark_set)
    if (
        run.benchmark_set_ref != current_set_ref
        or run.benchmark_set_hash != current_set_hash
    ):
        findings.append(
            _finding(
                "PRO_BENCH.RUN.BENCHMARK_SET_STALE",
                "run is not bound to the exact benchmark-set version/hash",
            )
        )
    if not benchmark_set_validation.qualified:
        findings.append(
            _finding(
                "PRO_BENCH.RUN.BENCHMARK_SET_NOT_QUALIFIED",
                "benchmark set failed its own rights/diversity/readiness gate",
            )
        )
    if (
        benchmark_set_validation.benchmark_set_ref != current_set_ref
        or benchmark_set_validation.benchmark_set_hash != current_set_hash
    ):
        findings.append(
            _finding(
                "PRO_BENCH.RUN.SET_VALIDATION_SNAPSHOT_MISMATCH",
                "benchmark-set validation belongs to another set snapshot",
            )
        )

    if run.mimicry_request_detected:
        findings.append(
            _finding(
                "PRO_BENCH.RIGHTS.MIMICRY_REQUEST_DETECTED",
                (
                    "benchmark run contains a named-author/style imitation request; "
                    "benchmarking may compare craft properties but not request mimicry"
                ),
            )
        )
    if run.protected_expression_reproduction_detected:
        findings.append(
            _finding(
                "PRO_BENCH.RIGHTS.PROTECTED_EXPRESSION_REPRODUCTION",
                "benchmark run detected reproduction of protected reference expression",
            )
        )

    evaluations_by_dimension: dict[str, BenchmarkDimensionEvaluation] = {}
    for evaluation in run.dimension_evaluations:
        if evaluation.dimension not in _VALID_DIMENSIONS:
            findings.append(
                _finding(
                    "PRO_BENCH.DIMENSION.UNKNOWN",
                    f"unknown benchmark dimension {evaluation.dimension}",
                    evaluation.dimension,
                )
            )
            continue
        if evaluation.dimension in evaluations_by_dimension:
            findings.append(
                _finding(
                    "PRO_BENCH.DIMENSION.DUPLICATE",
                    f"duplicate evaluation for {evaluation.dimension}",
                    evaluation.dimension,
                )
            )
            continue
        evaluations_by_dimension[evaluation.dimension] = evaluation

        if not evaluation.evaluation_ref.strip():
            findings.append(
                _finding(
                    "PRO_BENCH.EVALUATION.REF_MISSING",
                    f"dimension {evaluation.dimension} has no evaluation ref",
                    evaluation.dimension,
                )
            )
        if not evaluation.rubric_ref.strip():
            findings.append(
                _finding(
                    "PRO_BENCH.EVALUATION.RUBRIC_MISSING",
                    f"dimension {evaluation.dimension} has no rubric ref",
                    evaluation.dimension,
                )
            )
        if not evaluation.evaluator_identity.strip():
            findings.append(
                _finding(
                    "PRO_BENCH.EVALUATION.EVALUATOR_MISSING",
                    f"dimension {evaluation.dimension} has no evaluator identity",
                    evaluation.dimension,
                )
            )
        elif (
            policy.require_independent_semantic_evaluation
            and evaluation.evaluator_class != "DETERMINISTIC"
            and evaluation.evaluator_identity == run.writer_executor_identity
        ):
            findings.append(
                _finding(
                    "PRO_BENCH.EVALUATION.SAME_WRITER_EXECUTOR",
                    (
                        f"dimension {evaluation.dimension} uses the same executor "
                        "identity as the Writer"
                    ),
                    evaluation.dimension,
                )
            )
        _verified_artifact_matches(
            evaluation=evaluation,
            run=run,
            verified_evaluations=verified_evaluations,
            findings=findings,
        )

    for dimension in sorted(_required_dimensions(policy)):
        if dimension not in evaluations_by_dimension:
            findings.append(
                _finding(
                    "PRO_BENCH.DIMENSION.MISSING",
                    f"required benchmark dimension {dimension} is missing",
                    dimension,
                )
            )

    findings_by_dimension: dict[str, list[FictionBenchmarkFinding]] = {}
    for benchmark_finding in run.findings:
        findings_by_dimension.setdefault(
            benchmark_finding.dimension,
            [],
        ).append(benchmark_finding)
        if benchmark_finding.dimension not in evaluations_by_dimension:
            findings.append(
                _finding(
                    "PRO_BENCH.FINDING.NO_DIMENSION_EVALUATION",
                    (
                        f"finding {benchmark_finding.dimension} has no matching "
                        "dimension evaluation"
                    ),
                    benchmark_finding.dimension,
                )
            )
        matching_evaluation = evaluations_by_dimension.get(
            benchmark_finding.dimension
        )
        if (
            matching_evaluation is not None
            and benchmark_finding.evaluation_ref
            != matching_evaluation.evaluation_ref
        ):
            findings.append(
                _finding(
                    "PRO_BENCH.FINDING.EVALUATION_REF_MISMATCH",
                    (
                        f"finding {benchmark_finding.dimension} is bound to another "
                        "evaluation"
                    ),
                    benchmark_finding.dimension,
                )
            )
        if not benchmark_finding.observation.strip():
            findings.append(
                _finding(
                    "PRO_BENCH.FINDING.OBSERVATION_MISSING",
                    f"finding {benchmark_finding.dimension} has no observation",
                    benchmark_finding.dimension,
                )
            )
        if not benchmark_finding.recommended_action.strip():
            findings.append(
                _finding(
                    "PRO_BENCH.FINDING.ACTION_MISSING",
                    f"finding {benchmark_finding.dimension} has no recommended action",
                    benchmark_finding.dimension,
                )
            )
        if not benchmark_finding.manuscript_evidence_refs:
            findings.append(
                _finding(
                    "PRO_BENCH.FINDING.MANUSCRIPT_EVIDENCE_MISSING",
                    (
                        f"finding {benchmark_finding.dimension} has no manuscript "
                        "evidence refs"
                    ),
                    benchmark_finding.dimension,
                )
            )
        if not benchmark_finding.benchmark_observation_refs:
            findings.append(
                _finding(
                    "PRO_BENCH.FINDING.BENCHMARK_EVIDENCE_MISSING",
                    (
                        f"finding {benchmark_finding.dimension} has no benchmark "
                        "observation refs"
                    ),
                    benchmark_finding.dimension,
                )
            )
        if benchmark_finding.severity == "BLOCKING":
            findings.append(
                _finding(
                    "PRO_BENCH.FINDING.BLOCKING",
                    (
                        f"dimension {benchmark_finding.dimension} has a BLOCKING "
                        "professional benchmark gap"
                    ),
                    benchmark_finding.dimension,
                )
            )
        elif benchmark_finding.severity == "MAJOR":
            if (
                benchmark_finding.human_disposition_ref is None
                or not benchmark_finding.human_disposition_ref.strip()
            ):
                findings.append(
                    _finding(
                        "PRO_BENCH.FINDING.MAJOR_UNDISPOSED",
                        (
                            f"dimension {benchmark_finding.dimension} has MAJOR gap "
                            "without human disposition"
                        ),
                        benchmark_finding.dimension,
                    )
                )
            elif (
                benchmark_finding.human_disposition_ref
                not in verified_human_disposition_refs
            ):
                findings.append(
                    _finding(
                        "PRO_BENCH.FINDING.HUMAN_DISPOSITION_UNVERIFIED",
                        (
                            f"dimension {benchmark_finding.dimension} has unverified "
                            "human disposition"
                        ),
                        benchmark_finding.dimension,
                        benchmark_finding.human_disposition_ref,
                    )
                )

    for dimension, evaluation in evaluations_by_dimension.items():
        dimension_findings = findings_by_dimension.get(dimension, [])
        severities = {item.severity for item in dimension_findings}
        if evaluation.status == "PASS" and severities.intersection(
            {"BLOCKING", "MAJOR"}
        ):
            findings.append(
                _finding(
                    "PRO_BENCH.DIMENSION.PASS_CONTRADICTS_FINDINGS",
                    (
                        f"dimension {dimension} is PASS but has material findings"
                    ),
                    dimension,
                )
            )
        if evaluation.status == "BLOCKING_GAP" and "BLOCKING" not in severities:
            findings.append(
                _finding(
                    "PRO_BENCH.DIMENSION.BLOCKING_WITHOUT_FINDING",
                    (
                        f"dimension {dimension} is BLOCKING_GAP without BLOCKING finding"
                    ),
                    dimension,
                )
            )
        if evaluation.status == "MAJOR_GAP" and "MAJOR" not in severities:
            findings.append(
                _finding(
                    "PRO_BENCH.DIMENSION.MAJOR_WITHOUT_FINDING",
                    f"dimension {dimension} is MAJOR_GAP without MAJOR finding",
                    dimension,
                )
            )

    has_blocking = any(
        item.severity == "BLOCKING" for item in run.findings
    ) or any(
        item.status == "BLOCKING_GAP" for item in run.dimension_evaluations
    )
    has_major = any(item.severity == "MAJOR" for item in run.findings) or any(
        item.status == "MAJOR_GAP" for item in run.dimension_evaluations
    )

    if has_blocking and run.readiness_band != "BELOW_PROFESSIONAL_FLOOR":
        findings.append(
            _finding(
                "PRO_BENCH.BAND.BLOCKING_HIDDEN",
                "BLOCKING gap requires BELOW_PROFESSIONAL_FLOOR readiness band",
            )
        )
    elif (
        not has_blocking
        and has_major
        and _BAND_ORDER[run.readiness_band]
        > _BAND_ORDER["PROFESSIONAL_GAPS_REMAIN"]
    ):
        findings.append(
            _finding(
                "PRO_BENCH.BAND.MAJOR_GAP_HIDDEN",
                "MAJOR gaps cannot be hidden by a professional-range readiness band",
            )
        )
    elif (
        not has_blocking
        and not has_major
        and _BAND_ORDER[run.readiness_band]
        < _BAND_ORDER["PROFESSIONAL_RANGE_CANDIDATE"]
    ):
        findings.append(
            _finding(
                "PRO_BENCH.BAND.UNDERSTATED_WITHOUT_MATERIAL_GAPS",
                (
                    "run with no material gaps must use at least "
                    "PROFESSIONAL_RANGE_CANDIDATE"
                ),
            )
        )

    if run.readiness_band == "STRONG_PROFESSIONAL_CANDIDATE":
        if (
            run.strong_candidate_human_ref is None
            or not run.strong_candidate_human_ref.strip()
        ):
            findings.append(
                _finding(
                    "PRO_BENCH.BAND.STRONG_HUMAN_CONFIRMATION_MISSING",
                    (
                        "STRONG_PROFESSIONAL_CANDIDATE requires explicit human "
                        "confirmation"
                    ),
                )
            )
        elif run.strong_candidate_human_ref not in verified_human_disposition_refs:
            findings.append(
                _finding(
                    "PRO_BENCH.BAND.STRONG_HUMAN_CONFIRMATION_UNVERIFIED",
                    "strong-candidate human confirmation is not verified",
                    run.strong_candidate_human_ref,
                )
            )

    if (
        _BAND_ORDER[run.readiness_band]
        < _BAND_ORDER[policy.minimum_readiness_band]
    ):
        findings.append(
            _finding(
                "PRO_BENCH.BAND.BELOW_POLICY_MINIMUM",
                (
                    f"readiness {run.readiness_band} is below required "
                    f"{policy.minimum_readiness_band}"
                ),
            )
        )

    result_ref = _run_ref(run=run, policy=policy)
    return ProfessionalBenchmarkResult(
        qualified=not findings,
        professional_benchmark_ref=result_ref,
        benchmark_set_ref=current_set_ref,
        readiness_band=run.readiness_band,
        findings=tuple(findings),
    )


def verify_professional_benchmark(
    *,
    prior_professional_benchmark_ref: str,
    run: ProfessionalFictionBenchmarkRun,
    policy: ProfessionalBenchmarkPolicy,
    benchmark_set: FictionBenchmarkSet,
    benchmark_set_validation: BenchmarkSetValidationResult,
    current_manuscript_snapshot_ref: str,
    current_manuscript_snapshot_hash: str,
    current_evaluated_revision_refs: tuple[str, ...],
    verified_evaluations: Mapping[str, VerifiedEvaluationArtifact],
    verified_human_disposition_refs: frozenset[str] = frozenset(),
) -> ProfessionalBenchmarkVerification:
    current = evaluate_professional_benchmark(
        run=run,
        policy=policy,
        benchmark_set=benchmark_set,
        benchmark_set_validation=benchmark_set_validation,
        current_manuscript_snapshot_ref=current_manuscript_snapshot_ref,
        current_manuscript_snapshot_hash=current_manuscript_snapshot_hash,
        current_evaluated_revision_refs=current_evaluated_revision_refs,
        verified_evaluations=verified_evaluations,
        verified_human_disposition_refs=verified_human_disposition_refs,
    )
    if not current.qualified:
        return ProfessionalBenchmarkVerification(
            valid=False,
            reason="CURRENT_PROFESSIONAL_BENCHMARK_BLOCKED",
            current_result=current,
        )
    if current.professional_benchmark_ref != prior_professional_benchmark_ref:
        return ProfessionalBenchmarkVerification(
            valid=False,
            reason="PROFESSIONAL_BENCHMARK_SNAPSHOT_CHANGED",
            current_result=current,
        )
    return ProfessionalBenchmarkVerification(
        valid=True,
        reason=None,
        current_result=current,
    )


def sample_benchmark_evidence_from_result(
    *,
    result: ProfessionalBenchmarkResult,
    evaluator_identity: str,
) -> ProfessionalBenchmarkEvidence:
    """Bridge MYS-08 evidence into MYS-06 representative-sample readiness."""
    return ProfessionalBenchmarkEvidence(
        status="PASS" if result.qualified else "BLOCKING_GAP",
        benchmark_ref=result.professional_benchmark_ref,
        benchmark_set_ref=result.benchmark_set_ref,
        evaluator_identity=evaluator_identity,
    )
