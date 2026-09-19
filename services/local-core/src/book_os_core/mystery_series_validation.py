from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, TypeAlias

from .authority_types import JSONValue, content_hash
from .mystery_bench_validation import (
    EvaluatorClass,
    IndependenceState,
    VerifiedEvaluationArtifact,
)

SeriesProfileStatus: TypeAlias = Literal["DRAFT", "APPROVED"]
PassportAuthorityStatus: TypeAlias = Literal["APPROVED", "LOCKED"]
CollisionSeverity: TypeAlias = Literal["BLOCKING", "MAJOR", "MINOR", "NOTE"]
SemanticCollisionState: TypeAlias = Literal["CLEAR", "ATTENTION", "MATERIAL_COLLISION"]
CollisionKind: TypeAlias = Literal["EXACT", "COMPOSITE", "ASSET", "SEMANTIC"]
CollisionDimension: TypeAlias = Literal[
    "PREMISE",
    "CASE_TYPE",
    "VICTIM_TARGET_PROFILE",
    "CULPRIT_RELATIONSHIP",
    "MOTIVE_FAMILY",
    "MECHANISM",
    "CONCEALMENT",
    "SUSPECT_ARCHITECTURE",
    "CLUE_ARCHITECTURE",
    "RED_HERRING_PATTERN",
    "SUPERNATURAL_DEVICE",
    "SETTING_TYPE",
    "PROTAGONIST_JEOPARDY",
    "EMOTIONAL_CONFLICT",
    "RELATIONSHIP_MOVEMENT",
    "MIDPOINT_REVERSAL",
    "FINAL_REVEAL",
    "CLIMAX_STAGING",
    "ENDING_STATE",
    "OPENING_PATTERN",
    "BODY_DISCOVERY_PATTERN",
    "INTERVIEW_CADENCE",
    "CASE_SOLUTION_ARCHITECTURE",
    "PROSE_SCENE_PATTERN_RISK",
]

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_VALID_DIMENSIONS: frozenset[str] = frozenset(
    {
        "PREMISE",
        "CASE_TYPE",
        "VICTIM_TARGET_PROFILE",
        "CULPRIT_RELATIONSHIP",
        "MOTIVE_FAMILY",
        "MECHANISM",
        "CONCEALMENT",
        "SUSPECT_ARCHITECTURE",
        "CLUE_ARCHITECTURE",
        "RED_HERRING_PATTERN",
        "SUPERNATURAL_DEVICE",
        "SETTING_TYPE",
        "PROTAGONIST_JEOPARDY",
        "EMOTIONAL_CONFLICT",
        "RELATIONSHIP_MOVEMENT",
        "MIDPOINT_REVERSAL",
        "FINAL_REVEAL",
        "CLIMAX_STAGING",
        "ENDING_STATE",
        "OPENING_PATTERN",
        "BODY_DISCOVERY_PATTERN",
        "INTERVIEW_CADENCE",
        "CASE_SOLUTION_ARCHITECTURE",
        "PROSE_SCENE_PATTERN_RISK",
    }
)
_MINIMUM_SEMANTIC_DIMENSIONS: frozenset[str] = frozenset(
    {
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
    }
)
_VALID_SEMANTIC_STATES = frozenset({"CLEAR", "ATTENTION", "MATERIAL_COLLISION"})
_VALID_EVALUATOR_CLASSES = frozenset(
    {"DETERMINISTIC", "SEMANTIC", "LLM_JUDGE", "PAIRWISE", "HUMAN_LABEL"}
)
_VALID_INDEPENDENCE = frozenset({"INDEPENDENT", "SAME_CONFIG", "UNKNOWN", "NOT_APPLICABLE"})


@dataclass(frozen=True)
class SeriesProfileSnapshot:
    profile_id: str
    content_hash: str
    status: SeriesProfileStatus
    series_name: str
    allowed_recurring_asset_codes: tuple[str, ...] = ()
    shared_invariant_refs: tuple[str, ...] = ()
    strongly_serialized: bool = False


@dataclass(frozen=True)
class MysteryBookPassport:
    book_id: str
    book_number: int
    working_title: str
    series_profile_id: str
    series_profile_ref: str
    premise_signature: str
    primary_case_type: str
    victim_target_profile: str
    culprit_relationship: str
    motive_family: str
    mechanism: str
    concealment: str
    suspect_architecture: str
    clue_architecture: str
    red_herring_pattern: str
    supernatural_device: str
    setting_type: str
    protagonist_jeopardy: str
    emotional_conflict: str
    relationship_movement: str
    midpoint_reversal: str
    final_reveal: str
    climax_staging: str
    ending_state: str
    opening_pattern: str
    body_discovery_pattern: str
    interview_cadence: str
    case_solution_architecture: str
    prose_scene_pattern_risk: str
    assets_consumed: tuple[str, ...] = ()
    assets_reserved: tuple[str, ...] = ()
    reservation_claim_codes: tuple[str, ...] = ()
    primary_case_resolved: bool = True
    late_entry_orientation_ref: str | None = None


@dataclass(frozen=True)
class AcceptedBookPassport:
    passport: MysteryBookPassport
    passport_hash: str
    status: PassportAuthorityStatus
    recurring_asset_codes_at_acceptance: tuple[str, ...] = ()


@dataclass(frozen=True)
class SeriesCollisionPolicy:
    exact_blocking_dimensions: tuple[CollisionDimension, ...]
    exact_attention_dimensions: tuple[CollisionDimension, ...]
    semantic_required_dimensions: tuple[CollisionDimension, ...]
    require_semantic_independence: bool = True
    attention_requires_human_disposition: bool = True
    require_standalone_case_resolution: bool = True


@dataclass(frozen=True)
class SeriesSemanticCollisionEvidence:
    current_book_id: str
    prior_book_id: str
    dimension: CollisionDimension
    state: SemanticCollisionState
    evaluation_ref: str
    evaluator_identity: str
    evaluator_class: EvaluatorClass
    independence_state: IndependenceState
    rubric_ref: str
    human_disposition_ref: str | None = None


@dataclass(frozen=True)
class SeriesCollisionFinding:
    code: str
    severity: CollisionSeverity
    collision_kind: CollisionKind
    dimension: str
    current_book_id: str
    prior_book_id: str | None
    message: str
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class SeriesUniquenessResult:
    qualified: bool
    series_brain_ref: str
    current_passport_ref: str
    findings: tuple[SeriesCollisionFinding, ...]


@dataclass(frozen=True)
class SeriesUniquenessVerification:
    valid: bool
    reason: str | None
    current_result: SeriesUniquenessResult


def _finding(
    code: str,
    severity: CollisionSeverity,
    collision_kind: CollisionKind,
    dimension: str,
    current_book_id: str,
    prior_book_id: str | None,
    message: str,
    *evidence_refs: str,
) -> SeriesCollisionFinding:
    return SeriesCollisionFinding(
        code=code,
        severity=severity,
        collision_kind=collision_kind,
        dimension=dimension,
        current_book_id=current_book_id,
        prior_book_id=prior_book_id,
        message=message,
        evidence_refs=tuple(evidence_refs),
    )


def _json_strings(values: tuple[str, ...]) -> list[JSONValue]:
    result: list[JSONValue] = []
    for value in sorted(values):
        result.append(value)
    return result


def _series_profile_payload(
    profile: SeriesProfileSnapshot,
) -> dict[str, JSONValue]:
    return {
        "profile_id": profile.profile_id,
        "content_hash": profile.content_hash,
        "status": profile.status,
        "series_name": profile.series_name,
        "allowed_recurring_asset_codes": _json_strings(profile.allowed_recurring_asset_codes),
        "shared_invariant_refs": _json_strings(profile.shared_invariant_refs),
        "strongly_serialized": profile.strongly_serialized,
    }


def series_profile_ref(profile: SeriesProfileSnapshot) -> str:
    return f"series-profile:{profile.profile_id}:{profile.content_hash}"


def _passport_payload(passport: MysteryBookPassport) -> dict[str, JSONValue]:
    return {
        "book_id": passport.book_id,
        "book_number": passport.book_number,
        "working_title": passport.working_title,
        "series_profile_id": passport.series_profile_id,
        "series_profile_ref": passport.series_profile_ref,
        "premise_signature": passport.premise_signature,
        "primary_case_type": passport.primary_case_type,
        "victim_target_profile": passport.victim_target_profile,
        "culprit_relationship": passport.culprit_relationship,
        "motive_family": passport.motive_family,
        "mechanism": passport.mechanism,
        "concealment": passport.concealment,
        "suspect_architecture": passport.suspect_architecture,
        "clue_architecture": passport.clue_architecture,
        "red_herring_pattern": passport.red_herring_pattern,
        "supernatural_device": passport.supernatural_device,
        "setting_type": passport.setting_type,
        "protagonist_jeopardy": passport.protagonist_jeopardy,
        "emotional_conflict": passport.emotional_conflict,
        "relationship_movement": passport.relationship_movement,
        "midpoint_reversal": passport.midpoint_reversal,
        "final_reveal": passport.final_reveal,
        "climax_staging": passport.climax_staging,
        "ending_state": passport.ending_state,
        "opening_pattern": passport.opening_pattern,
        "body_discovery_pattern": passport.body_discovery_pattern,
        "interview_cadence": passport.interview_cadence,
        "case_solution_architecture": passport.case_solution_architecture,
        "prose_scene_pattern_risk": passport.prose_scene_pattern_risk,
        "assets_consumed": _json_strings(passport.assets_consumed),
        "assets_reserved": _json_strings(passport.assets_reserved),
        "reservation_claim_codes": _json_strings(passport.reservation_claim_codes),
        "primary_case_resolved": passport.primary_case_resolved,
        "late_entry_orientation_ref": passport.late_entry_orientation_ref,
    }


def passport_hash(passport: MysteryBookPassport) -> str:
    return content_hash(_passport_payload(passport))


def passport_ref(passport: MysteryBookPassport) -> str:
    return f"mystery-book-passport:{passport.book_id}:{passport_hash(passport)}"


def _policy_payload(policy: SeriesCollisionPolicy) -> dict[str, JSONValue]:
    return {
        "exact_blocking_dimensions": _json_strings(tuple(policy.exact_blocking_dimensions)),
        "exact_attention_dimensions": _json_strings(tuple(policy.exact_attention_dimensions)),
        "semantic_required_dimensions": _json_strings(tuple(policy.semantic_required_dimensions)),
        "require_semantic_independence": policy.require_semantic_independence,
        "attention_requires_human_disposition": (policy.attention_requires_human_disposition),
        "require_standalone_case_resolution": (policy.require_standalone_case_resolution),
    }


def _accepted_passport_payload(
    accepted: AcceptedBookPassport,
) -> dict[str, JSONValue]:
    return {
        "passport_ref": passport_ref(accepted.passport),
        "passport_hash": accepted.passport_hash,
        "status": accepted.status,
        "recurring_asset_codes_at_acceptance": _json_strings(
            accepted.recurring_asset_codes_at_acceptance
        ),
    }


def _semantic_payload(
    evidence: SeriesSemanticCollisionEvidence,
) -> dict[str, JSONValue]:
    return {
        "current_book_id": evidence.current_book_id,
        "prior_book_id": evidence.prior_book_id,
        "dimension": evidence.dimension,
        "state": evidence.state,
        "evaluation_ref": evidence.evaluation_ref,
        "evaluator_identity": evidence.evaluator_identity,
        "evaluator_class": evidence.evaluator_class,
        "independence_state": evidence.independence_state,
        "rubric_ref": evidence.rubric_ref,
        "human_disposition_ref": evidence.human_disposition_ref,
    }


def series_context_ref(
    *,
    profile: SeriesProfileSnapshot,
    current_passport: MysteryBookPassport,
    prior_passports: tuple[AcceptedBookPassport, ...],
    policy: SeriesCollisionPolicy,
    writer_executor_identity: str,
) -> str:
    prior_values: list[JSONValue] = []
    for accepted in sorted(
        prior_passports,
        key=lambda item: (item.passport.book_number, item.passport.book_id),
    ):
        prior_values.append(_accepted_passport_payload(accepted))
    payload: dict[str, JSONValue] = {
        "series_profile": _series_profile_payload(profile),
        "current_passport_ref": passport_ref(current_passport),
        "writer_executor_identity": writer_executor_identity,
        "prior_passports": prior_values,
        "policy": _policy_payload(policy),
    }
    return f"series-context:{content_hash(payload)}"


def series_brain_ref(
    *,
    context_ref: str,
    semantic_evidence: tuple[SeriesSemanticCollisionEvidence, ...],
) -> str:
    semantic_values: list[JSONValue] = []
    for evidence in sorted(
        semantic_evidence,
        key=lambda item: (
            item.prior_book_id,
            item.dimension,
            item.evaluation_ref,
        ),
    ):
        semantic_values.append(_semantic_payload(evidence))
    payload: dict[str, JSONValue] = {
        "series_context_ref": context_ref,
        "semantic_evidence": semantic_values,
    }
    return f"series-brain:{content_hash(payload)}"


def _field_value(
    passport: MysteryBookPassport,
    dimension: str,
) -> str:
    mapping = {
        "PREMISE": passport.premise_signature,
        "CASE_TYPE": passport.primary_case_type,
        "VICTIM_TARGET_PROFILE": passport.victim_target_profile,
        "CULPRIT_RELATIONSHIP": passport.culprit_relationship,
        "MOTIVE_FAMILY": passport.motive_family,
        "MECHANISM": passport.mechanism,
        "CONCEALMENT": passport.concealment,
        "SUSPECT_ARCHITECTURE": passport.suspect_architecture,
        "CLUE_ARCHITECTURE": passport.clue_architecture,
        "RED_HERRING_PATTERN": passport.red_herring_pattern,
        "SUPERNATURAL_DEVICE": passport.supernatural_device,
        "SETTING_TYPE": passport.setting_type,
        "PROTAGONIST_JEOPARDY": passport.protagonist_jeopardy,
        "EMOTIONAL_CONFLICT": passport.emotional_conflict,
        "RELATIONSHIP_MOVEMENT": passport.relationship_movement,
        "MIDPOINT_REVERSAL": passport.midpoint_reversal,
        "FINAL_REVEAL": passport.final_reveal,
        "CLIMAX_STAGING": passport.climax_staging,
        "ENDING_STATE": passport.ending_state,
        "OPENING_PATTERN": passport.opening_pattern,
        "BODY_DISCOVERY_PATTERN": passport.body_discovery_pattern,
        "INTERVIEW_CADENCE": passport.interview_cadence,
        "CASE_SOLUTION_ARCHITECTURE": passport.case_solution_architecture,
        "PROSE_SCENE_PATTERN_RISK": passport.prose_scene_pattern_risk,
    }
    return mapping.get(dimension, "")


def _validate_unique_values(
    values: tuple[str, ...],
    *,
    code: str,
    current_book_id: str,
    findings: list[SeriesCollisionFinding],
) -> None:
    if any(not value.strip() for value in values):
        findings.append(
            _finding(
                f"{code}.EMPTY",
                "BLOCKING",
                "ASSET",
                "ASSET",
                current_book_id,
                None,
                "asset/reservation code must not be blank",
            )
        )
    if len(set(values)) != len(values):
        findings.append(
            _finding(
                f"{code}.DUPLICATE",
                "BLOCKING",
                "ASSET",
                "ASSET",
                current_book_id,
                None,
                "asset/reservation codes must be unique",
            )
        )


def _valid_series_profile_ref_for_id(
    value: str,
    profile_id: str,
) -> bool:
    prefix = f"series-profile:{profile_id}:"
    if not value.startswith(prefix):
        return False
    return bool(_SHA256.fullmatch(value[len(prefix) :]))


def _validate_passport_shape(
    *,
    passport: MysteryBookPassport,
    expected_series_profile_id: str,
    expected_series_profile_ref: str,
    findings: list[SeriesCollisionFinding],
) -> None:
    if not passport.book_id.strip():
        findings.append(
            _finding(
                "SERIES.PASSPORT.BOOK_ID_MISSING",
                "BLOCKING",
                "EXACT",
                "PASSPORT",
                passport.book_id,
                None,
                "book_id must not be blank",
            )
        )
    if passport.book_number < 1:
        findings.append(
            _finding(
                "SERIES.PASSPORT.BOOK_NUMBER_INVALID",
                "BLOCKING",
                "EXACT",
                "PASSPORT",
                passport.book_id,
                None,
                "book_number must be positive",
            )
        )
    if not passport.working_title.strip():
        findings.append(
            _finding(
                "SERIES.PASSPORT.TITLE_MISSING",
                "BLOCKING",
                "EXACT",
                "PASSPORT",
                passport.book_id,
                None,
                "working_title must not be blank",
            )
        )
    if not passport.series_profile_id.strip():
        findings.append(
            _finding(
                "SERIES.PASSPORT.SERIES_PROFILE_ID_MISSING",
                "BLOCKING",
                "EXACT",
                "PASSPORT",
                passport.book_id,
                None,
                "Book Passport requires series_profile_id",
            )
        )
    elif passport.series_profile_id != expected_series_profile_id:
        findings.append(
            _finding(
                "SERIES.PASSPORT.SERIES_PROFILE_ID_MISMATCH",
                "BLOCKING",
                "EXACT",
                "PASSPORT",
                passport.book_id,
                None,
                "Book Passport belongs to another series identity",
            )
        )
    if not _valid_series_profile_ref_for_id(
        passport.series_profile_ref,
        passport.series_profile_id,
    ):
        findings.append(
            _finding(
                "SERIES.PASSPORT.SERIES_PROFILE_REF_INVALID",
                "BLOCKING",
                "EXACT",
                "PASSPORT",
                passport.book_id,
                None,
                "Book Passport Series Profile ref is malformed or belongs to another id",
            )
        )
    if passport.series_profile_ref != expected_series_profile_ref:
        findings.append(
            _finding(
                "SERIES.PASSPORT.SERIES_PROFILE_MISMATCH",
                "BLOCKING",
                "EXACT",
                "PASSPORT",
                passport.book_id,
                None,
                "Book Passport is not bound to the exact current Series Profile",
            )
        )

    required_text_fields = {
        "PREMISE": passport.premise_signature,
        "CASE_TYPE": passport.primary_case_type,
        "VICTIM_TARGET_PROFILE": passport.victim_target_profile,
        "CULPRIT_RELATIONSHIP": passport.culprit_relationship,
        "MOTIVE_FAMILY": passport.motive_family,
        "MECHANISM": passport.mechanism,
        "CONCEALMENT": passport.concealment,
        "SUSPECT_ARCHITECTURE": passport.suspect_architecture,
        "CLUE_ARCHITECTURE": passport.clue_architecture,
        "RED_HERRING_PATTERN": passport.red_herring_pattern,
        "SETTING_TYPE": passport.setting_type,
        "EMOTIONAL_CONFLICT": passport.emotional_conflict,
        "RELATIONSHIP_MOVEMENT": passport.relationship_movement,
        "MIDPOINT_REVERSAL": passport.midpoint_reversal,
        "FINAL_REVEAL": passport.final_reveal,
        "CLIMAX_STAGING": passport.climax_staging,
        "ENDING_STATE": passport.ending_state,
        "OPENING_PATTERN": passport.opening_pattern,
        "BODY_DISCOVERY_PATTERN": passport.body_discovery_pattern,
        "INTERVIEW_CADENCE": passport.interview_cadence,
        "CASE_SOLUTION_ARCHITECTURE": passport.case_solution_architecture,
        "PROSE_SCENE_PATTERN_RISK": passport.prose_scene_pattern_risk,
    }
    for dimension, value in required_text_fields.items():
        if not value.strip():
            findings.append(
                _finding(
                    "SERIES.PASSPORT.FIELD_MISSING",
                    "BLOCKING",
                    "EXACT",
                    dimension,
                    passport.book_id,
                    None,
                    f"Book Passport field {dimension} must not be blank",
                )
            )

    _validate_unique_values(
        passport.assets_consumed,
        code="SERIES.ASSET.CONSUMED",
        current_book_id=passport.book_id,
        findings=findings,
    )
    _validate_unique_values(
        passport.assets_reserved,
        code="SERIES.ASSET.RESERVED",
        current_book_id=passport.book_id,
        findings=findings,
    )
    _validate_unique_values(
        passport.reservation_claim_codes,
        code="SERIES.ASSET.CLAIM",
        current_book_id=passport.book_id,
        findings=findings,
    )
    overlapping = set(passport.assets_consumed) & set(passport.assets_reserved)
    for asset_code in sorted(overlapping):
        findings.append(
            _finding(
                "SERIES.ASSET.CONSUMED_AND_RESERVED",
                "BLOCKING",
                "ASSET",
                "ASSET",
                passport.book_id,
                None,
                f"asset {asset_code} cannot be consumed and newly reserved together",
                asset_code,
            )
        )


def _validate_profile(
    *,
    profile: SeriesProfileSnapshot,
    current_profile: SeriesProfileSnapshot,
    findings: list[SeriesCollisionFinding],
    current_book_id: str,
) -> None:
    if not profile.profile_id.strip():
        findings.append(
            _finding(
                "SERIES.PROFILE.ID_MISSING",
                "BLOCKING",
                "EXACT",
                "SERIES_PROFILE",
                current_book_id,
                None,
                "series profile id must not be blank",
            )
        )
    if not _SHA256.fullmatch(profile.content_hash):
        findings.append(
            _finding(
                "SERIES.PROFILE.HASH_INVALID",
                "BLOCKING",
                "EXACT",
                "SERIES_PROFILE",
                current_book_id,
                None,
                "series profile hash must be lowercase SHA-256",
            )
        )
    if profile.status != "APPROVED":
        findings.append(
            _finding(
                "SERIES.PROFILE.NOT_APPROVED",
                "BLOCKING",
                "EXACT",
                "SERIES_PROFILE",
                current_book_id,
                None,
                f"series profile status is {profile.status}",
            )
        )
    if profile != current_profile:
        findings.append(
            _finding(
                "SERIES.PROFILE.STALE",
                "BLOCKING",
                "EXACT",
                "SERIES_PROFILE",
                current_book_id,
                None,
                "Series Brain is not bound to the current exact Series Profile",
            )
        )
    if not profile.series_name.strip():
        findings.append(
            _finding(
                "SERIES.PROFILE.NAME_MISSING",
                "BLOCKING",
                "EXACT",
                "SERIES_PROFILE",
                current_book_id,
                None,
                "series name must not be blank",
            )
        )
    _validate_unique_values(
        profile.allowed_recurring_asset_codes,
        code="SERIES.PROFILE.RECURRING_ASSET",
        current_book_id=current_book_id,
        findings=findings,
    )
    _validate_unique_values(
        profile.shared_invariant_refs,
        code="SERIES.PROFILE.INVARIANT",
        current_book_id=current_book_id,
        findings=findings,
    )


def _validate_policy(
    *,
    policy: SeriesCollisionPolicy,
    current_book_id: str,
    findings: list[SeriesCollisionFinding],
) -> None:
    for label, values in (
        ("BLOCKING", policy.exact_blocking_dimensions),
        ("ATTENTION", policy.exact_attention_dimensions),
        ("SEMANTIC", policy.semantic_required_dimensions),
    ):
        if len(set(values)) != len(values):
            findings.append(
                _finding(
                    f"SERIES.POLICY.{label}_DUPLICATE_DIMENSION",
                    "BLOCKING",
                    "EXACT",
                    "POLICY",
                    current_book_id,
                    None,
                    f"{label} dimensions contain duplicates",
                )
            )
        for dimension in values:
            if dimension not in _VALID_DIMENSIONS:
                findings.append(
                    _finding(
                        "SERIES.POLICY.DIMENSION_UNKNOWN",
                        "BLOCKING",
                        "EXACT",
                        str(dimension),
                        current_book_id,
                        None,
                        f"unknown collision dimension {dimension}",
                    )
                )

    exact_overlap = set(policy.exact_blocking_dimensions).intersection(
        policy.exact_attention_dimensions
    )
    for dimension in sorted(exact_overlap):
        findings.append(
            _finding(
                "SERIES.POLICY.EXACT_DIMENSION_OVERLAP",
                "BLOCKING",
                "EXACT",
                dimension,
                current_book_id,
                None,
                (f"dimension {dimension} cannot be both exact-blocking and exact-attention"),
            )
        )

    semantic_missing = sorted(
        _MINIMUM_SEMANTIC_DIMENSIONS - set(policy.semantic_required_dimensions)
    )
    for dimension in semantic_missing:
        findings.append(
            _finding(
                "SERIES.POLICY.SEMANTIC_CORE_MISSING",
                "BLOCKING",
                "SEMANTIC",
                dimension,
                current_book_id,
                None,
                (f"semantic collision policy must cover core dimension {dimension}"),
            )
        )


def _validate_prior_passports(
    *,
    prior_passports: tuple[AcceptedBookPassport, ...],
    expected_series_profile_id: str,
    current_book_id: str,
    current_book_number: int,
    findings: list[SeriesCollisionFinding],
) -> None:
    book_ids: set[str] = set()
    book_numbers: set[int] = set()
    passport_refs: set[str] = set()
    for accepted in prior_passports:
        prior = accepted.passport
        ref = passport_ref(prior)
        if accepted.passport_hash != passport_hash(prior):
            findings.append(
                _finding(
                    "SERIES.PRIOR.HASH_MISMATCH",
                    "BLOCKING",
                    "EXACT",
                    "PASSPORT",
                    current_book_id,
                    prior.book_id,
                    "accepted prior passport hash does not match content",
                    ref,
                )
            )
        _validate_unique_values(
            accepted.recurring_asset_codes_at_acceptance,
            code="SERIES.PRIOR.RECURRING_ASSET",
            current_book_id=current_book_id,
            findings=findings,
        )
        if accepted.status not in {"APPROVED", "LOCKED"}:
            findings.append(
                _finding(
                    "SERIES.PRIOR.STATUS_INVALID",
                    "BLOCKING",
                    "EXACT",
                    "PASSPORT",
                    current_book_id,
                    prior.book_id,
                    f"prior passport status {accepted.status} is not accepted",
                    ref,
                )
            )
        if prior.series_profile_id != expected_series_profile_id:
            findings.append(
                _finding(
                    "SERIES.PRIOR.SERIES_PROFILE_ID_MISMATCH",
                    "BLOCKING",
                    "EXACT",
                    "PASSPORT",
                    current_book_id,
                    prior.book_id,
                    "prior passport belongs to another series identity",
                    ref,
                )
            )
        if not prior.series_profile_ref.strip():
            findings.append(
                _finding(
                    "SERIES.PRIOR.SERIES_PROFILE_REF_MISSING",
                    "BLOCKING",
                    "EXACT",
                    "PASSPORT",
                    current_book_id,
                    prior.book_id,
                    "prior passport is missing its historical Series Profile ref",
                    ref,
                )
            )
        else:
            _validate_passport_shape(
                passport=prior,
                expected_series_profile_id=expected_series_profile_id,
                expected_series_profile_ref=prior.series_profile_ref,
                findings=findings,
            )
        if prior.book_id == current_book_id:
            findings.append(
                _finding(
                    "SERIES.PRIOR.CURRENT_BOOK_INCLUDED",
                    "BLOCKING",
                    "EXACT",
                    "PASSPORT",
                    current_book_id,
                    prior.book_id,
                    "current book cannot appear among prior accepted passports",
                    ref,
                )
            )
        if prior.book_number == current_book_number:
            findings.append(
                _finding(
                    "SERIES.PRIOR.BOOK_NUMBER_COLLISION",
                    "BLOCKING",
                    "EXACT",
                    "PASSPORT",
                    current_book_id,
                    prior.book_id,
                    f"book number {current_book_number} is already used",
                    ref,
                )
            )
        elif prior.book_number > current_book_number:
            findings.append(
                _finding(
                    "SERIES.PRIOR.NOT_ACTUALLY_PRIOR",
                    "BLOCKING",
                    "EXACT",
                    "PASSPORT",
                    current_book_id,
                    prior.book_id,
                    (
                        f"passport book number {prior.book_number} is not prior "
                        f"to current book {current_book_number}"
                    ),
                    ref,
                )
            )
        if prior.book_id in book_ids:
            findings.append(
                _finding(
                    "SERIES.PRIOR.DUPLICATE_BOOK_ID",
                    "BLOCKING",
                    "EXACT",
                    "PASSPORT",
                    current_book_id,
                    prior.book_id,
                    "prior passport list repeats book_id",
                    ref,
                )
            )
        book_ids.add(prior.book_id)
        if prior.book_number in book_numbers:
            findings.append(
                _finding(
                    "SERIES.PRIOR.DUPLICATE_BOOK_NUMBER",
                    "BLOCKING",
                    "EXACT",
                    "PASSPORT",
                    current_book_id,
                    prior.book_id,
                    f"prior passport list repeats book number {prior.book_number}",
                    ref,
                )
            )
        book_numbers.add(prior.book_number)
        if ref in passport_refs:
            findings.append(
                _finding(
                    "SERIES.PRIOR.DUPLICATE_PASSPORT_REF",
                    "BLOCKING",
                    "EXACT",
                    "PASSPORT",
                    current_book_id,
                    prior.book_id,
                    "prior passport reference is duplicated",
                    ref,
                )
            )
        passport_refs.add(ref)


def _check_exact_collisions(
    *,
    current: MysteryBookPassport,
    prior_passports: tuple[AcceptedBookPassport, ...],
    policy: SeriesCollisionPolicy,
    findings: list[SeriesCollisionFinding],
) -> None:
    blocking = set(policy.exact_blocking_dimensions)
    attention = set(policy.exact_attention_dimensions)
    for accepted in prior_passports:
        prior = accepted.passport
        for dimension in sorted(blocking | attention):
            current_value = _field_value(current, dimension)
            prior_value = _field_value(prior, dimension)
            if not current_value.strip() or current_value != prior_value:
                continue
            if dimension in blocking:
                findings.append(
                    _finding(
                        "SERIES.COLLISION.EXACT_BLOCKING",
                        "BLOCKING",
                        "EXACT",
                        dimension,
                        current.book_id,
                        prior.book_id,
                        (f"exact series collision in {dimension}: {current_value!r}"),
                        passport_ref(prior),
                    )
                )
            else:
                findings.append(
                    _finding(
                        "SERIES.COLLISION.EXACT_ATTENTION",
                        "MINOR",
                        "EXACT",
                        dimension,
                        current.book_id,
                        prior.book_id,
                        (f"exact repeated pattern in {dimension}: {current_value!r}"),
                        passport_ref(prior),
                    )
                )

        if (
            current.culprit_relationship.strip()
            and current.culprit_relationship == prior.culprit_relationship
            and current.motive_family.strip()
            and current.motive_family == prior.motive_family
        ):
            findings.append(
                _finding(
                    "SERIES.COLLISION.CULPRIT_RELATIONSHIP_AND_MOTIVE",
                    "BLOCKING",
                    "COMPOSITE",
                    "CULPRIT_RELATIONSHIP+MOTIVE_FAMILY",
                    current.book_id,
                    prior.book_id,
                    (
                        "same culprit relationship and motive family recur "
                        "together with only surface variation"
                    ),
                    passport_ref(prior),
                )
            )


def _prior_asset_ledger(
    *,
    current_book_id: str,
    prior_passports: tuple[AcceptedBookPassport, ...],
    findings: list[SeriesCollisionFinding],
) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    all_consumed_by: dict[str, str] = {}
    one_use_consumed_by: dict[str, str] = {}
    reserved_by: dict[str, str] = {}

    for accepted in sorted(
        prior_passports,
        key=lambda item: (item.passport.book_number, item.passport.book_id),
    ):
        prior = accepted.passport
        recurring_at_acceptance = set(accepted.recurring_asset_codes_at_acceptance)
        prior_consumed = set(prior.assets_consumed)
        prior_claims = set(prior.reservation_claim_codes)

        for claim_code in sorted(prior_claims):
            reserving_book = reserved_by.get(claim_code)
            if reserving_book is None:
                findings.append(
                    _finding(
                        "SERIES.PRIOR_ASSET.CLAIM_UNKNOWN_RESERVATION",
                        "BLOCKING",
                        "ASSET",
                        "ASSET",
                        current_book_id,
                        prior.book_id,
                        (f"historical claim {claim_code} has no earlier reservation"),
                        claim_code,
                    )
                )
            if claim_code not in prior_consumed:
                findings.append(
                    _finding(
                        "SERIES.PRIOR_ASSET.CLAIM_NOT_CONSUMED",
                        "BLOCKING",
                        "ASSET",
                        "ASSET",
                        current_book_id,
                        prior.book_id,
                        (
                            f"historical claim {claim_code} does not appear in "
                            "that book's consumed assets"
                        ),
                        claim_code,
                    )
                )

        for asset_code in prior.assets_consumed:
            prior_consumer = all_consumed_by.get(asset_code)
            if asset_code not in recurring_at_acceptance and prior_consumer is not None:
                findings.append(
                    _finding(
                        "SERIES.PRIOR_ASSET.REUSED_CONSUMED",
                        "BLOCKING",
                        "ASSET",
                        "ASSET",
                        current_book_id,
                        prior.book_id,
                        (
                            f"historical one-use asset {asset_code} was already "
                            f"consumed by {prior_consumer}"
                        ),
                        asset_code,
                    )
                )
            reserving_book = reserved_by.get(asset_code)
            if reserving_book is not None and asset_code not in prior_claims:
                findings.append(
                    _finding(
                        "SERIES.PRIOR_ASSET.RESERVATION_NOT_CLAIMED",
                        "BLOCKING",
                        "ASSET",
                        "ASSET",
                        current_book_id,
                        prior.book_id,
                        (
                            f"historical asset {asset_code} was reserved by "
                            f"{reserving_book} but consumed without claim"
                        ),
                        asset_code,
                    )
                )
            all_consumed_by.setdefault(asset_code, prior.book_id)
            if asset_code not in recurring_at_acceptance:
                one_use_consumed_by.setdefault(asset_code, prior.book_id)
            reserved_by.pop(asset_code, None)

        for asset_code in prior.assets_reserved:
            if asset_code in recurring_at_acceptance:
                findings.append(
                    _finding(
                        "SERIES.PRIOR_ASSET.RESERVE_RECURRING_SIGNATURE",
                        "BLOCKING",
                        "ASSET",
                        "ASSET",
                        current_book_id,
                        prior.book_id,
                        (
                            f"historical recurring signature {asset_code} was "
                            "incorrectly reserved as one-use asset"
                        ),
                        asset_code,
                    )
                )
                continue
            if asset_code in all_consumed_by:
                findings.append(
                    _finding(
                        "SERIES.PRIOR_ASSET.RESERVE_ALREADY_CONSUMED",
                        "BLOCKING",
                        "ASSET",
                        "ASSET",
                        current_book_id,
                        prior.book_id,
                        (
                            f"historical reservation {asset_code} occurs after "
                            "the asset was already consumed"
                        ),
                        asset_code,
                    )
                )
            prior_reserver = reserved_by.get(asset_code)
            if prior_reserver is not None:
                findings.append(
                    _finding(
                        "SERIES.PRIOR_ASSET.RESERVE_DUPLICATE",
                        "BLOCKING",
                        "ASSET",
                        "ASSET",
                        current_book_id,
                        prior.book_id,
                        (f"historical asset {asset_code} was already reserved by {prior_reserver}"),
                        asset_code,
                    )
                )
            else:
                reserved_by[asset_code] = prior.book_id

    return all_consumed_by, one_use_consumed_by, reserved_by


def _check_assets(
    *,
    profile: SeriesProfileSnapshot,
    current: MysteryBookPassport,
    prior_passports: tuple[AcceptedBookPassport, ...],
    findings: list[SeriesCollisionFinding],
) -> None:
    recurring = set(profile.allowed_recurring_asset_codes)
    all_consumed_by, one_use_consumed_by, reserved_by = _prior_asset_ledger(
        current_book_id=current.book_id,
        prior_passports=prior_passports,
        findings=findings,
    )

    claimed = set(current.reservation_claim_codes)
    consumed = set(current.assets_consumed)
    reserved = set(current.assets_reserved)

    for claim_code in sorted(claimed):
        if claim_code not in reserved_by:
            findings.append(
                _finding(
                    "SERIES.ASSET.CLAIM_UNKNOWN_RESERVATION",
                    "BLOCKING",
                    "ASSET",
                    "ASSET",
                    current.book_id,
                    None,
                    f"reservation claim {claim_code} has no prior reservation",
                    claim_code,
                )
            )
        if claim_code not in consumed:
            findings.append(
                _finding(
                    "SERIES.ASSET.CLAIM_NOT_CONSUMED",
                    "BLOCKING",
                    "ASSET",
                    "ASSET",
                    current.book_id,
                    None,
                    (f"reservation claim {claim_code} must appear in assets_consumed"),
                    claim_code,
                )
            )

    for asset_code in sorted(consumed):
        prior_one_use_consumer = one_use_consumed_by.get(asset_code)
        if prior_one_use_consumer is not None:
            findings.append(
                _finding(
                    "SERIES.ASSET.REUSED_ONE_USE",
                    "BLOCKING",
                    "ASSET",
                    "ASSET",
                    current.book_id,
                    prior_one_use_consumer,
                    (
                        f"asset {asset_code} was accepted historically as one-use "
                        "and cannot be reclassified into a recurring signature"
                    ),
                    asset_code,
                )
            )
        reserving_book = reserved_by.get(asset_code)
        if reserving_book is not None and asset_code not in claimed:
            findings.append(
                _finding(
                    "SERIES.ASSET.RESERVATION_NOT_CLAIMED",
                    "BLOCKING",
                    "ASSET",
                    "ASSET",
                    current.book_id,
                    reserving_book,
                    (
                        f"reserved asset {asset_code} is consumed without an "
                        "explicit reservation claim"
                    ),
                    asset_code,
                )
            )
        if asset_code in recurring:
            continue
        prior_consumer = all_consumed_by.get(asset_code)
        if prior_consumer is not None and prior_one_use_consumer is None:
            findings.append(
                _finding(
                    "SERIES.ASSET.REUSED_AFTER_SIGNATURE_REMOVAL",
                    "BLOCKING",
                    "ASSET",
                    "ASSET",
                    current.book_id,
                    prior_consumer,
                    (
                        f"asset {asset_code} recurred historically but is no longer "
                        "allowed as a recurring signature in the current profile"
                    ),
                    asset_code,
                )
            )

    for asset_code in sorted(reserved):
        if asset_code in recurring:
            findings.append(
                _finding(
                    "SERIES.ASSET.RESERVE_RECURRING_SIGNATURE",
                    "BLOCKING",
                    "ASSET",
                    "ASSET",
                    current.book_id,
                    None,
                    (
                        f"recurring series signature {asset_code} must not be "
                        "reserved as a one-use future asset"
                    ),
                    asset_code,
                )
            )
        if asset_code in all_consumed_by:
            findings.append(
                _finding(
                    "SERIES.ASSET.RESERVE_ALREADY_CONSUMED",
                    "BLOCKING",
                    "ASSET",
                    "ASSET",
                    current.book_id,
                    all_consumed_by[asset_code],
                    f"cannot reserve already consumed asset {asset_code}",
                    asset_code,
                )
            )
        if asset_code in reserved_by:
            findings.append(
                _finding(
                    "SERIES.ASSET.RESERVE_DUPLICATE",
                    "BLOCKING",
                    "ASSET",
                    "ASSET",
                    current.book_id,
                    reserved_by[asset_code],
                    f"asset {asset_code} is already reserved",
                    asset_code,
                )
            )


def _validate_semantic_evidence(
    *,
    current: MysteryBookPassport,
    prior_passports: tuple[AcceptedBookPassport, ...],
    policy: SeriesCollisionPolicy,
    context_ref: str,
    writer_executor_identity: str,
    semantic_evidence: tuple[SeriesSemanticCollisionEvidence, ...],
    verified_evaluations: Mapping[str, VerifiedEvaluationArtifact],
    verified_human_disposition_refs: frozenset[str],
    findings: list[SeriesCollisionFinding],
) -> None:
    prior_ids = {accepted.passport.book_id for accepted in prior_passports}
    required_dimensions = set(policy.semantic_required_dimensions)
    evidence_by_key: dict[tuple[str, str], SeriesSemanticCollisionEvidence] = {}

    for evidence in semantic_evidence:
        if evidence.current_book_id != current.book_id:
            findings.append(
                _finding(
                    "SERIES.SEMANTIC.CURRENT_BOOK_MISMATCH",
                    "BLOCKING",
                    "SEMANTIC",
                    evidence.dimension,
                    current.book_id,
                    evidence.prior_book_id,
                    "semantic collision evidence belongs to another current book",
                    evidence.evaluation_ref,
                )
            )
        if evidence.prior_book_id not in prior_ids:
            findings.append(
                _finding(
                    "SERIES.SEMANTIC.PRIOR_BOOK_UNKNOWN",
                    "BLOCKING",
                    "SEMANTIC",
                    evidence.dimension,
                    current.book_id,
                    evidence.prior_book_id,
                    "semantic collision evidence references unknown prior book",
                    evidence.evaluation_ref,
                )
            )
        if evidence.dimension not in _VALID_DIMENSIONS:
            findings.append(
                _finding(
                    "SERIES.SEMANTIC.DIMENSION_UNKNOWN",
                    "BLOCKING",
                    "SEMANTIC",
                    str(evidence.dimension),
                    current.book_id,
                    evidence.prior_book_id,
                    f"unknown semantic collision dimension {evidence.dimension}",
                    evidence.evaluation_ref,
                )
            )
        if evidence.state not in _VALID_SEMANTIC_STATES:
            findings.append(
                _finding(
                    "SERIES.SEMANTIC.STATE_UNKNOWN",
                    "BLOCKING",
                    "SEMANTIC",
                    evidence.dimension,
                    current.book_id,
                    evidence.prior_book_id,
                    f"unknown semantic collision state {evidence.state}",
                    evidence.evaluation_ref,
                )
            )
        if evidence.evaluator_class not in _VALID_EVALUATOR_CLASSES:
            findings.append(
                _finding(
                    "SERIES.SEMANTIC.EVALUATOR_CLASS_UNKNOWN",
                    "BLOCKING",
                    "SEMANTIC",
                    evidence.dimension,
                    current.book_id,
                    evidence.prior_book_id,
                    "semantic evaluator class is unknown",
                    evidence.evaluation_ref,
                )
            )
        elif evidence.evaluator_class == "DETERMINISTIC":
            findings.append(
                _finding(
                    "SERIES.SEMANTIC.DETERMINISTIC_EVALUATOR_INVALID",
                    "BLOCKING",
                    "SEMANTIC",
                    evidence.dimension,
                    current.book_id,
                    evidence.prior_book_id,
                    "semantic collision evidence requires a semantic/human evaluator",
                    evidence.evaluation_ref,
                )
            )
        if evidence.independence_state not in _VALID_INDEPENDENCE:
            findings.append(
                _finding(
                    "SERIES.SEMANTIC.INDEPENDENCE_UNKNOWN",
                    "BLOCKING",
                    "SEMANTIC",
                    evidence.dimension,
                    current.book_id,
                    evidence.prior_book_id,
                    "semantic independence state is unknown",
                    evidence.evaluation_ref,
                )
            )
        elif policy.require_semantic_independence and evidence.independence_state != "INDEPENDENT":
            findings.append(
                _finding(
                    "SERIES.SEMANTIC.NOT_INDEPENDENT",
                    "BLOCKING",
                    "SEMANTIC",
                    evidence.dimension,
                    current.book_id,
                    evidence.prior_book_id,
                    "semantic collision evidence must be independent",
                    evidence.evaluation_ref,
                )
            )

        key = (evidence.prior_book_id, evidence.dimension)
        if key in evidence_by_key:
            findings.append(
                _finding(
                    "SERIES.SEMANTIC.DUPLICATE_EVIDENCE",
                    "BLOCKING",
                    "SEMANTIC",
                    evidence.dimension,
                    current.book_id,
                    evidence.prior_book_id,
                    "duplicate semantic collision evidence for pair/dimension",
                    evidence.evaluation_ref,
                )
            )
        else:
            evidence_by_key[key] = evidence

        if (
            policy.require_semantic_independence
            and evidence.evaluator_identity == writer_executor_identity
        ):
            findings.append(
                _finding(
                    "SERIES.SEMANTIC.SAME_WRITER_EXECUTOR",
                    "BLOCKING",
                    "SEMANTIC",
                    evidence.dimension,
                    current.book_id,
                    evidence.prior_book_id,
                    "semantic Series Editor cannot use the Writer executor identity",
                    evidence.evaluation_ref,
                )
            )

        artifact = verified_evaluations.get(evidence.evaluation_ref)
        if artifact is None:
            findings.append(
                _finding(
                    "SERIES.SEMANTIC.ARTIFACT_MISSING",
                    "BLOCKING",
                    "SEMANTIC",
                    evidence.dimension,
                    current.book_id,
                    evidence.prior_book_id,
                    "verified semantic evaluation artifact is missing",
                    evidence.evaluation_ref,
                )
            )
        else:
            expected_purpose = (
                f"SERIES_COLLISION:{current.book_id}:{evidence.prior_book_id}:{evidence.dimension}"
            )
            for code, actual, expected in (
                (
                    "SNAPSHOT_MISMATCH",
                    artifact.manuscript_snapshot_ref,
                    context_ref,
                ),
                (
                    "EVALUATOR_MISMATCH",
                    artifact.evaluator_identity,
                    evidence.evaluator_identity,
                ),
                (
                    "CLASS_MISMATCH",
                    artifact.evaluator_class,
                    evidence.evaluator_class,
                ),
                (
                    "RUBRIC_MISMATCH",
                    artifact.rubric_ref,
                    evidence.rubric_ref,
                ),
                (
                    "PURPOSE_MISMATCH",
                    artifact.purpose,
                    expected_purpose,
                ),
            ):
                if actual != expected:
                    findings.append(
                        _finding(
                            f"SERIES.SEMANTIC.ARTIFACT_{code}",
                            "BLOCKING",
                            "SEMANTIC",
                            evidence.dimension,
                            current.book_id,
                            evidence.prior_book_id,
                            (
                                f"semantic evaluation artifact {code.lower()} "
                                "against declared evidence"
                            ),
                            evidence.evaluation_ref,
                        )
                    )
            if artifact.status != "SUCCEEDED" or not artifact.current:
                findings.append(
                    _finding(
                        "SERIES.SEMANTIC.ARTIFACT_NOT_CURRENT_SUCCESS",
                        "BLOCKING",
                        "SEMANTIC",
                        evidence.dimension,
                        current.book_id,
                        evidence.prior_book_id,
                        "semantic evaluation artifact must be SUCCEEDED/current",
                        evidence.evaluation_ref,
                    )
                )

        if evidence.state == "MATERIAL_COLLISION":
            findings.append(
                _finding(
                    "SERIES.COLLISION.SEMANTIC_BLOCKING",
                    "BLOCKING",
                    "SEMANTIC",
                    evidence.dimension,
                    current.book_id,
                    evidence.prior_book_id,
                    "semantic judge found a material book-to-book collision",
                    evidence.evaluation_ref,
                )
            )
        elif evidence.state == "ATTENTION":
            if policy.attention_requires_human_disposition and (
                evidence.human_disposition_ref is None or not evidence.human_disposition_ref.strip()
            ):
                findings.append(
                    _finding(
                        "SERIES.COLLISION.SEMANTIC_ATTENTION_UNDISPOSED",
                        "MAJOR",
                        "SEMANTIC",
                        evidence.dimension,
                        current.book_id,
                        evidence.prior_book_id,
                        "semantic attention finding requires human disposition",
                        evidence.evaluation_ref,
                    )
                )
            elif (
                policy.attention_requires_human_disposition
                and evidence.human_disposition_ref not in verified_human_disposition_refs
            ):
                findings.append(
                    _finding(
                        "SERIES.COLLISION.SEMANTIC_ATTENTION_UNVERIFIED",
                        "MAJOR",
                        "SEMANTIC",
                        evidence.dimension,
                        current.book_id,
                        evidence.prior_book_id,
                        "semantic attention human disposition is unverified",
                        evidence.evaluation_ref,
                        evidence.human_disposition_ref or "",
                    )
                )

    for prior_book_id in sorted(prior_ids):
        for dimension in sorted(required_dimensions):
            if (prior_book_id, dimension) not in evidence_by_key:
                findings.append(
                    _finding(
                        "SERIES.SEMANTIC.REQUIRED_EVIDENCE_MISSING",
                        "BLOCKING",
                        "SEMANTIC",
                        dimension,
                        current.book_id,
                        prior_book_id,
                        (
                            "required semantic collision evidence is missing for "
                            "prior book/dimension"
                        ),
                    )
                )


def evaluate_series_uniqueness(
    *,
    profile: SeriesProfileSnapshot,
    current_profile: SeriesProfileSnapshot,
    current_passport: MysteryBookPassport,
    prior_passports: tuple[AcceptedBookPassport, ...],
    policy: SeriesCollisionPolicy,
    writer_executor_identity: str,
    semantic_evidence: tuple[SeriesSemanticCollisionEvidence, ...],
    verified_evaluations: Mapping[str, VerifiedEvaluationArtifact],
    verified_human_disposition_refs: frozenset[str] = frozenset(),
) -> SeriesUniquenessResult:
    findings: list[SeriesCollisionFinding] = []
    expected_profile_ref = series_profile_ref(profile)

    _validate_profile(
        profile=profile,
        current_profile=current_profile,
        findings=findings,
        current_book_id=current_passport.book_id,
    )
    _validate_policy(
        policy=policy,
        current_book_id=current_passport.book_id,
        findings=findings,
    )
    _validate_passport_shape(
        passport=current_passport,
        expected_series_profile_id=profile.profile_id,
        expected_series_profile_ref=expected_profile_ref,
        findings=findings,
    )
    _validate_prior_passports(
        prior_passports=prior_passports,
        expected_series_profile_id=profile.profile_id,
        current_book_id=current_passport.book_id,
        current_book_number=current_passport.book_number,
        findings=findings,
    )

    if not writer_executor_identity.strip():
        findings.append(
            _finding(
                "SERIES.WRITER_IDENTITY_MISSING",
                "BLOCKING",
                "SEMANTIC",
                "WRITER",
                current_passport.book_id,
                None,
                "Writer executor identity is required for semantic independence",
            )
        )

    context_ref = series_context_ref(
        profile=profile,
        current_passport=current_passport,
        prior_passports=prior_passports,
        policy=policy,
        writer_executor_identity=writer_executor_identity,
    )

    _check_exact_collisions(
        current=current_passport,
        prior_passports=prior_passports,
        policy=policy,
        findings=findings,
    )
    _check_assets(
        profile=profile,
        current=current_passport,
        prior_passports=prior_passports,
        findings=findings,
    )

    if (
        policy.require_standalone_case_resolution
        and not profile.strongly_serialized
        and not current_passport.primary_case_resolved
    ):
        findings.append(
            _finding(
                "SERIES.STANDALONE.PRIMARY_CASE_UNRESOLVED",
                "BLOCKING",
                "EXACT",
                "ENDING_STATE",
                current_passport.book_id,
                None,
                "series policy requires each volume to resolve its primary case",
            )
        )
    if (
        current_passport.book_number > 1
        and not profile.strongly_serialized
        and (
            current_passport.late_entry_orientation_ref is None
            or not current_passport.late_entry_orientation_ref.strip()
        )
    ):
        findings.append(
            _finding(
                "SERIES.STANDALONE.LATE_ENTRY_ORIENTATION_MISSING",
                "MAJOR",
                "EXACT",
                "SERIES_DEPENDENCY",
                current_passport.book_id,
                None,
                ("later standalone-friendly volume requires a bounded late-entry orientation ref"),
            )
        )

    _validate_semantic_evidence(
        current=current_passport,
        prior_passports=prior_passports,
        policy=policy,
        context_ref=context_ref,
        writer_executor_identity=writer_executor_identity,
        semantic_evidence=semantic_evidence,
        verified_evaluations=verified_evaluations,
        verified_human_disposition_refs=verified_human_disposition_refs,
        findings=findings,
    )

    final_brain_ref = series_brain_ref(
        context_ref=context_ref,
        semantic_evidence=semantic_evidence,
    )
    blockers = [finding for finding in findings if finding.severity in {"BLOCKING", "MAJOR"}]
    return SeriesUniquenessResult(
        qualified=not blockers,
        series_brain_ref=final_brain_ref,
        current_passport_ref=passport_ref(current_passport),
        findings=tuple(findings),
    )


def verify_series_uniqueness(
    *,
    prior_series_brain_ref: str,
    profile: SeriesProfileSnapshot,
    current_profile: SeriesProfileSnapshot,
    current_passport: MysteryBookPassport,
    prior_passports: tuple[AcceptedBookPassport, ...],
    policy: SeriesCollisionPolicy,
    writer_executor_identity: str,
    semantic_evidence: tuple[SeriesSemanticCollisionEvidence, ...],
    verified_evaluations: Mapping[str, VerifiedEvaluationArtifact],
    verified_human_disposition_refs: frozenset[str] = frozenset(),
) -> SeriesUniquenessVerification:
    current = evaluate_series_uniqueness(
        profile=profile,
        current_profile=current_profile,
        current_passport=current_passport,
        prior_passports=prior_passports,
        policy=policy,
        writer_executor_identity=writer_executor_identity,
        semantic_evidence=semantic_evidence,
        verified_evaluations=verified_evaluations,
        verified_human_disposition_refs=verified_human_disposition_refs,
    )
    if not current.qualified:
        return SeriesUniquenessVerification(
            valid=False,
            reason="CURRENT_SERIES_UNIQUENESS_BLOCKED",
            current_result=current,
        )
    if current.series_brain_ref != prior_series_brain_ref:
        return SeriesUniquenessVerification(
            valid=False,
            reason="SERIES_BRAIN_SNAPSHOT_CHANGED",
            current_result=current,
        )
    return SeriesUniquenessVerification(
        valid=True,
        reason=None,
        current_result=current,
    )
