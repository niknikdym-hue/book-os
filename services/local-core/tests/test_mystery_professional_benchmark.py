from __future__ import annotations

from dataclasses import replace
import hashlib

from book_os_core.mystery_bench_validation import VerifiedEvaluationArtifact
from book_os_core.mystery_professional_benchmark import (
    BenchmarkDimensionEvaluation,
    BenchmarkReference,
    BenchmarkSetPolicy,
    FictionBenchmarkFinding,
    FictionBenchmarkSet,
    ProfessionalBenchmarkPolicy,
    ProfessionalFictionBenchmarkRun,
    benchmark_set_hash,
    benchmark_set_ref,
    evaluate_professional_benchmark,
    sample_benchmark_evidence_from_result,
    validate_benchmark_set,
    verify_professional_benchmark,
)

NOW = 1_800_000_000
SNAPSHOT_REF = "bookbench-snapshot:book-1:v1"
SNAPSHOT_HASH = hashlib.sha256(b"benchmark-manuscript-v1").hexdigest()
WRITER_ID = "openai/writer-standard"
REVISION_REFS = (
    "scene-open@rev-1:" + hashlib.sha256(b"scene-open").hexdigest(),
    "scene-dialogue@rev-1:" + hashlib.sha256(b"scene-dialogue").hexdigest(),
    "scene-tension@rev-1:" + hashlib.sha256(b"scene-tension").hexdigest(),
)


def _reference(
    index: int,
    *,
    year: int,
    categories: tuple[str, ...],
    publisher_class: str = "ESTABLISHED_PUBLISHER",
    access_level: str = "LAWFUL_BOUNDED_TEXT",
    rights_basis: str = "USER_OWNED",
    author_ref: str | None = None,
) -> BenchmarkReference:
    reference_id = f"ref-{index}"
    craft_refs = (
        (f"benchmark-observation:{reference_id}:dialogue",)
        if access_level != "METADATA_ONLY"
        else ()
    )
    return BenchmarkReference(
        reference_id=reference_id,
        work_ref=f"work:{index}",
        author_ref=author_ref or f"author:{index}",
        publication_year=year,
        publisher_class=publisher_class,  # type: ignore[arg-type]
        publisher_ref=(
            f"publisher:{index}"
            if publisher_class == "ESTABLISHED_PUBLISHER"
            else None
        ),
        format_codes=("TEXT", "AUDIO") if index == 6 else ("TEXT",),
        selection_categories=categories,  # type: ignore[arg-type]
        selection_reason=f"reference {index} covers a distinct professional signal",
        prohibited_inference="do not imitate authorial voice or signature expression",
        access_level=access_level,  # type: ignore[arg-type]
        rights_basis=rights_basis,  # type: ignore[arg-type]
        rights_ref=f"rights:{index}",
        source_metadata_ref=f"metadata:{index}",
        craft_observation_refs=craft_refs,
    )


def _benchmark_set() -> FictionBenchmarkSet:
    return FictionBenchmarkSet(
        benchmark_set_id="modern-mystery-ru",
        version=1,
        subgenre="modern-mystical-detective",
        target_market="RU-commercial-fiction",
        language="ru",
        audience_ref="16+",
        publication_window="2012-2026",
        last_review_epoch=NOW - 100,
        references=(
            _reference(
                1,
                year=2012,
                categories=("COMMERCIAL_SUCCESS", "DURABLE_BACKLIST"),
            ),
            _reference(
                2,
                year=2015,
                categories=("CRITICAL_RESPECT",),
            ),
            _reference(
                3,
                year=2018,
                categories=("COMMERCIAL_SUCCESS",),
            ),
            _reference(
                4,
                year=2020,
                categories=("CRITICAL_RESPECT",),
            ),
            _reference(
                5,
                year=2024,
                categories=("RECENT_EXPECTATION", "CRITICAL_RESPECT"),
                publisher_class="SMALL_PRESS",
                access_level="DERIVED_NON_RECONSTRUCTIVE",
                rights_basis="OTHER_DOCUMENTED",
            ),
            _reference(
                6,
                year=2026,
                categories=(
                    "RECENT_EXPECTATION",
                    "DURABLE_BACKLIST",
                    "AUDIO_REFERENCE",
                ),
                publisher_class="OTHER",
                access_level="METADATA_ONLY",
                rights_basis="PUBLIC_METADATA",
            ),
        ),
    )


SET_POLICY = BenchmarkSetPolicy(
    expected_subgenre="modern-mystical-detective",
    expected_target_market="RU-commercial-fiction",
    expected_language="ru",
    min_references=6,
    min_distinct_authors=5,
    min_publication_span_years=10,
    max_single_author_fraction=0.34,
    min_text_access_references=4,
    required_categories=(
        "COMMERCIAL_SUCCESS",
        "CRITICAL_RESPECT",
        "DURABLE_BACKLIST",
        "RECENT_EXPECTATION",
    ),
    min_established_publisher_references=4,
    max_review_age_seconds=365 * 24 * 60 * 60,
)

SAMPLE_POLICY = ProfessionalBenchmarkPolicy(
    checkpoint="REPRESENTATIVE_SAMPLE",
    audio_selected=False,
    minimum_readiness_band="PROFESSIONAL_RANGE_CANDIDATE",
)

SAMPLE_DIMS = (
    "SCENES",
    "DIALOGUE",
    "SUSPENSE",
    "PROSE_VOICE",
    "SETTING",
    "EMOTIONAL_ARCHITECTURE",
    "ORIGINALITY",
)


def _dimension(
    dimension: str,
    *,
    status: str = "PASS",
    evaluator_identity: str = "benchmark-judge/model-b",
    evaluator_class: str = "LLM_JUDGE",
    comparison_mode: str = "CRITERION",
) -> BenchmarkDimensionEvaluation:
    return BenchmarkDimensionEvaluation(
        dimension=dimension,  # type: ignore[arg-type]
        status=status,  # type: ignore[arg-type]
        evaluation_ref=f"professional-eval:{dimension}:v1",
        rubric_ref=f"professional-fiction-rubric:{dimension}:v1",
        evaluator_identity=evaluator_identity,
        evaluator_class=evaluator_class,  # type: ignore[arg-type]
        comparison_mode=comparison_mode,  # type: ignore[arg-type]
    )


def _run(
    benchmark_set: FictionBenchmarkSet,
    *,
    checkpoint: str = "REPRESENTATIVE_SAMPLE",
    dimensions: tuple[BenchmarkDimensionEvaluation, ...] | None = None,
    findings: tuple[FictionBenchmarkFinding, ...] = (),
    readiness_band: str = "PROFESSIONAL_RANGE_CANDIDATE",
    mimicry: bool = False,
    protected_expression: bool = False,
    strong_ref: str | None = None,
) -> ProfessionalFictionBenchmarkRun:
    return ProfessionalFictionBenchmarkRun(
        book_id="book-1",
        checkpoint=checkpoint,  # type: ignore[arg-type]
        manuscript_snapshot_ref=SNAPSHOT_REF,
        manuscript_snapshot_hash=SNAPSHOT_HASH,
        evaluated_revision_refs=REVISION_REFS,
        benchmark_set_ref=benchmark_set_ref(benchmark_set),
        benchmark_set_hash=benchmark_set_hash(benchmark_set),
        writer_executor_identity=WRITER_ID,
        dimension_evaluations=(
            dimensions
            if dimensions is not None
            else tuple(_dimension(value) for value in SAMPLE_DIMS)
        ),
        findings=findings,
        readiness_band=readiness_band,  # type: ignore[arg-type]
        mimicry_request_detected=mimicry,
        protected_expression_reproduction_detected=protected_expression,
        strong_candidate_human_ref=strong_ref,
    )


def _verified_evaluations(
    run: ProfessionalFictionBenchmarkRun,
) -> dict[str, VerifiedEvaluationArtifact]:
    return {
        evaluation.evaluation_ref: VerifiedEvaluationArtifact(
            evaluation_ref=evaluation.evaluation_ref,
            manuscript_snapshot_ref=run.manuscript_snapshot_ref,
            evaluator_identity=evaluation.evaluator_identity,
            evaluator_class=evaluation.evaluator_class,
            rubric_ref=evaluation.rubric_ref,
            purpose=(
                f"PROFESSIONAL_BENCHMARK:{run.checkpoint}:"
                f"{evaluation.dimension}"
            ),
            status="SUCCEEDED",
            current=True,
        )
        for evaluation in run.dimension_evaluations
    }


def _set_validation(
    benchmark_set: FictionBenchmarkSet,
    *,
    policy: BenchmarkSetPolicy = SET_POLICY,
):
    return validate_benchmark_set(
        benchmark_set=benchmark_set,
        policy=policy,
        now_epoch=NOW,
    )


def _evaluate(
    run: ProfessionalFictionBenchmarkRun,
    benchmark_set: FictionBenchmarkSet,
    *,
    policy: ProfessionalBenchmarkPolicy = SAMPLE_POLICY,
    set_policy: BenchmarkSetPolicy = SET_POLICY,
    verified_evaluations: dict[str, VerifiedEvaluationArtifact] | None = None,
    manuscript_evidence_refs: frozenset[str] = frozenset(),
    human_refs: frozenset[str] = frozenset(),
    snapshot_ref: str = SNAPSHOT_REF,
    snapshot_hash: str = SNAPSHOT_HASH,
    revision_refs: tuple[str, ...] = REVISION_REFS,
):
    set_result = _set_validation(benchmark_set, policy=set_policy)
    return evaluate_professional_benchmark(
        run=run,
        policy=policy,
        benchmark_set=benchmark_set,
        benchmark_set_validation=set_result,
        current_manuscript_snapshot_ref=snapshot_ref,
        current_manuscript_snapshot_hash=snapshot_hash,
        current_evaluated_revision_refs=revision_refs,
        verified_evaluations=(
            verified_evaluations
            if verified_evaluations is not None
            else _verified_evaluations(run)
        ),
        verified_manuscript_evidence_refs=manuscript_evidence_refs,
        verified_human_disposition_refs=human_refs,
    )


def _codes(result) -> set[str]:  # type: ignore[no-untyped-def]
    return {finding.code for finding in result.findings}


def test_clean_benchmark_set_passes_rights_diversity_and_relevance_gate() -> None:
    benchmark_set = _benchmark_set()

    result = _set_validation(benchmark_set)

    assert result.qualified
    assert result.findings == ()
    assert result.benchmark_set_ref == benchmark_set_ref(benchmark_set)
    assert result.benchmark_set_hash == benchmark_set_hash(benchmark_set)


def test_benchmark_set_target_market_language_and_subgenre_are_exact() -> None:
    benchmark_set = _benchmark_set()
    wrong = replace(
        SET_POLICY,
        expected_subgenre="romance",
        expected_target_market="US-general",
        expected_language="en",
    )

    result = _set_validation(benchmark_set, policy=wrong)
    codes = _codes(result)

    assert "PRO_BENCH.SET.SUBGENRE_MISMATCH" in codes
    assert "PRO_BENCH.SET.TARGET_MARKET_MISMATCH" in codes
    assert "PRO_BENCH.SET.LANGUAGE_MISMATCH" in codes


def test_benchmark_set_rejects_monoculture_and_missing_market_coverage() -> None:
    base = _benchmark_set()
    repeated_author = tuple(
        replace(reference, author_ref="same-author")
        for reference in base.references
    )
    sparse_policy = replace(
        SET_POLICY,
        min_distinct_authors=5,
        required_categories=(
            *SET_POLICY.required_categories,
            "AUDIO_REFERENCE",
        ),
        min_established_publisher_references=6,
        min_text_access_references=6,
    )
    result = _set_validation(
        replace(base, references=repeated_author),
        policy=sparse_policy,
    )
    codes = _codes(result)

    assert "PRO_BENCH.SET.TOO_FEW_AUTHORS" in codes
    assert "PRO_BENCH.SET.AUTHOR_MONOCULTURE" in codes
    assert "PRO_BENCH.SET.ESTABLISHED_PUBLISHER_COVERAGE_LOW" in codes
    assert "PRO_BENCH.SET.TEXT_ACCESS_COVERAGE_LOW" in codes


def test_rights_gate_rejects_embedded_protected_text_and_false_text_access_basis() -> None:
    benchmark_set = _benchmark_set()
    first = replace(
        benchmark_set.references[0],
        raw_protected_text_embedded=True,
        rights_basis="PUBLIC_METADATA",
    )
    revised = replace(
        benchmark_set,
        references=(first, *benchmark_set.references[1:]),
    )

    result = _set_validation(revised)
    codes = _codes(result)

    assert "PRO_BENCH.RIGHTS.PROTECTED_TEXT_EMBEDDED" in codes
    assert "PRO_BENCH.RIGHTS.TEXT_ACCESS_BASIS_INVALID" in codes
    assert not result.qualified


def test_stale_benchmark_set_review_blocks_use() -> None:
    benchmark_set = replace(
        _benchmark_set(),
        last_review_epoch=NOW - (2 * 365 * 24 * 60 * 60),
    )

    result = _set_validation(benchmark_set)

    assert "PRO_BENCH.SET.REVIEW_STALE" in _codes(result)
    assert not result.qualified


def test_clean_representative_sample_benchmark_passes_without_global_score() -> None:
    benchmark_set = _benchmark_set()
    run = _run(benchmark_set)

    result = _evaluate(run, benchmark_set)

    assert result.qualified
    assert result.findings == ()
    assert result.readiness_band == "PROFESSIONAL_RANGE_CANDIDATE"
    assert result.professional_benchmark_ref.startswith(
        "professional-fiction-benchmark:"
    )


def test_missing_required_dimension_or_audio_dimension_blocks() -> None:
    benchmark_set = _benchmark_set()
    run = _run(
        benchmark_set,
        dimensions=tuple(
            _dimension(value)
            for value in SAMPLE_DIMS
            if value != "DIALOGUE"
        ),
    )
    missing = _evaluate(run, benchmark_set)
    assert "PRO_BENCH.DIMENSION.MISSING" in _codes(missing)

    audio_policy = replace(SAMPLE_POLICY, audio_selected=True)
    audio_run = _run(benchmark_set)
    audio = _evaluate(audio_run, benchmark_set, policy=audio_policy)
    assert "PRO_BENCH.DIMENSION.MISSING" in _codes(audio)


def test_evaluation_artifact_must_match_snapshot_evaluator_class_rubric_and_purpose() -> None:
    benchmark_set = _benchmark_set()
    run = _run(benchmark_set)
    target = run.dimension_evaluations[0]
    baseline = _verified_evaluations(run)[target.evaluation_ref]

    variants = (
        (
            replace(baseline, manuscript_snapshot_ref="snapshot:other"),
            "PRO_BENCH.EVALUATION.SNAPSHOT_MISMATCH",
        ),
        (
            replace(baseline, evaluator_identity="other/judge"),
            "PRO_BENCH.EVALUATION.EVALUATOR_MISMATCH",
        ),
        (
            replace(baseline, evaluator_class="SEMANTIC"),
            "PRO_BENCH.EVALUATION.CLASS_MISMATCH",
        ),
        (
            replace(baseline, rubric_ref="wrong-rubric"),
            "PRO_BENCH.EVALUATION.RUBRIC_MISMATCH",
        ),
        (
            replace(baseline, purpose="PROFESSIONAL_BENCHMARK:FINAL:SCENES"),
            "PRO_BENCH.EVALUATION.PURPOSE_MISMATCH",
        ),
        (
            replace(baseline, current=False),
            "PRO_BENCH.EVALUATION.NOT_CURRENT_SUCCESS",
        ),
    )

    for artifact, expected in variants:
        verified = _verified_evaluations(run)
        verified[target.evaluation_ref] = artifact
        result = _evaluate(
            run,
            benchmark_set,
            verified_evaluations=verified,
        )
        assert expected in _codes(result)
        assert not result.qualified


def test_writer_cannot_be_sole_semantic_professional_benchmark_judge() -> None:
    benchmark_set = _benchmark_set()
    dimensions = tuple(
        replace(
            _dimension(value),
            evaluator_identity=WRITER_ID,
        )
        if value == "PROSE_VOICE"
        else _dimension(value)
        for value in SAMPLE_DIMS
    )
    run = _run(benchmark_set, dimensions=dimensions)

    result = _evaluate(run, benchmark_set)

    assert "PRO_BENCH.EVALUATION.SAME_WRITER_EXECUTOR" in _codes(result)
    assert not result.qualified


def test_mimicry_or_protected_expression_reproduction_blocks() -> None:
    benchmark_set = _benchmark_set()

    mimicry = _evaluate(_run(benchmark_set, mimicry=True), benchmark_set)
    protected = _evaluate(
        _run(benchmark_set, protected_expression=True),
        benchmark_set,
    )

    assert "PRO_BENCH.RIGHTS.MIMICRY_REQUEST_DETECTED" in _codes(mimicry)
    assert "PRO_BENCH.RIGHTS.PROTECTED_EXPRESSION_REPRODUCTION" in _codes(
        protected
    )


def test_benchmark_findings_require_verified_manuscript_and_set_observation_refs() -> None:
    benchmark_set = _benchmark_set()
    evaluation = _dimension("PROSE_VOICE", status="MAJOR_GAP")
    finding = FictionBenchmarkFinding(
        dimension="PROSE_VOICE",
        severity="MAJOR",
        observation="voice is flatter than the benchmark range",
        recommended_action="rebuild the scene voice profile",
        manuscript_evidence_refs=("manuscript-evidence:unknown",),
        benchmark_observation_refs=("benchmark-observation:unknown",),
        evaluation_ref=evaluation.evaluation_ref,
        non_infringing_comparison="our prose has lower viewpoint specificity",
        human_disposition_ref="human:accept-major",
    )
    run = _run(
        benchmark_set,
        dimensions=tuple(
            evaluation if value == "PROSE_VOICE" else _dimension(value)
            for value in SAMPLE_DIMS
        ),
        findings=(finding,),
        readiness_band="PROFESSIONAL_GAPS_REMAIN",
    )
    policy = replace(
        SAMPLE_POLICY,
        minimum_readiness_band="PROFESSIONAL_GAPS_REMAIN",
    )

    result = _evaluate(
        run,
        benchmark_set,
        policy=policy,
        human_refs=frozenset({"human:accept-major"}),
    )
    codes = _codes(result)

    assert "PRO_BENCH.FINDING.MANUSCRIPT_EVIDENCE_UNVERIFIED" in codes
    assert "PRO_BENCH.FINDING.BENCHMARK_EVIDENCE_UNVERIFIED" in codes


def test_major_gap_can_be_human_disposed_but_cannot_hide_in_professional_range_band() -> None:
    benchmark_set = _benchmark_set()
    evaluation = _dimension("PROSE_VOICE", status="MAJOR_GAP")
    observation_ref = benchmark_set.references[0].craft_observation_refs[0]
    finding = FictionBenchmarkFinding(
        dimension="PROSE_VOICE",
        severity="MAJOR",
        observation="voice needs another literary pass",
        recommended_action="revise prose voice before range-candidate gate",
        manuscript_evidence_refs=("manuscript-evidence:voice-1",),
        benchmark_observation_refs=(observation_ref,),
        evaluation_ref=evaluation.evaluation_ref,
        non_infringing_comparison="our viewpoint embodiment is less specific",
        human_disposition_ref="human:accept-for-mid-stage",
    )
    dimensions = tuple(
        evaluation if value == "PROSE_VOICE" else _dimension(value)
        for value in SAMPLE_DIMS
    )

    gaps_policy = replace(
        SAMPLE_POLICY,
        minimum_readiness_band="PROFESSIONAL_GAPS_REMAIN",
    )
    gaps_run = _run(
        benchmark_set,
        dimensions=dimensions,
        findings=(finding,),
        readiness_band="PROFESSIONAL_GAPS_REMAIN",
    )
    allowed = _evaluate(
        gaps_run,
        benchmark_set,
        policy=gaps_policy,
        manuscript_evidence_refs=frozenset({"manuscript-evidence:voice-1"}),
        human_refs=frozenset({"human:accept-for-mid-stage"}),
    )
    assert allowed.qualified

    hidden_run = replace(
        gaps_run,
        readiness_band="PROFESSIONAL_RANGE_CANDIDATE",
    )
    hidden = _evaluate(
        hidden_run,
        benchmark_set,
        policy=gaps_policy,
        manuscript_evidence_refs=frozenset({"manuscript-evidence:voice-1"}),
        human_refs=frozenset({"human:accept-for-mid-stage"}),
    )
    assert "PRO_BENCH.BAND.MAJOR_GAP_HIDDEN" in _codes(hidden)
    assert not hidden.qualified


def test_blocking_gap_can_never_be_waived_or_hidden() -> None:
    benchmark_set = _benchmark_set()
    evaluation = _dimension("SCENES", status="BLOCKING_GAP")
    observation_ref = benchmark_set.references[0].craft_observation_refs[0]
    finding = FictionBenchmarkFinding(
        dimension="SCENES",
        severity="BLOCKING",
        observation="representative scene has no consequential state change",
        recommended_action="rebuild scene architecture",
        manuscript_evidence_refs=("manuscript-evidence:scene-1",),
        benchmark_observation_refs=(observation_ref,),
        evaluation_ref=evaluation.evaluation_ref,
        non_infringing_comparison="professional references show stronger consequence",
        human_disposition_ref="human:waive-attempt",
    )
    run = _run(
        benchmark_set,
        dimensions=tuple(
            evaluation if value == "SCENES" else _dimension(value)
            for value in SAMPLE_DIMS
        ),
        findings=(finding,),
        readiness_band="PROFESSIONAL_RANGE_CANDIDATE",
    )

    result = _evaluate(
        run,
        benchmark_set,
        manuscript_evidence_refs=frozenset({"manuscript-evidence:scene-1"}),
        human_refs=frozenset({"human:waive-attempt"}),
    )
    codes = _codes(result)

    assert "PRO_BENCH.FINDING.BLOCKING" in codes
    assert "PRO_BENCH.BAND.BLOCKING_HIDDEN" in codes
    assert not result.qualified


def test_strong_professional_candidate_requires_verified_human_confirmation() -> None:
    benchmark_set = _benchmark_set()
    run = _run(
        benchmark_set,
        readiness_band="STRONG_PROFESSIONAL_CANDIDATE",
        strong_ref="human:strong-candidate",
    )

    unverified = _evaluate(run, benchmark_set)
    assert "PRO_BENCH.BAND.STRONG_HUMAN_CONFIRMATION_UNVERIFIED" in _codes(
        unverified
    )

    verified = _evaluate(
        run,
        benchmark_set,
        human_refs=frozenset({"human:strong-candidate"}),
    )
    assert verified.qualified


def test_exact_benchmark_set_and_manuscript_snapshots_are_version_bound() -> None:
    benchmark_set = _benchmark_set()
    run = _run(benchmark_set)

    stale_manuscript = _evaluate(
        run,
        benchmark_set,
        snapshot_hash=hashlib.sha256(b"new-manuscript").hexdigest(),
    )
    assert "PRO_BENCH.RUN.MANUSCRIPT_STALE" in _codes(stale_manuscript)

    new_set = replace(benchmark_set, version=2)
    stale_set = _evaluate(run, new_set)
    assert "PRO_BENCH.RUN.BENCHMARK_SET_STALE" in _codes(stale_set)


def test_professional_benchmark_ref_is_version_bound_to_policy_and_evidence() -> None:
    benchmark_set = _benchmark_set()
    run = _run(benchmark_set)
    set_result = _set_validation(benchmark_set)
    result = _evaluate(run, benchmark_set)
    assert result.qualified

    verified = verify_professional_benchmark(
        prior_professional_benchmark_ref=result.professional_benchmark_ref,
        run=run,
        policy=SAMPLE_POLICY,
        benchmark_set=benchmark_set,
        benchmark_set_validation=set_result,
        current_manuscript_snapshot_ref=SNAPSHOT_REF,
        current_manuscript_snapshot_hash=SNAPSHOT_HASH,
        current_evaluated_revision_refs=REVISION_REFS,
        verified_evaluations=_verified_evaluations(run),
        verified_manuscript_evidence_refs=frozenset(),
    )
    assert verified.valid

    stricter = replace(
        SAMPLE_POLICY,
        minimum_readiness_band="STRONG_PROFESSIONAL_CANDIDATE",
    )
    changed = verify_professional_benchmark(
        prior_professional_benchmark_ref=result.professional_benchmark_ref,
        run=run,
        policy=stricter,
        benchmark_set=benchmark_set,
        benchmark_set_validation=set_result,
        current_manuscript_snapshot_ref=SNAPSHOT_REF,
        current_manuscript_snapshot_hash=SNAPSHOT_HASH,
        current_evaluated_revision_refs=REVISION_REFS,
        verified_evaluations=_verified_evaluations(run),
        verified_manuscript_evidence_refs=frozenset(),
    )
    assert not changed.valid


def test_mys08_result_bridges_into_mys06_sample_benchmark_evidence() -> None:
    benchmark_set = _benchmark_set()
    run = _run(benchmark_set)
    result = _evaluate(run, benchmark_set)

    evidence = sample_benchmark_evidence_from_result(
        result=result,
        evaluator_identity="professional-benchmark-gate",
    )

    assert evidence.status == "PASS"
    assert evidence.benchmark_ref == result.professional_benchmark_ref
    assert evidence.benchmark_set_ref == result.benchmark_set_ref


def test_runtime_unknown_codes_fail_closed_without_key_errors() -> None:
    benchmark_set = _benchmark_set()
    evaluation = replace(
        _dimension("SCENES"),
        status="ALIEN_STATUS",  # type: ignore[arg-type]
        comparison_mode="ALIEN_MODE",  # type: ignore[arg-type]
    )
    run = _run(
        benchmark_set,
        dimensions=tuple(
            evaluation if value == "SCENES" else _dimension(value)
            for value in SAMPLE_DIMS
        ),
        readiness_band="ALIEN_BAND",
    )

    result = _evaluate(run, benchmark_set)
    codes = _codes(result)

    assert "PRO_BENCH.EVALUATION.STATUS_UNKNOWN" in codes
    assert "PRO_BENCH.EVALUATION.COMPARISON_MODE_UNKNOWN" in codes
    assert "PRO_BENCH.BAND.UNKNOWN" in codes
    assert not result.qualified
