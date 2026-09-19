from __future__ import annotations

from dataclasses import replace
import hashlib

from book_os_core.mystery_anti_cliche_catalog import (
    DEFAULT_MYSTERY_ANTI_CLICHE_RULE_PACK,
)
from book_os_core.mystery_anti_cliche_validation import (
    AntiClicheException,
    AntiClicheFinding,
    AntiClichePolicy,
    AntiClicheRule,
    AntiClicheRulePack,
    AntiClicheRun,
    anti_cliche_finding_ref,
    anti_cliche_rule_pack_hash,
    anti_cliche_rule_pack_ref,
    evaluate_anti_cliche,
    verify_anti_cliche,
)
from book_os_core.mystery_bench_validation import VerifiedEvaluationArtifact


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


SNAPSHOT_REF = "anti-cliche-target:book-1:story-v1"
SNAPSHOT_HASH = _hash("story-v1")
WRITER_ID = "writer/model-standard"
JUDGE_ID = "anti-cliche/editor-independent"

RULE_BLOCKED = AntiClicheRule(
    code="TEST.BLOCKED",
    level="BLOCKED_BY_DEFAULT",
    category="TEST",
    title="Blocked trope",
    description="Synthetic blocked-by-default trope.",
    exception_allowed=True,
)
RULE_HIGH = AntiClicheRule(
    code="TEST.HIGH",
    level="HIGH_RISK_TROPE",
    category="TEST",
    title="High risk trope",
    description="Synthetic high-risk trope.",
    exception_allowed=False,
)
RULE_STYLE = AntiClicheRule(
    code="TEST.STYLE",
    level="STYLE_PATHOLOGY",
    category="TEST",
    title="Style pathology",
    description="Synthetic style pathology.",
    exception_allowed=False,
)
RULE_SERIES = AntiClicheRule(
    code="TEST.SERIES",
    level="SERIES_COLLISION",
    category="TEST",
    title="Series collision",
    description="Synthetic series collision.",
    exception_allowed=False,
)

RULE_PACK = AntiClicheRulePack(
    pack_id="synthetic-anti-cliche",
    version=1,
    rules=(RULE_BLOCKED, RULE_HIGH, RULE_STYLE, RULE_SERIES),
)
POLICY = AntiClichePolicy(stage="PRE_DRAFT")


def _finding(
    rule_code: str,
    *,
    severity: str = "BLOCKING",
    exact_use: str = "exact detected use",
    human_ref: str | None = None,
) -> AntiClicheFinding:
    return AntiClicheFinding(
        rule_code=rule_code,
        severity=severity,  # type: ignore[arg-type]
        observation=f"Detected {rule_code}",
        exact_proposed_use=exact_use,
        target_object_refs=("story-definition:book-1:v1",),
        evidence_refs=("evidence:anti-cliche:1",),
        evaluation_ref="anti-cliche-scan:v1",
        human_disposition_ref=human_ref,
    )


def _run(
    *,
    rule_pack: AntiClicheRulePack = RULE_PACK,
    findings: tuple[AntiClicheFinding, ...] = (),
    exceptions: tuple[AntiClicheException, ...] = (),
    series_book: bool = False,
    series_brain_ref: str | None = None,
    evaluator_identity: str = JUDGE_ID,
    evaluator_class: str = "LLM_JUDGE",
) -> AntiClicheRun:
    return AntiClicheRun(
        book_id="book-1",
        stage="PRE_DRAFT",
        target_snapshot_ref=SNAPSHOT_REF,
        target_snapshot_hash=SNAPSHOT_HASH,
        writer_executor_identity=WRITER_ID,
        rule_pack_ref=anti_cliche_rule_pack_ref(rule_pack),
        rule_pack_hash=anti_cliche_rule_pack_hash(rule_pack),
        scan_evaluation_ref="anti-cliche-scan:v1",
        scan_rubric_ref="anti-cliche-rubric:v1",
        evaluator_identity=evaluator_identity,
        evaluator_class=evaluator_class,  # type: ignore[arg-type]
        findings=findings,
        exceptions=exceptions,
        series_book=series_book,
        current_series_brain_ref=series_brain_ref,
    )


def _verified(run: AntiClicheRun) -> dict[str, VerifiedEvaluationArtifact]:
    return {
        run.scan_evaluation_ref: VerifiedEvaluationArtifact(
            evaluation_ref=run.scan_evaluation_ref,
            manuscript_snapshot_ref=run.target_snapshot_ref,
            evaluator_identity=run.evaluator_identity,
            evaluator_class=run.evaluator_class,
            rubric_ref=run.scan_rubric_ref,
            purpose=f"ANTI_CLICHE_SCAN:{run.stage}:{run.rule_pack_ref}",
            status="SUCCEEDED",
            current=True,
        )
    }


def _exception(
    finding: AntiClicheFinding,
    *,
    run: AntiClicheRun,
    decision: str = "ACCEPT",
    human_ref: str = "human:anti-cliche:accept:v1",
    exact_use: str | None = None,
    series_ref: str | None = None,
) -> AntiClicheException:
    return AntiClicheException(
        exception_id="anti-cliche-exception:1",
        finding_ref=anti_cliche_finding_ref(
            finding,
            target_snapshot_ref=run.target_snapshot_ref,
        ),
        rule_code=finding.rule_code,
        rule_pack_ref=run.rule_pack_ref,
        target_snapshot_ref=run.target_snapshot_ref,
        exact_proposed_use=exact_use or finding.exact_proposed_use,
        reinvention_rationale="The familiar surface is causally transformed.",
        expected_reader_familiarity="Experienced genre readers will recognize it.",
        material_transformation="Mechanism, consequence and character causality differ materially.",
        alternatives_considered=("alternative:a", "alternative:b"),
        series_collision_ref=series_ref,
        decision=decision,  # type: ignore[arg-type]
        human_decision_ref=human_ref,
    )


def _evaluate(
    run: AntiClicheRun,
    *,
    rule_pack: AntiClicheRulePack = RULE_PACK,
    verified: dict[str, VerifiedEvaluationArtifact] | None = None,
    human_refs: frozenset[str] = frozenset(),
    snapshot_ref: str = SNAPSHOT_REF,
    snapshot_hash: str = SNAPSHOT_HASH,
):
    return evaluate_anti_cliche(
        run=run,
        policy=POLICY,
        rule_pack=rule_pack,
        current_target_snapshot_ref=snapshot_ref,
        current_target_snapshot_hash=snapshot_hash,
        verified_evaluations=verified if verified is not None else _verified(run),
        verified_human_decision_refs=human_refs,
    )


def _codes(result) -> set[str]:  # type: ignore[no-untyped-def]
    return {finding.code for finding in result.findings}


def test_default_catalog_contains_project_specific_blocked_shortcuts() -> None:
    rules = {rule.code: rule for rule in DEFAULT_MYSTERY_ANTI_CLICHE_RULE_PACK.rules}

    for code in (
        "SUP.INHERITED_OLD_MANSION",
        "SUP.DUSTY_ARCHIVE_EXPLAINS_MYSTERY",
        "SUP.BOOKCASE_SECRET_ROOM",
        "TECH.CONVENIENT_FAILURE",
        "FORENSICS.LATE_DECISIVE_FACT",
        "DEVICE.AMNESIA_INFORMATION_HIDE",
        "MOTIVE.PSYCHIATRIC_DIAGNOSIS_SHORTCUT",
        "SUP.CHOSEN_BY_BLOODLINE",
        "SUP.CONVENIENT_PSYCHIC",
        "SUP.REPEATED_DEAD_CALL_FIXED_ENGINE",
    ):
        assert code in rules
        assert rules[code].level == "BLOCKED_BY_DEFAULT"

    assert len(DEFAULT_MYSTERY_ANTI_CLICHE_RULE_PACK.rules) >= 50


def test_clean_scan_passes_and_is_version_bound() -> None:
    run = _run()

    result = _evaluate(run)

    assert result.qualified
    assert result.findings == ()
    assert result.anti_cliche_ref.startswith("anti-cliche:")
    assert result.rule_pack_ref == anti_cliche_rule_pack_ref(RULE_PACK)

    verified = verify_anti_cliche(
        prior_anti_cliche_ref=result.anti_cliche_ref,
        run=run,
        policy=POLICY,
        rule_pack=RULE_PACK,
        current_target_snapshot_ref=SNAPSHOT_REF,
        current_target_snapshot_hash=SNAPSHOT_HASH,
        verified_evaluations=_verified(run),
    )
    assert verified.valid


def test_blocked_by_default_finding_requires_exact_human_exception() -> None:
    finding = _finding("TEST.BLOCKED")
    run = _run(findings=(finding,))

    result = _evaluate(run)

    assert "ANTI_CLICHE.BLOCKED_RULE.EXCEPTION_MISSING" in _codes(result)
    assert not result.qualified


def test_exact_accepted_exception_clears_blocked_by_default_finding() -> None:
    finding = _finding("TEST.BLOCKED")
    base = _run(findings=(finding,))
    exception = _exception(finding, run=base)
    run = replace(base, exceptions=(exception,))

    result = _evaluate(
        run,
        human_refs=frozenset({exception.human_decision_ref}),
    )

    assert result.qualified
    assert result.unresolved_blocking_codes == ()


def test_model_string_cannot_impersonate_human_exception_approval() -> None:
    finding = _finding("TEST.BLOCKED")
    base = _run(findings=(finding,))
    exception = _exception(
        finding,
        run=base,
        human_ref="human:invented-by-model",
    )
    run = replace(base, exceptions=(exception,))

    result = _evaluate(run)

    assert "ANTI_CLICHE.EXCEPTION.HUMAN_DECISION_UNVERIFIED" in _codes(result)
    assert not result.qualified


def test_rework_or_reject_exception_never_unlocks() -> None:
    finding = _finding("TEST.BLOCKED")
    base = _run(findings=(finding,))

    for decision in ("REWORK", "REJECT"):
        exception = _exception(
            finding,
            run=base,
            decision=decision,
        )
        run = replace(base, exceptions=(exception,))
        result = _evaluate(
            run,
            human_refs=frozenset({exception.human_decision_ref}),
        )
        assert "ANTI_CLICHE.EXCEPTION.NOT_ACCEPTED" in _codes(result)
        assert not result.qualified


def test_exception_is_scoped_to_exact_use_snapshot_and_rule_pack() -> None:
    finding = _finding("TEST.BLOCKED")
    base = _run(findings=(finding,))
    accepted = _exception(finding, run=base)

    variants = (
        (
            replace(accepted, exact_proposed_use="different use"),
            "ANTI_CLICHE.EXCEPTION.USE_MISMATCH",
        ),
        (
            replace(accepted, target_snapshot_ref="snapshot:old"),
            "ANTI_CLICHE.EXCEPTION.SNAPSHOT_STALE",
        ),
        (
            replace(accepted, rule_pack_ref="anti-cliche-rule-pack:old"),
            "ANTI_CLICHE.EXCEPTION.RULE_PACK_STALE",
        ),
    )

    for exception, expected in variants:
        run = replace(base, exceptions=(exception,))
        result = _evaluate(
            run,
            human_refs=frozenset({exception.human_decision_ref}),
        )
        assert expected in _codes(result)
        assert not result.qualified


def test_series_book_exception_must_cite_current_series_brain() -> None:
    finding = _finding("TEST.BLOCKED")
    brain_ref = "series-brain:current-v1"
    base = _run(
        findings=(finding,),
        series_book=True,
        series_brain_ref=brain_ref,
    )
    wrong = _exception(
        finding,
        run=base,
        series_ref="series-brain:old",
    )
    wrong_run = replace(base, exceptions=(wrong,))
    blocked = _evaluate(
        wrong_run,
        human_refs=frozenset({wrong.human_decision_ref}),
    )
    assert "ANTI_CLICHE.EXCEPTION.SERIES_REF_MISMATCH" in _codes(blocked)

    correct = replace(wrong, series_collision_ref=brain_ref)
    correct_run = replace(base, exceptions=(correct,))
    allowed = _evaluate(
        correct_run,
        human_refs=frozenset({correct.human_decision_ref}),
    )
    assert allowed.qualified


def test_series_collision_rule_cannot_be_waived_by_anti_cliche_exception() -> None:
    finding = _finding("TEST.SERIES")
    base = _run(
        findings=(finding,),
        series_book=True,
        series_brain_ref="series-brain:current-v1",
    )
    exception = _exception(
        finding,
        run=base,
        series_ref="series-brain:current-v1",
    )
    run = replace(base, exceptions=(exception,))

    result = _evaluate(
        run,
        human_refs=frozenset({exception.human_decision_ref}),
    )
    codes = _codes(result)

    assert "ANTI_CLICHE.SERIES_COLLISION.BLOCKING" in codes
    assert "ANTI_CLICHE.SERIES_COLLISION.EXCEPTION_INVALID" in codes
    assert not result.qualified


def test_high_risk_major_requires_verified_human_disposition() -> None:
    finding = _finding(
        "TEST.HIGH",
        severity="MAJOR",
        human_ref="human:high-risk:v1",
    )
    run = _run(findings=(finding,))

    blocked = _evaluate(run)
    assert "ANTI_CLICHE.FINDING.MAJOR_DISPOSITION_UNVERIFIED" in _codes(blocked)

    allowed = _evaluate(
        run,
        human_refs=frozenset({"human:high-risk:v1"}),
    )
    assert allowed.qualified


def test_high_risk_blocking_finding_cannot_be_human_waived() -> None:
    finding = _finding(
        "TEST.HIGH",
        severity="BLOCKING",
        human_ref="human:waive-attempt",
    )
    run = _run(findings=(finding,))

    result = _evaluate(
        run,
        human_refs=frozenset({"human:waive-attempt"}),
    )

    assert "ANTI_CLICHE.FINDING.BLOCKING" in _codes(result)
    assert not result.qualified


def test_scan_artifact_is_exact_and_independent_from_writer() -> None:
    run = _run()
    artifact = _verified(run)[run.scan_evaluation_ref]

    variants = (
        (
            replace(artifact, manuscript_snapshot_ref="snapshot:other"),
            "ANTI_CLICHE.SCAN.ARTIFACT_SNAPSHOT_MISMATCH",
        ),
        (
            replace(artifact, purpose="ANTI_CLICHE_SCAN:wrong"),
            "ANTI_CLICHE.SCAN.ARTIFACT_PURPOSE_MISMATCH",
        ),
        (
            replace(artifact, rubric_ref="rubric:wrong"),
            "ANTI_CLICHE.SCAN.ARTIFACT_RUBRIC_MISMATCH",
        ),
        (
            replace(artifact, current=False),
            "ANTI_CLICHE.SCAN.ARTIFACT_NOT_CURRENT_SUCCESS",
        ),
    )
    for changed, expected in variants:
        result = _evaluate(
            run,
            verified={run.scan_evaluation_ref: changed},
        )
        assert expected in _codes(result)
        assert not result.qualified

    same_writer = _run(evaluator_identity=WRITER_ID)
    same_writer_result = _evaluate(same_writer)
    assert "ANTI_CLICHE.SCAN.SAME_WRITER_EXECUTOR" in _codes(same_writer_result)


def test_deterministic_only_scan_cannot_certify_contextual_cliches() -> None:
    run = _run(evaluator_class="DETERMINISTIC")

    result = _evaluate(run)

    assert "ANTI_CLICHE.SCAN.EVALUATOR_CLASS_INVALID" in _codes(result)
    assert not result.qualified


def test_rule_pack_or_target_change_invalidates_old_scan() -> None:
    run = _run()
    stale_target = _evaluate(
        run,
        snapshot_hash=_hash("story-v2"),
    )
    assert "ANTI_CLICHE.RUN.SNAPSHOT_STALE" in _codes(stale_target)

    changed_pack = replace(RULE_PACK, version=2)
    stale_pack = _evaluate(
        run,
        rule_pack=changed_pack,
    )
    assert "ANTI_CLICHE.RUN.RULE_PACK_STALE" in _codes(stale_pack)


def test_unknown_rule_and_duplicate_exception_fail_closed() -> None:
    unknown = _finding("NO_SUCH_RULE")
    run = _run(findings=(unknown,))
    result = _evaluate(run)
    assert "ANTI_CLICHE.FINDING.RULE_UNKNOWN" in _codes(result)

    blocked = _finding("TEST.BLOCKED")
    base = _run(findings=(blocked,))
    exception = _exception(blocked, run=base)
    duplicate = replace(exception, exception_id="anti-cliche-exception:2")
    duplicate_run = replace(
        base,
        exceptions=(exception, duplicate),
    )
    duplicate_result = _evaluate(
        duplicate_run,
        human_refs=frozenset({exception.human_decision_ref}),
    )
    assert "ANTI_CLICHE.EXCEPTION.MULTIPLE_FOR_FINDING" in _codes(
        duplicate_result
    )


def test_invalid_series_collision_rule_pack_cannot_make_collision_waivable() -> None:
    invalid = replace(RULE_SERIES, exception_allowed=True)
    pack = replace(
        RULE_PACK,
        rules=(RULE_BLOCKED, RULE_HIGH, RULE_STYLE, invalid),
    )
    run = _run(rule_pack=pack)

    result = _evaluate(run, rule_pack=pack)

    assert (
        "ANTI_CLICHE.RULE.SERIES_COLLISION_EXCEPTION_FORBIDDEN"
        in _codes(result)
    )
    assert not result.qualified
