from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, TypeAlias

from .authority_types import JSONValue, content_hash
from .mystery_bench_validation import EvaluatorClass, VerifiedEvaluationArtifact

AntiClicheStage: TypeAlias = Literal[
    "PRE_DRAFT",
    "REPRESENTATIVE_SAMPLE",
    "MIDBOOK",
    "WHOLE_BOOK",
    "FINAL",
]
AntiClicheLevel: TypeAlias = Literal[
    "BLOCKED_BY_DEFAULT",
    "HIGH_RISK_TROPE",
    "STYLE_PATHOLOGY",
    "SERIES_COLLISION",
]
AntiClicheSeverity: TypeAlias = Literal["BLOCKING", "MAJOR", "MINOR", "NOTE"]
ExceptionDecision: TypeAlias = Literal["ACCEPT", "REWORK", "REJECT"]

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_VALID_STAGES = frozenset({"PRE_DRAFT", "REPRESENTATIVE_SAMPLE", "MIDBOOK", "WHOLE_BOOK", "FINAL"})
_VALID_LEVELS = frozenset(
    {
        "BLOCKED_BY_DEFAULT",
        "HIGH_RISK_TROPE",
        "STYLE_PATHOLOGY",
        "SERIES_COLLISION",
    }
)
_VALID_SEVERITIES = frozenset({"BLOCKING", "MAJOR", "MINOR", "NOTE"})
_VALID_DECISIONS = frozenset({"ACCEPT", "REWORK", "REJECT"})
_VALID_EVALUATOR_CLASSES = frozenset({"SEMANTIC", "LLM_JUDGE", "PAIRWISE", "HUMAN_LABEL"})


@dataclass(frozen=True)
class AntiClicheRule:
    code: str
    level: AntiClicheLevel
    category: str
    title: str
    description: str
    exception_allowed: bool
    semantic_review_required: bool = True


@dataclass(frozen=True)
class AntiClicheRulePack:
    pack_id: str
    version: int
    rules: tuple[AntiClicheRule, ...]


@dataclass(frozen=True)
class AntiClicheFinding:
    rule_code: str
    severity: AntiClicheSeverity
    observation: str
    exact_proposed_use: str
    target_object_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    evaluation_ref: str
    human_disposition_ref: str | None = None


@dataclass(frozen=True)
class AntiClicheException:
    exception_id: str
    finding_ref: str
    rule_code: str
    rule_pack_ref: str
    target_snapshot_ref: str
    exact_proposed_use: str
    reinvention_rationale: str
    expected_reader_familiarity: str
    material_transformation: str
    alternatives_considered: tuple[str, ...]
    series_collision_ref: str | None
    decision: ExceptionDecision
    human_decision_ref: str


@dataclass(frozen=True)
class AntiClicheRun:
    book_id: str
    stage: AntiClicheStage
    target_snapshot_ref: str
    target_snapshot_hash: str
    writer_executor_identity: str
    rule_pack_ref: str
    rule_pack_hash: str
    scan_evaluation_ref: str
    scan_rubric_ref: str
    evaluator_identity: str
    evaluator_class: EvaluatorClass
    findings: tuple[AntiClicheFinding, ...]
    exceptions: tuple[AntiClicheException, ...]
    series_book: bool = False
    current_series_brain_ref: str | None = None


@dataclass(frozen=True)
class AntiClichePolicy:
    stage: AntiClicheStage
    require_independent_semantic_scan: bool = True
    major_requires_human_disposition: bool = True


@dataclass(frozen=True)
class AntiClicheGateFinding:
    code: str
    severity: AntiClicheSeverity
    message: str
    object_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class AntiClicheResult:
    qualified: bool
    anti_cliche_ref: str
    rule_pack_ref: str
    unresolved_blocking_codes: tuple[str, ...]
    findings: tuple[AntiClicheGateFinding, ...]


@dataclass(frozen=True)
class AntiClicheVerification:
    valid: bool
    reason: str | None
    current_result: AntiClicheResult


def _finding(
    code: str,
    severity: AntiClicheSeverity,
    message: str,
    *object_refs: str,
) -> AntiClicheGateFinding:
    return AntiClicheGateFinding(
        code=code,
        severity=severity,
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


def _rule_payload(rule: AntiClicheRule) -> dict[str, JSONValue]:
    return {
        "code": rule.code,
        "level": rule.level,
        "category": rule.category,
        "title": rule.title,
        "description": rule.description,
        "exception_allowed": rule.exception_allowed,
        "semantic_review_required": rule.semantic_review_required,
    }


def _rule_pack_payload(rule_pack: AntiClicheRulePack) -> dict[str, JSONValue]:
    return {
        "pack_id": rule_pack.pack_id,
        "version": rule_pack.version,
        "rules": _json_objects(
            tuple(
                _rule_payload(rule) for rule in sorted(rule_pack.rules, key=lambda item: item.code)
            )
        ),
    }


def anti_cliche_rule_pack_hash(rule_pack: AntiClicheRulePack) -> str:
    return content_hash(_rule_pack_payload(rule_pack))


def anti_cliche_rule_pack_ref(rule_pack: AntiClicheRulePack) -> str:
    return (
        f"anti-cliche-rule-pack:{rule_pack.pack_id}:v{rule_pack.version}:"
        f"{anti_cliche_rule_pack_hash(rule_pack)}"
    )


def _finding_payload(
    finding: AntiClicheFinding,
    *,
    target_snapshot_ref: str,
) -> dict[str, JSONValue]:
    return {
        "rule_code": finding.rule_code,
        "severity": finding.severity,
        "observation": finding.observation,
        "exact_proposed_use": finding.exact_proposed_use,
        "target_object_refs": _json_strings(finding.target_object_refs),
        "evidence_refs": _json_strings(finding.evidence_refs),
        "evaluation_ref": finding.evaluation_ref,
        "human_disposition_ref": finding.human_disposition_ref,
        "target_snapshot_ref": target_snapshot_ref,
    }


def anti_cliche_finding_ref(
    finding: AntiClicheFinding,
    *,
    target_snapshot_ref: str,
) -> str:
    return (
        f"anti-cliche-finding:"
        f"{content_hash(_finding_payload(finding, target_snapshot_ref=target_snapshot_ref))}"
    )


def _exception_payload(exception: AntiClicheException) -> dict[str, JSONValue]:
    return {
        "exception_id": exception.exception_id,
        "finding_ref": exception.finding_ref,
        "rule_code": exception.rule_code,
        "rule_pack_ref": exception.rule_pack_ref,
        "target_snapshot_ref": exception.target_snapshot_ref,
        "exact_proposed_use": exception.exact_proposed_use,
        "reinvention_rationale": exception.reinvention_rationale,
        "expected_reader_familiarity": exception.expected_reader_familiarity,
        "material_transformation": exception.material_transformation,
        "alternatives_considered": _json_strings(exception.alternatives_considered),
        "series_collision_ref": exception.series_collision_ref,
        "decision": exception.decision,
        "human_decision_ref": exception.human_decision_ref,
    }


def _policy_payload(policy: AntiClichePolicy) -> dict[str, JSONValue]:
    return {
        "stage": policy.stage,
        "require_independent_semantic_scan": (policy.require_independent_semantic_scan),
        "major_requires_human_disposition": (policy.major_requires_human_disposition),
    }


def _run_ref(
    *,
    run: AntiClicheRun,
    policy: AntiClichePolicy,
) -> str:
    finding_values: list[JSONValue] = []
    for finding in sorted(
        run.findings,
        key=lambda item: (
            item.rule_code,
            item.severity,
            anti_cliche_finding_ref(
                item,
                target_snapshot_ref=run.target_snapshot_ref,
            ),
        ),
    ):
        finding_values.append(
            _finding_payload(
                finding,
                target_snapshot_ref=run.target_snapshot_ref,
            )
        )
    exception_values: list[JSONValue] = []
    for exception in sorted(
        run.exceptions,
        key=lambda item: (item.finding_ref, item.exception_id),
    ):
        exception_values.append(_exception_payload(exception))
    payload: dict[str, JSONValue] = {
        "book_id": run.book_id,
        "policy": _policy_payload(policy),
        "stage": run.stage,
        "target_snapshot_ref": run.target_snapshot_ref,
        "target_snapshot_hash": run.target_snapshot_hash,
        "writer_executor_identity": run.writer_executor_identity,
        "rule_pack_ref": run.rule_pack_ref,
        "rule_pack_hash": run.rule_pack_hash,
        "scan_evaluation_ref": run.scan_evaluation_ref,
        "scan_rubric_ref": run.scan_rubric_ref,
        "evaluator_identity": run.evaluator_identity,
        "evaluator_class": run.evaluator_class,
        "findings": finding_values,
        "exceptions": exception_values,
        "series_book": run.series_book,
        "current_series_brain_ref": run.current_series_brain_ref,
    }
    return f"anti-cliche:{content_hash(payload)}"


def validate_rule_pack(
    rule_pack: AntiClicheRulePack,
) -> tuple[AntiClicheGateFinding, ...]:
    findings: list[AntiClicheGateFinding] = []
    if not rule_pack.pack_id.strip():
        findings.append(
            _finding(
                "ANTI_CLICHE.RULE_PACK.ID_MISSING",
                "BLOCKING",
                "rule pack id must not be blank",
            )
        )
    if rule_pack.version < 1:
        findings.append(
            _finding(
                "ANTI_CLICHE.RULE_PACK.VERSION_INVALID",
                "BLOCKING",
                "rule pack version must be positive",
            )
        )
    if not rule_pack.rules:
        findings.append(
            _finding(
                "ANTI_CLICHE.RULE_PACK.EMPTY",
                "BLOCKING",
                "rule pack must contain rules",
            )
        )

    seen: set[str] = set()
    for rule in rule_pack.rules:
        if not rule.code.strip():
            findings.append(
                _finding(
                    "ANTI_CLICHE.RULE.CODE_MISSING",
                    "BLOCKING",
                    "rule code must not be blank",
                )
            )
            continue
        if rule.code in seen:
            findings.append(
                _finding(
                    "ANTI_CLICHE.RULE.DUPLICATE_CODE",
                    "BLOCKING",
                    f"duplicate anti-cliche rule {rule.code}",
                    rule.code,
                )
            )
        seen.add(rule.code)
        if rule.level not in _VALID_LEVELS:
            findings.append(
                _finding(
                    "ANTI_CLICHE.RULE.LEVEL_UNKNOWN",
                    "BLOCKING",
                    f"unknown enforcement level {rule.level}",
                    rule.code,
                )
            )
        for field_name, value in (
            ("CATEGORY", rule.category),
            ("TITLE", rule.title),
            ("DESCRIPTION", rule.description),
        ):
            if not value.strip():
                findings.append(
                    _finding(
                        f"ANTI_CLICHE.RULE.{field_name}_MISSING",
                        "BLOCKING",
                        f"rule {rule.code} has blank {field_name.lower()}",
                        rule.code,
                    )
                )
        if rule.level == "SERIES_COLLISION" and rule.exception_allowed:
            findings.append(
                _finding(
                    "ANTI_CLICHE.RULE.SERIES_COLLISION_EXCEPTION_FORBIDDEN",
                    "BLOCKING",
                    (
                        f"series-collision rule {rule.code} cannot be made "
                        "waivable by AntiClicheException"
                    ),
                    rule.code,
                )
            )
    return tuple(findings)


def _validate_scan_artifact(
    *,
    run: AntiClicheRun,
    verified_evaluations: Mapping[str, VerifiedEvaluationArtifact],
    policy: AntiClichePolicy,
    findings: list[AntiClicheGateFinding],
) -> None:
    if not run.scan_evaluation_ref.strip():
        findings.append(
            _finding(
                "ANTI_CLICHE.SCAN.REF_MISSING",
                "BLOCKING",
                "anti-cliche scan evaluation ref is missing",
            )
        )
        return
    artifact = verified_evaluations.get(run.scan_evaluation_ref)
    if artifact is None:
        findings.append(
            _finding(
                "ANTI_CLICHE.SCAN.ARTIFACT_MISSING",
                "BLOCKING",
                "verified anti-cliche scan artifact is missing",
                run.scan_evaluation_ref,
            )
        )
        return

    expected_purpose = f"ANTI_CLICHE_SCAN:{run.stage}:{run.rule_pack_ref}"
    for code, actual, expected in (
        ("ID_MISMATCH", artifact.evaluation_ref, run.scan_evaluation_ref),
        ("SNAPSHOT_MISMATCH", artifact.manuscript_snapshot_ref, run.target_snapshot_ref),
        ("EVALUATOR_MISMATCH", artifact.evaluator_identity, run.evaluator_identity),
        ("CLASS_MISMATCH", artifact.evaluator_class, run.evaluator_class),
        ("RUBRIC_MISMATCH", artifact.rubric_ref, run.scan_rubric_ref),
        ("PURPOSE_MISMATCH", artifact.purpose, expected_purpose),
    ):
        if actual != expected:
            findings.append(
                _finding(
                    f"ANTI_CLICHE.SCAN.ARTIFACT_{code}",
                    "BLOCKING",
                    f"anti-cliche scan artifact {code.lower()}",
                    run.scan_evaluation_ref,
                )
            )
    if artifact.status != "SUCCEEDED" or not artifact.current:
        findings.append(
            _finding(
                "ANTI_CLICHE.SCAN.ARTIFACT_NOT_CURRENT_SUCCESS",
                "BLOCKING",
                "anti-cliche scan artifact must be SUCCEEDED/current",
                run.scan_evaluation_ref,
            )
        )
    if run.evaluator_class not in _VALID_EVALUATOR_CLASSES:
        findings.append(
            _finding(
                "ANTI_CLICHE.SCAN.EVALUATOR_CLASS_INVALID",
                "BLOCKING",
                (
                    "anti-cliche scan requires semantic/pairwise/human "
                    "evaluation, not deterministic-only evidence"
                ),
                run.scan_evaluation_ref,
            )
        )
    if (
        policy.require_independent_semantic_scan
        and run.evaluator_identity == run.writer_executor_identity
    ):
        findings.append(
            _finding(
                "ANTI_CLICHE.SCAN.SAME_WRITER_EXECUTOR",
                "BLOCKING",
                "Writer cannot be the sole anti-cliche semantic judge",
                run.scan_evaluation_ref,
            )
        )


def _exception_for_finding(
    *,
    finding_ref: str,
    exceptions: tuple[AntiClicheException, ...],
) -> list[AntiClicheException]:
    return [exception for exception in exceptions if exception.finding_ref == finding_ref]


def evaluate_anti_cliche(
    *,
    run: AntiClicheRun,
    policy: AntiClichePolicy,
    rule_pack: AntiClicheRulePack,
    current_target_snapshot_ref: str,
    current_target_snapshot_hash: str,
    verified_evaluations: Mapping[str, VerifiedEvaluationArtifact],
    verified_human_decision_refs: frozenset[str] = frozenset(),
) -> AntiClicheResult:
    findings: list[AntiClicheGateFinding] = list(validate_rule_pack(rule_pack))

    if not run.book_id.strip():
        findings.append(
            _finding(
                "ANTI_CLICHE.RUN.BOOK_ID_MISSING",
                "BLOCKING",
                "book_id must not be blank",
            )
        )
    if run.stage not in _VALID_STAGES or policy.stage not in _VALID_STAGES:
        findings.append(
            _finding(
                "ANTI_CLICHE.RUN.STAGE_UNKNOWN",
                "BLOCKING",
                "anti-cliche stage is unknown",
            )
        )
    if run.stage != policy.stage:
        findings.append(
            _finding(
                "ANTI_CLICHE.RUN.STAGE_POLICY_MISMATCH",
                "BLOCKING",
                f"run stage {run.stage} differs from policy {policy.stage}",
            )
        )
    if not _SHA256.fullmatch(run.target_snapshot_hash):
        findings.append(
            _finding(
                "ANTI_CLICHE.RUN.SNAPSHOT_HASH_INVALID",
                "BLOCKING",
                "target snapshot hash must be lowercase SHA-256",
            )
        )
    if (
        run.target_snapshot_ref != current_target_snapshot_ref
        or run.target_snapshot_hash != current_target_snapshot_hash
    ):
        findings.append(
            _finding(
                "ANTI_CLICHE.RUN.SNAPSHOT_STALE",
                "BLOCKING",
                "anti-cliche run is not bound to the current target snapshot",
            )
        )

    current_pack_ref = anti_cliche_rule_pack_ref(rule_pack)
    current_pack_hash = anti_cliche_rule_pack_hash(rule_pack)
    if run.rule_pack_ref != current_pack_ref or run.rule_pack_hash != current_pack_hash:
        findings.append(
            _finding(
                "ANTI_CLICHE.RUN.RULE_PACK_STALE",
                "BLOCKING",
                "anti-cliche run is not bound to the exact current rule pack",
            )
        )

    if not run.writer_executor_identity.strip():
        findings.append(
            _finding(
                "ANTI_CLICHE.RUN.WRITER_IDENTITY_MISSING",
                "BLOCKING",
                "Writer executor identity is required",
            )
        )
    if not run.evaluator_identity.strip():
        findings.append(
            _finding(
                "ANTI_CLICHE.RUN.EVALUATOR_IDENTITY_MISSING",
                "BLOCKING",
                "anti-cliche evaluator identity is required",
            )
        )
    if not run.scan_rubric_ref.strip():
        findings.append(
            _finding(
                "ANTI_CLICHE.SCAN.RUBRIC_MISSING",
                "BLOCKING",
                "anti-cliche scan rubric ref is required",
            )
        )

    if run.series_book:
        if run.current_series_brain_ref is None or not run.current_series_brain_ref.strip():
            findings.append(
                _finding(
                    "ANTI_CLICHE.SERIES.BRAIN_REF_MISSING",
                    "BLOCKING",
                    "series book anti-cliche run requires current Series Brain ref",
                )
            )
    elif run.current_series_brain_ref is not None:
        findings.append(
            _finding(
                "ANTI_CLICHE.SERIES.UNEXPECTED_BRAIN_REF",
                "MAJOR",
                "standalone run should not carry Series Brain provenance",
                run.current_series_brain_ref,
            )
        )

    _validate_scan_artifact(
        run=run,
        verified_evaluations=verified_evaluations,
        policy=policy,
        findings=findings,
    )

    rules_by_code = {rule.code: rule for rule in rule_pack.rules}
    finding_refs_seen: set[str] = set()
    exception_ids_seen: set[str] = set()
    exception_finding_refs_seen: set[str] = set()

    for exception in run.exceptions:
        if not exception.exception_id.strip():
            findings.append(
                _finding(
                    "ANTI_CLICHE.EXCEPTION.ID_MISSING",
                    "BLOCKING",
                    "exception id must not be blank",
                )
            )
        elif exception.exception_id in exception_ids_seen:
            findings.append(
                _finding(
                    "ANTI_CLICHE.EXCEPTION.DUPLICATE_ID",
                    "BLOCKING",
                    f"duplicate exception id {exception.exception_id}",
                    exception.exception_id,
                )
            )
        exception_ids_seen.add(exception.exception_id)
        if exception.finding_ref in exception_finding_refs_seen:
            findings.append(
                _finding(
                    "ANTI_CLICHE.EXCEPTION.MULTIPLE_FOR_FINDING",
                    "BLOCKING",
                    "one exact finding may have only one active exception",
                    exception.finding_ref,
                )
            )
        exception_finding_refs_seen.add(exception.finding_ref)

    for anti_finding in run.findings:
        finding_ref = anti_cliche_finding_ref(
            anti_finding,
            target_snapshot_ref=run.target_snapshot_ref,
        )
        if finding_ref in finding_refs_seen:
            findings.append(
                _finding(
                    "ANTI_CLICHE.FINDING.DUPLICATE",
                    "BLOCKING",
                    "duplicate anti-cliche finding",
                    finding_ref,
                )
            )
            continue
        finding_refs_seen.add(finding_ref)

        rule = rules_by_code.get(anti_finding.rule_code)
        if rule is None:
            findings.append(
                _finding(
                    "ANTI_CLICHE.FINDING.RULE_UNKNOWN",
                    "BLOCKING",
                    f"finding references unknown rule {anti_finding.rule_code}",
                    finding_ref,
                )
            )
            continue
        if anti_finding.severity not in _VALID_SEVERITIES:
            findings.append(
                _finding(
                    "ANTI_CLICHE.FINDING.SEVERITY_UNKNOWN",
                    "BLOCKING",
                    f"finding has unknown severity {anti_finding.severity}",
                    finding_ref,
                )
            )
        for code, value in (
            ("OBSERVATION", anti_finding.observation),
            ("EXACT_PROPOSED_USE", anti_finding.exact_proposed_use),
        ):
            if not value.strip():
                findings.append(
                    _finding(
                        f"ANTI_CLICHE.FINDING.{code}_MISSING",
                        "BLOCKING",
                        f"finding {finding_ref} lacks {code.lower()}",
                        finding_ref,
                    )
                )
        if not anti_finding.target_object_refs:
            findings.append(
                _finding(
                    "ANTI_CLICHE.FINDING.TARGET_REFS_MISSING",
                    "BLOCKING",
                    "finding requires exact target object refs",
                    finding_ref,
                )
            )
        if not anti_finding.evidence_refs:
            findings.append(
                _finding(
                    "ANTI_CLICHE.FINDING.EVIDENCE_MISSING",
                    "BLOCKING",
                    "finding requires evidence refs",
                    finding_ref,
                )
            )
        if anti_finding.evaluation_ref != run.scan_evaluation_ref:
            findings.append(
                _finding(
                    "ANTI_CLICHE.FINDING.EVALUATION_REF_MISMATCH",
                    "BLOCKING",
                    "finding is not bound to the current anti-cliche scan",
                    finding_ref,
                    anti_finding.evaluation_ref,
                )
            )

        matching = _exception_for_finding(
            finding_ref=finding_ref,
            exceptions=run.exceptions,
        )

        if rule.level == "SERIES_COLLISION":
            findings.append(
                _finding(
                    "ANTI_CLICHE.SERIES_COLLISION.BLOCKING",
                    "BLOCKING",
                    (
                        f"rule {rule.code} is a series collision and must be "
                        "resolved by Series Brain, not AntiClicheException"
                    ),
                    finding_ref,
                    rule.code,
                )
            )
            if matching:
                findings.append(
                    _finding(
                        "ANTI_CLICHE.SERIES_COLLISION.EXCEPTION_INVALID",
                        "BLOCKING",
                        "AntiClicheException cannot waive a Series Brain collision",
                        finding_ref,
                    )
                )
            continue

        if rule.level == "BLOCKED_BY_DEFAULT":
            if not rule.exception_allowed:
                findings.append(
                    _finding(
                        "ANTI_CLICHE.BLOCKED_RULE.NON_WAIVABLE",
                        "BLOCKING",
                        f"blocked-by-default rule {rule.code} is non-waivable",
                        finding_ref,
                        rule.code,
                    )
                )
                continue
            if not matching:
                findings.append(
                    _finding(
                        "ANTI_CLICHE.BLOCKED_RULE.EXCEPTION_MISSING",
                        "BLOCKING",
                        (
                            f"blocked-by-default rule {rule.code} requires "
                            "an exact human-gated reinvention exception"
                        ),
                        finding_ref,
                        rule.code,
                    )
                )
                continue

        if anti_finding.severity == "BLOCKING" and rule.level != "BLOCKED_BY_DEFAULT":
            findings.append(
                _finding(
                    "ANTI_CLICHE.FINDING.BLOCKING",
                    "BLOCKING",
                    f"rule {rule.code} has unresolved BLOCKING finding",
                    finding_ref,
                )
            )
        elif (
            anti_finding.severity == "MAJOR"
            and rule.level != "BLOCKED_BY_DEFAULT"
            and policy.major_requires_human_disposition
        ):
            if (
                anti_finding.human_disposition_ref is None
                or not anti_finding.human_disposition_ref.strip()
            ):
                findings.append(
                    _finding(
                        "ANTI_CLICHE.FINDING.MAJOR_UNDISPOSED",
                        "MAJOR",
                        f"rule {rule.code} has MAJOR finding without human disposition",
                        finding_ref,
                    )
                )
            elif anti_finding.human_disposition_ref not in verified_human_decision_refs:
                findings.append(
                    _finding(
                        "ANTI_CLICHE.FINDING.MAJOR_DISPOSITION_UNVERIFIED",
                        "MAJOR",
                        f"rule {rule.code} has unverified human disposition",
                        finding_ref,
                        anti_finding.human_disposition_ref,
                    )
                )

    known_finding_refs = finding_refs_seen
    for exception in run.exceptions:
        if exception.finding_ref not in known_finding_refs:
            findings.append(
                _finding(
                    "ANTI_CLICHE.EXCEPTION.FINDING_UNKNOWN",
                    "BLOCKING",
                    "exception references a finding not present in this exact run",
                    exception.finding_ref,
                )
            )
            continue
        matching_finding = next(
            item
            for item in run.findings
            if anti_cliche_finding_ref(
                item,
                target_snapshot_ref=run.target_snapshot_ref,
            )
            == exception.finding_ref
        )
        rule = rules_by_code.get(matching_finding.rule_code)
        if rule is None:
            continue

        if exception.rule_code != matching_finding.rule_code:
            findings.append(
                _finding(
                    "ANTI_CLICHE.EXCEPTION.RULE_MISMATCH",
                    "BLOCKING",
                    "exception rule code differs from exact finding",
                    exception.finding_ref,
                )
            )
        if exception.rule_pack_ref != current_pack_ref:
            findings.append(
                _finding(
                    "ANTI_CLICHE.EXCEPTION.RULE_PACK_STALE",
                    "BLOCKING",
                    "exception was accepted under another rule-pack revision",
                    exception.finding_ref,
                )
            )
        if exception.target_snapshot_ref != run.target_snapshot_ref:
            findings.append(
                _finding(
                    "ANTI_CLICHE.EXCEPTION.SNAPSHOT_STALE",
                    "BLOCKING",
                    "exception belongs to another target snapshot",
                    exception.finding_ref,
                )
            )
        if exception.exact_proposed_use != matching_finding.exact_proposed_use:
            findings.append(
                _finding(
                    "ANTI_CLICHE.EXCEPTION.USE_MISMATCH",
                    "BLOCKING",
                    "exception is not scoped to the exact detected use",
                    exception.finding_ref,
                )
            )
        for code, value in (
            ("RATIONALE", exception.reinvention_rationale),
            ("FAMILIARITY", exception.expected_reader_familiarity),
            ("TRANSFORMATION", exception.material_transformation),
            ("HUMAN_DECISION_REF", exception.human_decision_ref),
        ):
            if not value.strip():
                findings.append(
                    _finding(
                        f"ANTI_CLICHE.EXCEPTION.{code}_MISSING",
                        "BLOCKING",
                        f"exception lacks {code.lower()}",
                        exception.finding_ref,
                    )
                )
        if not exception.alternatives_considered:
            findings.append(
                _finding(
                    "ANTI_CLICHE.EXCEPTION.ALTERNATIVES_MISSING",
                    "BLOCKING",
                    "reinvention exception must record alternatives considered",
                    exception.finding_ref,
                )
            )
        if exception.decision not in _VALID_DECISIONS:
            findings.append(
                _finding(
                    "ANTI_CLICHE.EXCEPTION.DECISION_UNKNOWN",
                    "BLOCKING",
                    f"unknown exception decision {exception.decision}",
                    exception.finding_ref,
                )
            )
        elif exception.decision != "ACCEPT":
            findings.append(
                _finding(
                    "ANTI_CLICHE.EXCEPTION.NOT_ACCEPTED",
                    "BLOCKING",
                    f"exception decision is {exception.decision}, not ACCEPT",
                    exception.finding_ref,
                )
            )
        elif exception.human_decision_ref not in verified_human_decision_refs:
            findings.append(
                _finding(
                    "ANTI_CLICHE.EXCEPTION.HUMAN_DECISION_UNVERIFIED",
                    "BLOCKING",
                    "accepted exception lacks verified human authority",
                    exception.finding_ref,
                    exception.human_decision_ref,
                )
            )

        if run.series_book:
            if exception.series_collision_ref != run.current_series_brain_ref:
                findings.append(
                    _finding(
                        "ANTI_CLICHE.EXCEPTION.SERIES_REF_MISMATCH",
                        "BLOCKING",
                        ("series-book exception must cite the exact current Series Brain ref"),
                        exception.finding_ref,
                    )
                )
        elif exception.series_collision_ref is not None:
            findings.append(
                _finding(
                    "ANTI_CLICHE.EXCEPTION.UNEXPECTED_SERIES_REF",
                    "MAJOR",
                    "standalone exception should not carry Series Brain ref",
                    exception.finding_ref,
                )
            )

    unresolved = tuple(
        sorted({finding.code for finding in findings if finding.severity in {"BLOCKING", "MAJOR"}})
    )
    result_ref = _run_ref(run=run, policy=policy)
    return AntiClicheResult(
        qualified=not unresolved,
        anti_cliche_ref=result_ref,
        rule_pack_ref=current_pack_ref,
        unresolved_blocking_codes=unresolved,
        findings=tuple(findings),
    )


def verify_anti_cliche(
    *,
    prior_anti_cliche_ref: str,
    run: AntiClicheRun,
    policy: AntiClichePolicy,
    rule_pack: AntiClicheRulePack,
    current_target_snapshot_ref: str,
    current_target_snapshot_hash: str,
    verified_evaluations: Mapping[str, VerifiedEvaluationArtifact],
    verified_human_decision_refs: frozenset[str] = frozenset(),
) -> AntiClicheVerification:
    current = evaluate_anti_cliche(
        run=run,
        policy=policy,
        rule_pack=rule_pack,
        current_target_snapshot_ref=current_target_snapshot_ref,
        current_target_snapshot_hash=current_target_snapshot_hash,
        verified_evaluations=verified_evaluations,
        verified_human_decision_refs=verified_human_decision_refs,
    )
    if not current.qualified:
        return AntiClicheVerification(
            valid=False,
            reason="CURRENT_ANTI_CLICHE_BLOCKED",
            current_result=current,
        )
    if current.anti_cliche_ref != prior_anti_cliche_ref:
        return AntiClicheVerification(
            valid=False,
            reason="ANTI_CLICHE_SNAPSHOT_CHANGED",
            current_result=current,
        )
    return AntiClicheVerification(
        valid=True,
        reason=None,
        current_result=current,
    )
