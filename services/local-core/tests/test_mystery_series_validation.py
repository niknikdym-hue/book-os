from __future__ import annotations

from dataclasses import replace
import hashlib

from book_os_core.mystery_bench_validation import VerifiedEvaluationArtifact
from book_os_core.mystery_series_validation import (
    AcceptedBookPassport,
    MysteryBookPassport,
    SeriesCollisionPolicy,
    SeriesProfileSnapshot,
    SeriesSemanticCollisionEvidence,
    evaluate_series_uniqueness,
    passport_hash,
    passport_ref,
    series_context_ref,
    series_profile_ref,
    verify_series_uniqueness,
)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


PROFILE = SeriesProfileSnapshot(
    profile_id="series-112",
    content_hash=_hash("series-profile-v2"),
    status="APPROVED",
    series_name="Линия 112",
    allowed_recurring_asset_codes=("signature-city", "signature-team"),
    shared_invariant_refs=("invariant:modern-city", "invariant:mystic-real"),
    strongly_serialized=False,
)

HISTORICAL_PROFILE_REF = f"series-profile:{PROFILE.profile_id}:{_hash('series-profile-v1')}"
CURRENT_PROFILE_REF = series_profile_ref(PROFILE)
WRITER_ID = "writer/model-standard"

POLICY = SeriesCollisionPolicy(
    exact_blocking_dimensions=(
        "MECHANISM",
        "SUPERNATURAL_DEVICE",
        "SUSPECT_ARCHITECTURE",
        "FINAL_REVEAL",
        "CLIMAX_STAGING",
        "RELATIONSHIP_MOVEMENT",
        "CASE_SOLUTION_ARCHITECTURE",
    ),
    exact_attention_dimensions=("OPENING_PATTERN", "INTERVIEW_CADENCE"),
    semantic_required_dimensions=(
        "PREMISE",
        "CASE_TYPE",
        "CULPRIT_RELATIONSHIP",
        "MOTIVE_FAMILY",
        "MECHANISM",
        "CONCEALMENT",
        "SUSPECT_ARCHITECTURE",
        "CLUE_ARCHITECTURE",
        "SUPERNATURAL_DEVICE",
        "MIDPOINT_REVERSAL",
        "PROTAGONIST_JEOPARDY",
        "EMOTIONAL_CONFLICT",
        "RELATIONSHIP_MOVEMENT",
        "FINAL_REVEAL",
        "CLIMAX_STAGING",
        "SETTING_TYPE",
        "CASE_SOLUTION_ARCHITECTURE",
        "PROSE_SCENE_PATTERN_RISK",
    ),
)


def _passport(
    *,
    book_id: str,
    number: int,
    profile_ref: str,
    suffix: str,
    profile_id: str = PROFILE.profile_id,
    assets_consumed: tuple[str, ...] = (),
    assets_reserved: tuple[str, ...] = (),
    claims: tuple[str, ...] = (),
    primary_case_resolved: bool = True,
    orientation: str | None = "orientation:v1",
) -> MysteryBookPassport:
    return MysteryBookPassport(
        book_id=book_id,
        book_number=number,
        working_title=f"Book {number}",
        series_profile_id=profile_id,
        series_profile_ref=profile_ref,
        premise_signature=f"premise-{suffix}",
        primary_case_type=f"case-type-{suffix}",
        victim_target_profile=f"victim-{suffix}",
        culprit_relationship=f"culprit-relation-{suffix}",
        motive_family=f"motive-{suffix}",
        mechanism=f"mechanism-{suffix}",
        concealment=f"concealment-{suffix}",
        suspect_architecture=f"suspects-{suffix}",
        clue_architecture=f"clues-{suffix}",
        red_herring_pattern=f"red-herring-{suffix}",
        supernatural_device=f"mystic-{suffix}",
        setting_type=f"setting-{suffix}",
        protagonist_jeopardy=f"jeopardy-{suffix}",
        emotional_conflict=f"emotion-{suffix}",
        relationship_movement=f"relationship-{suffix}",
        midpoint_reversal=f"midpoint-{suffix}",
        final_reveal=f"reveal-{suffix}",
        climax_staging=f"climax-{suffix}",
        ending_state=f"ending-{suffix}",
        opening_pattern=f"opening-{suffix}",
        body_discovery_pattern=f"body-{suffix}",
        interview_cadence=f"interviews-{suffix}",
        case_solution_architecture=f"solution-{suffix}",
        prose_scene_pattern_risk=f"prose-risk-{suffix}",
        assets_consumed=assets_consumed,
        assets_reserved=assets_reserved,
        reservation_claim_codes=claims,
        primary_case_resolved=primary_case_resolved,
        late_entry_orientation_ref=orientation if number > 1 else None,
    )


PRIOR_ONE = _passport(
    book_id="book-1",
    number=1,
    profile_ref=HISTORICAL_PROFILE_REF,
    suffix="one",
    assets_consumed=("asset-used-1", "signature-city"),
    assets_reserved=("asset-reserved-for-future",),
)
ACCEPTED_ONE = AcceptedBookPassport(
    passport=PRIOR_ONE,
    passport_hash=passport_hash(PRIOR_ONE),
    status="APPROVED",
    recurring_asset_codes_at_acceptance=("signature-city", "signature-team"),
)

CURRENT = _passport(
    book_id="book-2",
    number=2,
    profile_ref=CURRENT_PROFILE_REF,
    suffix="two",
    assets_consumed=("asset-reserved-for-future", "signature-city"),
    claims=("asset-reserved-for-future",),
)


def _accepted(
    passport: MysteryBookPassport,
    *,
    recurring_asset_codes: tuple[str, ...] = ("signature-city", "signature-team"),
) -> AcceptedBookPassport:
    return AcceptedBookPassport(
        passport=passport,
        passport_hash=passport_hash(passport),
        status="APPROVED",
        recurring_asset_codes_at_acceptance=recurring_asset_codes,
    )


def _semantic_evidence(
    *,
    current: MysteryBookPassport = CURRENT,
    prior: tuple[AcceptedBookPassport, ...] = (ACCEPTED_ONE,),
    policy: SeriesCollisionPolicy = POLICY,
    state_overrides: dict[tuple[str, str], str] | None = None,
    human_refs: dict[tuple[str, str], str] | None = None,
) -> tuple[
    tuple[SeriesSemanticCollisionEvidence, ...],
    dict[str, VerifiedEvaluationArtifact],
]:
    context_ref = series_context_ref(
        profile=PROFILE,
        current_passport=current,
        prior_passports=prior,
        policy=policy,
        writer_executor_identity=WRITER_ID,
    )
    rows: list[SeriesSemanticCollisionEvidence] = []
    artifacts: dict[str, VerifiedEvaluationArtifact] = {}
    for accepted in prior:
        prior_id = accepted.passport.book_id
        for dimension in policy.semantic_required_dimensions:
            key = (prior_id, dimension)
            state = (state_overrides or {}).get(key, "CLEAR")
            evaluation_ref = f"series-eval:{current.book_id}:{prior_id}:{dimension}:v1"
            evaluator_identity = "series-editor/model-independent"
            rubric_ref = f"series-collision-rubric:{dimension}:v1"
            row = SeriesSemanticCollisionEvidence(
                current_book_id=current.book_id,
                prior_book_id=prior_id,
                dimension=dimension,
                state=state,  # type: ignore[arg-type]
                evaluation_ref=evaluation_ref,
                evaluator_identity=evaluator_identity,
                evaluator_class="LLM_JUDGE",
                independence_state="INDEPENDENT",
                rubric_ref=rubric_ref,
                human_disposition_ref=(human_refs or {}).get(key),
            )
            rows.append(row)
            artifacts[evaluation_ref] = VerifiedEvaluationArtifact(
                evaluation_ref=evaluation_ref,
                manuscript_snapshot_ref=context_ref,
                evaluator_identity=evaluator_identity,
                evaluator_class="LLM_JUDGE",
                rubric_ref=rubric_ref,
                purpose=(f"SERIES_COLLISION:{current.book_id}:{prior_id}:{dimension}"),
                status="SUCCEEDED",
                current=True,
            )
    return tuple(rows), artifacts


def _evaluate(
    *,
    current: MysteryBookPassport = CURRENT,
    prior: tuple[AcceptedBookPassport, ...] = (ACCEPTED_ONE,),
    profile: SeriesProfileSnapshot = PROFILE,
    current_profile: SeriesProfileSnapshot = PROFILE,
    policy: SeriesCollisionPolicy = POLICY,
    semantic: tuple[SeriesSemanticCollisionEvidence, ...] | None = None,
    artifacts: dict[str, VerifiedEvaluationArtifact] | None = None,
    human_refs: frozenset[str] = frozenset(),
):
    if semantic is None or artifacts is None:
        semantic, artifacts = _semantic_evidence(
            current=current,
            prior=prior,
            policy=policy,
        )
    return evaluate_series_uniqueness(
        profile=profile,
        current_profile=current_profile,
        current_passport=current,
        prior_passports=prior,
        policy=policy,
        writer_executor_identity=WRITER_ID,
        semantic_evidence=semantic,
        verified_evaluations=artifacts,
        verified_human_disposition_refs=human_refs,
    )


def _codes(result) -> set[str]:  # type: ignore[no-untyped-def]
    return {finding.code for finding in result.findings}


def test_clean_new_volume_passes_against_all_prior_passports() -> None:
    result = _evaluate()

    assert result.qualified
    assert result.findings == ()
    assert result.current_passport_ref == passport_ref(CURRENT)
    assert result.series_brain_ref.startswith("series-brain:")


def test_historical_series_profile_revision_does_not_invalidate_prior_books() -> None:
    assert PRIOR_ONE.series_profile_ref != CURRENT.series_profile_ref
    assert PRIOR_ONE.series_profile_id == CURRENT.series_profile_id

    result = _evaluate()

    assert "SERIES.PRIOR.SERIES_PROFILE_ID_MISMATCH" not in _codes(result)
    assert result.qualified


def test_current_passport_must_use_exact_current_series_profile() -> None:
    stale_current = replace(CURRENT, series_profile_ref=HISTORICAL_PROFILE_REF)
    semantic, artifacts = _semantic_evidence(current=stale_current)

    result = _evaluate(
        current=stale_current,
        semantic=semantic,
        artifacts=artifacts,
    )

    assert "SERIES.PASSPORT.SERIES_PROFILE_MISMATCH" in _codes(result)
    assert not result.qualified


def test_series_profile_snapshot_itself_is_version_bound() -> None:
    stale_profile = replace(PROFILE, content_hash=_hash("series-profile-v3"))
    semantic, artifacts = _semantic_evidence()

    result = _evaluate(
        profile=PROFILE,
        current_profile=stale_profile,
        semantic=semantic,
        artifacts=artifacts,
    )

    assert "SERIES.PROFILE.STALE" in _codes(result)
    assert not result.qualified


def test_exact_blocking_dimension_reuse_blocks_even_with_other_surface_changes() -> None:
    current = replace(CURRENT, mechanism=PRIOR_ONE.mechanism)
    semantic, artifacts = _semantic_evidence(current=current)

    result = _evaluate(
        current=current,
        semantic=semantic,
        artifacts=artifacts,
    )

    assert "SERIES.COLLISION.EXACT_BLOCKING" in _codes(result)
    assert any(finding.dimension == "MECHANISM" for finding in result.findings)
    assert not result.qualified


def test_exact_attention_pattern_is_diagnostic_not_automatic_blocker() -> None:
    current = replace(CURRENT, opening_pattern=PRIOR_ONE.opening_pattern)
    semantic, artifacts = _semantic_evidence(current=current)

    result = _evaluate(
        current=current,
        semantic=semantic,
        artifacts=artifacts,
    )

    assert "SERIES.COLLISION.EXACT_ATTENTION" in _codes(result)
    assert result.qualified


def test_same_culprit_relationship_and_motive_family_is_composite_blocker() -> None:
    current = replace(
        CURRENT,
        culprit_relationship=PRIOR_ONE.culprit_relationship,
        motive_family=PRIOR_ONE.motive_family,
    )
    semantic, artifacts = _semantic_evidence(current=current)

    result = _evaluate(
        current=current,
        semantic=semantic,
        artifacts=artifacts,
    )

    assert "SERIES.COLLISION.CULPRIT_RELATIONSHIP_AND_MOTIVE" in _codes(result)
    assert not result.qualified


def test_consumed_one_use_asset_cannot_be_reused_but_recurring_signature_can() -> None:
    current = replace(
        CURRENT,
        assets_consumed=(
            "asset-used-1",
            "asset-reserved-for-future",
            "signature-city",
        ),
        reservation_claim_codes=("asset-reserved-for-future",),
    )
    semantic, artifacts = _semantic_evidence(current=current)

    result = _evaluate(
        current=current,
        semantic=semantic,
        artifacts=artifacts,
    )

    assert "SERIES.ASSET.REUSED_ONE_USE" in _codes(result)
    assert not any(
        finding.code == "SERIES.ASSET.REUSED_ONE_USE" and "signature-city" in finding.evidence_refs
        for finding in result.findings
    )


def test_reserved_asset_requires_explicit_claim_before_consumption() -> None:
    current = replace(CURRENT, reservation_claim_codes=())
    semantic, artifacts = _semantic_evidence(current=current)

    result = _evaluate(
        current=current,
        semantic=semantic,
        artifacts=artifacts,
    )

    assert "SERIES.ASSET.RESERVATION_NOT_CLAIMED" in _codes(result)
    assert not result.qualified


def test_unknown_reservation_claim_blocks() -> None:
    current = replace(
        CURRENT,
        reservation_claim_codes=(
            "asset-reserved-for-future",
            "never-reserved",
        ),
        assets_consumed=(
            "asset-reserved-for-future",
            "never-reserved",
            "signature-city",
        ),
    )
    semantic, artifacts = _semantic_evidence(current=current)

    result = _evaluate(
        current=current,
        semantic=semantic,
        artifacts=artifacts,
    )

    assert "SERIES.ASSET.CLAIM_UNKNOWN_RESERVATION" in _codes(result)


def test_imported_prior_asset_history_is_revalidated() -> None:
    book2 = _passport(
        book_id="book-historical-2",
        number=2,
        profile_ref=HISTORICAL_PROFILE_REF,
        suffix="historical-two",
        assets_consumed=("asset-used-1",),
        orientation="orientation:historical-2",
    )
    accepted2 = _accepted(book2)
    current = replace(CURRENT, book_number=3, late_entry_orientation_ref="orientation:v3")
    prior = (ACCEPTED_ONE, accepted2)
    semantic, artifacts = _semantic_evidence(current=current, prior=prior)

    result = _evaluate(
        current=current,
        prior=prior,
        semantic=semantic,
        artifacts=artifacts,
    )

    assert "SERIES.PRIOR_ASSET.REUSED_CONSUMED" in _codes(result)
    assert not result.qualified


def test_tampered_prior_passport_hash_blocks() -> None:
    tampered = replace(ACCEPTED_ONE, passport_hash=_hash("tampered"))
    semantic, artifacts = _semantic_evidence(prior=(tampered,))

    result = _evaluate(
        prior=(tampered,),
        semantic=semantic,
        artifacts=artifacts,
    )

    assert "SERIES.PRIOR.HASH_MISMATCH" in _codes(result)


def test_semantic_evidence_is_required_for_every_prior_book_and_dimension() -> None:
    semantic, artifacts = _semantic_evidence()
    missing = semantic[:-1]

    result = _evaluate(
        semantic=missing,
        artifacts=artifacts,
    )

    assert "SERIES.SEMANTIC.REQUIRED_EVIDENCE_MISSING" in _codes(result)
    assert not result.qualified


def test_semantic_material_collision_blocks_when_lexical_fields_differ() -> None:
    key = (PRIOR_ONE.book_id, "PREMISE")
    semantic, artifacts = _semantic_evidence(
        state_overrides={key: "MATERIAL_COLLISION"},
    )

    result = _evaluate(
        semantic=semantic,
        artifacts=artifacts,
    )

    assert "SERIES.COLLISION.SEMANTIC_BLOCKING" in _codes(result)
    assert not result.qualified


def test_semantic_attention_requires_verified_human_disposition() -> None:
    key = (PRIOR_ONE.book_id, "EMOTIONAL_CONFLICT")
    semantic, artifacts = _semantic_evidence(
        state_overrides={key: "ATTENTION"},
        human_refs={key: "human:series-attention:v1"},
    )

    unverified = _evaluate(
        semantic=semantic,
        artifacts=artifacts,
    )
    assert "SERIES.COLLISION.SEMANTIC_ATTENTION_UNVERIFIED" in _codes(unverified)

    verified = _evaluate(
        semantic=semantic,
        artifacts=artifacts,
        human_refs=frozenset({"human:series-attention:v1"}),
    )
    assert verified.qualified


def test_semantic_artifact_must_match_exact_series_context_and_purpose() -> None:
    semantic, artifacts = _semantic_evidence()
    target = semantic[0]
    baseline = artifacts[target.evaluation_ref]

    variants = (
        (
            replace(baseline, manuscript_snapshot_ref="series-context:other"),
            "SERIES.SEMANTIC.ARTIFACT_SNAPSHOT_MISMATCH",
        ),
        (
            replace(baseline, purpose="SERIES_COLLISION:wrong:purpose"),
            "SERIES.SEMANTIC.ARTIFACT_PURPOSE_MISMATCH",
        ),
        (
            replace(baseline, rubric_ref="rubric:wrong"),
            "SERIES.SEMANTIC.ARTIFACT_RUBRIC_MISMATCH",
        ),
        (
            replace(baseline, current=False),
            "SERIES.SEMANTIC.ARTIFACT_NOT_CURRENT_SUCCESS",
        ),
    )

    for artifact, expected_code in variants:
        revised_artifacts = dict(artifacts)
        revised_artifacts[target.evaluation_ref] = artifact
        result = _evaluate(
            semantic=semantic,
            artifacts=revised_artifacts,
        )
        assert expected_code in _codes(result)
        assert not result.qualified


def test_series_brain_ref_changes_when_semantic_evidence_changes() -> None:
    semantic, artifacts = _semantic_evidence()
    initial = _evaluate(semantic=semantic, artifacts=artifacts)
    assert initial.qualified

    first = semantic[0]
    changed_first = replace(
        first,
        evaluation_ref=first.evaluation_ref + ":rerun",
    )
    changed_semantic = (changed_first, *semantic[1:])
    context_ref = series_context_ref(
        profile=PROFILE,
        current_passport=CURRENT,
        prior_passports=(ACCEPTED_ONE,),
        policy=POLICY,
        writer_executor_identity=WRITER_ID,
    )
    changed_artifacts = dict(artifacts)
    del changed_artifacts[first.evaluation_ref]
    changed_artifacts[changed_first.evaluation_ref] = VerifiedEvaluationArtifact(
        evaluation_ref=changed_first.evaluation_ref,
        manuscript_snapshot_ref=context_ref,
        evaluator_identity=changed_first.evaluator_identity,
        evaluator_class=changed_first.evaluator_class,
        rubric_ref=changed_first.rubric_ref,
        purpose=(
            f"SERIES_COLLISION:{CURRENT.book_id}:{PRIOR_ONE.book_id}:{changed_first.dimension}"
        ),
        status="SUCCEEDED",
        current=True,
    )
    current = _evaluate(
        semantic=changed_semantic,
        artifacts=changed_artifacts,
    )

    assert current.qualified
    assert current.series_brain_ref != initial.series_brain_ref

    verification = verify_series_uniqueness(
        prior_series_brain_ref=initial.series_brain_ref,
        profile=PROFILE,
        current_profile=PROFILE,
        current_passport=CURRENT,
        prior_passports=(ACCEPTED_ONE,),
        policy=POLICY,
        writer_executor_identity=WRITER_ID,
        semantic_evidence=changed_semantic,
        verified_evaluations=changed_artifacts,
    )
    assert not verification.valid
    assert verification.reason == "SERIES_BRAIN_SNAPSHOT_CHANGED"


def test_series_policy_change_invalidates_previous_series_brain_ref() -> None:
    semantic, artifacts = _semantic_evidence()
    initial = _evaluate(semantic=semantic, artifacts=artifacts)
    assert initial.qualified

    changed_policy = replace(
        POLICY,
        exact_attention_dimensions=(
            *POLICY.exact_attention_dimensions,
            "BODY_DISCOVERY_PATTERN",
        ),
    )
    changed_semantic, changed_artifacts = _semantic_evidence(
        policy=changed_policy,
    )
    current = _evaluate(
        policy=changed_policy,
        semantic=changed_semantic,
        artifacts=changed_artifacts,
    )

    assert current.qualified
    assert current.series_brain_ref != initial.series_brain_ref


def test_standalone_series_requires_case_resolution_and_late_entry_orientation() -> None:
    unresolved = replace(
        CURRENT,
        primary_case_resolved=False,
        late_entry_orientation_ref=None,
    )
    semantic, artifacts = _semantic_evidence(current=unresolved)

    result = _evaluate(
        current=unresolved,
        semantic=semantic,
        artifacts=artifacts,
    )
    codes = _codes(result)

    assert "SERIES.STANDALONE.PRIMARY_CASE_UNRESOLVED" in codes
    assert "SERIES.STANDALONE.LATE_ENTRY_ORIENTATION_MISSING" in codes
    assert not result.qualified


def test_strongly_serialized_profile_can_relax_standalone_rules() -> None:
    serialized_profile = replace(
        PROFILE,
        content_hash=_hash("series-profile-serialized-v3"),
        strongly_serialized=True,
    )
    current = replace(
        CURRENT,
        series_profile_ref=series_profile_ref(serialized_profile),
        primary_case_resolved=False,
        late_entry_orientation_ref=None,
    )
    semantic, artifacts = _semantic_evidence(current=current)
    # Rebuild semantic evidence against the serialized profile context.
    context_ref = series_context_ref(
        profile=serialized_profile,
        current_passport=current,
        prior_passports=(ACCEPTED_ONE,),
        policy=POLICY,
        writer_executor_identity=WRITER_ID,
    )
    artifacts = {
        ref: replace(artifact, manuscript_snapshot_ref=context_ref)
        for ref, artifact in artifacts.items()
    }

    result = evaluate_series_uniqueness(
        profile=serialized_profile,
        current_profile=serialized_profile,
        current_passport=current,
        prior_passports=(ACCEPTED_ONE,),
        policy=POLICY,
        writer_executor_identity=WRITER_ID,
        semantic_evidence=semantic,
        verified_evaluations=artifacts,
    )

    assert "SERIES.STANDALONE.PRIMARY_CASE_UNRESOLVED" not in _codes(result)
    assert "SERIES.STANDALONE.LATE_ENTRY_ORIENTATION_MISSING" not in _codes(result)


def test_book_one_requires_no_semantic_evidence_when_there_are_no_prior_books() -> None:
    book1 = _passport(
        book_id="new-series-book-1",
        number=1,
        profile_ref=CURRENT_PROFILE_REF,
        suffix="fresh-one",
        orientation=None,
    )

    result = _evaluate(
        current=book1,
        prior=(),
        semantic=(),
        artifacts={},
    )

    assert result.qualified


def test_runtime_unknown_policy_dimension_and_semantic_state_fail_closed() -> None:
    bad_policy = SeriesCollisionPolicy(
        exact_blocking_dimensions=("ALIEN_DIMENSION",),  # type: ignore[arg-type]
        exact_attention_dimensions=(),
        semantic_required_dimensions=POLICY.semantic_required_dimensions,
    )
    semantic, artifacts = _semantic_evidence(policy=bad_policy)
    first = semantic[0]
    bad_semantic = (
        replace(first, state="ALIEN_STATE"),  # type: ignore[arg-type]
        *semantic[1:],
    )

    result = _evaluate(
        policy=bad_policy,
        semantic=bad_semantic,
        artifacts=artifacts,
    )
    codes = _codes(result)

    assert "SERIES.POLICY.DIMENSION_UNKNOWN" in codes
    assert "SERIES.SEMANTIC.STATE_UNKNOWN" in codes
    assert not result.qualified


def test_policy_dimension_overlap_is_rejected() -> None:
    overlapping = replace(
        POLICY,
        exact_attention_dimensions=(
            *POLICY.exact_attention_dimensions,
            "MECHANISM",
        ),
    )
    semantic, artifacts = _semantic_evidence(policy=overlapping)

    result = _evaluate(
        policy=overlapping,
        semantic=semantic,
        artifacts=artifacts,
    )

    assert "SERIES.POLICY.EXACT_DIMENSION_OVERLAP" in _codes(result)
    assert not result.qualified


def test_semantic_series_editor_cannot_be_writer_executor() -> None:
    semantic, artifacts = _semantic_evidence()
    target = semantic[0]
    changed = replace(
        target,
        evaluator_identity=WRITER_ID,
    )
    revised = (changed, *semantic[1:])
    revised_artifacts = dict(artifacts)
    revised_artifacts[target.evaluation_ref] = replace(
        revised_artifacts[target.evaluation_ref],
        evaluator_identity=WRITER_ID,
    )

    result = _evaluate(
        semantic=revised,
        artifacts=revised_artifacts,
    )

    assert "SERIES.SEMANTIC.SAME_WRITER_EXECUTOR" in _codes(result)
    assert not result.qualified


def test_malformed_historical_series_profile_ref_blocks() -> None:
    broken_prior = replace(
        PRIOR_ONE,
        series_profile_ref="series-profile:other:garbage",
    )
    accepted = _accepted(broken_prior)
    semantic, artifacts = _semantic_evidence(prior=(accepted,))

    result = _evaluate(
        prior=(accepted,),
        semantic=semantic,
        artifacts=artifacts,
    )

    assert "SERIES.PASSPORT.SERIES_PROFILE_REF_INVALID" in _codes(result)
    assert not result.qualified


def test_prior_passport_number_must_really_precede_current_book() -> None:
    future_prior = _passport(
        book_id="book-future",
        number=9,
        profile_ref=HISTORICAL_PROFILE_REF,
        suffix="future",
    )
    accepted = _accepted(future_prior)
    semantic, artifacts = _semantic_evidence(prior=(accepted,))

    result = _evaluate(
        prior=(accepted,),
        semantic=semantic,
        artifacts=artifacts,
    )

    assert "SERIES.PRIOR.NOT_ACTUALLY_PRIOR" in _codes(result)
    assert not result.qualified


def test_semantic_core_cannot_be_disabled_by_policy() -> None:
    weakened = replace(
        POLICY,
        semantic_required_dimensions=("PREMISE",),
    )
    semantic, artifacts = _semantic_evidence(policy=weakened)

    result = _evaluate(
        policy=weakened,
        semantic=semantic,
        artifacts=artifacts,
    )

    assert "SERIES.POLICY.SEMANTIC_CORE_MISSING" in _codes(result)
    assert not result.qualified


def test_exact_and_semantic_overlap_is_required_not_rejected() -> None:
    assert "MECHANISM" in POLICY.exact_blocking_dimensions
    assert "MECHANISM" in POLICY.semantic_required_dimensions

    result = _evaluate()

    assert "SERIES.POLICY.EXACT_DIMENSION_OVERLAP" not in _codes(result)
    assert result.qualified


def test_later_profile_cannot_reclassify_old_one_use_asset_as_recurring() -> None:
    expanded_profile = replace(
        PROFILE,
        content_hash=_hash("series-profile-v3-add-old-asset"),
        allowed_recurring_asset_codes=(
            *PROFILE.allowed_recurring_asset_codes,
            "asset-used-1",
        ),
    )
    current = replace(
        CURRENT,
        series_profile_ref=series_profile_ref(expanded_profile),
        assets_consumed=(
            "asset-reserved-for-future",
            "signature-city",
            "asset-used-1",
        ),
    )
    semantic, artifacts = _semantic_evidence(current=current)
    context_ref = series_context_ref(
        profile=expanded_profile,
        current_passport=current,
        prior_passports=(ACCEPTED_ONE,),
        policy=POLICY,
        writer_executor_identity=WRITER_ID,
    )
    artifacts = {
        ref: replace(artifact, manuscript_snapshot_ref=context_ref)
        for ref, artifact in artifacts.items()
    }

    result = evaluate_series_uniqueness(
        profile=expanded_profile,
        current_profile=expanded_profile,
        current_passport=current,
        prior_passports=(ACCEPTED_ONE,),
        policy=POLICY,
        writer_executor_identity=WRITER_ID,
        semantic_evidence=semantic,
        verified_evaluations=artifacts,
    )

    assert "SERIES.ASSET.REUSED_ONE_USE" in _codes(result)
    assert not result.qualified


def test_deterministic_evaluator_cannot_satisfy_semantic_collision_core() -> None:
    semantic, artifacts = _semantic_evidence()
    target = semantic[0]
    changed = replace(
        target,
        evaluator_class="DETERMINISTIC",
    )
    revised = (changed, *semantic[1:])
    revised_artifacts = dict(artifacts)
    revised_artifacts[target.evaluation_ref] = replace(
        revised_artifacts[target.evaluation_ref],
        evaluator_class="DETERMINISTIC",
    )

    result = _evaluate(
        semantic=revised,
        artifacts=revised_artifacts,
    )

    assert "SERIES.SEMANTIC.DETERMINISTIC_EVALUATOR_INVALID" in _codes(result)
    assert not result.qualified
