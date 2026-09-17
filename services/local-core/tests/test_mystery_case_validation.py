from __future__ import annotations

from book_os_core.mystery_case_validation import (
    CaseEvent,
    ClueRecord,
    KnowledgeAcquisition,
    KnowledgeUse,
    TravelRule,
    validate_case_integrity,
)


def _codes(result) -> set[str]:  # type: ignore[no-untyped-def]
    return {finding.code for finding in result.findings}


def test_clean_case_passes_deterministic_integrity() -> None:
    events = (
        CaseEvent("origin", 0, 10, "flat", ("suspect",)),
        CaseEvent("travelled", 100, 110, "office", ("suspect",)),
        CaseEvent("learn", 120, 130, "office", ("investigator",)),
        CaseEvent("expose", 140, 150, "office", ("investigator",)),
        CaseEvent("payoff", 200, 210, "station", ("investigator",)),
    )
    result = validate_case_integrity(
        events=events,
        travel_rules=(TravelRule("flat", "office", 60), TravelRule("office", "station", 30)),
        acquisitions=(KnowledgeAcquisition("investigator", "fact-a", "learn", 125),),
        uses=(KnowledgeUse("investigator", "fact-a", "expose", 145),),
        clues=(
            ClueRecord(
                "clue-a",
                origin_event_id="origin",
                exposure_event_id="expose",
                payoff_event_id="payoff",
                decisive=True,
            ),
        ),
    )

    assert result.passed
    assert result.findings == ()


def test_duplicate_ids_and_invalid_event_interval_are_blocking() -> None:
    result = validate_case_integrity(
        events=(
            CaseEvent("same", 10, 5),
            CaseEvent("same", 20, 30),
        ),
        clues=(
            ClueRecord("c", "same"),
            ClueRecord("c", "same"),
        ),
    )

    codes = _codes(result)
    assert "CASE.EVENT.INVALID_INTERVAL" in codes
    assert "CASE.EVENT.DUPLICATE_ID" in codes
    assert "CASE.CLUE.DUPLICATE_ID" in codes
    assert not result.passed


def test_actor_double_location_and_impossible_travel_are_detected() -> None:
    overlap = validate_case_integrity(
        events=(
            CaseEvent("a", 0, 100, "north", ("x",)),
            CaseEvent("b", 50, 150, "south", ("x",)),
        ),
    )
    assert "CASE.ACTOR.DOUBLE_LOCATION" in _codes(overlap)

    impossible = validate_case_integrity(
        events=(
            CaseEvent("a", 0, 10, "north", ("x",)),
            CaseEvent("b", 30, 40, "south", ("x",)),
        ),
        travel_rules=(TravelRule("north", "south", 60),),
    )
    assert "CASE.TRAVEL.IMPOSSIBLE" in _codes(impossible)

    missing_rule = validate_case_integrity(
        events=(
            CaseEvent("a", 0, 10, "north", ("x",)),
            CaseEvent("b", 1000, 1010, "south", ("x",)),
        ),
    )
    assert "CASE.TRAVEL.RULE_MISSING" in _codes(missing_rule)


def test_conflicting_or_invalid_travel_rules_do_not_silently_choose_a_value() -> None:
    result = validate_case_integrity(
        events=(
            CaseEvent("a", 0, 10, "north", ("x",)),
            CaseEvent("b", 100, 110, "south", ("x",)),
        ),
        travel_rules=(
            TravelRule("north", "south", 60),
            TravelRule("north", "south", 90),
            TravelRule("south", "north", -1),
        ),
    )

    codes = _codes(result)
    assert "CASE.TRAVEL.RULE_CONFLICT" in codes
    assert "CASE.TRAVEL.RULE_INVALID" in codes
    assert not result.passed


def test_character_cannot_use_knowledge_before_valid_acquisition() -> None:
    events = (
        CaseEvent("early", 0, 10),
        CaseEvent("late", 100, 110),
    )
    result = validate_case_integrity(
        events=events,
        acquisitions=(KnowledgeAcquisition("hero", "door-code", "late", 105),),
        uses=(
            KnowledgeUse("hero", "door-code", "early", 5),
            KnowledgeUse("hero", "initial-fact", "early", 6),
        ),
        initial_knowledge={"hero": frozenset({"initial-fact"})},
    )

    findings = [
        finding
        for finding in result.findings
        if finding.code == "CASE.KNOWLEDGE.USED_BEFORE_ACQUIRED"
    ]
    assert len(findings) == 1
    assert "door-code" in findings[0].object_refs


def test_knowledge_event_and_timestamp_references_are_checked() -> None:
    events = (CaseEvent("scene", 10, 20),)
    result = validate_case_integrity(
        events=events,
        acquisitions=(
            KnowledgeAcquisition("hero", "a", "missing", 10),
            KnowledgeAcquisition("hero", "b", "scene", 30),
        ),
        uses=(
            KnowledgeUse("hero", "a", "missing", 10),
            KnowledgeUse("hero", "b", "scene", 5),
        ),
    )

    codes = _codes(result)
    assert "CASE.KNOWLEDGE.EVENT_MISSING" in codes
    assert "CASE.KNOWLEDGE.TIME_OUTSIDE_EVENT" in codes


def test_decisive_clue_fair_play_is_profile_aware_but_payoff_is_always_required() -> None:
    events = (CaseEvent("origin", 0, 10),)
    clue = ClueRecord("key", "origin", decisive=True)

    required = validate_case_integrity(events=events, clues=(clue,), fair_play_mode="REQUIRED")
    required_findings = {finding.code: finding for finding in required.findings}
    assert required_findings["CASE.CLUE.DECISIVE_NOT_EXPOSED"].severity == "BLOCKING"
    assert required_findings["CASE.CLUE.DECISIVE_NO_PAYOFF"].severity == "BLOCKING"

    expected = validate_case_integrity(events=events, clues=(clue,), fair_play_mode="EXPECTED")
    expected_findings = {finding.code: finding for finding in expected.findings}
    assert expected_findings["CASE.CLUE.DECISIVE_NOT_EXPOSED"].severity == "MAJOR"

    relaxed = validate_case_integrity(events=events, clues=(clue,), fair_play_mode="RELAXED")
    relaxed_findings = {finding.code: finding for finding in relaxed.findings}
    assert relaxed_findings["CASE.CLUE.DECISIVE_NOT_EXPOSED"].severity == "NOTE"
    assert relaxed_findings["CASE.CLUE.DECISIVE_NO_PAYOFF"].severity == "BLOCKING"


def test_clue_event_references_and_lifecycle_order_are_validated() -> None:
    events = (
        CaseEvent("expose", 0, 10),
        CaseEvent("origin", 100, 110),
        CaseEvent("payoff", 50, 60),
    )
    result = validate_case_integrity(
        events=events,
        clues=(
            ClueRecord(
                "c1",
                origin_event_id="origin",
                exposure_event_id="expose",
                payoff_event_id="payoff",
            ),
            ClueRecord("c2", origin_event_id="missing"),
            ClueRecord("c3", origin_event_id="origin", exposure_event_id="missing-expose"),
            ClueRecord("c4", origin_event_id="origin", payoff_event_id="missing-payoff"),
        ),
    )

    codes = _codes(result)
    assert "CASE.CLUE.EXPOSED_BEFORE_ORIGIN" in codes
    assert "CASE.CLUE.PAYOFF_BEFORE_EXPOSURE" not in codes
    assert "CASE.CLUE.ORIGIN_MISSING" in codes
    assert "CASE.CLUE.EXPOSURE_MISSING_EVENT" in codes
    assert "CASE.CLUE.PAYOFF_MISSING_EVENT" in codes


def test_temporal_exception_requires_an_accepted_rule_reference() -> None:
    events = (
        CaseEvent("vision", 0, 10),
        CaseEvent("origin", 100, 110),
        CaseEvent("payoff", 200, 210),
    )
    clue = ClueRecord(
        "premonition",
        origin_event_id="origin",
        exposure_event_id="vision",
        payoff_event_id="payoff",
        temporal_rule_ref="rule-premonition",
    )

    rejected = validate_case_integrity(events=events, clues=(clue,))
    rejected_codes = _codes(rejected)
    assert "CASE.CLUE.TEMPORAL_RULE_UNKNOWN" in rejected_codes
    assert "CASE.CLUE.EXPOSED_BEFORE_ORIGIN" in rejected_codes

    accepted = validate_case_integrity(
        events=events,
        clues=(clue,),
        accepted_temporal_rule_refs=frozenset({"rule-premonition"}),
    )
    accepted_codes = _codes(accepted)
    assert "CASE.CLUE.TEMPORAL_RULE_UNKNOWN" not in accepted_codes
    assert "CASE.CLUE.EXPOSED_BEFORE_ORIGIN" not in accepted_codes


def test_clue_dependencies_must_exist_and_be_acyclic() -> None:
    events = (CaseEvent("origin", 0, 10),)
    result = validate_case_integrity(
        events=events,
        clues=(
            ClueRecord("a", "origin", dependency_clue_ids=("b",)),
            ClueRecord("b", "origin", dependency_clue_ids=("a",)),
            ClueRecord("c", "origin", dependency_clue_ids=("missing",)),
        ),
    )

    codes = _codes(result)
    assert "CASE.CLUE.DEPENDENCY_CYCLE" in codes
    assert "CASE.CLUE.DEPENDENCY_MISSING" in codes
