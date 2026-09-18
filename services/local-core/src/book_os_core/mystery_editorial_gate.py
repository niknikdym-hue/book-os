from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace
from typing import Literal, TypeAlias

from .authority_types import ActorKind, JSONValue, content_hash
from .mystery_authority import (
    AuthorityDependency,
    MysteryAuthorityGraph,
    MysteryAuthorityRevision,
    create_authority_revision,
    revise_authority,
    transition_authority_status,
)
from .mystery_case_validation import CaseIntegrityResult
from .mystery_narrative_validation import NarrativeValidationResult
from .mystery_research_validation import ResearchLedgerResult, research_entity_id
from .mystery_sample_qualification import SampleQualificationResult

GateStatus: TypeAlias = Literal[
    "NOT_STARTED",
    "DRAFT",
    "BLOCKED",
    "PASS",
    "STALE",
    "HUMAN_REVIEW_REQUIRED",
]
ProductionMode: TypeAlias = Literal["REPRESENTATIVE_SAMPLE", "MASS_DRAFT"]
SceneAdmissionStatus: TypeAlias = Literal["REVIEWED", "APPROVED", "LOCKED"]


@dataclass(frozen=True)
class SceneContract:
    scene_id: str
    viewpoint_character_id: str
    time_ref: str
    location_ref: str
    purpose: str
    entering_state_ref: str
    exiting_state_ref: str
    knowledge_state_ref: str
    state_change_codes: tuple[str, ...]
    mystery_question_refs: tuple[str, ...] = ()
    clue_operation_refs: tuple[str, ...] = ()
    reveal_operation_refs: tuple[str, ...] = ()
    suspect_hypothesis_movement: tuple[str, ...] = ()
    character_relationship_movement: tuple[str, ...] = ()
    tension_source: str = ""
    prohibited_disclosure_fact_ids: tuple[str, ...] = ()
    continuity_constraint_refs: tuple[str, ...] = ()
    required_authority_entity_ids: tuple[str, ...] = ()
    required_research_ids: tuple[str, ...] = ()
    anti_cliche_warning_codes: tuple[str, ...] = ()
    audio_listenability_notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class WritingGatePolicy:
    book_id: str
    story_definition_entity_id: str
    narrative_contract_entity_id: str
    case_solution_entity_id: str
    production_mode: ProductionMode
    extra_required_authority_entity_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class ExternalWritingReadiness:
    unresolved_blocked_cliche_codes: tuple[str, ...] = ()
    anti_cliche_evaluation_ref: str | None = None
    representative_sample_qualified: bool = False
    representative_sample_ref: str | None = None
    writer_qualified: bool = False
    writer_qualification_ref: str | None = None
    provider_execution_requested: bool = False
    execution_route_ref: str | None = None
    execution_authorization_ref: str | None = None
    cost_authorization_ref: str | None = None


def readiness_with_sample_qualification(
    readiness: ExternalWritingReadiness,
    qualification: SampleQualificationResult,
) -> ExternalWritingReadiness:
    """Bind MYS-06 exact qualification evidence into MYS-05 mass-draft readiness."""
    return replace(
        readiness,
        representative_sample_qualified=qualification.representative_sample_qualified,
        representative_sample_ref=(
            qualification.representative_sample_ref
            if qualification.representative_sample_qualified
            else None
        ),
        writer_qualified=qualification.writer_qualified,
        writer_qualification_ref=(
            qualification.writer_qualification_ref if qualification.writer_qualified else None
        ),
    )


@dataclass(frozen=True)
class GateRecord:
    gate_id: str
    status: GateStatus
    authority_refs: tuple[str, ...] = ()
    blocking_findings: tuple[str, ...] = ()
    evaluation_refs: tuple[str, ...] = ()
    human_decision_ref: str | None = None


@dataclass(frozen=True)
class EditorialMachineGateState:
    book_id: str
    current_stage: str
    gates: tuple[GateRecord, ...]
    writing_allowed: bool
    writing_allowed_scope: tuple[str, ...]
    stale_reasons: tuple[str, ...]


@dataclass(frozen=True)
class WritingAdmissionToken:
    admission_id: str
    book_id: str
    scene_id: str
    production_mode: ProductionMode
    scene_revision_ref: str
    dependency_fingerprint: str
    authority_revision_refs: tuple[str, ...]
    evaluation_refs: tuple[str, ...]
    not_after_epoch: int | None = None


@dataclass(frozen=True)
class WritingGateResult:
    state: EditorialMachineGateState
    token: WritingAdmissionToken | None


def _json_strings(values: Iterable[str]) -> list[JSONValue]:
    result: list[JSONValue] = []
    for value in sorted(values):
        result.append(value)
    return result


def _unique_nonempty(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted({value for value in values if value.strip()}))


def scene_contract_entity_id(book_id: str, scene_id: str) -> str:
    return f"scene-contract:{book_id}:{scene_id}"


def scene_contract_payload(contract: SceneContract) -> dict[str, JSONValue]:
    return {
        "scene_id": contract.scene_id,
        "viewpoint_character_id": contract.viewpoint_character_id,
        "time_ref": contract.time_ref,
        "location_ref": contract.location_ref,
        "purpose": contract.purpose,
        "entering_state_ref": contract.entering_state_ref,
        "exiting_state_ref": contract.exiting_state_ref,
        "knowledge_state_ref": contract.knowledge_state_ref,
        "state_change_codes": _json_strings(contract.state_change_codes),
        "mystery_question_refs": _json_strings(contract.mystery_question_refs),
        "clue_operation_refs": _json_strings(contract.clue_operation_refs),
        "reveal_operation_refs": _json_strings(contract.reveal_operation_refs),
        "suspect_hypothesis_movement": _json_strings(contract.suspect_hypothesis_movement),
        "character_relationship_movement": _json_strings(contract.character_relationship_movement),
        "tension_source": contract.tension_source,
        "prohibited_disclosure_fact_ids": _json_strings(contract.prohibited_disclosure_fact_ids),
        "continuity_constraint_refs": _json_strings(contract.continuity_constraint_refs),
        "required_authority_entity_ids": _json_strings(contract.required_authority_entity_ids),
        "required_research_ids": _json_strings(contract.required_research_ids),
        "anti_cliche_warning_codes": _json_strings(contract.anti_cliche_warning_codes),
        "audio_listenability_notes": _json_strings(contract.audio_listenability_notes),
    }


def create_scene_contract_revision(
    *,
    book_id: str,
    contract: SceneContract,
    supersedes_revision_id: str | None = None,
) -> MysteryAuthorityRevision:
    return create_authority_revision(
        entity_id=scene_contract_entity_id(book_id, contract.scene_id),
        kind="SCENE_CONTRACT",
        payload=scene_contract_payload(contract),
        supersedes_revision_id=supersedes_revision_id,
    )


def revise_scene_contract_revision(
    previous: MysteryAuthorityRevision,
    contract: SceneContract,
) -> MysteryAuthorityRevision:
    if previous.kind != "SCENE_CONTRACT":
        raise ValueError("can only revise SCENE_CONTRACT authority")
    return revise_authority(previous, scene_contract_payload(contract))


def transition_scene_contract_status(
    revision: MysteryAuthorityRevision,
    *,
    target_status: Literal["PROPOSED", "REVIEWED", "APPROVED", "LOCKED"],
    actor_kind: ActorKind,
) -> MysteryAuthorityRevision:
    if revision.kind != "SCENE_CONTRACT":
        raise ValueError("revision is not SCENE_CONTRACT authority")
    return transition_authority_status(
        revision,
        target_status=target_status,
        actor_kind=actor_kind,
    )


def _scene_structure_blockers(contract: SceneContract) -> tuple[str, ...]:
    blockers: list[str] = []
    required_text = (
        ("SCENE_ID", contract.scene_id),
        ("VIEWPOINT", contract.viewpoint_character_id),
        ("TIME_REF", contract.time_ref),
        ("LOCATION_REF", contract.location_ref),
        ("PURPOSE", contract.purpose),
        ("ENTERING_STATE", contract.entering_state_ref),
        ("EXITING_STATE", contract.exiting_state_ref),
        ("KNOWLEDGE_STATE", contract.knowledge_state_ref),
        ("TENSION_SOURCE", contract.tension_source),
    )
    for field_name, value in required_text:
        if not value.strip():
            blockers.append(f"SCENE_CONTRACT.{field_name}_MISSING")
    if not _unique_nonempty(contract.state_change_codes):
        blockers.append("SCENE_CONTRACT.STATE_CHANGE_MISSING")
    return tuple(blockers)


def _scene_revision_blockers(
    *,
    graph: MysteryAuthorityGraph,
    policy: WritingGatePolicy,
    contract: SceneContract,
    revision: MysteryAuthorityRevision,
) -> tuple[str, ...]:
    blockers: list[str] = []
    expected_entity_id = scene_contract_entity_id(policy.book_id, contract.scene_id)
    if revision.kind != "SCENE_CONTRACT":
        blockers.append("SCENE_REVISION.WRONG_KIND")
    if revision.entity_id != expected_entity_id:
        blockers.append("SCENE_REVISION.WRONG_ENTITY")
    if revision.revision_hash != content_hash(scene_contract_payload(contract)):
        blockers.append("SCENE_REVISION.HASH_MISMATCH")
    latest = graph.latest(expected_entity_id)
    if latest is None:
        blockers.append("SCENE_REVISION.NOT_REGISTERED")
    elif (
        latest.revision_id != revision.revision_id or latest.revision_hash != revision.revision_hash
    ):
        blockers.append("SCENE_REVISION.NOT_LATEST")
    if revision.status not in {"REVIEWED", "APPROVED", "LOCKED"}:
        blockers.append(f"SCENE_REVISION.STATUS_NOT_ADMISSIBLE:{revision.status}")
    return tuple(blockers)


def _required_upstream_ids(
    policy: WritingGatePolicy,
    contract: SceneContract,
) -> tuple[str, ...]:
    values = (
        policy.story_definition_entity_id,
        policy.narrative_contract_entity_id,
        policy.case_solution_entity_id,
        *policy.extra_required_authority_entity_ids,
        *contract.required_authority_entity_ids,
        *(research_entity_id(research_id) for research_id in contract.required_research_ids),
    )
    return _unique_nonempty(values)


def _dependency_key(binding: AuthorityDependency) -> str:
    return (
        f"{binding.dependent_entity_id}@{binding.dependent_revision_id}->"
        f"{binding.upstream_entity_id}@{binding.upstream_revision_id}"
    )


def _dependency_fingerprint(bindings: tuple[AuthorityDependency, ...]) -> str:
    payload: dict[str, JSONValue] = {
        "dependencies": _json_strings(_dependency_key(binding) for binding in bindings)
    }
    return content_hash(payload)


@dataclass(frozen=True)
class _AuthorityGateEvidence:
    blockers: tuple[str, ...]
    authority_refs: tuple[str, ...]
    dependency_fingerprint: str
    bound_upstream_entity_ids: frozenset[str]


def _authority_gate_evidence(
    *,
    graph: MysteryAuthorityGraph,
    policy: WritingGatePolicy,
    contract: SceneContract,
    revision: MysteryAuthorityRevision,
) -> _AuthorityGateEvidence:
    blockers: list[str] = []
    required_ids = _required_upstream_ids(policy, contract)
    stale = graph.stale_entities()
    bindings = tuple(
        sorted(
            graph.dependencies_for(revision.entity_id),
            key=lambda item: (
                item.upstream_entity_id,
                item.upstream_revision_id,
                item.dependent_revision_id,
            ),
        )
    )
    by_upstream = {binding.upstream_entity_id: binding for binding in bindings}
    authority_refs: set[str] = set()
    bound_ids: set[str] = set()

    for upstream_id in required_ids:
        effective = graph.effective(upstream_id)
        if effective is None:
            blockers.append(f"AUTHORITY.MISSING_EFFECTIVE:{upstream_id}")
            continue
        authority_refs.add(effective.revision_ref)
        if upstream_id in stale:
            blockers.append(f"AUTHORITY.STALE:{upstream_id}")
        binding = by_upstream.get(upstream_id)
        if binding is None:
            blockers.append(f"SCENE_DEPENDENCY.MISSING:{upstream_id}")
            continue
        bound_ids.add(upstream_id)
        if binding.dependent_revision_id != revision.revision_id:
            blockers.append(f"SCENE_DEPENDENCY.WRONG_DEPENDENT_REVISION:{upstream_id}")
        if binding.upstream_revision_id != effective.revision_id:
            blockers.append(f"SCENE_DEPENDENCY.STALE:{upstream_id}")

    for binding in bindings:
        bound_ids.add(binding.upstream_entity_id)
        effective = graph.effective(binding.upstream_entity_id)
        if effective is None:
            blockers.append(f"SCENE_DEPENDENCY.UPSTREAM_NOT_EFFECTIVE:{binding.upstream_entity_id}")
            continue
        authority_refs.add(effective.revision_ref)
        if binding.upstream_entity_id in stale:
            blockers.append(f"AUTHORITY.STALE:{binding.upstream_entity_id}")
        if binding.upstream_revision_id != effective.revision_id:
            blockers.append(f"SCENE_DEPENDENCY.STALE:{binding.upstream_entity_id}")

    return _AuthorityGateEvidence(
        blockers=tuple(sorted(set(blockers))),
        authority_refs=tuple(sorted(authority_refs)),
        dependency_fingerprint=_dependency_fingerprint(bindings),
        bound_upstream_entity_ids=frozenset(bound_ids),
    )


def _finding_ref(prefix: str, findings: Iterable[object]) -> str:
    rows: list[str] = []
    for finding in findings:
        code = getattr(finding, "code", "")
        severity = getattr(finding, "severity", "")
        object_refs = getattr(finding, "object_refs", ())
        rows.append(f"{code}|{severity}|{'/'.join(sorted(object_refs))}")
    payload: dict[str, JSONValue] = {"findings": _json_strings(rows)}
    return f"{prefix}:{content_hash(payload)}"


def _case_gate(case_integrity: CaseIntegrityResult) -> GateRecord:
    blockers = tuple(
        sorted({f"CASE:{finding.code}" for finding in case_integrity.blocking_findings})
    )
    return GateRecord(
        gate_id="CASE_INTEGRITY",
        status="BLOCKED" if blockers else "PASS",
        blocking_findings=blockers,
        evaluation_refs=(_finding_ref("case", case_integrity.findings),),
    )


def _narrative_gate(
    narrative: NarrativeValidationResult,
    *,
    scene_id: str,
) -> GateRecord:
    blockers_set = {f"NARRATIVE:{finding.code}" for finding in narrative.blocking_findings}
    if not any(checkpoint.scene_id == scene_id for checkpoint in narrative.reader_checkpoints):
        blockers_set.add(f"NARRATIVE.SCENE_NOT_EVALUATED:{scene_id}")
    blockers = tuple(sorted(blockers_set))
    rows = [
        *(
            f"{finding.code}|{finding.severity}|{'/'.join(sorted(finding.object_refs))}"
            for finding in narrative.findings
        ),
        *(
            f"reader:{checkpoint.scene_id}:{checkpoint.reader_order}:"
            f"{','.join(sorted(checkpoint.known_fact_ids))}"
            for checkpoint in narrative.reader_checkpoints
        ),
    ]
    payload: dict[str, JSONValue] = {"narrative": _json_strings(rows)}
    return GateRecord(
        gate_id="NARRATIVE_FAIRNESS",
        status="BLOCKED" if blockers else "PASS",
        blocking_findings=blockers,
        evaluation_refs=(f"narrative:{content_hash(payload)}",),
    )


@dataclass(frozen=True)
class _ResearchGateEvidence:
    record: GateRecord
    not_after_epoch: int | None


def _relevant_research_entities(
    *,
    graph: MysteryAuthorityGraph,
    contract: SceneContract,
    scene_revision: MysteryAuthorityRevision,
    authority_evidence: _AuthorityGateEvidence,
) -> frozenset[str]:
    relevant: set[str] = {
        research_entity_id(research_id) for research_id in contract.required_research_ids
    }
    pending = list(authority_evidence.bound_upstream_entity_ids)
    visited: set[str] = set()

    for binding in graph.dependencies_for(scene_revision.entity_id):
        if binding.upstream_entity_id.startswith("fiction-research:"):
            relevant.add(binding.upstream_entity_id)

    while pending:
        entity_id = pending.pop()
        if entity_id in visited:
            continue
        visited.add(entity_id)
        if entity_id.startswith("fiction-research:"):
            relevant.add(entity_id)
            continue
        for binding in graph.effective_dependencies_for(entity_id):
            upstream_id = binding.upstream_entity_id
            if upstream_id.startswith("fiction-research:"):
                relevant.add(upstream_id)
            else:
                pending.append(upstream_id)
    return frozenset(relevant)


def _research_gate(
    *,
    graph: MysteryAuthorityGraph,
    contract: SceneContract,
    scene_revision: MysteryAuthorityRevision,
    authority_evidence: _AuthorityGateEvidence,
    research: ResearchLedgerResult,
    now_epoch: int,
) -> _ResearchGateEvidence:
    required_research_ids = frozenset(contract.required_research_ids)
    relevant_research_entities = _relevant_research_entities(
        graph=graph,
        contract=contract,
        scene_revision=scene_revision,
        authority_evidence=authority_evidence,
    )
    relevant_authorities = authority_evidence.bound_upstream_entity_ids
    blockers: set[str] = set()

    invalid_relevant = research.invalid_research_entity_ids & (
        relevant_research_entities | relevant_authorities
    )
    for entity_id in invalid_relevant:
        blockers.add(f"RESEARCH.INVALID:{entity_id}")

    affected_scope = relevant_authorities | frozenset({scene_revision.entity_id})
    affected = research.affected_authority_entity_ids & affected_scope
    for entity_id in affected:
        blockers.add(f"RESEARCH.AFFECTS_AUTHORITY:{entity_id}")

    snapshot_by_entity = dict(research.evaluation_snapshot_refs_by_entity)
    evaluation_refs: set[str] = set()
    for entity_id in sorted(relevant_research_entities):
        snapshot_ref = snapshot_by_entity.get(entity_id)
        if snapshot_ref is None:
            blockers.add(f"RESEARCH.SNAPSHOT_MISSING:{entity_id}")
        else:
            evaluation_refs.add(snapshot_ref)

    deadlines = dict(research.research_recheck_epochs)
    relevant_deadlines = [
        epoch for entity_id, epoch in deadlines.items() if entity_id in relevant_research_entities
    ]
    not_after_epoch = min(relevant_deadlines) if relevant_deadlines else None
    if not_after_epoch is not None and now_epoch >= not_after_epoch:
        for entity_id, epoch in sorted(deadlines.items()):
            if entity_id in relevant_research_entities and now_epoch >= epoch:
                blockers.add(f"RESEARCH.RECHECK_DUE:{entity_id}:{epoch}")

    relevant_object_refs = required_research_ids | relevant_research_entities
    rows: list[str] = []
    for finding in research.findings:
        if not finding.object_refs or relevant_object_refs.intersection(finding.object_refs):
            rows.append(
                f"{finding.code}|{finding.severity}|{'/'.join(sorted(finding.object_refs))}"
            )
    for entity_id in sorted(invalid_relevant):
        rows.append(f"invalid:{entity_id}")
    for entity_id in sorted(affected):
        rows.append(f"affected:{entity_id}")
    for entity_id in sorted(relevant_research_entities):
        rows.append(f"relevant:{entity_id}")
    if not_after_epoch is not None:
        rows.append(f"not-after:{not_after_epoch}")

    payload: dict[str, JSONValue] = {"research": _json_strings(rows)}
    evaluation_refs.add(f"research:{content_hash(payload)}")
    status: GateStatus
    if blockers and any(code.startswith("RESEARCH.RECHECK_DUE:") for code in blockers):
        status = "STALE"
    else:
        status = "BLOCKED" if blockers else "PASS"
    return _ResearchGateEvidence(
        record=GateRecord(
            gate_id="REALISM_RESEARCH",
            status=status,
            blocking_findings=tuple(sorted(blockers)),
            evaluation_refs=tuple(sorted(evaluation_refs)),
        ),
        not_after_epoch=not_after_epoch,
    )


def _anti_cliche_gate(readiness: ExternalWritingReadiness) -> GateRecord:
    unresolved = _unique_nonempty(readiness.unresolved_blocked_cliche_codes)
    blockers = [f"ANTI_CLICHE.UNRESOLVED:{code}" for code in unresolved]
    evaluation_refs: tuple[str, ...] = ()
    if readiness.anti_cliche_evaluation_ref:
        evaluation_refs = (readiness.anti_cliche_evaluation_ref,)
    else:
        blockers.append("ANTI_CLICHE.EVALUATION_REF_MISSING")
    return GateRecord(
        gate_id="ANTI_CLICHE_EXTERNAL",
        status="BLOCKED" if blockers else "PASS",
        blocking_findings=tuple(blockers),
        evaluation_refs=evaluation_refs,
    )


def _qualification_gate(
    policy: WritingGatePolicy,
    readiness: ExternalWritingReadiness,
) -> GateRecord:
    if policy.production_mode == "REPRESENTATIVE_SAMPLE":
        return GateRecord(
            gate_id="SAMPLE_WRITER_QUALIFICATION",
            status="PASS",
            evaluation_refs=tuple(
                ref
                for ref in (
                    readiness.representative_sample_ref,
                    readiness.writer_qualification_ref,
                )
                if ref
            ),
        )

    blockers: list[str] = []
    refs: list[str] = []
    if not readiness.representative_sample_qualified:
        blockers.append("REPRESENTATIVE_SAMPLE.NOT_QUALIFIED")
    if not readiness.representative_sample_ref:
        blockers.append("REPRESENTATIVE_SAMPLE.REF_MISSING")
    else:
        refs.append(readiness.representative_sample_ref)
    if not readiness.writer_qualified:
        blockers.append("WRITER.NOT_QUALIFIED")
    if not readiness.writer_qualification_ref:
        blockers.append("WRITER.QUALIFICATION_REF_MISSING")
    else:
        refs.append(readiness.writer_qualification_ref)
    return GateRecord(
        gate_id="SAMPLE_WRITER_QUALIFICATION",
        status="BLOCKED" if blockers else "PASS",
        blocking_findings=tuple(blockers),
        evaluation_refs=tuple(refs),
    )


def _execution_gate(readiness: ExternalWritingReadiness) -> GateRecord:
    if not readiness.provider_execution_requested:
        return GateRecord(gate_id="EXECUTION_AUTHORIZATION", status="PASS")

    blockers: list[str] = []
    refs: list[str] = []
    for code, ref in (
        ("EXECUTION.ROUTE_REF_MISSING", readiness.execution_route_ref),
        ("EXECUTION.AUTHORIZATION_REF_MISSING", readiness.execution_authorization_ref),
        ("EXECUTION.COST_AUTHORIZATION_REF_MISSING", readiness.cost_authorization_ref),
    ):
        if not ref:
            blockers.append(code)
        else:
            refs.append(ref)
    return GateRecord(
        gate_id="EXECUTION_AUTHORIZATION",
        status="BLOCKED" if blockers else "PASS",
        blocking_findings=tuple(blockers),
        evaluation_refs=tuple(refs),
    )


def _scene_contract_gate(
    *,
    graph: MysteryAuthorityGraph,
    policy: WritingGatePolicy,
    contract: SceneContract,
    revision: MysteryAuthorityRevision,
) -> GateRecord:
    blockers = (
        *_scene_structure_blockers(contract),
        *_scene_revision_blockers(
            graph=graph,
            policy=policy,
            contract=contract,
            revision=revision,
        ),
    )
    status: GateStatus = "BLOCKED" if blockers else "PASS"
    return GateRecord(
        gate_id="SCENE_CONTRACT",
        status=status,
        authority_refs=(revision.revision_ref,),
        blocking_findings=tuple(sorted(set(blockers))),
    )


def _authority_gate(evidence: _AuthorityGateEvidence) -> GateRecord:
    return GateRecord(
        gate_id="AUTHORITY_FRESHNESS",
        status="BLOCKED" if evidence.blockers else "PASS",
        authority_refs=evidence.authority_refs,
        blocking_findings=evidence.blockers,
        evaluation_refs=(f"dependencies:{evidence.dependency_fingerprint}",),
    )


def _admission_token(
    *,
    policy: WritingGatePolicy,
    contract: SceneContract,
    revision: MysteryAuthorityRevision,
    authority_evidence: _AuthorityGateEvidence,
    gates: tuple[GateRecord, ...],
    not_after_epoch: int | None,
) -> WritingAdmissionToken:
    evaluation_refs = tuple(sorted({ref for gate in gates for ref in gate.evaluation_refs}))
    authority_refs = tuple(
        sorted(
            {
                revision.revision_ref,
                *authority_evidence.authority_refs,
            }
        )
    )
    payload: dict[str, JSONValue] = {
        "book_id": policy.book_id,
        "scene_id": contract.scene_id,
        "production_mode": policy.production_mode,
        "scene_revision_ref": revision.revision_ref,
        "dependency_fingerprint": authority_evidence.dependency_fingerprint,
        "authority_refs": _json_strings(authority_refs),
        "evaluation_refs": _json_strings(evaluation_refs),
        "not_after_epoch": not_after_epoch,
    }
    return WritingAdmissionToken(
        admission_id=f"writing-admission:{content_hash(payload)}",
        book_id=policy.book_id,
        scene_id=contract.scene_id,
        production_mode=policy.production_mode,
        scene_revision_ref=revision.revision_ref,
        dependency_fingerprint=authority_evidence.dependency_fingerprint,
        authority_revision_refs=authority_refs,
        evaluation_refs=evaluation_refs,
        not_after_epoch=not_after_epoch,
    )


def evaluate_scene_writing_gate(
    *,
    graph: MysteryAuthorityGraph,
    policy: WritingGatePolicy,
    contract: SceneContract,
    scene_revision: MysteryAuthorityRevision,
    case_integrity: CaseIntegrityResult,
    narrative_validation: NarrativeValidationResult,
    research_ledger: ResearchLedgerResult,
    readiness: ExternalWritingReadiness,
    now_epoch: int,
) -> WritingGateResult:
    """Compose MYS-01..04 plus external future-gate evidence into scene admission."""
    scene_gate = _scene_contract_gate(
        graph=graph,
        policy=policy,
        contract=contract,
        revision=scene_revision,
    )
    authority_evidence = _authority_gate_evidence(
        graph=graph,
        policy=policy,
        contract=contract,
        revision=scene_revision,
    )
    authority_gate = _authority_gate(authority_evidence)
    case_gate = _case_gate(case_integrity)
    narrative_gate = _narrative_gate(
        narrative_validation,
        scene_id=contract.scene_id,
    )
    research_evidence = _research_gate(
        graph=graph,
        contract=contract,
        scene_revision=scene_revision,
        authority_evidence=authority_evidence,
        research=research_ledger,
        now_epoch=now_epoch,
    )
    research_gate = research_evidence.record
    anti_cliche_gate = _anti_cliche_gate(readiness)
    qualification_gate = _qualification_gate(policy, readiness)
    execution_gate = _execution_gate(readiness)

    gates = (
        scene_gate,
        authority_gate,
        case_gate,
        narrative_gate,
        research_gate,
        anti_cliche_gate,
        qualification_gate,
        execution_gate,
    )
    blockers = tuple(sorted({blocker for gate in gates for blocker in gate.blocking_findings}))
    writing_allowed = not blockers
    token = (
        _admission_token(
            policy=policy,
            contract=contract,
            revision=scene_revision,
            authority_evidence=authority_evidence,
            gates=gates,
            not_after_epoch=research_evidence.not_after_epoch,
        )
        if writing_allowed
        else None
    )
    state = EditorialMachineGateState(
        book_id=policy.book_id,
        current_stage="WRITING_ADMISSION",
        gates=gates,
        writing_allowed=writing_allowed,
        writing_allowed_scope=(contract.scene_id,) if writing_allowed else (),
        stale_reasons=tuple(
            blocker
            for blocker in blockers
            if ("STALE" in blocker or "RECHECK_DUE" in blocker or "EXPIRED" in blocker)
        ),
    )
    return WritingGateResult(state=state, token=token)


@dataclass(frozen=True)
class WritingTokenVerification:
    valid: bool
    reason: str | None
    current_result: WritingGateResult


def verify_writing_admission_token(
    token: WritingAdmissionToken,
    *,
    graph: MysteryAuthorityGraph,
    policy: WritingGatePolicy,
    contract: SceneContract,
    scene_revision: MysteryAuthorityRevision,
    case_integrity: CaseIntegrityResult,
    narrative_validation: NarrativeValidationResult,
    research_ledger: ResearchLedgerResult,
    readiness: ExternalWritingReadiness,
    now_epoch: int,
) -> WritingTokenVerification:
    """Re-run the gate immediately before Writer/provider access."""
    current = evaluate_scene_writing_gate(
        graph=graph,
        policy=policy,
        contract=contract,
        scene_revision=scene_revision,
        case_integrity=case_integrity,
        narrative_validation=narrative_validation,
        research_ledger=research_ledger,
        readiness=readiness,
        now_epoch=now_epoch,
    )
    if not current.state.writing_allowed or current.token is None:
        return WritingTokenVerification(
            valid=False,
            reason="CURRENT_GATE_BLOCKED",
            current_result=current,
        )
    if current.token.admission_id != token.admission_id:
        return WritingTokenVerification(
            valid=False,
            reason="ADMISSION_SNAPSHOT_CHANGED",
            current_result=current,
        )
    return WritingTokenVerification(valid=True, reason=None, current_result=current)
