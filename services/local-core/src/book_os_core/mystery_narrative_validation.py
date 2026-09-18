from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal, TypeAlias

NarrativeMode: TypeAlias = Literal[
    "FIRST_SINGLE",
    "FIRST_MULTI",
    "THIRD_LIMITED_SINGLE",
    "THIRD_LIMITED_MULTI",
    "CONTROLLED_OMNISCIENT",
    "EPISTOLARY_HYBRID",
    "MIXED",
]
GrammaticalPerson: TypeAlias = Literal["FIRST", "THIRD", "MIXED"]
ScenePerson: TypeAlias = Literal["FIRST", "THIRD"]
NarrativeTense: TypeAlias = Literal["PAST", "PRESENT", "MIXED_CONTROLLED"]
SceneTense: TypeAlias = Literal["PAST", "PRESENT"]
ReliabilityMode: TypeAlias = Literal[
    "RELIABLE", "LIMITED", "UNRELIABLE_EXPLICIT", "UNRELIABLE_BOUNDED"
]
CulpritPovPolicy: TypeAlias = Literal[
    "IDENTITY_KNOWN_TO_READER",
    "IDENTITY_CONCEALED_SEMANTICALLY_HONEST",
    "PRE_ACT_CONSCIOUSNESS",
    "FORMALLY_LIMITED_FRAME",
]
NarrativeSeverity: TypeAlias = Literal["BLOCKING", "MAJOR", "MINOR", "NOTE"]


@dataclass(frozen=True)
class ViewpointRule:
    character_id: str
    function: str
    culprit_pov: bool = False
    culprit_pov_policy: CulpritPovPolicy | None = None
    culprit_identity_fact_ids: frozenset[str] = frozenset()
    protected_fact_ids: frozenset[str] = frozenset()


@dataclass(frozen=True)
class NarrativeContractRules:
    narrative_mode: NarrativeMode
    grammatical_person: GrammaticalPerson
    tense: NarrativeTense
    viewpoints: tuple[ViewpointRule, ...]
    reliability_mode: ReliabilityMode = "RELIABLE"
    reliability_source_ref: str | None = None
    unreliable_domain_codes: frozenset[str] = frozenset()
    reliability_signal_refs: frozenset[str] = frozenset()
    allowed_withholding_mechanisms: frozenset[str] = frozenset()
    prohibited_withholding_mechanisms: frozenset[str] = frozenset()
    accepted_narrative_device_refs: frozenset[str] = frozenset()
    allow_viewpointless_scenes: bool = False
    restrict_interior_to_pov: bool = True
    restrict_reader_to_pov_knowledge: bool = True


@dataclass(frozen=True)
class WithholdingDecision:
    fact_id: str
    mechanism_code: str


@dataclass(frozen=True)
class NarrativeSceneState:
    scene_id: str
    reader_order: int
    viewpoint_character_id: str | None
    grammatical_person: ScenePerson
    tense: SceneTense
    pov_known_fact_ids: frozenset[str] = frozenset()
    pov_conscious_fact_ids: frozenset[str] = frozenset()
    externally_observable_fact_ids: frozenset[str] = frozenset()
    reader_exposed_fact_ids: frozenset[str] = frozenset()
    withholding_decisions: tuple[WithholdingDecision, ...] = ()
    interior_access_character_ids: frozenset[str] = frozenset()
    narrative_device_refs: frozenset[str] = frozenset()


@dataclass(frozen=True)
class NarrativeFinding:
    code: str
    severity: NarrativeSeverity
    message: str
    object_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReaderKnowledgeCheckpoint:
    scene_id: str
    reader_order: int
    known_fact_ids: frozenset[str]


@dataclass(frozen=True)
class NarrativeValidationResult:
    findings: tuple[NarrativeFinding, ...]
    reader_checkpoints: tuple[ReaderKnowledgeCheckpoint, ...]

    @property
    def blocking_findings(self) -> tuple[NarrativeFinding, ...]:
        return tuple(
            finding for finding in self.findings if finding.severity == "BLOCKING"
        )

    @property
    def passed(self) -> bool:
        return not self.blocking_findings


def _finding(
    code: str,
    message: str,
    *object_refs: str,
    severity: NarrativeSeverity = "BLOCKING",
) -> NarrativeFinding:
    return NarrativeFinding(
        code=code,
        severity=severity,
        message=message,
        object_refs=tuple(object_refs),
    )


def _validate_contract(
    contract: NarrativeContractRules, findings: list[NarrativeFinding]
) -> dict[str, ViewpointRule]:
    viewpoint_by_id: dict[str, ViewpointRule] = {}
    for viewpoint in contract.viewpoints:
        if not viewpoint.character_id:
            findings.append(
                _finding(
                    "NARRATIVE.CONTRACT.EMPTY_VIEWPOINT",
                    "viewpoint character_id must not be empty",
                )
            )
            continue
        if viewpoint.character_id in viewpoint_by_id:
            findings.append(
                _finding(
                    "NARRATIVE.CONTRACT.DUPLICATE_VIEWPOINT",
                    f"duplicate viewpoint rule for {viewpoint.character_id}",
                    viewpoint.character_id,
                )
            )
            continue
        viewpoint_by_id[viewpoint.character_id] = viewpoint
        if viewpoint.culprit_pov:
            if viewpoint.culprit_pov_policy is None:
                findings.append(
                    _finding(
                        "NARRATIVE.CONTRACT.CULPRIT_POV_POLICY_MISSING",
                        (
                            f"culprit POV {viewpoint.character_id} requires an explicit "
                            "culprit_pov_policy"
                        ),
                        viewpoint.character_id,
                    )
                )
            elif (
                viewpoint.culprit_pov_policy != "PRE_ACT_CONSCIOUSNESS"
                and not viewpoint.culprit_identity_fact_ids
            ):
                findings.append(
                    _finding(
                        "NARRATIVE.CONTRACT.CULPRIT_IDENTITY_FACT_MISSING",
                        (
                            f"culprit POV {viewpoint.character_id} policy "
                            f"{viewpoint.culprit_pov_policy} requires explicit "
                            "culprit_identity_fact_ids"
                        ),
                        viewpoint.character_id,
                    )
                )
        elif viewpoint.culprit_pov_policy is not None or viewpoint.culprit_identity_fact_ids:
            findings.append(
                _finding(
                    "NARRATIVE.CONTRACT.CULPRIT_POLICY_WITHOUT_CULPRIT_POV",
                    (
                        f"viewpoint {viewpoint.character_id} declares culprit-only policy/data "
                        "without culprit_pov=True"
                    ),
                    viewpoint.character_id,
                )
            )

    if contract.narrative_mode in {"FIRST_SINGLE", "THIRD_LIMITED_SINGLE"}:
        if len(viewpoint_by_id) != 1:
            findings.append(
                _finding(
                    "NARRATIVE.CONTRACT.VIEWPOINT_COUNT",
                    (
                        f"{contract.narrative_mode} requires exactly one viewpoint; "
                        f"got {len(viewpoint_by_id)}"
                    ),
                )
            )
    elif contract.narrative_mode in {"FIRST_MULTI", "THIRD_LIMITED_MULTI"}:
        if len(viewpoint_by_id) < 2:
            findings.append(
                _finding(
                    "NARRATIVE.CONTRACT.VIEWPOINT_COUNT",
                    (
                        f"{contract.narrative_mode} requires at least two viewpoints; "
                        f"got {len(viewpoint_by_id)}"
                    ),
                )
            )

    expected_person: GrammaticalPerson | None = None
    if contract.narrative_mode in {"FIRST_SINGLE", "FIRST_MULTI"}:
        expected_person = "FIRST"
    elif contract.narrative_mode in {"THIRD_LIMITED_SINGLE", "THIRD_LIMITED_MULTI"}:
        expected_person = "THIRD"
    if expected_person is not None and contract.grammatical_person != expected_person:
        findings.append(
            _finding(
                "NARRATIVE.CONTRACT.MODE_PERSON_CONFLICT",
                (
                    f"{contract.narrative_mode} requires {expected_person} grammatical person; "
                    f"got {contract.grammatical_person}"
                ),
            )
        )

    policy_overlap = (
        contract.allowed_withholding_mechanisms
        & contract.prohibited_withholding_mechanisms
    )
    if policy_overlap:
        findings.append(
            _finding(
                "NARRATIVE.CONTRACT.WITHHOLDING_POLICY_CONFLICT",
                "withholding mechanisms are both allowed and prohibited: "
                + ", ".join(sorted(policy_overlap)),
                *sorted(policy_overlap),
            )
        )

    if contract.reliability_mode in {"UNRELIABLE_EXPLICIT", "UNRELIABLE_BOUNDED"}:
        if not contract.reliability_source_ref:
            findings.append(
                _finding(
                    "NARRATIVE.CONTRACT.UNRELIABLE_SOURCE_MISSING",
                    f"{contract.reliability_mode} requires a declared source of unreliability",
                )
            )
        if not contract.unreliable_domain_codes:
            findings.append(
                _finding(
                    "NARRATIVE.CONTRACT.UNRELIABLE_DOMAINS_MISSING",
                    (
                        f"{contract.reliability_mode} requires bounded unreliable domains; "
                        "arbitrary unreliability is not allowed"
                    ),
                )
            )
        if not contract.reliability_signal_refs:
            findings.append(
                _finding(
                    "NARRATIVE.CONTRACT.UNRELIABLE_WITHOUT_SIGNAL",
                    (
                        f"{contract.reliability_mode} requires at least one declared "
                        "reader-facing reliability signal"
                    ),
                )
            )

    return viewpoint_by_id


def _unique_scenes(
    scenes: Sequence[NarrativeSceneState], findings: list[NarrativeFinding]
) -> tuple[NarrativeSceneState, ...]:
    scene_by_id: dict[str, NarrativeSceneState] = {}
    order_to_scene: dict[int, str] = {}
    for scene in scenes:
        if not scene.scene_id:
            findings.append(
                _finding(
                    "NARRATIVE.SCENE.EMPTY_ID",
                    "narrative scene must have a non-empty scene_id",
                )
            )
            continue
        if scene.scene_id in scene_by_id:
            findings.append(
                _finding(
                    "NARRATIVE.SCENE.DUPLICATE_ID",
                    f"duplicate narrative scene id: {scene.scene_id}",
                    scene.scene_id,
                )
            )
            continue
        scene_by_id[scene.scene_id] = scene
        prior_scene = order_to_scene.get(scene.reader_order)
        if prior_scene is not None:
            findings.append(
                _finding(
                    "NARRATIVE.SCENE.DUPLICATE_ORDER",
                    (
                        f"reader_order {scene.reader_order} is shared by "
                        f"{prior_scene} and {scene.scene_id}"
                    ),
                    prior_scene,
                    scene.scene_id,
                )
            )
        else:
            order_to_scene[scene.reader_order] = scene.scene_id
    return tuple(
        sorted(
            scene_by_id.values(),
            key=lambda scene: (scene.reader_order, scene.scene_id),
        )
    )


def _person_is_allowed(
    contract_person: GrammaticalPerson, scene_person: ScenePerson
) -> bool:
    return contract_person == "MIXED" or contract_person == scene_person


def _tense_is_allowed(contract_tense: NarrativeTense, scene_tense: SceneTense) -> bool:
    return contract_tense == "MIXED_CONTROLLED" or contract_tense == scene_tense


def _validate_withholding(
    *,
    scene: NarrativeSceneState,
    viewpoint_rule: ViewpointRule | None,
    contract: NarrativeContractRules,
    decisive_fact_ids: frozenset[str],
    findings: list[NarrativeFinding],
) -> None:
    decisions_by_fact: dict[str, WithholdingDecision] = {}
    for decision in scene.withholding_decisions:
        if decision.fact_id in decisions_by_fact:
            findings.append(
                _finding(
                    "NARRATIVE.WITHHOLDING.DUPLICATE_FACT",
                    (
                        f"scene {scene.scene_id} has multiple withholding decisions "
                        f"for fact {decision.fact_id}"
                    ),
                    scene.scene_id,
                    decision.fact_id,
                )
            )
            continue
        decisions_by_fact[decision.fact_id] = decision

        if (
            decision.fact_id not in scene.pov_known_fact_ids
            or decision.fact_id not in scene.pov_conscious_fact_ids
        ):
            findings.append(
                _finding(
                    "NARRATIVE.WITHHOLDING.UNKNOWN_FACT",
                    (
                        f"scene {scene.scene_id} withholds fact {decision.fact_id} "
                        "that is not declared conscious POV knowledge"
                    ),
                    scene.scene_id,
                    decision.fact_id,
                )
            )

        if decision.fact_id in scene.reader_exposed_fact_ids:
            findings.append(
                _finding(
                    "NARRATIVE.WITHHOLDING.EXPOSED_CONFLICT",
                    (
                        f"scene {scene.scene_id} marks fact {decision.fact_id} as "
                        "both exposed and withheld"
                    ),
                    scene.scene_id,
                    decision.fact_id,
                )
            )

        if decision.mechanism_code in contract.prohibited_withholding_mechanisms:
            findings.append(
                _finding(
                    "NARRATIVE.WITHHOLDING.PROHIBITED_MECHANISM",
                    (
                        f"scene {scene.scene_id} uses prohibited withholding mechanism "
                        f"{decision.mechanism_code}"
                    ),
                    scene.scene_id,
                    decision.fact_id,
                    decision.mechanism_code,
                )
            )
        elif decision.mechanism_code not in contract.allowed_withholding_mechanisms:
            findings.append(
                _finding(
                    "NARRATIVE.WITHHOLDING.UNKNOWN_MECHANISM",
                    (
                        f"scene {scene.scene_id} uses unapproved withholding mechanism "
                        f"{decision.mechanism_code}"
                    ),
                    scene.scene_id,
                    decision.fact_id,
                    decision.mechanism_code,
                )
            )

    if viewpoint_rule is not None:
        hidden_protected = (
            viewpoint_rule.protected_fact_ids
            & scene.pov_conscious_fact_ids
            - scene.reader_exposed_fact_ids
        )
        for fact_id in sorted(hidden_protected):
            findings.append(
                _finding(
                    "NARRATIVE.WITHHOLDING.PROTECTED_FACT",
                    (
                        f"scene {scene.scene_id} suppresses protected fact {fact_id} "
                        f"from viewpoint {viewpoint_rule.character_id}"
                    ),
                    scene.scene_id,
                    fact_id,
                    viewpoint_rule.character_id,
                )
            )

    silently_hidden_decisive = (
        decisive_fact_ids
        & scene.pov_conscious_fact_ids
        - scene.reader_exposed_fact_ids
        - decisions_by_fact.keys()
    )
    for fact_id in sorted(silently_hidden_decisive):
        findings.append(
            _finding(
                "NARRATIVE.FAIRNESS.HIDDEN_DECISIVE_FACT",
                (
                    f"scene {scene.scene_id} keeps conscious decisive fact {fact_id} "
                    "from the reader without a contractual withholding decision"
                ),
                scene.scene_id,
                fact_id,
            )
        )


def _validate_culprit_pov_scene(
    *,
    scene: NarrativeSceneState,
    viewpoint_rule: ViewpointRule | None,
    contract: NarrativeContractRules,
    findings: list[NarrativeFinding],
) -> None:
    if viewpoint_rule is None or not viewpoint_rule.culprit_pov:
        return
    policy = viewpoint_rule.culprit_pov_policy
    if policy is None:
        return

    active_identity_facts = (
        viewpoint_rule.culprit_identity_fact_ids & scene.pov_conscious_fact_ids
    )
    hidden_identity_facts = active_identity_facts - scene.reader_exposed_fact_ids

    if policy == "PRE_ACT_CONSCIOUSNESS" and active_identity_facts:
        findings.append(
            _finding(
                "NARRATIVE.CULPRIT_POV.PRE_ACT_IDENTITY_ACTIVE",
                (
                    f"scene {scene.scene_id} uses PRE_ACT_CONSCIOUSNESS after culprit identity "
                    "is consciously active"
                ),
                scene.scene_id,
                viewpoint_rule.character_id,
                *sorted(active_identity_facts),
            )
        )
        return

    if policy == "IDENTITY_KNOWN_TO_READER":
        for fact_id in sorted(hidden_identity_facts):
            findings.append(
                _finding(
                    "NARRATIVE.CULPRIT_POV.IDENTITY_NOT_EXPOSED",
                    (
                        f"scene {scene.scene_id} hides culprit identity fact {fact_id} under "
                        "IDENTITY_KNOWN_TO_READER policy"
                    ),
                    scene.scene_id,
                    viewpoint_rule.character_id,
                    fact_id,
                )
            )
        return

    if policy == "IDENTITY_CONCEALED_SEMANTICALLY_HONEST":
        decisions_by_fact = {
            decision.fact_id: decision for decision in scene.withholding_decisions
        }
        for fact_id in sorted(hidden_identity_facts):
            if fact_id not in decisions_by_fact:
                findings.append(
                    _finding(
                        "NARRATIVE.CULPRIT_POV.IDENTITY_HIDDEN_WITHOUT_DECISION",
                        (
                            f"scene {scene.scene_id} conceals culprit identity fact {fact_id} "
                            "without an explicit withholding decision"
                        ),
                        scene.scene_id,
                        viewpoint_rule.character_id,
                        fact_id,
                    )
                )
        return

    if policy == "FORMALLY_LIMITED_FRAME":
        approved_frame_refs = (
            scene.narrative_device_refs & contract.accepted_narrative_device_refs
        )
        if not approved_frame_refs:
            findings.append(
                _finding(
                    "NARRATIVE.CULPRIT_POV.FORMAL_FRAME_DEVICE_MISSING",
                    (
                        f"scene {scene.scene_id} uses FORMALLY_LIMITED_FRAME without an "
                        "accepted narrative-device ref"
                    ),
                    scene.scene_id,
                    viewpoint_rule.character_id,
                )
            )


def _validate_scene(
    *,
    scene: NarrativeSceneState,
    contract: NarrativeContractRules,
    viewpoint_by_id: Mapping[str, ViewpointRule],
    decisive_fact_ids: frozenset[str],
    authoritative_known_facts_by_scene: Mapping[str, frozenset[str]] | None,
    findings: list[NarrativeFinding],
) -> None:
    viewpoint_rule: ViewpointRule | None = None
    if scene.viewpoint_character_id is None:
        if not contract.allow_viewpointless_scenes:
            findings.append(
                _finding(
                    "NARRATIVE.POV.MISSING",
                    f"scene {scene.scene_id} has no viewpoint character",
                    scene.scene_id,
                )
            )
    else:
        viewpoint_rule = viewpoint_by_id.get(scene.viewpoint_character_id)
        if viewpoint_rule is None:
            findings.append(
                _finding(
                    "NARRATIVE.POV.UNAUTHORIZED",
                    (
                        f"scene {scene.scene_id} uses unauthorized viewpoint "
                        f"{scene.viewpoint_character_id}"
                    ),
                    scene.scene_id,
                    scene.viewpoint_character_id,
                )
            )

    if not _person_is_allowed(contract.grammatical_person, scene.grammatical_person):
        findings.append(
            _finding(
                "NARRATIVE.POV.PERSON_DRIFT",
                (
                    f"scene {scene.scene_id} uses {scene.grammatical_person} person "
                    f"under {contract.grammatical_person} contract"
                ),
                scene.scene_id,
            )
        )
    if not _tense_is_allowed(contract.tense, scene.tense):
        findings.append(
            _finding(
                "NARRATIVE.POV.TENSE_DRIFT",
                (
                    f"scene {scene.scene_id} uses {scene.tense} tense under "
                    f"{contract.tense} contract"
                ),
                scene.scene_id,
            )
        )

    if contract.restrict_interior_to_pov:
        permitted_interior = (
            frozenset()
            if scene.viewpoint_character_id is None
            else frozenset({scene.viewpoint_character_id})
        )
        leaked_interior = scene.interior_access_character_ids - permitted_interior
        if leaked_interior:
            findings.append(
                _finding(
                    "NARRATIVE.POV.HEAD_HOPPING",
                    (
                        f"scene {scene.scene_id} directly accesses interior state of "
                        + ", ".join(sorted(leaked_interior))
                    ),
                    scene.scene_id,
                    *sorted(leaked_interior),
                )
            )

    unsupported_conscious = scene.pov_conscious_fact_ids - scene.pov_known_fact_ids
    if unsupported_conscious:
        findings.append(
            _finding(
                "NARRATIVE.POV.CONSCIOUS_FACT_NOT_KNOWN",
                (
                    f"scene {scene.scene_id} marks facts conscious but not known: "
                    + ", ".join(sorted(unsupported_conscious))
                ),
                scene.scene_id,
                *sorted(unsupported_conscious),
            )
        )

    if authoritative_known_facts_by_scene is not None:
        authoritative = authoritative_known_facts_by_scene.get(scene.scene_id)
        if authoritative is None:
            findings.append(
                _finding(
                    "NARRATIVE.POV.KNOWLEDGE_STATE_MISSING",
                    (
                        f"scene {scene.scene_id} has no authoritative character "
                        "knowledge snapshot"
                    ),
                    scene.scene_id,
                )
            )
        else:
            unsupported_known = scene.pov_known_fact_ids - authoritative
            if unsupported_known:
                findings.append(
                    _finding(
                        "NARRATIVE.POV.KNOWLEDGE_UNSUPPORTED",
                        (
                            f"scene {scene.scene_id} gives POV unsupported facts: "
                            + ", ".join(sorted(unsupported_known))
                        ),
                        scene.scene_id,
                        *sorted(unsupported_known),
                    )
                )

    if contract.restrict_reader_to_pov_knowledge:
        permitted_reader_facts = (
            scene.pov_known_fact_ids | scene.externally_observable_fact_ids
        )
        leaked_reader_facts = scene.reader_exposed_fact_ids - permitted_reader_facts
        if leaked_reader_facts:
            findings.append(
                _finding(
                    "NARRATIVE.READER.KNOWLEDGE_LEAK",
                    (
                        f"scene {scene.scene_id} exposes facts outside POV knowledge or "
                        "declared external observation: "
                        + ", ".join(sorted(leaked_reader_facts))
                    ),
                    scene.scene_id,
                    *sorted(leaked_reader_facts),
                )
            )

    unapproved_devices = (
        scene.narrative_device_refs - contract.accepted_narrative_device_refs
    )
    if unapproved_devices:
        findings.append(
            _finding(
                "NARRATIVE.DEVICE.UNAPPROVED",
                (
                    f"scene {scene.scene_id} uses unapproved narrative devices: "
                    + ", ".join(sorted(unapproved_devices))
                ),
                scene.scene_id,
                *sorted(unapproved_devices),
            )
        )

    _validate_culprit_pov_scene(
        scene=scene,
        viewpoint_rule=viewpoint_rule,
        contract=contract,
        findings=findings,
    )

    _validate_withholding(
        scene=scene,
        viewpoint_rule=viewpoint_rule,
        contract=contract,
        decisive_fact_ids=decisive_fact_ids,
        findings=findings,
    )


def validate_narrative_fairness(
    *,
    contract: NarrativeContractRules,
    scenes: Sequence[NarrativeSceneState],
    decisive_fact_ids: frozenset[str] = frozenset(),
    authoritative_known_facts_by_scene: Mapping[str, frozenset[str]] | None = None,
) -> NarrativeValidationResult:
    """Validate declared narrative information flow without reading prose semantics."""
    findings: list[NarrativeFinding] = []
    viewpoint_by_id = _validate_contract(contract, findings)
    unique_scenes = _unique_scenes(scenes, findings)

    known_to_reader: set[str] = set()
    checkpoints: list[ReaderKnowledgeCheckpoint] = []
    for scene in unique_scenes:
        _validate_scene(
            scene=scene,
            contract=contract,
            viewpoint_by_id=viewpoint_by_id,
            decisive_fact_ids=decisive_fact_ids,
            authoritative_known_facts_by_scene=authoritative_known_facts_by_scene,
            findings=findings,
        )
        known_to_reader.update(scene.reader_exposed_fact_ids)
        checkpoints.append(
            ReaderKnowledgeCheckpoint(
                scene_id=scene.scene_id,
                reader_order=scene.reader_order,
                known_fact_ids=frozenset(known_to_reader),
            )
        )

    return NarrativeValidationResult(
        findings=tuple(findings),
        reader_checkpoints=tuple(checkpoints),
    )
