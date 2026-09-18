from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal, TypeAlias

FindingSeverity: TypeAlias = Literal["BLOCKING", "MAJOR", "MINOR", "NOTE"]
FairPlayMode: TypeAlias = Literal["REQUIRED", "EXPECTED", "RELAXED"]


@dataclass(frozen=True)
class CaseEvent:
    event_id: str
    start_second: int
    end_second: int
    location_id: str | None = None
    actor_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class TravelRule:
    origin_location_id: str
    destination_location_id: str
    minimum_seconds: int


@dataclass(frozen=True)
class KnowledgeAcquisition:
    character_id: str
    fact_id: str
    event_id: str
    at_second: int


@dataclass(frozen=True)
class KnowledgeUse:
    character_id: str
    fact_id: str
    event_id: str
    at_second: int


@dataclass(frozen=True)
class ClueRecord:
    clue_id: str
    origin_event_id: str
    exposure_event_id: str | None = None
    exposure_order: int | None = None
    payoff_event_id: str | None = None
    payoff_order: int | None = None
    decisive: bool = False
    dependency_clue_ids: tuple[str, ...] = ()
    temporal_rule_ref: str | None = None


@dataclass(frozen=True)
class ValidationFinding:
    code: str
    severity: FindingSeverity
    message: str
    object_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class CaseIntegrityResult:
    findings: tuple[ValidationFinding, ...]

    @property
    def blocking_findings(self) -> tuple[ValidationFinding, ...]:
        return tuple(finding for finding in self.findings if finding.severity == "BLOCKING")

    @property
    def passed(self) -> bool:
        return not self.blocking_findings


def _finding(
    code: str,
    message: str,
    *object_refs: str,
    severity: FindingSeverity = "BLOCKING",
) -> ValidationFinding:
    return ValidationFinding(
        code=code,
        severity=severity,
        message=message,
        object_refs=tuple(object_refs),
    )


def _event_map(
    events: Sequence[CaseEvent], findings: list[ValidationFinding]
) -> dict[str, CaseEvent]:
    result: dict[str, CaseEvent] = {}
    for event in events:
        if not event.event_id:
            findings.append(
                _finding(
                    "CASE.EVENT.EMPTY_ID",
                    "case event must have a non-empty event_id",
                )
            )
            continue
        if event.event_id in result:
            findings.append(
                _finding(
                    "CASE.EVENT.DUPLICATE_ID",
                    f"duplicate case event id: {event.event_id}",
                    event.event_id,
                )
            )
            continue
        result[event.event_id] = event
        if event.end_second < event.start_second:
            findings.append(
                _finding(
                    "CASE.EVENT.INVALID_INTERVAL",
                    (
                        f"event {event.event_id} ends before it starts: "
                        f"{event.start_second}..{event.end_second}"
                    ),
                    event.event_id,
                )
            )
    return result


def _travel_rule_map(
    travel_rules: Sequence[TravelRule], findings: list[ValidationFinding]
) -> dict[tuple[str, str], TravelRule]:
    result: dict[tuple[str, str], TravelRule] = {}
    for rule in travel_rules:
        key = (rule.origin_location_id, rule.destination_location_id)
        if rule.minimum_seconds < 0:
            findings.append(
                _finding(
                    "CASE.TRAVEL.RULE_INVALID",
                    (
                        f"travel rule {rule.origin_location_id} -> "
                        f"{rule.destination_location_id} has negative minimum"
                    ),
                    rule.origin_location_id,
                    rule.destination_location_id,
                )
            )
            continue
        previous = result.get(key)
        if previous is not None and previous.minimum_seconds != rule.minimum_seconds:
            findings.append(
                _finding(
                    "CASE.TRAVEL.RULE_CONFLICT",
                    (
                        f"conflicting minimum travel times for "
                        f"{rule.origin_location_id} -> {rule.destination_location_id}: "
                        f"{previous.minimum_seconds} vs {rule.minimum_seconds}"
                    ),
                    rule.origin_location_id,
                    rule.destination_location_id,
                )
            )
            continue
        result[key] = rule
    return result


def _validate_actor_timeline(
    events: Sequence[CaseEvent],
    travel_rules: Mapping[tuple[str, str], TravelRule],
    findings: list[ValidationFinding],
) -> None:
    by_actor: dict[str, list[CaseEvent]] = defaultdict(list)
    for event in events:
        if event.end_second < event.start_second or event.location_id is None:
            continue
        for actor_id in event.actor_ids:
            by_actor[actor_id].append(event)

    for actor_id, actor_events in by_actor.items():
        actor_events.sort(key=lambda item: (item.start_second, item.end_second, item.event_id))
        previous: CaseEvent | None = None
        for event in actor_events:
            if previous is None:
                previous = event
                continue
            if previous.location_id == event.location_id:
                if event.end_second > previous.end_second:
                    previous = event
                continue

            if event.start_second <= previous.end_second:
                findings.append(
                    _finding(
                        "CASE.ACTOR.DOUBLE_LOCATION",
                        (
                            f"actor {actor_id} is placed at {previous.location_id} and "
                            f"{event.location_id} at overlapping time"
                        ),
                        actor_id,
                        previous.event_id,
                        event.event_id,
                    )
                )
                if event.end_second > previous.end_second:
                    previous = event
                continue

            assert previous.location_id is not None
            assert event.location_id is not None
            rule = travel_rules.get((previous.location_id, event.location_id))
            if rule is None:
                findings.append(
                    _finding(
                        "CASE.TRAVEL.RULE_MISSING",
                        (
                            f"cannot prove travel feasibility for actor {actor_id}: "
                            f"{previous.location_id} -> {event.location_id}"
                        ),
                        actor_id,
                        previous.event_id,
                        event.event_id,
                    )
                )
            else:
                available = event.start_second - previous.end_second
                if available < rule.minimum_seconds:
                    findings.append(
                        _finding(
                            "CASE.TRAVEL.IMPOSSIBLE",
                            (
                                f"actor {actor_id} has {available}s for travel from "
                                f"{previous.location_id} to {event.location_id}; "
                                f"minimum is {rule.minimum_seconds}s"
                            ),
                            actor_id,
                            previous.event_id,
                            event.event_id,
                        )
                    )
            previous = event


def _time_is_inside_event(at_second: int, event: CaseEvent) -> bool:
    return event.start_second <= at_second <= event.end_second


def _validate_knowledge(
    event_by_id: Mapping[str, CaseEvent],
    acquisitions: Sequence[KnowledgeAcquisition],
    uses: Sequence[KnowledgeUse],
    initial_knowledge: Mapping[str, frozenset[str]],
    findings: list[ValidationFinding],
) -> None:
    first_acquisition: dict[tuple[str, str], int] = {}

    for acquisition in acquisitions:
        event = event_by_id.get(acquisition.event_id)
        if event is None:
            findings.append(
                _finding(
                    "CASE.KNOWLEDGE.EVENT_MISSING",
                    (f"knowledge acquisition references missing event {acquisition.event_id}"),
                    acquisition.character_id,
                    acquisition.fact_id,
                    acquisition.event_id,
                )
            )
            continue
        if not _time_is_inside_event(acquisition.at_second, event):
            findings.append(
                _finding(
                    "CASE.KNOWLEDGE.TIME_OUTSIDE_EVENT",
                    (
                        "knowledge acquisition for "
                        f"{acquisition.character_id}/{acquisition.fact_id} occurs "
                        f"outside event {acquisition.event_id}"
                    ),
                    acquisition.character_id,
                    acquisition.fact_id,
                    acquisition.event_id,
                )
            )
            continue
        key = (acquisition.character_id, acquisition.fact_id)
        current = first_acquisition.get(key)
        if current is None or acquisition.at_second < current:
            first_acquisition[key] = acquisition.at_second

    for use in uses:
        event = event_by_id.get(use.event_id)
        if event is None:
            findings.append(
                _finding(
                    "CASE.KNOWLEDGE.EVENT_MISSING",
                    f"knowledge use references missing event {use.event_id}",
                    use.character_id,
                    use.fact_id,
                    use.event_id,
                )
            )
            continue
        if not _time_is_inside_event(use.at_second, event):
            findings.append(
                _finding(
                    "CASE.KNOWLEDGE.TIME_OUTSIDE_EVENT",
                    (
                        f"knowledge use for {use.character_id}/{use.fact_id} occurs "
                        f"outside event {use.event_id}"
                    ),
                    use.character_id,
                    use.fact_id,
                    use.event_id,
                )
            )
            continue
        if use.fact_id in initial_knowledge.get(use.character_id, frozenset()):
            continue
        acquired_at = first_acquisition.get((use.character_id, use.fact_id))
        if acquired_at is None or acquired_at > use.at_second:
            findings.append(
                _finding(
                    "CASE.KNOWLEDGE.USED_BEFORE_ACQUIRED",
                    (
                        f"{use.character_id} uses fact {use.fact_id} at "
                        f"{use.at_second} before any valid acquisition"
                    ),
                    use.character_id,
                    use.fact_id,
                    use.event_id,
                )
            )


def _clue_map(
    clues: Sequence[ClueRecord], findings: list[ValidationFinding]
) -> dict[str, ClueRecord]:
    result: dict[str, ClueRecord] = {}
    for clue in clues:
        if not clue.clue_id:
            findings.append(_finding("CASE.CLUE.EMPTY_ID", "clue must have a non-empty clue_id"))
            continue
        if clue.clue_id in result:
            findings.append(
                _finding(
                    "CASE.CLUE.DUPLICATE_ID",
                    f"duplicate clue id: {clue.clue_id}",
                    clue.clue_id,
                )
            )
            continue
        result[clue.clue_id] = clue
    return result


def _validate_clue_dependencies(
    clue_by_id: Mapping[str, ClueRecord], findings: list[ValidationFinding]
) -> None:
    graph: dict[str, tuple[str, ...]] = {}
    for clue in clue_by_id.values():
        valid_dependencies: list[str] = []
        for dependency_id in clue.dependency_clue_ids:
            if dependency_id not in clue_by_id:
                findings.append(
                    _finding(
                        "CASE.CLUE.DEPENDENCY_MISSING",
                        f"clue {clue.clue_id} depends on missing clue {dependency_id}",
                        clue.clue_id,
                        dependency_id,
                    )
                )
                continue
            valid_dependencies.append(dependency_id)
        graph[clue.clue_id] = tuple(valid_dependencies)

    visiting: set[str] = set()
    visited: set[str] = set()
    reported_cycles: set[frozenset[str]] = set()

    def visit(clue_id: str, path: tuple[str, ...]) -> None:
        if clue_id in visited:
            return
        if clue_id in visiting:
            try:
                start_index = path.index(clue_id)
            except ValueError:
                start_index = 0
            cycle = path[start_index:] + (clue_id,)
            cycle_key = frozenset(cycle)
            if cycle_key not in reported_cycles:
                reported_cycles.add(cycle_key)
                findings.append(
                    _finding(
                        "CASE.CLUE.DEPENDENCY_CYCLE",
                        "clue dependency cycle: " + " -> ".join(cycle),
                        *cycle,
                    )
                )
            return
        visiting.add(clue_id)
        for dependency_id in graph.get(clue_id, ()):
            visit(dependency_id, path + (clue_id,))
        visiting.remove(clue_id)
        visited.add(clue_id)

    for clue_id in graph:
        visit(clue_id, ())


def _validate_reader_order_fields(clue: ClueRecord, findings: list[ValidationFinding]) -> None:
    if clue.exposure_event_id is None and clue.exposure_order is not None:
        findings.append(
            _finding(
                "CASE.CLUE.EXPOSURE_EVENT_REQUIRED",
                (f"clue {clue.clue_id} has exposure_order without an exposure_event_id"),
                clue.clue_id,
            )
        )
    if clue.exposure_event_id is not None and clue.exposure_order is None:
        findings.append(
            _finding(
                "CASE.CLUE.EXPOSURE_ORDER_MISSING",
                (f"clue {clue.clue_id} has an exposure event but no reader exposure_order"),
                clue.clue_id,
                clue.exposure_event_id,
            )
        )
    if clue.payoff_event_id is None and clue.payoff_order is not None:
        findings.append(
            _finding(
                "CASE.CLUE.PAYOFF_EVENT_REQUIRED",
                f"clue {clue.clue_id} has payoff_order without payoff_event_id",
                clue.clue_id,
            )
        )
    if clue.payoff_event_id is not None and clue.payoff_order is None:
        findings.append(
            _finding(
                "CASE.CLUE.PAYOFF_ORDER_MISSING",
                (f"clue {clue.clue_id} has a payoff event but no reader payoff_order"),
                clue.clue_id,
                clue.payoff_event_id,
            )
        )
    if (
        clue.exposure_order is not None
        and clue.payoff_order is not None
        and clue.payoff_order < clue.exposure_order
    ):
        findings.append(
            _finding(
                "CASE.CLUE.PAYOFF_BEFORE_EXPOSURE",
                (
                    f"clue {clue.clue_id} payoff_order {clue.payoff_order} is "
                    f"before exposure_order {clue.exposure_order}"
                ),
                clue.clue_id,
            )
        )


def _validate_clues(
    clue_by_id: Mapping[str, ClueRecord],
    event_by_id: Mapping[str, CaseEvent],
    fair_play_mode: FairPlayMode,
    accepted_temporal_rule_refs: frozenset[str],
    findings: list[ValidationFinding],
) -> None:
    for clue in clue_by_id.values():
        _validate_reader_order_fields(clue, findings)
        origin = event_by_id.get(clue.origin_event_id)
        if origin is None:
            findings.append(
                _finding(
                    "CASE.CLUE.ORIGIN_MISSING",
                    (f"clue {clue.clue_id} references missing origin event {clue.origin_event_id}"),
                    clue.clue_id,
                    clue.origin_event_id,
                )
            )

        exposure: CaseEvent | None = None
        if clue.exposure_event_id is not None:
            exposure = event_by_id.get(clue.exposure_event_id)
            if exposure is None:
                findings.append(
                    _finding(
                        "CASE.CLUE.EXPOSURE_MISSING_EVENT",
                        (
                            f"clue {clue.clue_id} references missing exposure event "
                            f"{clue.exposure_event_id}"
                        ),
                        clue.clue_id,
                        clue.exposure_event_id,
                    )
                )

        if clue.payoff_event_id is not None:
            payoff = event_by_id.get(clue.payoff_event_id)
            if payoff is None:
                findings.append(
                    _finding(
                        "CASE.CLUE.PAYOFF_MISSING_EVENT",
                        (
                            f"clue {clue.clue_id} references missing payoff event "
                            f"{clue.payoff_event_id}"
                        ),
                        clue.clue_id,
                        clue.payoff_event_id,
                    )
                )

        if (
            clue.temporal_rule_ref is not None
            and clue.temporal_rule_ref not in accepted_temporal_rule_refs
        ):
            findings.append(
                _finding(
                    "CASE.CLUE.TEMPORAL_RULE_UNKNOWN",
                    (
                        f"clue {clue.clue_id} references unaccepted temporal rule "
                        f"{clue.temporal_rule_ref}"
                    ),
                    clue.clue_id,
                    clue.temporal_rule_ref,
                )
            )

        temporal_exception_valid = (
            clue.temporal_rule_ref is not None
            and clue.temporal_rule_ref in accepted_temporal_rule_refs
        )
        if (
            origin is not None
            and exposure is not None
            and exposure.start_second < origin.start_second
            and not temporal_exception_valid
        ):
            findings.append(
                _finding(
                    "CASE.CLUE.EXPOSED_BEFORE_ORIGIN",
                    (
                        f"clue {clue.clue_id} is exposed at event "
                        f"{exposure.event_id} before origin event {origin.event_id}"
                    ),
                    clue.clue_id,
                    origin.event_id,
                    exposure.event_id,
                )
            )

        if clue.decisive and clue.exposure_event_id is None:
            if fair_play_mode == "REQUIRED":
                severity: FindingSeverity = "BLOCKING"
            elif fair_play_mode == "EXPECTED":
                severity = "MAJOR"
            else:
                severity = "NOTE"
            findings.append(
                _finding(
                    "CASE.CLUE.DECISIVE_NOT_EXPOSED",
                    f"decisive clue {clue.clue_id} has no reader exposure event",
                    clue.clue_id,
                    severity=severity,
                )
            )

        if clue.decisive and clue.payoff_event_id is None:
            findings.append(
                _finding(
                    "CASE.CLUE.DECISIVE_NO_PAYOFF",
                    (f"decisive clue {clue.clue_id} has no payoff/recontextualization event"),
                    clue.clue_id,
                )
            )

    _validate_clue_dependencies(clue_by_id, findings)


def validate_case_integrity(
    *,
    events: Sequence[CaseEvent],
    travel_rules: Sequence[TravelRule] = (),
    acquisitions: Sequence[KnowledgeAcquisition] = (),
    uses: Sequence[KnowledgeUse] = (),
    initial_knowledge: Mapping[str, frozenset[str]] | None = None,
    clues: Sequence[ClueRecord] = (),
    fair_play_mode: FairPlayMode = "REQUIRED",
    accepted_temporal_rule_refs: frozenset[str] = frozenset(),
) -> CaseIntegrityResult:
    """Run deterministic case-integrity checks with no model/network dependency."""
    findings: list[ValidationFinding] = []
    event_by_id = _event_map(events, findings)
    unique_events = tuple(event_by_id.values())
    travel_rule_by_pair = _travel_rule_map(travel_rules, findings)
    _validate_actor_timeline(unique_events, travel_rule_by_pair, findings)
    _validate_knowledge(
        event_by_id,
        acquisitions,
        uses,
        initial_knowledge or {},
        findings,
    )
    clue_by_id = _clue_map(clues, findings)
    _validate_clues(
        clue_by_id,
        event_by_id,
        fair_play_mode,
        accepted_temporal_rule_refs,
        findings,
    )
    return CaseIntegrityResult(findings=tuple(findings))
