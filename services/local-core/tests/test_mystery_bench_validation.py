from __future__ import annotations

from dataclasses import replace
import hashlib

from book_os_core.mystery_bench_validation import (
    AdversarialCaseReconstruction,
    ColdReaderCheckpoint,
    MysteryBenchPack,
    MysteryBenchPolicy,
    MysteryDimensionEvidence,
    adversarial_protocol_ref,
    cold_reader_protocol_ref,
    evaluate_mystery_bench,
    verify_mystery_bench,
)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


SNAPSHOT_REF = "bookbench-snapshot:book-1:v1"
SNAPSHOT_HASH = _hash("book-snapshot-v1")
WRITER_ID = "openai/writer-model/standard"
CASE_REF = "case@rev-1:" + _hash("case")
AUTHORITY_REFS = (
    "story@rev-1:" + _hash("story"),
    "narrative@rev-1:" + _hash("narrative"),
    CASE_REF,
)


def _cold_checkpoint(kind: str) -> ColdReaderCheckpoint:
    is_post = kind == "POST_REVEAL"
    return ColdReaderCheckpoint(
        checkpoint=kind,  # type: ignore[arg-type]
        manuscript_snapshot_ref=SNAPSHOT_REF,
        evaluation_ref=f"cold-eval:{kind}:v1",
        evaluator_identity="cold-reader/model-b",
        private_case_solution_exposed=False,
        top_suspect_ids=("suspect-a",),
        hypothesis_refs=(f"hypothesis:{kind}:1",),
        perceived_clue_refs=(f"clue:{kind}:1",),
        engagement_state="ENGAGED",
        solution_inferable=True if is_post else None,
        solution_earned=True if is_post else None,
        late_invention_detected=False if is_post else None,
        stronger_alternative_detected=False if is_post else None,
    )


def _final_cold_checkpoints() -> tuple[ColdReaderCheckpoint, ...]:
    return tuple(
        _cold_checkpoint(kind)
        for kind in (
            "EARLY",
            "QUARTER",
            "MIDPOINT",
            "THREE_QUARTER",
            "PRE_REVEAL",
            "POST_REVEAL",
        )
    )


def _midbook_cold_checkpoints() -> tuple[ColdReaderCheckpoint, ...]:
    return tuple(
        _cold_checkpoint(kind)
        for kind in ("EARLY", "QUARTER", "MIDPOINT")
    )


def _adversarial(**overrides: object) -> AdversarialCaseReconstruction:
    values: dict[str, object] = {
        "manuscript_snapshot_ref": SNAPSHOT_REF,
        "evaluator_identity": "adversary/model-c",
        "reconstruction_ref": "blind-reconstruction:v1",
        "blind_input_refs": (SNAPSHOT_REF,),
        "accepted_case_solution_revision_ref": CASE_REF,
        "comparison_ref": "case-comparison:v1",
        "reveal_order": "RECONSTRUCTION_THEN_CASE_SOLUTION",
    }
    values.update(overrides)
    return AdversarialCaseReconstruction(**values)  # type: ignore[arg-type]


def _required_final_dimensions(
    *,
    supernatural: bool = True,
    audio: bool = True,
) -> tuple[str, ...]:
    values = [
        "CASE_COHERENCE",
        "FAIR_PLAY",
        "REVEAL_QUALITY",
        "SUSPECT_QUALITY",
        "CHARACTER_CAUSALITY",
        "NARRATIVE_INTEGRITY",
        "TENSION_PACING",
        "ORIGINALITY_ANTI_CLICHE",
        "PROSE_VOICE",
        "SETTING_FUNCTION",
        "RESEARCH_REALISM",
        "EMOTIONAL_ARCHITECTURE",
    ]
    if supernatural:
        values.append("SUPERNATURAL_INTEGRITY")
    if audio:
        values.append("AUDIO_READINESS")
    return tuple(values)


def _required_midbook_dimensions(*, supernatural: bool = True) -> tuple[str, ...]:
    values = [
        "CASE_COHERENCE",
        "FAIR_PLAY",
        "CHARACTER_CAUSALITY",
        "NARRATIVE_INTEGRITY",
        "TENSION_PACING",
        "ORIGINALITY_ANTI_CLICHE",
        "RESEARCH_REALISM",
        "EMOTIONAL_ARCHITECTURE",
    ]
    if supernatural:
        values.append("SUPERNATURAL_INTEGRITY")
    return tuple(values)


def _dimension(
    dimension: str,
    *,
    status: str = "PASS",
    supports: tuple[str, ...] = (),
    evaluator_identity: str = "judge/model-d",
    evaluator_class: str = "LLM_JUDGE",
    independence: str = "INDEPENDENT",
    human_disposition_ref: str | None = None,
    snapshot_ref: str = SNAPSHOT_REF,
) -> MysteryDimensionEvidence:
    return MysteryDimensionEvidence(
        dimension=dimension,  # type: ignore[arg-type]
        status=status,  # type: ignore[arg-type]
        evaluation_ref=f"bookbench-eval:{dimension}:v1",
        bookbench_snapshot_ref=snapshot_ref,
        rubric_ref=f"mystery-rubric:{dimension}:v1",
        evaluator_identity=evaluator_identity,
        evaluator_class=evaluator_class,  # type: ignore[arg-type]
        independence_state=independence,  # type: ignore[arg-type]
        supporting_evidence_refs=supports,
        human_disposition_ref=human_disposition_ref,
    )


def _final_pack(
    *,
    policy: MysteryBenchPolicy | None = None,
    cold: tuple[ColdReaderCheckpoint, ...] | None = None,
    adversarial: AdversarialCaseReconstruction | None = None,
    dimensions: tuple[MysteryDimensionEvidence, ...] | None = None,
) -> tuple[MysteryBenchPack, MysteryBenchPolicy]:
    selected_policy = policy or MysteryBenchPolicy(
        stage="FINAL",
        supernatural_material=True,
        audio_selected=True,
    )
    cold_rows = cold if cold is not None else _final_cold_checkpoints()
    adversary = adversarial if adversarial is not None else _adversarial()
    cold_ref = cold_reader_protocol_ref(cold_rows)
    adversarial_ref = adversarial_protocol_ref(adversary)
    if dimensions is None:
        rows: list[MysteryDimensionEvidence] = []
        for dimension in _required_final_dimensions(
            supernatural=selected_policy.supernatural_material,
            audio=selected_policy.audio_selected,
        ):
            supports: list[str] = []
            if dimension in {"FAIR_PLAY", "REVEAL_QUALITY"}:
                supports.append(cold_ref)
            if dimension in {"CASE_COHERENCE", "FAIR_PLAY", "NARRATIVE_INTEGRITY"}:
                supports.append(adversarial_ref)
            rows.append(_dimension(dimension, supports=tuple(supports)))
        dimensions = tuple(rows)
    pack = MysteryBenchPack(
        book_id="book-1",
        manuscript_snapshot_ref=SNAPSHOT_REF,
        manuscript_snapshot_hash=SNAPSHOT_HASH,
        authority_revision_refs=AUTHORITY_REFS,
        private_spoiler_authority_refs=(CASE_REF,),
        writer_executor_identity=WRITER_ID,
        dimension_evidence=dimensions,
        cold_reader_checkpoints=cold_rows,
        adversarial_reconstruction=adversary,
    )
    return pack, selected_policy


def _verified_evaluation_refs(pack: MysteryBenchPack) -> frozenset[str]:
    values = {
        evidence.evaluation_ref
        for evidence in pack.dimension_evidence
        if evidence.evaluation_ref
    }
    values.update(
        checkpoint.evaluation_ref
        for checkpoint in pack.cold_reader_checkpoints
        if checkpoint.evaluation_ref
    )
    if pack.adversarial_reconstruction is not None:
        values.add(pack.adversarial_reconstruction.reconstruction_ref)
        values.add(pack.adversarial_reconstruction.comparison_ref)
    return frozenset(values)


def _evaluate(
    pack: MysteryBenchPack,
    policy: MysteryBenchPolicy,
    *,
    current_snapshot_ref: str = SNAPSHOT_REF,
    current_snapshot_hash: str = SNAPSHOT_HASH,
    authority_refs: tuple[str, ...] = AUTHORITY_REFS,
    verified_evaluation_refs: frozenset[str] | None = None,
    verified_human_disposition_refs: frozenset[str] = frozenset(),
):
    return evaluate_mystery_bench(
        pack=pack,
        policy=policy,
        current_manuscript_snapshot_ref=current_snapshot_ref,
        current_manuscript_snapshot_hash=current_snapshot_hash,
        current_authority_revision_refs=authority_refs,
        verified_evaluation_refs=(
            verified_evaluation_refs
            if verified_evaluation_refs is not None
            else _verified_evaluation_refs(pack)
        ),
        verified_human_disposition_refs=verified_human_disposition_refs,
    )


def _codes(result) -> set[str]:  # type: ignore[no-untyped-def]
    return {finding.code for finding in result.findings}


def test_clean_final_mysterybench_passes_with_coldreader_and_adversarial_evidence() -> None:
    pack, policy = _final_pack()

    result = _evaluate(pack, policy)

    assert result.qualified
    assert result.findings == ()
    assert result.mystery_bench_ref.startswith("mystery-bench:")
    assert result.cold_reader_protocol_ref is not None
    assert result.adversarial_protocol_ref is not None


def test_required_dimension_missing_blocks() -> None:
    pack, policy = _final_pack()
    dimensions = tuple(
        row for row in pack.dimension_evidence if row.dimension != "CASE_COHERENCE"
    )

    result = _evaluate(replace(pack, dimension_evidence=dimensions), policy)

    assert "MYSTERYBENCH.DIMENSION.MISSING" in _codes(result)
    assert not result.qualified


def test_blocking_gap_cannot_be_waived() -> None:
    pack, policy = _final_pack()
    dimensions = tuple(
        replace(
            row,
            status="BLOCKING_GAP",
            human_disposition_ref="human:waive-attempt",
        )
        if row.dimension == "CASE_COHERENCE"
        else row
        for row in pack.dimension_evidence
    )

    result = _evaluate(replace(pack, dimension_evidence=dimensions), policy)

    assert "MYSTERYBENCH.EVIDENCE.BLOCKING_GAP" in _codes(result)
    assert not result.qualified


def test_major_gap_requires_explicit_human_disposition() -> None:
    pack, policy = _final_pack()
    undisposed = tuple(
        replace(row, status="MAJOR_GAP")
        if row.dimension == "PROSE_VOICE"
        else row
        for row in pack.dimension_evidence
    )
    blocked = _evaluate(replace(pack, dimension_evidence=undisposed), policy)
    assert "MYSTERYBENCH.EVIDENCE.MAJOR_UNDISPOSED" in _codes(blocked)

    disposed = tuple(
        replace(
            row,
            status="MAJOR_GAP",
            human_disposition_ref="human-disposition:prose-voice:v1",
        )
        if row.dimension == "PROSE_VOICE"
        else row
        for row in pack.dimension_evidence
    )
    allowed = _evaluate(
        replace(pack, dimension_evidence=disposed),
        policy,
        verified_human_disposition_refs=frozenset(
            {"human-disposition:prose-voice:v1"}
        ),
    )
    assert allowed.qualified


def test_semantic_evaluation_must_be_independent_from_writer() -> None:
    pack, policy = _final_pack()
    dimensions = tuple(
        replace(
            row,
            evaluator_identity=WRITER_ID,
            independence_state="SAME_CONFIG",
        )
        if row.dimension == "PROSE_VOICE"
        else row
        for row in pack.dimension_evidence
    )

    result = _evaluate(replace(pack, dimension_evidence=dimensions), policy)
    codes = _codes(result)

    assert "MYSTERYBENCH.EVIDENCE.NOT_INDEPENDENT" in codes
    assert "MYSTERYBENCH.EVIDENCE.SAME_WRITER_EXECUTOR" in codes


def test_deterministic_evidence_may_use_not_applicable_independence() -> None:
    pack, policy = _final_pack()
    dimensions = tuple(
        replace(
            row,
            evaluator_class="DETERMINISTIC",
            evaluator_identity="bookbench-deterministic",
            independence_state="NOT_APPLICABLE",
        )
        if row.dimension == "RESEARCH_REALISM"
        else row
        for row in pack.dimension_evidence
    )

    result = _evaluate(replace(pack, dimension_evidence=dimensions), policy)

    assert result.qualified


def test_stale_manuscript_or_authority_snapshot_blocks() -> None:
    pack, policy = _final_pack()

    manuscript = _evaluate(
        pack,
        policy,
        current_snapshot_hash=_hash("new-manuscript"),
    )
    authority = _evaluate(
        pack,
        policy,
        authority_refs=(AUTHORITY_REFS[0], AUTHORITY_REFS[1], "case@rev-2:" + _hash("v2")),
    )

    assert "MYSTERYBENCH.MANUSCRIPT.STALE" in _codes(manuscript)
    assert "MYSTERYBENCH.AUTHORITY.STALE" in _codes(authority)


def test_cold_reader_never_receives_private_case_solution_or_spoiler_authority() -> None:
    cold = list(_final_cold_checkpoints())
    cold[0] = replace(
        cold[0],
        private_case_solution_exposed=True,
        private_spoiler_authority_refs=(CASE_REF,),
    )
    pack, policy = _final_pack(cold=tuple(cold))

    result = _evaluate(pack, policy)
    codes = _codes(result)

    assert "MYSTERYBENCH.COLD_READER.CASE_SOLUTION_EXPOSED" in codes
    assert "MYSTERYBENCH.COLD_READER.SPOILER_AUTHORITY_EXPOSED" in codes


def test_final_cold_reader_requires_all_checkpoints_and_post_reveal_fields() -> None:
    cold = tuple(
        row for row in _final_cold_checkpoints() if row.checkpoint != "THREE_QUARTER"
    )
    post_missing = tuple(
        replace(row, solution_earned=None)
        if row.checkpoint == "POST_REVEAL"
        else row
        for row in cold
    )
    pack, policy = _final_pack(cold=post_missing)

    result = _evaluate(pack, policy)
    codes = _codes(result)

    assert "MYSTERYBENCH.COLD_READER.CHECKPOINT_MISSING" in codes
    assert "MYSTERYBENCH.COLD_READER.POST_REVEAL_FIELD_MISSING" in codes


def test_adversarial_reconstruction_is_blind_then_compared_to_accepted_case() -> None:
    contaminated = _adversarial(blind_input_refs=(SNAPSHOT_REF, CASE_REF))
    pack, policy = _final_pack(adversarial=contaminated)

    result = _evaluate(pack, policy)

    assert "MYSTERYBENCH.ADVERSARIAL.PRIVATE_AUTHORITY_IN_BLIND_INPUT" in _codes(result)


def test_adversarial_case_defects_block_final_bench() -> None:
    adversary = _adversarial(
        missing_required_fact=True,
        stronger_alternative_solution=True,
        unfair_decisive_withholding=True,
    )
    pack, policy = _final_pack(adversarial=adversary)

    result = _evaluate(pack, policy)
    codes = _codes(result)

    assert "MYSTERYBENCH.ADVERSARIAL.MISSING_REQUIRED_FACT" in codes
    assert "MYSTERYBENCH.ADVERSARIAL.STRONGER_ALTERNATIVE" in codes
    assert "MYSTERYBENCH.ADVERSARIAL.UNFAIR_WITHHOLDING" in codes
    assert not result.qualified


def test_final_fair_play_reveal_and_case_dimensions_must_consume_protocol_evidence() -> None:
    pack, policy = _final_pack()
    dimensions = tuple(
        replace(row, supporting_evidence_refs=())
        if row.dimension in {
            "CASE_COHERENCE",
            "FAIR_PLAY",
            "REVEAL_QUALITY",
            "NARRATIVE_INTEGRITY",
        }
        else row
        for row in pack.dimension_evidence
    )

    result = _evaluate(replace(pack, dimension_evidence=dimensions), policy)
    codes = _codes(result)

    assert "MYSTERYBENCH.EVIDENCE.COLD_READER_NOT_CONSUMED" in codes
    assert "MYSTERYBENCH.EVIDENCE.ADVERSARIAL_NOT_CONSUMED" in codes


def test_supernatural_and_audio_dimensions_are_conditional() -> None:
    plain_policy = MysteryBenchPolicy(
        stage="FINAL",
        supernatural_material=False,
        audio_selected=False,
    )
    pack, _ = _final_pack(policy=plain_policy)

    assert all(
        row.dimension not in {"SUPERNATURAL_INTEGRITY", "AUDIO_READINESS"}
        for row in pack.dimension_evidence
    )
    assert _evaluate(pack, plain_policy).qualified

    mystic_policy = replace(plain_policy, supernatural_material=True)
    mystic_pack, _ = _final_pack(policy=mystic_policy)
    missing = tuple(
        row
        for row in mystic_pack.dimension_evidence
        if row.dimension != "SUPERNATURAL_INTEGRITY"
    )
    blocked = _evaluate(replace(mystic_pack, dimension_evidence=missing), mystic_policy)
    assert "MYSTERYBENCH.DIMENSION.MISSING" in _codes(blocked)


def test_midbook_requires_only_midbook_dimensions_and_checkpoints_by_default() -> None:
    policy = MysteryBenchPolicy(
        stage="MIDBOOK",
        supernatural_material=True,
        audio_selected=False,
    )
    cold = _midbook_cold_checkpoints()
    dimensions = tuple(_dimension(name) for name in _required_midbook_dimensions())
    pack = MysteryBenchPack(
        book_id="book-1",
        manuscript_snapshot_ref=SNAPSHOT_REF,
        manuscript_snapshot_hash=SNAPSHOT_HASH,
        authority_revision_refs=AUTHORITY_REFS,
        private_spoiler_authority_refs=(CASE_REF,),
        writer_executor_identity=WRITER_ID,
        dimension_evidence=dimensions,
        cold_reader_checkpoints=cold,
        adversarial_reconstruction=None,
    )

    result = _evaluate(pack, policy)

    assert result.qualified
    assert result.adversarial_protocol_ref is None


def test_mysterybench_ref_is_version_bound_to_policy_and_evidence() -> None:
    pack, policy = _final_pack()
    result = _evaluate(pack, policy)
    assert result.qualified

    verified = verify_mystery_bench(
        prior_mystery_bench_ref=result.mystery_bench_ref,
        pack=pack,
        policy=policy,
        current_manuscript_snapshot_ref=SNAPSHOT_REF,
        current_manuscript_snapshot_hash=SNAPSHOT_HASH,
        current_authority_revision_refs=AUTHORITY_REFS,
        verified_evaluation_refs=_verified_evaluation_refs(pack),
    )
    assert verified.valid

    changed_policy = replace(policy, audio_selected=False)
    changed = verify_mystery_bench(
        prior_mystery_bench_ref=result.mystery_bench_ref,
        pack=pack,
        policy=changed_policy,
        current_manuscript_snapshot_ref=SNAPSHOT_REF,
        current_manuscript_snapshot_hash=SNAPSHOT_HASH,
        current_authority_revision_refs=AUTHORITY_REFS,
        verified_evaluation_refs=_verified_evaluation_refs(pack),
    )
    assert not changed.valid
    assert changed.reason in {
        "CURRENT_MYSTERYBENCH_BLOCKED",
        "MYSTERYBENCH_SNAPSHOT_CHANGED",
    }


def test_unverified_evaluation_ref_cannot_be_used_as_bookbench_evidence() -> None:
    pack, policy = _final_pack()
    verified = set(_verified_evaluation_refs(pack))
    target = next(
        row for row in pack.dimension_evidence if row.dimension == "PROSE_VOICE"
    )
    verified.remove(target.evaluation_ref)

    result = _evaluate(
        pack,
        policy,
        verified_evaluation_refs=frozenset(verified),
    )

    assert "MYSTERYBENCH.EVIDENCE.REF_UNVERIFIED" in _codes(result)
    assert not result.qualified


def test_fake_human_disposition_string_does_not_clear_major_gap() -> None:
    pack, policy = _final_pack()
    dimensions = tuple(
        replace(
            row,
            status="MAJOR_GAP",
            human_disposition_ref="human:invented-by-model",
        )
        if row.dimension == "PROSE_VOICE"
        else row
        for row in pack.dimension_evidence
    )
    revised = replace(pack, dimension_evidence=dimensions)

    result = _evaluate(revised, policy)

    assert "MYSTERYBENCH.EVIDENCE.HUMAN_DISPOSITION_UNVERIFIED" in _codes(result)
    assert not result.qualified


def test_private_spoiler_authority_must_be_part_of_exact_authority_snapshot() -> None:
    pack, policy = _final_pack()
    revised = replace(
        pack,
        private_spoiler_authority_refs=(CASE_REF, "reveal-plan@private"),
    )

    result = _evaluate(revised, policy)

    assert "MYSTERYBENCH.AUTHORITY.PRIVATE_SPOILER_NOT_IN_SNAPSHOT" in _codes(result)
