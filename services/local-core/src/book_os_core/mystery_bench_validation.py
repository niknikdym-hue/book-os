from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, TypeAlias

from .authority_types import JSONValue, content_hash

MysteryBenchStage: TypeAlias = Literal["MIDBOOK", "FINAL"]
MysteryDimension: TypeAlias = Literal[
    "CASE_COHERENCE",
    "FAIR_PLAY",
    "REVEAL_QUALITY",
    "SUSPECT_QUALITY",
    "CHARACTER_CAUSALITY",
    "NARRATIVE_INTEGRITY",
    "SUPERNATURAL_INTEGRITY",
    "TENSION_PACING",
    "ORIGINALITY_ANTI_CLICHE",
    "PROSE_VOICE",
    "SETTING_FUNCTION",
    "RESEARCH_REALISM",
    "EMOTIONAL_ARCHITECTURE",
    "AUDIO_READINESS",
]
EvaluationStatus: TypeAlias = Literal[
    "PASS",
    "MAJOR_GAP",
    "BLOCKING_GAP",
    "NOT_EVALUATED",
]
EvaluatorClass: TypeAlias = Literal[
    "DETERMINISTIC",
    "SEMANTIC",
    "LLM_JUDGE",
    "PAIRWISE",
    "HUMAN_LABEL",
]
IndependenceState: TypeAlias = Literal[
    "INDEPENDENT",
    "SAME_CONFIG",
    "UNKNOWN",
    "NOT_APPLICABLE",
]
ColdReaderCheckpointKind: TypeAlias = Literal[
    "EARLY",
    "QUARTER",
    "MIDPOINT",
    "THREE_QUARTER",
    "PRE_REVEAL",
    "POST_REVEAL",
]
EngagementState: TypeAlias = Literal["ENGAGED", "ATTENTION", "BREAKDOWN"]
AdversarialRevealOrder: TypeAlias = Literal["RECONSTRUCTION_THEN_CASE_SOLUTION"]

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_VALID_DIMENSIONS: frozenset[str] = frozenset(
    {
        "CASE_COHERENCE",
        "FAIR_PLAY",
        "REVEAL_QUALITY",
        "SUSPECT_QUALITY",
        "CHARACTER_CAUSALITY",
        "NARRATIVE_INTEGRITY",
        "SUPERNATURAL_INTEGRITY",
        "TENSION_PACING",
        "ORIGINALITY_ANTI_CLICHE",
        "PROSE_VOICE",
        "SETTING_FUNCTION",
        "RESEARCH_REALISM",
        "EMOTIONAL_ARCHITECTURE",
        "AUDIO_READINESS",
    }
)
_VALID_STATUSES: frozenset[str] = frozenset(
    {"PASS", "MAJOR_GAP", "BLOCKING_GAP", "NOT_EVALUATED"}
)
_VALID_EVALUATOR_CLASSES: frozenset[str] = frozenset(
    {"DETERMINISTIC", "SEMANTIC", "LLM_JUDGE", "PAIRWISE", "HUMAN_LABEL"}
)
_VALID_INDEPENDENCE_STATES: frozenset[str] = frozenset(
    {"INDEPENDENT", "SAME_CONFIG", "UNKNOWN", "NOT_APPLICABLE"}
)
_VALID_CHECKPOINTS: frozenset[str] = frozenset(
    {"EARLY", "QUARTER", "MIDPOINT", "THREE_QUARTER", "PRE_REVEAL", "POST_REVEAL"}
)


@dataclass(frozen=True)
class MysteryBenchPolicy:
    stage: MysteryBenchStage
    supernatural_material: bool = False
    audio_selected: bool = False
    require_cold_reader: bool = True
    require_adversarial_reconstruction: bool = True


@dataclass(frozen=True)
class MysteryDimensionEvidence:
    dimension: MysteryDimension
    status: EvaluationStatus
    evaluation_ref: str
    bookbench_snapshot_ref: str
    rubric_ref: str
    evaluator_identity: str
    evaluator_class: EvaluatorClass
    independence_state: IndependenceState
    supporting_evidence_refs: tuple[str, ...] = ()
    human_disposition_ref: str | None = None


@dataclass(frozen=True)
class ColdReaderCheckpoint:
    checkpoint: ColdReaderCheckpointKind
    manuscript_snapshot_ref: str
    evaluation_ref: str
    evaluator_identity: str
    private_case_solution_exposed: bool
    private_spoiler_authority_refs: tuple[str, ...] = ()
    top_suspect_ids: tuple[str, ...] = ()
    hypothesis_refs: tuple[str, ...] = ()
    perceived_clue_refs: tuple[str, ...] = ()
    confusion_point_refs: tuple[str, ...] = ()
    predicted_twist_refs: tuple[str, ...] = ()
    engagement_state: EngagementState = "ENGAGED"
    solution_inferable: bool | None = None
    solution_earned: bool | None = None
    late_invention_detected: bool | None = None
    stronger_alternative_detected: bool | None = None


@dataclass(frozen=True)
class AdversarialCaseReconstruction:
    manuscript_snapshot_ref: str
    evaluator_identity: str
    reconstruction_ref: str
    blind_input_refs: tuple[str, ...]
    accepted_case_solution_revision_ref: str
    comparison_ref: str
    reveal_order: AdversarialRevealOrder
    missing_required_fact: bool = False
    impossible_timeline: bool = False
    stronger_alternative_solution: bool = False
    accepted_solution_contradicts_manuscript: bool = False
    unstated_decisive_supernatural_rule: bool = False
    unfair_decisive_withholding: bool = False


@dataclass(frozen=True)
class MysteryBenchPack:
    book_id: str
    manuscript_snapshot_ref: str
    manuscript_snapshot_hash: str
    authority_revision_refs: tuple[str, ...]
    writer_executor_identity: str
    dimension_evidence: tuple[MysteryDimensionEvidence, ...]
    cold_reader_checkpoints: tuple[ColdReaderCheckpoint, ...] = ()
    adversarial_reconstruction: AdversarialCaseReconstruction | None = None


@dataclass(frozen=True)
class MysteryBenchFinding:
    code: str
    message: str
    object_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class MysteryBenchResult:
    qualified: bool
    mystery_bench_ref: str
    cold_reader_protocol_ref: str | None
    adversarial_protocol_ref: str | None
    findings: tuple[MysteryBenchFinding, ...]


@dataclass(frozen=True)
class MysteryBenchVerification:
    valid: bool
    reason: str | None
    current_result: MysteryBenchResult


def _finding(code: str, message: str, *object_refs: str) -> MysteryBenchFinding:
    return MysteryBenchFinding(code=code, message=message, object_refs=tuple(object_refs))


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


def _required_dimensions(policy: MysteryBenchPolicy) -> frozenset[str]:
    if policy.stage == "MIDBOOK":
        required = {
            "CASE_COHERENCE",
            "FAIR_PLAY",
            "CHARACTER_CAUSALITY",
            "NARRATIVE_INTEGRITY",
            "TENSION_PACING",
            "ORIGINALITY_ANTI_CLICHE",
            "RESEARCH_REALISM",
            "EMOTIONAL_ARCHITECTURE",
        }
    else:
        required = {
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
        }
    if policy.supernatural_material:
        required.add("SUPERNATURAL_INTEGRITY")
    if policy.audio_selected:
        required.add("AUDIO_READINESS")
    return frozenset(required)


def _required_cold_reader_checkpoints(
    policy: MysteryBenchPolicy,
) -> frozenset[str]:
    if not policy.require_cold_reader:
        return frozenset()
    if policy.stage == "MIDBOOK":
        return frozenset({"EARLY", "QUARTER", "MIDPOINT"})
    return frozenset(
        {
            "EARLY",
            "QUARTER",
            "MIDPOINT",
            "THREE_QUARTER",
            "PRE_REVEAL",
            "POST_REVEAL",
        }
    )


def _cold_reader_checkpoint_payload(
    checkpoint: ColdReaderCheckpoint,
) -> dict[str, JSONValue]:
    return {
        "checkpoint": checkpoint.checkpoint,
        "manuscript_snapshot_ref": checkpoint.manuscript_snapshot_ref,
        "evaluation_ref": checkpoint.evaluation_ref,
        "evaluator_identity": checkpoint.evaluator_identity,
        "private_case_solution_exposed": checkpoint.private_case_solution_exposed,
        "private_spoiler_authority_refs": _json_strings(
            checkpoint.private_spoiler_authority_refs
        ),
        "top_suspect_ids": _json_strings(checkpoint.top_suspect_ids),
        "hypothesis_refs": _json_strings(checkpoint.hypothesis_refs),
        "perceived_clue_refs": _json_strings(checkpoint.perceived_clue_refs),
        "confusion_point_refs": _json_strings(checkpoint.confusion_point_refs),
        "predicted_twist_refs": _json_strings(checkpoint.predicted_twist_refs),
        "engagement_state": checkpoint.engagement_state,
        "solution_inferable": checkpoint.solution_inferable,
        "solution_earned": checkpoint.solution_earned,
        "late_invention_detected": checkpoint.late_invention_detected,
        "stronger_alternative_detected": checkpoint.stronger_alternative_detected,
    }


def cold_reader_protocol_ref(
    checkpoints: tuple[ColdReaderCheckpoint, ...],
) -> str:
    payload: dict[str, JSONValue] = {
        "checkpoints": _json_objects(
            tuple(
                _cold_reader_checkpoint_payload(checkpoint)
                for checkpoint in sorted(
                    checkpoints,
                    key=lambda item: (item.checkpoint, item.evaluation_ref),
                )
            )
        )
    }
    return f"cold-reader:{content_hash(payload)}"


def _adversarial_payload(
    evidence: AdversarialCaseReconstruction,
) -> dict[str, JSONValue]:
    return {
        "manuscript_snapshot_ref": evidence.manuscript_snapshot_ref,
        "evaluator_identity": evidence.evaluator_identity,
        "reconstruction_ref": evidence.reconstruction_ref,
        "blind_input_refs": _json_strings(evidence.blind_input_refs),
        "accepted_case_solution_revision_ref": (
            evidence.accepted_case_solution_revision_ref
        ),
        "comparison_ref": evidence.comparison_ref,
        "reveal_order": evidence.reveal_order,
        "missing_required_fact": evidence.missing_required_fact,
        "impossible_timeline": evidence.impossible_timeline,
        "stronger_alternative_solution": evidence.stronger_alternative_solution,
        "accepted_solution_contradicts_manuscript": (
            evidence.accepted_solution_contradicts_manuscript
        ),
        "unstated_decisive_supernatural_rule": (
            evidence.unstated_decisive_supernatural_rule
        ),
        "unfair_decisive_withholding": evidence.unfair_decisive_withholding,
    }


def adversarial_protocol_ref(evidence: AdversarialCaseReconstruction) -> str:
    return f"adversarial-reconstruction:{content_hash(_adversarial_payload(evidence))}"


def _dimension_payload(
    evidence: MysteryDimensionEvidence,
) -> dict[str, JSONValue]:
    return {
        "dimension": evidence.dimension,
        "status": evidence.status,
        "evaluation_ref": evidence.evaluation_ref,
        "bookbench_snapshot_ref": evidence.bookbench_snapshot_ref,
        "rubric_ref": evidence.rubric_ref,
        "evaluator_identity": evidence.evaluator_identity,
        "evaluator_class": evidence.evaluator_class,
        "independence_state": evidence.independence_state,
        "supporting_evidence_refs": _json_strings(evidence.supporting_evidence_refs),
        "human_disposition_ref": evidence.human_disposition_ref,
    }


def _policy_payload(policy: MysteryBenchPolicy) -> dict[str, JSONValue]:
    return {
        "stage": policy.stage,
        "supernatural_material": policy.supernatural_material,
        "audio_selected": policy.audio_selected,
        "require_cold_reader": policy.require_cold_reader,
        "require_adversarial_reconstruction": (
            policy.require_adversarial_reconstruction
        ),
    }


def _pack_ref(
    *,
    pack: MysteryBenchPack,
    policy: MysteryBenchPolicy,
    cold_ref: str | None,
    adversarial_ref: str | None,
) -> str:
    payload: dict[str, JSONValue] = {
        "book_id": pack.book_id,
        "policy": _policy_payload(policy),
        "manuscript_snapshot_ref": pack.manuscript_snapshot_ref,
        "manuscript_snapshot_hash": pack.manuscript_snapshot_hash,
        "authority_revision_refs": _json_strings(pack.authority_revision_refs),
        "writer_executor_identity": pack.writer_executor_identity,
        "dimension_evidence": _json_objects(
            tuple(
                _dimension_payload(evidence)
                for evidence in sorted(
                    pack.dimension_evidence,
                    key=lambda item: (item.dimension, item.evaluation_ref),
                )
            )
        ),
        "cold_reader_protocol_ref": cold_ref,
        "adversarial_protocol_ref": adversarial_ref,
    }
    return f"mystery-bench:{content_hash(payload)}"


def _validate_cold_reader(
    *,
    pack: MysteryBenchPack,
    policy: MysteryBenchPolicy,
    findings: list[MysteryBenchFinding],
) -> str | None:
    if not policy.require_cold_reader:
        if pack.cold_reader_checkpoints:
            findings.append(
                _finding(
                    "MYSTERYBENCH.COLD_READER.UNEXPECTED",
                    "cold-reader evidence exists while policy disables the protocol",
                )
            )
        return None

    by_kind: dict[str, ColdReaderCheckpoint] = {}
    for checkpoint in pack.cold_reader_checkpoints:
        if checkpoint.checkpoint not in _VALID_CHECKPOINTS:
            findings.append(
                _finding(
                    "MYSTERYBENCH.COLD_READER.CHECKPOINT_UNKNOWN",
                    f"unknown cold-reader checkpoint {checkpoint.checkpoint}",
                    checkpoint.checkpoint,
                )
            )
            continue
        if checkpoint.checkpoint in by_kind:
            findings.append(
                _finding(
                    "MYSTERYBENCH.COLD_READER.DUPLICATE_CHECKPOINT",
                    f"duplicate cold-reader checkpoint {checkpoint.checkpoint}",
                    checkpoint.checkpoint,
                )
            )
            continue
        by_kind[checkpoint.checkpoint] = checkpoint

        if checkpoint.manuscript_snapshot_ref != pack.manuscript_snapshot_ref:
            findings.append(
                _finding(
                    "MYSTERYBENCH.COLD_READER.SNAPSHOT_MISMATCH",
                    (
                        f"cold-reader checkpoint {checkpoint.checkpoint} uses a "
                        "different manuscript snapshot"
                    ),
                    checkpoint.checkpoint,
                )
            )
        if not checkpoint.evaluation_ref.strip():
            findings.append(
                _finding(
                    "MYSTERYBENCH.COLD_READER.EVALUATION_REF_MISSING",
                    f"checkpoint {checkpoint.checkpoint} has no evaluation ref",
                    checkpoint.checkpoint,
                )
            )
        if not checkpoint.evaluator_identity.strip():
            findings.append(
                _finding(
                    "MYSTERYBENCH.COLD_READER.EVALUATOR_MISSING",
                    f"checkpoint {checkpoint.checkpoint} has no evaluator identity",
                    checkpoint.checkpoint,
                )
            )
        elif checkpoint.evaluator_identity == pack.writer_executor_identity:
            findings.append(
                _finding(
                    "MYSTERYBENCH.COLD_READER.NOT_INDEPENDENT",
                    (
                        f"checkpoint {checkpoint.checkpoint} uses the same executor "
                        "identity as the Writer"
                    ),
                    checkpoint.checkpoint,
                )
            )
        if checkpoint.private_case_solution_exposed:
            findings.append(
                _finding(
                    "MYSTERYBENCH.COLD_READER.CASE_SOLUTION_EXPOSED",
                    (
                        f"checkpoint {checkpoint.checkpoint} was contaminated by "
                        "private CaseSolution authority"
                    ),
                    checkpoint.checkpoint,
                )
            )
        if checkpoint.private_spoiler_authority_refs:
            findings.append(
                _finding(
                    "MYSTERYBENCH.COLD_READER.SPOILER_AUTHORITY_EXPOSED",
                    (
                        f"checkpoint {checkpoint.checkpoint} received private spoiler "
                        "authority refs"
                    ),
                    checkpoint.checkpoint,
                    *checkpoint.private_spoiler_authority_refs,
                )
            )

    for checkpoint_kind in sorted(_required_cold_reader_checkpoints(policy)):
        if checkpoint_kind not in by_kind:
            findings.append(
                _finding(
                    "MYSTERYBENCH.COLD_READER.CHECKPOINT_MISSING",
                    f"required cold-reader checkpoint {checkpoint_kind} is missing",
                    checkpoint_kind,
                )
            )

    post = by_kind.get("POST_REVEAL")
    if policy.stage == "FINAL" and post is not None:
        for field_name, value in (
            ("solution_inferable", post.solution_inferable),
            ("solution_earned", post.solution_earned),
            ("late_invention_detected", post.late_invention_detected),
            ("stronger_alternative_detected", post.stronger_alternative_detected),
        ):
            if value is None:
                findings.append(
                    _finding(
                        "MYSTERYBENCH.COLD_READER.POST_REVEAL_FIELD_MISSING",
                        f"POST_REVEAL requires {field_name}",
                        field_name,
                    )
                )

    return cold_reader_protocol_ref(pack.cold_reader_checkpoints)


def _validate_adversarial(
    *,
    pack: MysteryBenchPack,
    policy: MysteryBenchPolicy,
    findings: list[MysteryBenchFinding],
) -> str | None:
    evidence = pack.adversarial_reconstruction
    if not policy.require_adversarial_reconstruction:
        if evidence is not None:
            findings.append(
                _finding(
                    "MYSTERYBENCH.ADVERSARIAL.UNEXPECTED",
                    "adversarial reconstruction exists while policy disables it",
                )
            )
        return None
    if evidence is None:
        findings.append(
            _finding(
                "MYSTERYBENCH.ADVERSARIAL.MISSING",
                "required blind adversarial reconstruction is missing",
            )
        )
        return None

    if evidence.manuscript_snapshot_ref != pack.manuscript_snapshot_ref:
        findings.append(
            _finding(
                "MYSTERYBENCH.ADVERSARIAL.SNAPSHOT_MISMATCH",
                "adversarial reconstruction uses a different manuscript snapshot",
            )
        )
    if not evidence.evaluator_identity.strip():
        findings.append(
            _finding(
                "MYSTERYBENCH.ADVERSARIAL.EVALUATOR_MISSING",
                "adversarial reconstruction has no evaluator identity",
            )
        )
    elif evidence.evaluator_identity == pack.writer_executor_identity:
        findings.append(
            _finding(
                "MYSTERYBENCH.ADVERSARIAL.NOT_INDEPENDENT",
                "adversarial reconstruction cannot use the Writer executor identity",
            )
        )
    if not evidence.reconstruction_ref.strip():
        findings.append(
            _finding(
                "MYSTERYBENCH.ADVERSARIAL.RECONSTRUCTION_REF_MISSING",
                "blind reconstruction ref is missing",
            )
        )
    if not evidence.comparison_ref.strip():
        findings.append(
            _finding(
                "MYSTERYBENCH.ADVERSARIAL.COMPARISON_REF_MISSING",
                "post-reconstruction CaseSolution comparison ref is missing",
            )
        )
    if not evidence.accepted_case_solution_revision_ref.strip():
        findings.append(
            _finding(
                "MYSTERYBENCH.ADVERSARIAL.CASE_SOLUTION_REF_MISSING",
                "accepted CaseSolution revision ref is missing",
            )
        )
    elif evidence.accepted_case_solution_revision_ref not in pack.authority_revision_refs:
        findings.append(
            _finding(
                "MYSTERYBENCH.ADVERSARIAL.CASE_SOLUTION_NOT_IN_AUTHORITY_SNAPSHOT",
                (
                    "adversarial comparison CaseSolution is not present in the "
                    "MysteryBench authority snapshot"
                ),
                evidence.accepted_case_solution_revision_ref,
            )
        )
    if evidence.accepted_case_solution_revision_ref in evidence.blind_input_refs:
        findings.append(
            _finding(
                "MYSTERYBENCH.ADVERSARIAL.CASE_SOLUTION_IN_BLIND_INPUT",
                "private CaseSolution was included in blind reconstruction inputs",
                evidence.accepted_case_solution_revision_ref,
            )
        )
    if evidence.reveal_order != "RECONSTRUCTION_THEN_CASE_SOLUTION":
        findings.append(
            _finding(
                "MYSTERYBENCH.ADVERSARIAL.REVEAL_ORDER_INVALID",
                "CaseSolution may only be revealed after blind reconstruction is fixed",
            )
        )

    for code, active in (
        ("MISSING_REQUIRED_FACT", evidence.missing_required_fact),
        ("IMPOSSIBLE_TIMELINE", evidence.impossible_timeline),
        ("STRONGER_ALTERNATIVE", evidence.stronger_alternative_solution),
        (
            "SOLUTION_CONTRADICTS_MANUSCRIPT",
            evidence.accepted_solution_contradicts_manuscript,
        ),
        (
            "UNSTATED_SUPERNATURAL_RULE",
            evidence.unstated_decisive_supernatural_rule,
        ),
        ("UNFAIR_WITHHOLDING", evidence.unfair_decisive_withholding),
    ):
        if active:
            findings.append(
                _finding(
                    f"MYSTERYBENCH.ADVERSARIAL.{code}",
                    f"adversarial reconstruction detected {code.lower()}",
                )
            )

    return adversarial_protocol_ref(evidence)


def evaluate_mystery_bench(
    *,
    pack: MysteryBenchPack,
    policy: MysteryBenchPolicy,
    current_manuscript_snapshot_ref: str,
    current_manuscript_snapshot_hash: str,
    current_authority_revision_refs: tuple[str, ...],
) -> MysteryBenchResult:
    """Validate version-bound MysteryBench evidence without running any evaluator."""
    findings: list[MysteryBenchFinding] = []

    if not pack.book_id.strip():
        findings.append(
            _finding("MYSTERYBENCH.BOOK_ID_MISSING", "book_id must not be blank")
        )
    if not pack.manuscript_snapshot_ref.strip():
        findings.append(
            _finding(
                "MYSTERYBENCH.MANUSCRIPT.SNAPSHOT_REF_MISSING",
                "manuscript snapshot ref is missing",
            )
        )
    if not _SHA256.fullmatch(pack.manuscript_snapshot_hash):
        findings.append(
            _finding(
                "MYSTERYBENCH.MANUSCRIPT.SNAPSHOT_HASH_INVALID",
                "manuscript snapshot hash must be lowercase SHA-256",
            )
        )
    if (
        pack.manuscript_snapshot_ref != current_manuscript_snapshot_ref
        or pack.manuscript_snapshot_hash != current_manuscript_snapshot_hash
    ):
        findings.append(
            _finding(
                "MYSTERYBENCH.MANUSCRIPT.STALE",
                "MysteryBench evidence is not bound to the current manuscript snapshot",
            )
        )

    authority_refs = tuple(sorted(set(pack.authority_revision_refs)))
    if not authority_refs or any(not value.strip() for value in authority_refs):
        findings.append(
            _finding(
                "MYSTERYBENCH.AUTHORITY.REFS_MISSING",
                "MysteryBench requires exact non-empty authority revision refs",
            )
        )
    if len(authority_refs) != len(pack.authority_revision_refs):
        findings.append(
            _finding(
                "MYSTERYBENCH.AUTHORITY.DUPLICATE_REF",
                "MysteryBench authority snapshot contains duplicate refs",
            )
        )
    if authority_refs != tuple(sorted(set(current_authority_revision_refs))):
        findings.append(
            _finding(
                "MYSTERYBENCH.AUTHORITY.STALE",
                "MysteryBench authority snapshot differs from current authority",
            )
        )
    if not pack.writer_executor_identity.strip():
        findings.append(
            _finding(
                "MYSTERYBENCH.WRITER_IDENTITY_MISSING",
                "Writer executor identity is required for independence checks",
            )
        )

    cold_ref = _validate_cold_reader(pack=pack, policy=policy, findings=findings)
    adversarial_ref = _validate_adversarial(
        pack=pack,
        policy=policy,
        findings=findings,
    )

    by_dimension: dict[str, MysteryDimensionEvidence] = {}
    evaluation_refs_seen: set[str] = set()
    for evidence in pack.dimension_evidence:
        if evidence.dimension not in _VALID_DIMENSIONS:
            findings.append(
                _finding(
                    "MYSTERYBENCH.DIMENSION.UNKNOWN",
                    f"unknown mystery dimension {evidence.dimension}",
                    evidence.dimension,
                )
            )
            continue
        if evidence.dimension in by_dimension:
            findings.append(
                _finding(
                    "MYSTERYBENCH.DIMENSION.DUPLICATE",
                    f"duplicate mystery dimension {evidence.dimension}",
                    evidence.dimension,
                )
            )
            continue
        by_dimension[evidence.dimension] = evidence

        if not evidence.evaluation_ref.strip():
            findings.append(
                _finding(
                    "MYSTERYBENCH.EVIDENCE.REF_MISSING",
                    f"dimension {evidence.dimension} has no evaluation ref",
                    evidence.dimension,
                )
            )
        elif evidence.evaluation_ref in evaluation_refs_seen:
            findings.append(
                _finding(
                    "MYSTERYBENCH.EVIDENCE.REF_REUSED",
                    (
                        f"evaluation ref {evidence.evaluation_ref} is reused across "
                        "mystery dimensions"
                    ),
                    evidence.evaluation_ref,
                )
            )
        else:
            evaluation_refs_seen.add(evidence.evaluation_ref)

        if evidence.bookbench_snapshot_ref != pack.manuscript_snapshot_ref:
            findings.append(
                _finding(
                    "MYSTERYBENCH.EVIDENCE.SNAPSHOT_MISMATCH",
                    (
                        f"dimension {evidence.dimension} is not bound to the exact "
                        "manuscript/BookBench snapshot"
                    ),
                    evidence.dimension,
                )
            )
        if not evidence.rubric_ref.strip():
            findings.append(
                _finding(
                    "MYSTERYBENCH.EVIDENCE.RUBRIC_REF_MISSING",
                    f"dimension {evidence.dimension} has no versioned rubric ref",
                    evidence.dimension,
                )
            )
        if not evidence.evaluator_identity.strip():
            findings.append(
                _finding(
                    "MYSTERYBENCH.EVIDENCE.EVALUATOR_MISSING",
                    f"dimension {evidence.dimension} has no evaluator identity",
                    evidence.dimension,
                )
            )
        if evidence.evaluator_class not in _VALID_EVALUATOR_CLASSES:
            findings.append(
                _finding(
                    "MYSTERYBENCH.EVIDENCE.EVALUATOR_CLASS_UNKNOWN",
                    f"dimension {evidence.dimension} has unknown evaluator class",
                    evidence.dimension,
                )
            )
        if evidence.independence_state not in _VALID_INDEPENDENCE_STATES:
            findings.append(
                _finding(
                    "MYSTERYBENCH.EVIDENCE.INDEPENDENCE_UNKNOWN",
                    f"dimension {evidence.dimension} has invalid independence state",
                    evidence.dimension,
                )
            )
        elif evidence.evaluator_class == "DETERMINISTIC":
            if evidence.independence_state not in {"NOT_APPLICABLE", "INDEPENDENT"}:
                findings.append(
                    _finding(
                        "MYSTERYBENCH.EVIDENCE.DETERMINISTIC_INDEPENDENCE_INVALID",
                        (
                            f"deterministic dimension {evidence.dimension} has "
                            f"independence={evidence.independence_state}"
                        ),
                        evidence.dimension,
                    )
                )
        else:
            if evidence.independence_state != "INDEPENDENT":
                findings.append(
                    _finding(
                        "MYSTERYBENCH.EVIDENCE.NOT_INDEPENDENT",
                        (
                            f"dimension {evidence.dimension} requires independent "
                            "semantic/human evaluation"
                        ),
                        evidence.dimension,
                    )
                )
            if evidence.evaluator_identity == pack.writer_executor_identity:
                findings.append(
                    _finding(
                        "MYSTERYBENCH.EVIDENCE.SAME_WRITER_EXECUTOR",
                        (
                            f"dimension {evidence.dimension} uses the same executor "
                            "identity as the Writer"
                        ),
                        evidence.dimension,
                    )
                )

        if evidence.status not in _VALID_STATUSES:
            findings.append(
                _finding(
                    "MYSTERYBENCH.EVIDENCE.STATUS_UNKNOWN",
                    f"dimension {evidence.dimension} has unknown status {evidence.status}",
                    evidence.dimension,
                )
            )
        elif evidence.status == "BLOCKING_GAP":
            findings.append(
                _finding(
                    "MYSTERYBENCH.EVIDENCE.BLOCKING_GAP",
                    (
                        f"dimension {evidence.dimension} has unresolved BLOCKING gap; "
                        "it cannot be waived"
                    ),
                    evidence.dimension,
                )
            )
        elif evidence.status == "NOT_EVALUATED":
            findings.append(
                _finding(
                    "MYSTERYBENCH.EVIDENCE.NOT_EVALUATED",
                    f"dimension {evidence.dimension} was not evaluated",
                    evidence.dimension,
                )
            )
        elif evidence.status == "MAJOR_GAP" and (
            evidence.human_disposition_ref is None
            or not evidence.human_disposition_ref.strip()
        ):
            findings.append(
                _finding(
                    "MYSTERYBENCH.EVIDENCE.MAJOR_UNDISPOSED",
                    (
                        f"dimension {evidence.dimension} has MAJOR gap without "
                        "explicit human disposition"
                    ),
                    evidence.dimension,
                )
            )

    for dimension in sorted(_required_dimensions(policy)):
        if dimension not in by_dimension:
            findings.append(
                _finding(
                    "MYSTERYBENCH.DIMENSION.MISSING",
                    f"required mystery dimension {dimension} is missing",
                    dimension,
                )
            )

    if policy.stage == "FINAL" and policy.require_cold_reader and cold_ref is not None:
        for dimension in ("FAIR_PLAY", "REVEAL_QUALITY"):
            evidence = by_dimension.get(dimension)
            if evidence is not None and cold_ref not in evidence.supporting_evidence_refs:
                findings.append(
                    _finding(
                        "MYSTERYBENCH.EVIDENCE.COLD_READER_NOT_CONSUMED",
                        (
                            f"final {dimension} evaluation does not cite exact "
                            "ColdReader protocol evidence"
                        ),
                        dimension,
                        cold_ref,
                    )
                )

    if (
        policy.stage == "FINAL"
        and policy.require_adversarial_reconstruction
        and adversarial_ref is not None
    ):
        for dimension in ("CASE_COHERENCE", "FAIR_PLAY", "NARRATIVE_INTEGRITY"):
            evidence = by_dimension.get(dimension)
            if (
                evidence is not None
                and adversarial_ref not in evidence.supporting_evidence_refs
            ):
                findings.append(
                    _finding(
                        "MYSTERYBENCH.EVIDENCE.ADVERSARIAL_NOT_CONSUMED",
                        (
                            f"final {dimension} evaluation does not cite exact "
                            "adversarial reconstruction evidence"
                        ),
                        dimension,
                        adversarial_ref,
                    )
                )

    result_ref = _pack_ref(
        pack=pack,
        policy=policy,
        cold_ref=cold_ref,
        adversarial_ref=adversarial_ref,
    )
    return MysteryBenchResult(
        qualified=not findings,
        mystery_bench_ref=result_ref,
        cold_reader_protocol_ref=cold_ref,
        adversarial_protocol_ref=adversarial_ref,
        findings=tuple(findings),
    )


def verify_mystery_bench(
    *,
    prior_mystery_bench_ref: str,
    pack: MysteryBenchPack,
    policy: MysteryBenchPolicy,
    current_manuscript_snapshot_ref: str,
    current_manuscript_snapshot_hash: str,
    current_authority_revision_refs: tuple[str, ...],
) -> MysteryBenchVerification:
    current = evaluate_mystery_bench(
        pack=pack,
        policy=policy,
        current_manuscript_snapshot_ref=current_manuscript_snapshot_ref,
        current_manuscript_snapshot_hash=current_manuscript_snapshot_hash,
        current_authority_revision_refs=current_authority_revision_refs,
    )
    if not current.qualified:
        return MysteryBenchVerification(
            valid=False,
            reason="CURRENT_MYSTERYBENCH_BLOCKED",
            current_result=current,
        )
    if current.mystery_bench_ref != prior_mystery_bench_ref:
        return MysteryBenchVerification(
            valid=False,
            reason="MYSTERYBENCH_SNAPSHOT_CHANGED",
            current_result=current,
        )
    return MysteryBenchVerification(
        valid=True,
        reason=None,
        current_result=current,
    )
