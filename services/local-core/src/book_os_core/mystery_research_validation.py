from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, TypeAlias

from .authority_types import (
    ActorKind,
    AuthorityStatus,
    InvalidAuthorityOperation,
    JSONValue,
    content_hash,
)
from .mystery_authority import (
    MysteryAuthorityGraph,
    MysteryAuthorityRevision,
    create_authority_revision,
    revise_authority,
    transition_authority_status,
)
from .research import EvidenceRelationship, EvidenceStrength

ResearchRiskClass: TypeAlias = Literal["R0", "R1", "R2", "R3", "R4"]
ResearchDisposition: TypeAlias = Literal[
    "VERIFIED", "QUALIFIED", "FICTIONALIZED", "RESEARCH_NEEDED", "REJECTED"
]
ResearchConfidence: TypeAlias = Literal["UNKNOWN", "LOW", "MEDIUM", "HIGH"]
ResearchContextScope: TypeAlias = Literal[
    "GLOBAL_OR_SELF_CONTAINED",
    "JURISDICTION",
    "TIME_PERIOD",
    "JURISDICTION_AND_TIME",
]
FreshnessMode: TypeAlias = Literal["STABLE", "VALID_UNTIL", "RECHECK_REQUIRED"]
ExpertReviewState: TypeAlias = Literal["NOT_NEEDED", "RECOMMENDED", "REQUIRED", "COMPLETED"]
SourceAccessStatus: TypeAlias = Literal[
    "METADATA_ONLY", "ABSTRACT_AVAILABLE", "FULL_SOURCE_INSPECTED"
]
PrimarySecondary: TypeAlias = Literal["PRIMARY", "SECONDARY", "UNCLASSIFIED"]
ResearchSeverity: TypeAlias = Literal["BLOCKING", "MAJOR", "MINOR", "NOTE"]


@dataclass(frozen=True)
class SharedResearchEvidence:
    """Read-only projection of BOOK OS shared Source/Evidence primitives."""

    evidence_ref: str
    source_ref: str
    relationship: EvidenceRelationship
    strength: EvidenceStrength
    source_access_status: SourceAccessStatus
    primary_secondary: PrimarySecondary = "UNCLASSIFIED"
    active: bool = True


@dataclass(frozen=True)
class FictionResearchItem:
    """Versionable conclusion used by fiction authority.

    Source/evidence bytes remain in the shared BOOK OS research subsystem. This object
    stores only the editorial conclusion and exact shared refs consumed by the story.
    """

    research_id: str
    question: str
    risk_class: ResearchRiskClass
    domain: str
    disposition: ResearchDisposition
    confidence: ResearchConfidence = "UNKNOWN"
    context_scope: ResearchContextScope = "GLOBAL_OR_SELF_CONTAINED"
    jurisdiction: str | None = None
    time_period: str | None = None
    assumed_answer: str | None = None
    source_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    contradiction_resolution: str | None = None
    intentional_fictionalization: bool = False
    real_world_baseline: str | None = None
    fictionalization_rationale: str | None = None
    fictionalization_decision_ref: str | None = None
    logic_safe_under_qualification: bool = False
    freshness_mode: FreshnessMode = "STABLE"
    fresh_until_epoch: int | None = None
    expert_review: ExpertReviewState = "NOT_NEEDED"
    risk_review_ref: str | None = None


@dataclass(frozen=True)
class ResearchFinding:
    code: str
    severity: ResearchSeverity
    message: str
    object_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResearchValidationResult:
    findings: tuple[ResearchFinding, ...]

    @property
    def blocking_findings(self) -> tuple[ResearchFinding, ...]:
        return tuple(finding for finding in self.findings if finding.severity == "BLOCKING")

    @property
    def passed(self) -> bool:
        return not self.blocking_findings


@dataclass(frozen=True)
class ResearchLedgerResult:
    findings: tuple[ResearchFinding, ...]
    invalid_research_entity_ids: frozenset[str]
    affected_authority_entity_ids: frozenset[str]

    @property
    def passed(self) -> bool:
        return not self.invalid_research_entity_ids and not self.affected_authority_entity_ids


def _finding(
    code: str,
    message: str,
    *object_refs: str,
    severity: ResearchSeverity = "BLOCKING",
) -> ResearchFinding:
    return ResearchFinding(
        code=code,
        severity=severity,
        message=message,
        object_refs=tuple(object_refs),
    )


def research_entity_id(research_id: str) -> str:
    return f"fiction-research:{research_id}"


def _json_string_list(values: tuple[str, ...]) -> list[JSONValue]:
    result: list[JSONValue] = []
    for value in sorted(values):
        result.append(value)
    return result


def research_item_payload(item: FictionResearchItem) -> dict[str, JSONValue]:
    """Canonical authority payload; shared evidence content is referenced, not copied."""
    return {
        "research_id": item.research_id,
        "question": item.question,
        "risk_class": item.risk_class,
        "domain": item.domain,
        "disposition": item.disposition,
        "confidence": item.confidence,
        "context_scope": item.context_scope,
        "jurisdiction": item.jurisdiction,
        "time_period": item.time_period,
        "assumed_answer": item.assumed_answer,
        "source_refs": _json_string_list(item.source_refs),
        "evidence_refs": _json_string_list(item.evidence_refs),
        "limitations": _json_string_list(item.limitations),
        "contradiction_resolution": item.contradiction_resolution,
        "intentional_fictionalization": item.intentional_fictionalization,
        "real_world_baseline": item.real_world_baseline,
        "fictionalization_rationale": item.fictionalization_rationale,
        "fictionalization_decision_ref": item.fictionalization_decision_ref,
        "logic_safe_under_qualification": item.logic_safe_under_qualification,
        "freshness_mode": item.freshness_mode,
        "fresh_until_epoch": item.fresh_until_epoch,
        "expert_review": item.expert_review,
        "risk_review_ref": item.risk_review_ref,
    }


def _unresolved_severity(risk_class: ResearchRiskClass) -> ResearchSeverity:
    if risk_class == "R0":
        return "NOTE"
    if risk_class == "R1":
        return "MAJOR"
    return "BLOCKING"


def _validate_context(item: FictionResearchItem, findings: list[ResearchFinding]) -> None:
    if item.context_scope in {"JURISDICTION", "JURISDICTION_AND_TIME"}:
        if item.jurisdiction is None or not item.jurisdiction.strip():
            findings.append(
                _finding(
                    "RESEARCH.CONTEXT.JURISDICTION_MISSING",
                    (
                        f"research {item.research_id} requires jurisdiction context "
                        f"under {item.context_scope}"
                    ),
                    item.research_id,
                )
            )
    if item.context_scope in {"TIME_PERIOD", "JURISDICTION_AND_TIME"}:
        if item.time_period is None or not item.time_period.strip():
            findings.append(
                _finding(
                    "RESEARCH.CONTEXT.TIME_PERIOD_MISSING",
                    (
                        f"research {item.research_id} requires time-period context "
                        f"under {item.context_scope}"
                    ),
                    item.research_id,
                )
            )


def _validate_disposition(item: FictionResearchItem, findings: list[ResearchFinding]) -> None:
    if item.disposition == "RESEARCH_NEEDED":
        findings.append(
            _finding(
                "RESEARCH.DISPOSITION.RESEARCH_NEEDED",
                f"research {item.research_id} is unresolved",
                item.research_id,
                severity=_unresolved_severity(item.risk_class),
            )
        )
    elif item.disposition == "REJECTED":
        findings.append(
            _finding(
                "RESEARCH.DISPOSITION.REJECTED",
                f"research {item.research_id} conclusion was rejected",
                item.research_id,
            )
        )
    elif item.disposition == "QUALIFIED":
        if item.assumed_answer is None or not item.assumed_answer.strip():
            findings.append(
                _finding(
                    "RESEARCH.DISPOSITION.ANSWER_MISSING",
                    f"qualified research {item.research_id} has no bounded answer",
                    item.research_id,
                )
            )
        if item.risk_class in {"R3", "R4"}:
            findings.append(
                _finding(
                    "RESEARCH.DISPOSITION.QUALIFIED_PLOT_CRITICAL",
                    (
                        f"{item.risk_class} research {item.research_id} cannot govern "
                        "plot-critical writing while only QUALIFIED"
                    ),
                    item.research_id,
                )
            )
        elif item.risk_class == "R2" and not item.logic_safe_under_qualification:
            findings.append(
                _finding(
                    "RESEARCH.DISPOSITION.R2_UNSAFE_QUALIFICATION",
                    (
                        f"R2 research {item.research_id} is qualified but uncertainty "
                        "is not proven safe for scene/case logic"
                    ),
                    item.research_id,
                )
            )
    elif item.disposition == "VERIFIED":
        if item.risk_class != "R0" and (
            item.assumed_answer is None or not item.assumed_answer.strip()
        ):
            findings.append(
                _finding(
                    "RESEARCH.DISPOSITION.ANSWER_MISSING",
                    f"verified research {item.research_id} has no assumed_answer",
                    item.research_id,
                )
            )


def _validate_fictionalization(item: FictionResearchItem, findings: list[ResearchFinding]) -> None:
    if item.disposition == "FICTIONALIZED":
        if not item.intentional_fictionalization:
            findings.append(
                _finding(
                    "RESEARCH.FICTIONALIZATION.FLAG_MISSING",
                    (
                        f"research {item.research_id} is FICTIONALIZED without "
                        "intentional_fictionalization=True"
                    ),
                    item.research_id,
                )
            )
        if item.fictionalization_rationale is None or not item.fictionalization_rationale.strip():
            findings.append(
                _finding(
                    "RESEARCH.FICTIONALIZATION.RATIONALE_MISSING",
                    f"fictionalized research {item.research_id} has no rationale",
                    item.research_id,
                )
            )
        if (
            item.fictionalization_decision_ref is None
            or not item.fictionalization_decision_ref.strip()
        ):
            findings.append(
                _finding(
                    "RESEARCH.FICTIONALIZATION.DECISION_MISSING",
                    (
                        f"fictionalized research {item.research_id} has no prior "
                        "fictionalization decision ref"
                    ),
                    item.research_id,
                )
            )
        if item.risk_class in {"R2", "R3", "R4"} and (
            item.real_world_baseline is None or not item.real_world_baseline.strip()
        ):
            findings.append(
                _finding(
                    "RESEARCH.FICTIONALIZATION.BASELINE_MISSING",
                    (
                        f"{item.risk_class} fictionalization {item.research_id} requires "
                        "a verified real-world baseline"
                    ),
                    item.research_id,
                )
            )
    elif item.intentional_fictionalization:
        findings.append(
            _finding(
                "RESEARCH.FICTIONALIZATION.DISPOSITION_CONFLICT",
                (
                    f"research {item.research_id} is marked intentional fictionalization "
                    f"but disposition is {item.disposition}"
                ),
                item.research_id,
            )
        )


def _validate_freshness(
    item: FictionResearchItem, *, now_epoch: int, findings: list[ResearchFinding]
) -> None:
    if item.freshness_mode == "RECHECK_REQUIRED":
        findings.append(
            _finding(
                "RESEARCH.FRESHNESS.RECHECK_REQUIRED",
                f"research {item.research_id} requires re-verification",
                item.research_id,
            )
        )
        return
    if item.freshness_mode == "VALID_UNTIL":
        if item.fresh_until_epoch is None:
            findings.append(
                _finding(
                    "RESEARCH.FRESHNESS.DEADLINE_MISSING",
                    f"research {item.research_id} uses VALID_UNTIL without a deadline",
                    item.research_id,
                )
            )
        elif item.fresh_until_epoch <= now_epoch:
            findings.append(
                _finding(
                    "RESEARCH.FRESHNESS.EXPIRED",
                    (
                        f"research {item.research_id} expired at "
                        f"{item.fresh_until_epoch}; now={now_epoch}"
                    ),
                    item.research_id,
                )
            )


def _validate_evidence(
    item: FictionResearchItem,
    *,
    evidence_catalog: Mapping[str, SharedResearchEvidence],
    available_source_refs: frozenset[str] | None,
    findings: list[ResearchFinding],
) -> None:
    if any(not source_ref.strip() for source_ref in item.source_refs):
        findings.append(
            _finding(
                "RESEARCH.SOURCE.EMPTY_REF",
                f"research {item.research_id} contains an empty source ref",
                item.research_id,
            )
        )
    if any(not evidence_ref.strip() for evidence_ref in item.evidence_refs):
        findings.append(
            _finding(
                "RESEARCH.EVIDENCE.EMPTY_REF",
                f"research {item.research_id} contains an empty evidence ref",
                item.research_id,
            )
        )
    if len(set(item.source_refs)) != len(item.source_refs):
        findings.append(
            _finding(
                "RESEARCH.SOURCE.DUPLICATE_REF",
                f"research {item.research_id} contains duplicate source refs",
                item.research_id,
            )
        )
    if len(set(item.evidence_refs)) != len(item.evidence_refs):
        findings.append(
            _finding(
                "RESEARCH.EVIDENCE.DUPLICATE_REF",
                f"research {item.research_id} contains duplicate evidence refs",
                item.research_id,
            )
        )

    if available_source_refs is not None:
        for source_ref in item.source_refs:
            if source_ref not in available_source_refs:
                findings.append(
                    _finding(
                        "RESEARCH.SOURCE.UNKNOWN_REF",
                        (
                            f"research {item.research_id} references unknown shared source "
                            f"{source_ref}"
                        ),
                        item.research_id,
                        source_ref,
                    )
                )

    evidence_rows: list[SharedResearchEvidence] = []
    for evidence_ref in item.evidence_refs:
        evidence = evidence_catalog.get(evidence_ref)
        if evidence is None:
            findings.append(
                _finding(
                    "RESEARCH.EVIDENCE.UNKNOWN_REF",
                    (
                        f"research {item.research_id} references unknown shared evidence "
                        f"{evidence_ref}"
                    ),
                    item.research_id,
                    evidence_ref,
                )
            )
            continue
        evidence_rows.append(evidence)
        if evidence.evidence_ref != evidence_ref:
            findings.append(
                _finding(
                    "RESEARCH.EVIDENCE.CATALOG_ID_MISMATCH",
                    (
                        f"catalog key {evidence_ref} resolves to evidence payload "
                        f"{evidence.evidence_ref}"
                    ),
                    item.research_id,
                    evidence_ref,
                    evidence.evidence_ref,
                )
            )
        if not evidence.active:
            findings.append(
                _finding(
                    "RESEARCH.EVIDENCE.INACTIVE",
                    (
                        f"research {item.research_id} consumes inactive/superseded evidence "
                        f"{evidence_ref}"
                    ),
                    item.research_id,
                    evidence_ref,
                )
            )
        if evidence.source_ref not in item.source_refs:
            findings.append(
                _finding(
                    "RESEARCH.EVIDENCE.SOURCE_NOT_DECLARED",
                    (
                        f"evidence {evidence_ref} belongs to source {evidence.source_ref}, "
                        "which is absent from the research item's source_refs"
                    ),
                    item.research_id,
                    evidence_ref,
                    evidence.source_ref,
                )
            )

    needs_material_evidence = item.risk_class in {"R2", "R3", "R4"} and item.disposition in {
        "VERIFIED",
        "QUALIFIED",
        "FICTIONALIZED",
    }
    if needs_material_evidence and not item.evidence_refs:
        findings.append(
            _finding(
                "RESEARCH.EVIDENCE.MATERIAL_EVIDENCE_MISSING",
                (
                    f"{item.risk_class} research {item.research_id} has no exact shared "
                    "evidence refs"
                ),
                item.research_id,
            )
        )
        return

    active_rows = [row for row in evidence_rows if row.active]
    if needs_material_evidence and active_rows:
        inspected = [
            row for row in active_rows if row.source_access_status == "FULL_SOURCE_INSPECTED"
        ]
        if not inspected:
            findings.append(
                _finding(
                    "RESEARCH.EVIDENCE.FULL_SOURCE_NOT_INSPECTED",
                    (
                        f"material research {item.research_id} has evidence refs but no "
                        "FULL_SOURCE_INSPECTED source"
                    ),
                    item.research_id,
                )
            )

    if item.disposition == "VERIFIED" and item.risk_class in {"R2", "R3", "R4"}:
        supportive = [row for row in active_rows if row.relationship == "SUPPORTS"]
        if not supportive:
            findings.append(
                _finding(
                    "RESEARCH.EVIDENCE.VERIFIED_WITHOUT_SUPPORT",
                    (
                        f"verified {item.risk_class} research {item.research_id} has no "
                        "active SUPPORTS evidence"
                    ),
                    item.research_id,
                )
            )

        contradictions = [row for row in active_rows if row.relationship == "CONTRADICTS"]
        if contradictions and (
            item.contradiction_resolution is None or not item.contradiction_resolution.strip()
        ):
            findings.append(
                _finding(
                    "RESEARCH.EVIDENCE.CONTRADICTION_UNRESOLVED",
                    (
                        f"verified research {item.research_id} has active contradicting "
                        "evidence without an explicit resolution"
                    ),
                    item.research_id,
                    *sorted(row.evidence_ref for row in contradictions),
                )
            )

    if item.risk_class in {"R3", "R4"} and item.disposition in {
        "VERIFIED",
        "FICTIONALIZED",
    }:
        if item.disposition == "VERIFIED":
            strength_rows = [
                row for row in active_rows if row.relationship in {"SUPPORTS", "PARTIALLY_SUPPORTS"}
            ]
        else:
            # Fictionalization evidence establishes the real-world baseline, not the
            # invented story rule, so relationship-to-conclusion is not authoritative.
            strength_rows = [row for row in active_rows if row.relationship != "CONTRADICTS"]
        strong_primary = any(
            row.strength == "STRONG"
            and row.source_access_status == "FULL_SOURCE_INSPECTED"
            and row.primary_secondary == "PRIMARY"
            for row in strength_rows
        )
        independent_full_sources = {
            row.source_ref
            for row in strength_rows
            if row.strength in {"MODERATE", "STRONG"}
            and row.source_access_status == "FULL_SOURCE_INSPECTED"
        }
        if not strong_primary and len(independent_full_sources) < 2:
            findings.append(
                _finding(
                    "RESEARCH.EVIDENCE.PLOT_CRITICAL_STRENGTH_INSUFFICIENT",
                    (
                        f"{item.risk_class} research {item.research_id} requires either "
                        "strong inspected primary evidence or two independent inspected "
                        "material sources"
                    ),
                    item.research_id,
                )
            )


def _validate_risk_review(item: FictionResearchItem, findings: list[ResearchFinding]) -> None:
    if item.expert_review == "REQUIRED" and item.risk_class != "R4":
        findings.append(
            _finding(
                "RESEARCH.EXPERT_REVIEW.REQUIRED_NOT_COMPLETED",
                f"research {item.research_id} requires expert review before use",
                item.research_id,
            )
        )
    elif item.expert_review == "RECOMMENDED":
        findings.append(
            _finding(
                "RESEARCH.EXPERT_REVIEW.RECOMMENDED",
                f"expert review is recommended for research {item.research_id}",
                item.research_id,
                severity="MAJOR",
            )
        )

    if item.risk_class == "R4":
        if item.risk_review_ref is None or not item.risk_review_ref.strip():
            findings.append(
                _finding(
                    "RESEARCH.R4.RISK_REVIEW_MISSING",
                    f"R4 research {item.research_id} has no safety/legal/risk review ref",
                    item.research_id,
                )
            )
        if item.expert_review != "COMPLETED":
            findings.append(
                _finding(
                    "RESEARCH.R4.EXPERT_REVIEW_INCOMPLETE",
                    f"R4 research {item.research_id} requires completed expert review",
                    item.research_id,
                )
            )


def validate_fiction_research_item(
    item: FictionResearchItem,
    *,
    evidence_catalog: Mapping[str, SharedResearchEvidence] | None = None,
    available_source_refs: frozenset[str] | None = None,
    now_epoch: int,
) -> ResearchValidationResult:
    """Validate a fiction realism conclusion against explicit shared evidence refs."""
    findings: list[ResearchFinding] = []
    if not item.research_id.strip():
        findings.append(_finding("RESEARCH.ITEM.EMPTY_ID", "research_id must not be blank"))
    if not item.question.strip():
        findings.append(
            _finding(
                "RESEARCH.ITEM.EMPTY_QUESTION",
                f"research {item.research_id} question must not be blank",
                item.research_id,
            )
        )
    if not item.domain.strip():
        findings.append(
            _finding(
                "RESEARCH.ITEM.EMPTY_DOMAIN",
                f"research {item.research_id} domain must not be blank",
                item.research_id,
            )
        )

    _validate_context(item, findings)
    _validate_disposition(item, findings)
    _validate_fictionalization(item, findings)
    _validate_freshness(item, now_epoch=now_epoch, findings=findings)
    _validate_evidence(
        item,
        evidence_catalog=evidence_catalog or {},
        available_source_refs=available_source_refs,
        findings=findings,
    )
    _validate_risk_review(item, findings)

    if item.disposition == "VERIFIED":
        if item.risk_class in {"R2", "R3", "R4"} and item.confidence in {"UNKNOWN", "LOW"}:
            findings.append(
                _finding(
                    "RESEARCH.CONFIDENCE.TOO_LOW_FOR_VERIFIED",
                    (
                        f"verified {item.risk_class} research {item.research_id} "
                        f"has confidence={item.confidence}"
                    ),
                    item.research_id,
                )
            )
        if item.risk_class in {"R3", "R4"} and item.confidence != "HIGH":
            findings.append(
                _finding(
                    "RESEARCH.CONFIDENCE.PLOT_CRITICAL_NOT_HIGH",
                    (
                        f"verified {item.risk_class} research {item.research_id} "
                        "requires HIGH confidence"
                    ),
                    item.research_id,
                )
            )

    return ResearchValidationResult(findings=tuple(findings))


def create_fiction_research_revision(
    item: FictionResearchItem,
    *,
    supersedes_revision_id: str | None = None,
) -> MysteryAuthorityRevision:
    return create_authority_revision(
        entity_id=research_entity_id(item.research_id),
        kind="FICTION_RESEARCH_ITEM",
        payload=research_item_payload(item),
        supersedes_revision_id=supersedes_revision_id,
    )


def revise_fiction_research_revision(
    previous: MysteryAuthorityRevision,
    item: FictionResearchItem,
) -> MysteryAuthorityRevision:
    if previous.kind != "FICTION_RESEARCH_ITEM":
        raise InvalidAuthorityOperation("can only revise FICTION_RESEARCH_ITEM authority")
    if previous.entity_id != research_entity_id(item.research_id):
        raise InvalidAuthorityOperation(
            "research item identity cannot change across authority revisions"
        )
    return revise_authority(previous, research_item_payload(item))


def _require_revision_matches_item(
    revision: MysteryAuthorityRevision, item: FictionResearchItem
) -> None:
    if revision.kind != "FICTION_RESEARCH_ITEM":
        raise InvalidAuthorityOperation("revision is not FICTION_RESEARCH_ITEM authority")
    if revision.entity_id != research_entity_id(item.research_id):
        raise InvalidAuthorityOperation("research item does not match revision entity_id")
    expected_hash = content_hash(research_item_payload(item))
    if revision.revision_hash != expected_hash:
        raise InvalidAuthorityOperation(
            "research item payload does not match the exact authority revision hash"
        )


def transition_fiction_research_status(
    revision: MysteryAuthorityRevision,
    item: FictionResearchItem,
    *,
    target_status: AuthorityStatus,
    actor_kind: ActorKind,
    evidence_catalog: Mapping[str, SharedResearchEvidence] | None = None,
    available_source_refs: frozenset[str] | None = None,
    now_epoch: int,
) -> MysteryAuthorityRevision:
    """Apply authority transition; acceptance/lock is fail-closed on realism readiness."""
    _require_revision_matches_item(revision, item)
    if target_status in {"APPROVED", "LOCKED"}:
        validation = validate_fiction_research_item(
            item,
            evidence_catalog=evidence_catalog,
            available_source_refs=available_source_refs,
            now_epoch=now_epoch,
        )
        if not validation.passed:
            codes = ",".join(finding.code for finding in validation.blocking_findings)
            raise InvalidAuthorityOperation(
                f"research authority cannot become {target_status}; blockers={codes}"
            )
    return transition_authority_status(
        revision,
        target_status=target_status,
        actor_kind=actor_kind,
    )


def bind_research_dependency(
    graph: MysteryAuthorityGraph,
    *,
    dependent_entity_id: str,
    research_id: str,
    reason: str,
) -> None:
    """Bind a story authority revision to the governing research revision."""
    graph.bind_dependency(
        dependent_entity_id=dependent_entity_id,
        upstream_entity_id=research_entity_id(research_id),
        reason=reason,
    )


def research_affected_authorities(
    graph: MysteryAuthorityGraph,
    invalid_research_entity_ids: frozenset[str],
) -> frozenset[str]:
    """Propagate external research invalidation over effective authority dependencies."""
    reverse_edges: dict[str, set[str]] = defaultdict(set)
    for head in graph.effective_heads():
        for dependency in graph.effective_dependencies_for(head.entity_id):
            reverse_edges[dependency.upstream_entity_id].add(head.entity_id)

    affected: set[str] = set()
    queue: deque[str] = deque(invalid_research_entity_ids)
    visited: set[str] = set(invalid_research_entity_ids)
    while queue:
        upstream = queue.popleft()
        for dependent in reverse_edges.get(upstream, set()):
            if dependent not in visited:
                visited.add(dependent)
                affected.add(dependent)
                queue.append(dependent)
    return frozenset(affected)


def evaluate_research_ledger(
    graph: MysteryAuthorityGraph,
    *,
    items_by_revision_id: Mapping[str, FictionResearchItem],
    evidence_catalog: Mapping[str, SharedResearchEvidence] | None = None,
    available_source_refs: frozenset[str] | None = None,
    now_epoch: int,
) -> ResearchLedgerResult:
    """Evaluate effective research authority plus freshness/evidence external state."""
    findings: list[ResearchFinding] = []
    invalid: set[str] = set()
    catalog = evidence_catalog or {}
    graph_stale = graph.stale_entities()

    for revision in graph.effective_heads():
        if revision.kind != "FICTION_RESEARCH_ITEM":
            continue
        item = items_by_revision_id.get(revision.revision_id)
        if item is None:
            invalid.add(revision.entity_id)
            findings.append(
                _finding(
                    "RESEARCH.LEDGER.ITEM_MISSING",
                    (
                        f"effective research authority {revision.entity_id}@"
                        f"{revision.revision_id} has no exact runtime FictionResearchItem "
                        "projection"
                    ),
                    revision.entity_id,
                    revision.revision_id,
                )
            )
            continue
        expected_hash = content_hash(research_item_payload(item))
        if revision.revision_hash != expected_hash:
            invalid.add(revision.entity_id)
            findings.append(
                _finding(
                    "RESEARCH.LEDGER.REVISION_MISMATCH",
                    (
                        f"runtime research item for {revision.entity_id} does not match "
                        "its effective authority revision"
                    ),
                    revision.entity_id,
                )
            )
            continue

        validation = validate_fiction_research_item(
            item,
            evidence_catalog=catalog,
            available_source_refs=available_source_refs,
            now_epoch=now_epoch,
        )
        findings.extend(validation.findings)
        if not validation.passed or revision.entity_id in graph_stale:
            invalid.add(revision.entity_id)

    affected = research_affected_authorities(graph, frozenset(invalid))
    return ResearchLedgerResult(
        findings=tuple(findings),
        invalid_research_entity_ids=frozenset(invalid),
        affected_authority_entity_ids=affected,
    )
