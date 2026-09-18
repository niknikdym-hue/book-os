from __future__ import annotations

from dataclasses import replace
import hashlib

from book_os_core.mystery_editorial_gate import (
    ExternalWritingReadiness,
    readiness_with_sample_qualification,
)
from book_os_core.mystery_sample_qualification import (
    ProfessionalBenchmarkEvidence,
    RepresentativeSamplePack,
    RepresentativeSamplePolicy,
    SampleArtifact,
    SampleEvaluationEvidence,
    StyleProfileSnapshot,
    WriterCandidate,
    qualify_representative_sample,
    verify_writer_qualification,
)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


STYLE = StyleProfileSnapshot(
    profile_id="style-1",
    content_hash=_hash("style-v1"),
    status="APPROVED",
)
WRITER = WriterCandidate(
    writer_candidate_id="writer-a",
    executor_identity="openai/model-a/high",
    provider="openai",
    model="model-a",
    route_ref="route:standard-writer:v1",
    prompt_ref="prompt:fiction-scene:v1",
)
AUTHORITY_REFS = (
    "story@rev-1:" + _hash("story"),
    "narrative@rev-1:" + _hash("narrative"),
    "case@rev-1:" + _hash("case"),
)
POLICY = RepresentativeSamplePolicy(
    min_distinct_samples=2,
    min_characters_per_sample=1000,
    require_tension_mystic=True,
)
CORE = (
    "NARRATIVE_CONTRACT",
    "POV_INTEGRITY",
    "VOICE_STYLE",
    "SCENE_CAUSALITY",
    "ANTI_CLICHE",
    "FACTUAL_REALISM",
)


def _sample(
    sample_id: str,
    scene_id: str,
    function: str,
    *,
    revision_class: str = "NONE",
    writer_id: str = "writer-a",
    writer_hash: str | None = None,
    final_hash: str | None = None,
    character_count: int = 4000,
) -> SampleArtifact:
    output_hash = writer_hash or _hash(f"{sample_id}:writer")
    end_hash = final_hash or output_hash
    return SampleArtifact(
        sample_id=sample_id,
        scene_id=scene_id,
        scene_revision_ref=f"scene-contract:book-1:{scene_id}@rev-1:{_hash(scene_id)}",
        writing_admission_id=f"writing-admission:{sample_id}",
        writer_candidate_id=writer_id,
        writer_output_hash=output_hash,
        final_text_hash=end_hash,
        final_character_count=character_count,
        function_codes=(function,),  # type: ignore[arg-type]
        post_writer_revision_class=revision_class,  # type: ignore[arg-type]
        post_writer_revision_ref=(
            None if revision_class == "NONE" else f"revision-evidence:{sample_id}:v1"
        ),
    )


def _evaluation(
    sample: SampleArtifact,
    *,
    status: str = "PASS",
    evaluator_identity: str = "judge/model-b/high",
) -> SampleEvaluationEvidence:
    coverage = list(CORE)
    if "INVESTIGATION_DIALOGUE" in sample.function_codes:
        coverage.append("DIALOGUE")
    if "TENSION_MYSTIC" in sample.function_codes:
        coverage.append("SUSPENSE_INFORMATION_CONTROL")
    return SampleEvaluationEvidence(
        sample_id=sample.sample_id,
        status=status,  # type: ignore[arg-type]
        coverage_dimensions=tuple(coverage),  # type: ignore[arg-type]
        evaluation_ref=f"sample-eval:{sample.sample_id}:v1",
        evaluator_identity=evaluator_identity,
    )


def _benchmark(
    *,
    status: str = "PASS",
    evaluator_identity: str = "benchmark/model-c/high",
) -> ProfessionalBenchmarkEvidence:
    return ProfessionalBenchmarkEvidence(
        status=status,  # type: ignore[arg-type]
        benchmark_ref="professional-benchmark:sample-pack:v1",
        benchmark_set_ref="benchmark-set:mystery-commercial:v1",
        evaluator_identity=evaluator_identity,
    )


def _pack(
    *,
    samples: tuple[SampleArtifact, ...] | None = None,
    evaluations: tuple[SampleEvaluationEvidence, ...] | None = None,
    style: StyleProfileSnapshot = STYLE,
    writer: WriterCandidate = WRITER,
    benchmark: ProfessionalBenchmarkEvidence | None = None,
    authority_refs: tuple[str, ...] = AUTHORITY_REFS,
) -> RepresentativeSamplePack:
    sample_rows = samples or (
        _sample("open", "scene-open", "OPENING"),
        _sample("investigation", "scene-investigation", "INVESTIGATION_DIALOGUE"),
        _sample("tension", "scene-tension", "TENSION_MYSTIC"),
    )
    evaluation_rows = evaluations or tuple(_evaluation(sample) for sample in sample_rows)
    return RepresentativeSamplePack(
        book_id="book-1",
        style_profile=style,
        writer_candidate=writer,
        authority_revision_refs=authority_refs,
        samples=sample_rows,
        evaluations=evaluation_rows,
        professional_benchmark=benchmark or _benchmark(),
    )


def _admissions(pack: RepresentativeSamplePack) -> dict[str, str]:
    return {
        sample.writing_admission_id: sample.scene_revision_ref
        for sample in pack.samples
    }


def _qualify(
    pack: RepresentativeSamplePack,
    *,
    policy: RepresentativeSamplePolicy = POLICY,
    current_style: StyleProfileSnapshot = STYLE,
    authority_refs: tuple[str, ...] = AUTHORITY_REFS,
    admissions: dict[str, str] | None = None,
):
    return qualify_representative_sample(
        pack=pack,
        policy=policy,
        current_style_profile=current_style,
        current_authority_revision_refs=authority_refs,
        valid_admission_scene_refs=admissions if admissions is not None else _admissions(pack),
    )


def _codes(result) -> set[str]:  # type: ignore[no-untyped-def]
    return {finding.code for finding in result.findings}


def test_clean_representative_sample_qualifies_sample_and_writer() -> None:
    pack = _pack()

    result = _qualify(pack)

    assert result.representative_sample_qualified
    assert result.writer_qualified
    assert result.representative_sample_ref.startswith("representative-sample:")
    assert result.writer_qualification_ref is not None
    assert result.writer_qualification_ref.startswith("writer-qualification:")
    assert result.findings == ()


def test_required_sample_functions_and_minimum_distinct_scenes_are_fail_closed() -> None:
    opening = _sample("open", "scene-open", "OPENING")
    pack = _pack(
        samples=(opening,),
        evaluations=(_evaluation(opening),),
    )

    result = _qualify(pack)

    codes = _codes(result)
    assert "SAMPLE.COVERAGE.TOO_FEW_SAMPLES" in codes
    assert "SAMPLE.COVERAGE.FUNCTION_MISSING" in codes
    assert not result.representative_sample_qualified
    assert not result.writer_qualified


def test_mystical_profile_requires_tension_mystic_sample_but_non_mystic_policy_does_not() -> None:
    opening = _sample("open", "scene-open", "OPENING")
    investigation = _sample(
        "investigation",
        "scene-investigation",
        "INVESTIGATION_DIALOGUE",
    )
    pack = _pack(
        samples=(opening, investigation),
        evaluations=(_evaluation(opening), _evaluation(investigation)),
    )

    mystical = _qualify(pack)
    assert "SAMPLE.COVERAGE.FUNCTION_MISSING" in _codes(mystical)

    ordinary_policy = replace(POLICY, require_tension_mystic=False)
    ordinary = _qualify(pack, policy=ordinary_policy)
    assert ordinary.representative_sample_qualified
    assert ordinary.writer_qualified


def test_style_profile_must_be_approved_and_exactly_current() -> None:
    pack = _pack()
    draft_style = replace(STYLE, status="DRAFT")
    stale_style = replace(STYLE, content_hash=_hash("style-v2"))

    draft = _qualify(replace(pack, style_profile=draft_style), current_style=draft_style)
    stale = _qualify(pack, current_style=stale_style)

    assert "SAMPLE.STYLE.NOT_APPROVED" in _codes(draft)
    assert "SAMPLE.STYLE.STALE" in _codes(stale)


def test_sample_must_come_from_verified_mys05_admission_for_exact_scene_revision() -> None:
    pack = _pack()
    first = pack.samples[0]
    unknown = _admissions(pack)
    unknown.pop(first.writing_admission_id)

    missing = _qualify(pack, admissions=unknown)
    assert "SAMPLE.ARTIFACT.ADMISSION_UNKNOWN" in _codes(missing)

    mismatched = _admissions(pack)
    mismatched[first.writing_admission_id] = "scene-contract:other@rev:x"
    mismatch_result = _qualify(pack, admissions=mismatched)
    assert "SAMPLE.ARTIFACT.ADMISSION_SCENE_MISMATCH" in _codes(mismatch_result)


def test_sample_evaluation_must_be_independent_and_cover_required_dimensions() -> None:
    pack = _pack()
    first = pack.samples[0]
    bad_eval = replace(
        _evaluation(first),
        evaluator_identity=WRITER.executor_identity,
        coverage_dimensions=("VOICE_STYLE",),
    )
    evaluations = (
        bad_eval,
        *tuple(_evaluation(sample) for sample in pack.samples[1:]),
    )

    result = _qualify(replace(pack, evaluations=evaluations))

    codes = _codes(result)
    assert "SAMPLE.EVALUATION.NOT_INDEPENDENT" in codes
    assert "SAMPLE.EVALUATION.DIMENSION_MISSING" in codes
    assert not result.representative_sample_qualified


def test_major_or_blocking_sample_gap_blocks_scaling() -> None:
    pack = _pack()
    first = pack.samples[0]
    major = replace(_evaluation(first), status="MAJOR_GAP")
    evaluations = (
        major,
        *tuple(_evaluation(sample) for sample in pack.samples[1:]),
    )

    result = _qualify(replace(pack, evaluations=evaluations))

    assert "SAMPLE.EVALUATION.MAJOR_GAP" in _codes(result)
    assert not result.representative_sample_qualified
    assert not result.writer_qualified


def test_professional_benchmark_is_mandatory_and_independent() -> None:
    pack = _pack()

    gap = _qualify(replace(pack, professional_benchmark=_benchmark(status="MAJOR_GAP")))
    same_writer = _qualify(
        replace(
            pack,
            professional_benchmark=_benchmark(
                evaluator_identity=WRITER.executor_identity
            ),
        )
    )

    assert "SAMPLE.BENCHMARK.MAJOR_GAP" in _codes(gap)
    assert "SAMPLE.BENCHMARK.NOT_INDEPENDENT" in _codes(same_writer)


def test_material_editor_rewrite_can_qualify_final_sample_but_not_writer() -> None:
    pack = _pack()
    first = pack.samples[0]
    rewritten = replace(
        first,
        final_text_hash=_hash("human-rewritten-final"),
        post_writer_revision_class="MATERIAL",
    )
    samples = (rewritten, *pack.samples[1:])
    evaluations = tuple(_evaluation(sample) for sample in samples)
    revised_pack = replace(pack, samples=samples, evaluations=evaluations)

    result = _qualify(revised_pack)

    assert result.representative_sample_qualified
    assert not result.writer_qualified
    assert result.writer_qualification_ref is None
    assert "WRITER_QUALIFICATION.MATERIAL_REWRITE" in _codes(result)


def test_undeclared_writer_output_change_blocks_writer_qualification_only() -> None:
    pack = _pack()
    first = replace(
        pack.samples[0],
        final_text_hash=_hash("different-final"),
        post_writer_revision_class="NONE",
    )
    samples = (first, *pack.samples[1:])
    revised_pack = replace(
        pack,
        samples=samples,
        evaluations=tuple(_evaluation(sample) for sample in samples),
    )

    result = _qualify(revised_pack)

    assert result.representative_sample_qualified
    assert not result.writer_qualified
    assert "WRITER_QUALIFICATION.UNDECLARED_REWRITE" in _codes(result)


def test_different_writer_candidate_cannot_inherit_another_writers_good_sample() -> None:
    pack = _pack()
    other = replace(WRITER, writer_candidate_id="writer-b")

    result = _qualify(replace(pack, writer_candidate=other))

    assert result.representative_sample_qualified
    assert not result.writer_qualified
    assert "WRITER_QUALIFICATION.CANDIDATE_MISMATCH" in _codes(result)


def test_sample_authority_snapshot_must_match_current_context() -> None:
    pack = _pack()
    changed_refs = (
        AUTHORITY_REFS[0],
        AUTHORITY_REFS[1],
        "case@rev-2:" + _hash("case-v2"),
    )

    result = _qualify(pack, authority_refs=changed_refs)

    assert "SAMPLE.AUTHORITY.STALE" in _codes(result)
    assert not result.representative_sample_qualified


def test_too_short_or_hash_invalid_sample_cannot_qualify() -> None:
    pack = _pack()
    first = replace(
        pack.samples[0],
        final_character_count=99,
        writer_output_hash="not-a-hash",
        final_text_hash="also-not-a-hash",
    )
    samples = (first, *pack.samples[1:])
    revised = replace(
        pack,
        samples=samples,
        evaluations=tuple(_evaluation(sample) for sample in samples),
    )

    result = _qualify(revised)

    codes = _codes(result)
    assert "SAMPLE.ARTIFACT.TOO_SHORT" in codes
    assert "SAMPLE.ARTIFACT.WRITER_OUTPUT_HASH_INVALID" in codes
    assert "SAMPLE.ARTIFACT.FINAL_TEXT_HASH_INVALID" in codes


def test_audio_selected_requires_audio_listenability_coverage() -> None:
    pack = _pack()
    audio_policy = replace(POLICY, audio_selected=True)

    blocked = _qualify(pack, policy=audio_policy)
    assert "SAMPLE.EVALUATION.DIMENSION_MISSING" in _codes(blocked)

    evaluations = tuple(
        replace(
            _evaluation(sample),
            coverage_dimensions=(
                *_evaluation(sample).coverage_dimensions,
                "AUDIO_LISTENABILITY",
            ),
        )
        for sample in pack.samples
    )
    admitted = _qualify(
        replace(pack, evaluations=evaluations),
        policy=audio_policy,
    )
    assert admitted.representative_sample_qualified


def test_writer_qualification_ref_is_version_bound_to_exact_sample_snapshot() -> None:
    pack = _pack()
    result = _qualify(pack)
    assert result.writer_qualification_ref is not None

    verified = verify_writer_qualification(
        prior_writer_qualification_ref=result.writer_qualification_ref,
        pack=pack,
        policy=POLICY,
        current_style_profile=STYLE,
        current_authority_revision_refs=AUTHORITY_REFS,
        valid_admission_scene_refs=_admissions(pack),
    )
    assert verified.valid

    changed_first = replace(
        pack.samples[0],
        writer_output_hash=_hash("changed-writer-output"),
        final_text_hash=_hash("changed-writer-output"),
    )
    changed_samples = (changed_first, *pack.samples[1:])
    changed_pack = replace(
        pack,
        samples=changed_samples,
        evaluations=tuple(_evaluation(sample) for sample in changed_samples),
    )
    changed = verify_writer_qualification(
        prior_writer_qualification_ref=result.writer_qualification_ref,
        pack=changed_pack,
        policy=POLICY,
        current_style_profile=STYLE,
        current_authority_revision_refs=AUTHORITY_REFS,
        valid_admission_scene_refs=_admissions(changed_pack),
    )

    assert not changed.valid
    assert changed.reason == "QUALIFICATION_SNAPSHOT_CHANGED"


def test_mys06_result_populates_mys05_mass_draft_readiness_without_manual_flags() -> None:
    pack = _pack()
    qualification = _qualify(pack)

    readiness = readiness_with_sample_qualification(
        ExternalWritingReadiness(
            anti_cliche_evaluation_ref="anti-cliche:v1",
        ),
        qualification,
    )

    assert readiness.representative_sample_qualified
    assert readiness.representative_sample_ref == qualification.representative_sample_ref
    assert readiness.writer_qualified
    assert readiness.writer_qualification_ref == qualification.writer_qualification_ref


def test_material_rewrite_never_sets_mys05_writer_qualified() -> None:
    pack = _pack()
    rewritten = replace(
        pack.samples[0],
        final_text_hash=_hash("material-final"),
        post_writer_revision_class="MATERIAL",
    )
    samples = (rewritten, *pack.samples[1:])
    revised_pack = replace(
        pack,
        samples=samples,
        evaluations=tuple(_evaluation(sample) for sample in samples),
    )
    qualification = _qualify(revised_pack)

    readiness = readiness_with_sample_qualification(
        ExternalWritingReadiness(
            anti_cliche_evaluation_ref="anti-cliche:v1",
        ),
        qualification,
    )

    assert readiness.representative_sample_qualified
    assert readiness.representative_sample_ref is not None
    assert not readiness.writer_qualified
    assert readiness.writer_qualification_ref is None


def test_nontrivial_post_writer_revision_requires_evidence_ref() -> None:
    pack = _pack()
    first = replace(
        pack.samples[0],
        post_writer_revision_class="MECHANICAL",
        post_writer_revision_ref=None,
    )
    samples = (first, *pack.samples[1:])
    revised = replace(
        pack,
        samples=samples,
        evaluations=tuple(_evaluation(sample) for sample in samples),
    )

    result = _qualify(revised)

    assert "SAMPLE.ARTIFACT.REVISION_REF_MISSING" in _codes(result)
    assert not result.representative_sample_qualified


def test_unknown_runtime_codes_are_blocked_even_if_python_types_are_bypassed() -> None:
    pack = _pack()
    first = replace(
        pack.samples[0],
        function_codes=("OPENING", "NOT_A_FUNCTION"),  # type: ignore[arg-type]
        post_writer_revision_class="NOT_A_REVISION_CLASS",  # type: ignore[arg-type]
    )
    bad_eval = replace(
        _evaluation(first),
        status="ALIEN_STATUS",  # type: ignore[arg-type]
        coverage_dimensions=(
            *CORE,
            "NOT_A_DIMENSION",  # type: ignore[arg-type]
        ),
    )
    evaluations = (
        bad_eval,
        *tuple(_evaluation(sample) for sample in pack.samples[1:]),
    )
    revised = replace(
        pack,
        samples=(first, *pack.samples[1:]),
        evaluations=evaluations,
    )

    result = _qualify(revised)

    codes = _codes(result)
    assert "SAMPLE.ARTIFACT.FUNCTION_UNKNOWN" in codes
    assert "SAMPLE.ARTIFACT.REVISION_CLASS_UNKNOWN" in codes
    assert "SAMPLE.EVALUATION.STATUS_UNKNOWN" in codes
    assert "SAMPLE.EVALUATION.DIMENSION_UNKNOWN" in codes
    assert not result.representative_sample_qualified


def test_writer_qualification_ref_changes_when_gate_policy_changes() -> None:
    pack = _pack()
    initial = _qualify(pack)
    assert initial.writer_qualification_ref is not None

    stricter_policy = replace(POLICY, min_characters_per_sample=1200)
    current = _qualify(pack, policy=stricter_policy)
    assert current.writer_qualified
    assert current.writer_qualification_ref is not None
    assert current.writer_qualification_ref != initial.writer_qualification_ref

    verification = verify_writer_qualification(
        prior_writer_qualification_ref=initial.writer_qualification_ref,
        pack=pack,
        policy=stricter_policy,
        current_style_profile=STYLE,
        current_authority_revision_refs=AUTHORITY_REFS,
        valid_admission_scene_refs=_admissions(pack),
    )
    assert not verification.valid
    assert verification.reason == "QUALIFICATION_SNAPSHOT_CHANGED"
