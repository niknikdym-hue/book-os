from __future__ import annotations

from book_os_core.mystery_narrative_validation import (
    NarrativeContractRules,
    NarrativeSceneState,
    NarrativeValidationResult,
    ViewpointRule,
    WithholdingDecision,
    validate_narrative_fairness,
)


def _codes(result: NarrativeValidationResult) -> set[str]:
    return {finding.code for finding in result.findings}


def _third_limited_contract(**overrides: object) -> NarrativeContractRules:
    values: dict[str, object] = {
        "narrative_mode": "THIRD_LIMITED_SINGLE",
        "grammatical_person": "THIRD",
        "tense": "PAST",
        "viewpoints": (ViewpointRule("alice", "lead investigator"),),
        "allowed_withholding_mechanisms": frozenset({"ATTENTION_ELSEWHERE"}),
        "prohibited_withholding_mechanisms": frozenset({"DIRECT_LIE_TO_READER"}),
        "accepted_narrative_device_refs": frozenset({"FLASHBACK-A"}),
    }
    values.update(overrides)
    return NarrativeContractRules(**values)  # type: ignore[arg-type]


def test_clean_limited_pov_information_flow_passes() -> None:
    contract = _third_limited_contract()
    scenes = (
        NarrativeSceneState(
            scene_id="s1",
            reader_order=10,
            viewpoint_character_id="alice",
            grammatical_person="THIRD",
            tense="PAST",
            pov_known_fact_ids=frozenset({"clue-a"}),
            pov_conscious_fact_ids=frozenset({"clue-a"}),
            reader_exposed_fact_ids=frozenset({"clue-a"}),
            interior_access_character_ids=frozenset({"alice"}),
        ),
        NarrativeSceneState(
            scene_id="s2",
            reader_order=20,
            viewpoint_character_id="alice",
            grammatical_person="THIRD",
            tense="PAST",
            pov_known_fact_ids=frozenset({"clue-a", "weather"}),
            externally_observable_fact_ids=frozenset({"door-open"}),
            reader_exposed_fact_ids=frozenset({"door-open"}),
            interior_access_character_ids=frozenset({"alice"}),
        ),
    )

    result = validate_narrative_fairness(
        contract=contract,
        scenes=scenes,
        decisive_fact_ids=frozenset({"clue-a"}),
    )

    assert result.passed
    assert result.findings == ()
    assert result.reader_checkpoints[0].known_fact_ids == frozenset({"clue-a"})
    assert result.reader_checkpoints[1].known_fact_ids == frozenset({"clue-a", "door-open"})


def test_conscious_decisive_fact_cannot_be_silently_hidden() -> None:
    contract = _third_limited_contract()
    scene = NarrativeSceneState(
        scene_id="s1",
        reader_order=10,
        viewpoint_character_id="alice",
        grammatical_person="THIRD",
        tense="PAST",
        pov_known_fact_ids=frozenset({"culprit-id"}),
        pov_conscious_fact_ids=frozenset({"culprit-id"}),
    )

    result = validate_narrative_fairness(
        contract=contract,
        scenes=(scene,),
        decisive_fact_ids=frozenset({"culprit-id"}),
    )

    assert "NARRATIVE.FAIRNESS.HIDDEN_DECISIVE_FACT" in _codes(result)
    assert not result.passed


def test_allowed_withholding_can_cover_decisive_fact_but_not_protected_fact() -> None:
    contract = _third_limited_contract(
        viewpoints=(
            ViewpointRule(
                "alice",
                "lead investigator",
                protected_fact_ids=frozenset({"protected"}),
            ),
        )
    )
    scene = NarrativeSceneState(
        scene_id="s1",
        reader_order=10,
        viewpoint_character_id="alice",
        grammatical_person="THIRD",
        tense="PAST",
        pov_known_fact_ids=frozenset({"decisive", "protected"}),
        pov_conscious_fact_ids=frozenset({"decisive", "protected"}),
        withholding_decisions=(
            WithholdingDecision("decisive", "ATTENTION_ELSEWHERE"),
            WithholdingDecision("protected", "ATTENTION_ELSEWHERE"),
        ),
    )

    result = validate_narrative_fairness(
        contract=contract,
        scenes=(scene,),
        decisive_fact_ids=frozenset({"decisive", "protected"}),
    )

    codes = _codes(result)
    assert "NARRATIVE.FAIRNESS.HIDDEN_DECISIVE_FACT" not in codes
    assert "NARRATIVE.WITHHOLDING.PROTECTED_FACT" in codes
    assert not result.passed


def test_withholding_must_be_known_conscious_allowed_and_not_exposed() -> None:
    contract = _third_limited_contract()
    scene = NarrativeSceneState(
        scene_id="s1",
        reader_order=10,
        viewpoint_character_id="alice",
        grammatical_person="THIRD",
        tense="PAST",
        pov_known_fact_ids=frozenset({"known", "exposed", "forbidden"}),
        pov_conscious_fact_ids=frozenset({"known", "exposed", "forbidden"}),
        reader_exposed_fact_ids=frozenset({"exposed"}),
        withholding_decisions=(
            WithholdingDecision("unknown", "ATTENTION_ELSEWHERE"),
            WithholdingDecision("known", "NOT_APPROVED"),
            WithholdingDecision("forbidden", "DIRECT_LIE_TO_READER"),
            WithholdingDecision("exposed", "ATTENTION_ELSEWHERE"),
        ),
    )

    result = validate_narrative_fairness(contract=contract, scenes=(scene,))
    codes = _codes(result)

    assert "NARRATIVE.WITHHOLDING.UNKNOWN_FACT" in codes
    assert "NARRATIVE.WITHHOLDING.UNKNOWN_MECHANISM" in codes
    assert "NARRATIVE.WITHHOLDING.PROHIBITED_MECHANISM" in codes
    assert "NARRATIVE.WITHHOLDING.EXPOSED_CONFLICT" in codes


def test_unauthorized_pov_person_tense_and_head_hopping_are_blocked() -> None:
    contract = _third_limited_contract()
    scene = NarrativeSceneState(
        scene_id="s1",
        reader_order=10,
        viewpoint_character_id="bob",
        grammatical_person="FIRST",
        tense="PRESENT",
        interior_access_character_ids=frozenset({"bob", "alice", "charlie"}),
    )

    result = validate_narrative_fairness(contract=contract, scenes=(scene,))
    codes = _codes(result)

    assert "NARRATIVE.POV.UNAUTHORIZED" in codes
    assert "NARRATIVE.POV.PERSON_DRIFT" in codes
    assert "NARRATIVE.POV.TENSE_DRIFT" in codes
    assert "NARRATIVE.POV.HEAD_HOPPING" in codes


def test_reader_fact_must_be_known_or_externally_observable_in_limited_pov() -> None:
    contract = _third_limited_contract()
    scene = NarrativeSceneState(
        scene_id="s1",
        reader_order=10,
        viewpoint_character_id="alice",
        grammatical_person="THIRD",
        tense="PAST",
        pov_known_fact_ids=frozenset({"known"}),
        externally_observable_fact_ids=frozenset({"visible"}),
        reader_exposed_fact_ids=frozenset({"known", "visible", "impossible"}),
    )

    result = validate_narrative_fairness(contract=contract, scenes=(scene,))

    assert "NARRATIVE.READER.KNOWLEDGE_LEAK" in _codes(result)


def test_conscious_facts_and_authoritative_knowledge_are_cross_checked() -> None:
    contract = _third_limited_contract()
    scene = NarrativeSceneState(
        scene_id="s1",
        reader_order=10,
        viewpoint_character_id="alice",
        grammatical_person="THIRD",
        tense="PAST",
        pov_known_fact_ids=frozenset({"real", "unsupported"}),
        pov_conscious_fact_ids=frozenset({"real", "not-known"}),
    )

    result = validate_narrative_fairness(
        contract=contract,
        scenes=(scene,),
        authoritative_known_facts_by_scene={"s1": frozenset({"real"})},
    )
    codes = _codes(result)

    assert "NARRATIVE.POV.CONSCIOUS_FACT_NOT_KNOWN" in codes
    assert "NARRATIVE.POV.KNOWLEDGE_UNSUPPORTED" in codes

    missing_snapshot = validate_narrative_fairness(
        contract=contract,
        scenes=(scene,),
        authoritative_known_facts_by_scene={},
    )
    assert "NARRATIVE.POV.KNOWLEDGE_STATE_MISSING" in _codes(missing_snapshot)


def test_contract_detects_duplicate_viewpoints_policy_conflict_and_unreliable_no_signal() -> None:
    contract = NarrativeContractRules(
        narrative_mode="THIRD_LIMITED_MULTI",
        grammatical_person="THIRD",
        tense="PAST",
        viewpoints=(
            ViewpointRule("alice", "one"),
            ViewpointRule("alice", "duplicate"),
        ),
        reliability_mode="UNRELIABLE_BOUNDED",
        allowed_withholding_mechanisms=frozenset({"X"}),
        prohibited_withholding_mechanisms=frozenset({"X"}),
    )

    result = validate_narrative_fairness(contract=contract, scenes=())
    codes = _codes(result)

    assert "NARRATIVE.CONTRACT.DUPLICATE_VIEWPOINT" in codes
    assert "NARRATIVE.CONTRACT.VIEWPOINT_COUNT" in codes
    assert "NARRATIVE.CONTRACT.WITHHOLDING_POLICY_CONFLICT" in codes
    assert "NARRATIVE.CONTRACT.UNRELIABLE_WITHOUT_SIGNAL" in codes


def test_duplicate_scene_order_and_unapproved_device_are_detected() -> None:
    contract = _third_limited_contract()
    scenes = (
        NarrativeSceneState(
            scene_id="same",
            reader_order=10,
            viewpoint_character_id="alice",
            grammatical_person="THIRD",
            tense="PAST",
            narrative_device_refs=frozenset({"NOT-APPROVED"}),
        ),
        NarrativeSceneState(
            scene_id="other",
            reader_order=10,
            viewpoint_character_id="alice",
            grammatical_person="THIRD",
            tense="PAST",
        ),
        NarrativeSceneState(
            scene_id="same",
            reader_order=20,
            viewpoint_character_id="alice",
            grammatical_person="THIRD",
            tense="PAST",
        ),
    )

    result = validate_narrative_fairness(contract=contract, scenes=scenes)
    codes = _codes(result)

    assert "NARRATIVE.SCENE.DUPLICATE_ID" in codes
    assert "NARRATIVE.SCENE.DUPLICATE_ORDER" in codes
    assert "NARRATIVE.DEVICE.UNAPPROVED" in codes


def test_viewpointless_scene_requires_explicit_contract_permission() -> None:
    scene = NarrativeSceneState(
        scene_id="document",
        reader_order=10,
        viewpoint_character_id=None,
        grammatical_person="THIRD",
        tense="PAST",
    )

    blocked = validate_narrative_fairness(contract=_third_limited_contract(), scenes=(scene,))
    assert "NARRATIVE.POV.MISSING" in _codes(blocked)

    allowed = validate_narrative_fairness(
        contract=_third_limited_contract(
            allow_viewpointless_scenes=True,
            restrict_interior_to_pov=True,
        ),
        scenes=(scene,),
    )
    assert "NARRATIVE.POV.MISSING" not in _codes(allowed)


def test_reader_knowledge_accumulates_by_reader_order_not_input_order() -> None:
    contract = _third_limited_contract()
    later = NarrativeSceneState(
        scene_id="later",
        reader_order=20,
        viewpoint_character_id="alice",
        grammatical_person="THIRD",
        tense="PAST",
        pov_known_fact_ids=frozenset({"a", "b"}),
        reader_exposed_fact_ids=frozenset({"b"}),
    )
    earlier = NarrativeSceneState(
        scene_id="earlier",
        reader_order=10,
        viewpoint_character_id="alice",
        grammatical_person="THIRD",
        tense="PAST",
        pov_known_fact_ids=frozenset({"a"}),
        reader_exposed_fact_ids=frozenset({"a"}),
    )

    result = validate_narrative_fairness(contract=contract, scenes=(later, earlier))

    assert [checkpoint.scene_id for checkpoint in result.reader_checkpoints] == [
        "earlier",
        "later",
    ]
    assert result.reader_checkpoints[0].known_fact_ids == frozenset({"a"})
    assert result.reader_checkpoints[1].known_fact_ids == frozenset({"a", "b"})


def test_narrative_mode_and_grammatical_person_must_agree() -> None:
    contract = NarrativeContractRules(
        narrative_mode="FIRST_SINGLE",
        grammatical_person="THIRD",
        tense="PAST",
        viewpoints=(ViewpointRule("alice", "lead"),),
    )

    result = validate_narrative_fairness(contract=contract, scenes=())

    assert "NARRATIVE.CONTRACT.MODE_PERSON_CONFLICT" in _codes(result)


def test_culprit_pov_requires_explicit_policy_and_identity_contract() -> None:
    missing_policy = NarrativeContractRules(
        narrative_mode="THIRD_LIMITED_SINGLE",
        grammatical_person="THIRD",
        tense="PAST",
        viewpoints=(ViewpointRule("culprit", "antagonist", culprit_pov=True),),
    )
    result = validate_narrative_fairness(contract=missing_policy, scenes=())
    assert "NARRATIVE.CONTRACT.CULPRIT_POV_POLICY_MISSING" in _codes(result)

    missing_identity = NarrativeContractRules(
        narrative_mode="THIRD_LIMITED_SINGLE",
        grammatical_person="THIRD",
        tense="PAST",
        viewpoints=(
            ViewpointRule(
                "culprit",
                "antagonist",
                culprit_pov=True,
                culprit_pov_policy="IDENTITY_CONCEALED_SEMANTICALLY_HONEST",
            ),
        ),
    )
    result = validate_narrative_fairness(contract=missing_identity, scenes=())
    assert "NARRATIVE.CONTRACT.CULPRIT_IDENTITY_FACT_MISSING" in _codes(result)


def test_culprit_identity_known_to_reader_cannot_be_hidden() -> None:
    contract = NarrativeContractRules(
        narrative_mode="THIRD_LIMITED_SINGLE",
        grammatical_person="THIRD",
        tense="PAST",
        viewpoints=(
            ViewpointRule(
                "culprit",
                "antagonist",
                culprit_pov=True,
                culprit_pov_policy="IDENTITY_KNOWN_TO_READER",
                culprit_identity_fact_ids=frozenset({"culprit-is-self"}),
            ),
        ),
    )
    scene = NarrativeSceneState(
        scene_id="s1",
        reader_order=10,
        viewpoint_character_id="culprit",
        grammatical_person="THIRD",
        tense="PAST",
        pov_known_fact_ids=frozenset({"culprit-is-self"}),
        pov_conscious_fact_ids=frozenset({"culprit-is-self"}),
    )

    result = validate_narrative_fairness(contract=contract, scenes=(scene,))

    assert "NARRATIVE.CULPRIT_POV.IDENTITY_NOT_EXPOSED" in _codes(result)


def test_concealed_culprit_identity_requires_explicit_withholding_decision() -> None:
    contract = NarrativeContractRules(
        narrative_mode="THIRD_LIMITED_SINGLE",
        grammatical_person="THIRD",
        tense="PAST",
        viewpoints=(
            ViewpointRule(
                "culprit",
                "antagonist",
                culprit_pov=True,
                culprit_pov_policy="IDENTITY_CONCEALED_SEMANTICALLY_HONEST",
                culprit_identity_fact_ids=frozenset({"culprit-is-self"}),
            ),
        ),
        allowed_withholding_mechanisms=frozenset({"SEMANTICALLY_HONEST_IDENTITY_CONCEALMENT"}),
    )
    scene = NarrativeSceneState(
        scene_id="s1",
        reader_order=10,
        viewpoint_character_id="culprit",
        grammatical_person="THIRD",
        tense="PAST",
        pov_known_fact_ids=frozenset({"culprit-is-self"}),
        pov_conscious_fact_ids=frozenset({"culprit-is-self"}),
    )

    blocked = validate_narrative_fairness(contract=contract, scenes=(scene,))
    assert "NARRATIVE.CULPRIT_POV.IDENTITY_HIDDEN_WITHOUT_DECISION" in _codes(blocked)

    allowed_scene = NarrativeSceneState(
        scene_id="s1",
        reader_order=10,
        viewpoint_character_id="culprit",
        grammatical_person="THIRD",
        tense="PAST",
        pov_known_fact_ids=frozenset({"culprit-is-self"}),
        pov_conscious_fact_ids=frozenset({"culprit-is-self"}),
        withholding_decisions=(
            WithholdingDecision(
                "culprit-is-self",
                "SEMANTICALLY_HONEST_IDENTITY_CONCEALMENT",
            ),
        ),
    )
    allowed = validate_narrative_fairness(contract=contract, scenes=(allowed_scene,))
    assert "NARRATIVE.CULPRIT_POV.IDENTITY_HIDDEN_WITHOUT_DECISION" not in _codes(allowed)


def test_unreliable_narration_requires_source_domains_and_reader_signals() -> None:
    contract = NarrativeContractRules(
        narrative_mode="THIRD_LIMITED_SINGLE",
        grammatical_person="THIRD",
        tense="PAST",
        viewpoints=(ViewpointRule("alice", "lead"),),
        reliability_mode="UNRELIABLE_BOUNDED",
    )

    result = validate_narrative_fairness(contract=contract, scenes=())
    codes = _codes(result)

    assert "NARRATIVE.CONTRACT.UNRELIABLE_SOURCE_MISSING" in codes
    assert "NARRATIVE.CONTRACT.UNRELIABLE_DOMAINS_MISSING" in codes
    assert "NARRATIVE.CONTRACT.UNRELIABLE_WITHOUT_SIGNAL" in codes


def test_pre_act_culprit_pov_tracks_act_awareness_not_identity() -> None:
    missing_awareness_contract = NarrativeContractRules(
        narrative_mode="THIRD_LIMITED_SINGLE",
        grammatical_person="THIRD",
        tense="PAST",
        viewpoints=(
            ViewpointRule(
                "future-culprit",
                "antagonist",
                culprit_pov=True,
                culprit_pov_policy="PRE_ACT_CONSCIOUSNESS",
            ),
        ),
    )
    missing = validate_narrative_fairness(contract=missing_awareness_contract, scenes=())
    assert "NARRATIVE.CONTRACT.CULPRIT_ACT_AWARENESS_FACT_MISSING" in _codes(missing)

    contract = NarrativeContractRules(
        narrative_mode="THIRD_LIMITED_SINGLE",
        grammatical_person="THIRD",
        tense="PAST",
        viewpoints=(
            ViewpointRule(
                "future-culprit",
                "antagonist",
                culprit_pov=True,
                culprit_pov_policy="PRE_ACT_CONSCIOUSNESS",
                culprit_act_awareness_fact_ids=frozenset({"understands-relevant-act"}),
            ),
        ),
    )
    before_awareness = NarrativeSceneState(
        scene_id="before",
        reader_order=10,
        viewpoint_character_id="future-culprit",
        grammatical_person="THIRD",
        tense="PAST",
        pov_known_fact_ids=frozenset({"own-name"}),
        pov_conscious_fact_ids=frozenset({"own-name"}),
        reader_exposed_fact_ids=frozenset({"own-name"}),
    )
    before = validate_narrative_fairness(contract=contract, scenes=(before_awareness,))
    assert "NARRATIVE.CULPRIT_POV.PRE_ACT_AWARENESS_ACTIVE" not in _codes(before)

    after_awareness = NarrativeSceneState(
        scene_id="after",
        reader_order=20,
        viewpoint_character_id="future-culprit",
        grammatical_person="THIRD",
        tense="PAST",
        pov_known_fact_ids=frozenset({"understands-relevant-act"}),
        pov_conscious_fact_ids=frozenset({"understands-relevant-act"}),
    )
    after = validate_narrative_fairness(contract=contract, scenes=(after_awareness,))
    assert "NARRATIVE.CULPRIT_POV.PRE_ACT_AWARENESS_ACTIVE" in _codes(after)
