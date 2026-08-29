from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DatabaseError

from book_os_core.db import create_database
from book_os_core.pilot import (
    PilotGateError,
    PilotObservationRequest,
    PilotService,
    PilotStageEventRequest,
)
from book_os_core.projects import NewBookRequest, ProjectService
from book_os_core.secrets import DictSecretStore


def _project(data_dir: Path) -> str:
    return ProjectService(data_dir).create_project(
        NewBookRequest(working_title="Private Pilot Book", primary_subtype="Strategy")
    ).book_id


def test_fresh_project_migrates_to_0010_and_only_one_active_pilot(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    book_id = _project(data_dir)
    database = data_dir / "projects" / book_id / "project.sqlite"
    engine = create_database(database)
    try:
        with engine.connect() as connection:
            assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "0010"
    finally:
        engine.dispose()

    service = PilotService(data_dir)
    with pytest.raises(PilotGateError, match="human actor"):
        service.start(book_id, human_actor="  ")
    first = service.start(book_id, human_actor="Elena")
    assert first.status == "ACTIVE"
    assert service.active(book_id) == first
    with pytest.raises(PilotGateError, match="active pilot"):
        service.start(book_id, human_actor="Elena")


def test_pilot_events_and_observations_do_not_mutate_authority(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    book_id = _project(data_dir)
    service = PilotService(data_dir)
    pilot = service.start(book_id, human_actor="Elena")
    database = data_dir / "projects" / book_id / "project.sqlite"
    engine = create_database(database)
    try:
        with engine.connect() as connection:
            revisions_before = connection.execute(text("SELECT COUNT(*) FROM revisions")).scalar_one()
    finally:
        engine.dispose()

    with pytest.raises(PilotGateError, match="requires a reason"):
        service.record_stage_event(
            book_id,
            pilot.pilot_id,
            PilotStageEventRequest(
                stage="BOOK_MEMORY",
                event_kind="NOT_APPLICABLE",
                actor="Elena",
                actor_kind="HUMAN",
                outcome="NOT_APPLICABLE",
            ),
        )

    event = service.record_stage_event(
        book_id,
        pilot.pilot_id,
        PilotStageEventRequest(
            stage="IDEA",
            event_kind="COMPLETED",
            actor="Elena",
            actor_kind="HUMAN",
            human_minutes=12,
            outcome="SUCCESS",
            metadata={"decision_ref": "local-private"},
        ),
    )
    assert event.stage == "IDEA"

    observation = service.add_observation(
        book_id,
        pilot.pilot_id,
        PilotObservationRequest(
            stage="IDEA",
            category="WORKFLOW_FRICTION",
            severity="BLOCKING",
            actor="Elena",
            actor_kind="HUMAN",
            description="Synthetic local-only friction fixture.",
        ),
    )
    summary = service.summary(book_id, pilot.pilot_id)
    assert summary.open_observations_by_severity["BLOCKING"] == 1
    assert "PILOT_BLOCKING_OBSERVATIONS:1" in summary.go_no_go.blockers

    resolved = service.resolve_observation(
        book_id,
        pilot.pilot_id,
        observation.observation_id,
        actor="Elena",
        actor_kind="HUMAN",
        reason="Synthetic resolution fixture.",
    )
    assert resolved.resolved_at is not None
    with pytest.raises(PilotGateError, match="already resolved"):
        service.resolve_observation(
            book_id,
            pilot.pilot_id,
            observation.observation_id,
            actor="Elena",
            actor_kind="HUMAN",
            reason="Second resolution is forbidden.",
        )

    engine = create_database(database)
    try:
        with engine.connect() as connection:
            revisions_after = connection.execute(text("SELECT COUNT(*) FROM revisions")).scalar_one()
    finally:
        engine.dispose()
    assert revisions_after == revisions_before


def test_openai_preflight_is_zero_call_and_secret_safe() -> None:
    secret = "SENTINEL_OPENAI_SECRET_DO_NOT_LEAK"
    available = PilotService.openai_preflight(
        DictSecretStore({"openai_api_key": secret}),
        writer_model="writer-model",
        evaluator_model="evaluator-model",
    )
    missing = PilotService.openai_preflight(
        DictSecretStore({}),
        writer_model="writer-model",
        evaluator_model="evaluator-model",
    )
    assert available.credential_state == "AVAILABLE"
    assert missing.credential_state == "NOT_AVAILABLE"
    assert available.external_calls == 0
    assert available.paid_calls == 0
    assert secret not in available.model_dump_json()


def test_final_decision_requires_ready_evidence_and_is_human_and_immutable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data_dir = tmp_path / "data"
    book_id = _project(data_dir)
    service = PilotService(data_dir)
    pilot = service.start(book_id, human_actor="Elena")

    with pytest.raises(PilotGateError, match="evidence is not ready"):
        service.record_final_decision(
            book_id,
            pilot.pilot_id,
            decision="GO",
            actor="Elena",
            actor_kind="HUMAN",
            reason="Too early.",
        )

    monkeypatch.setattr(
        service,
        "summary",
        lambda _book_id, _pilot_id: SimpleNamespace(
            go_no_go=SimpleNamespace(ready=True, blockers=[])
        ),
    )
    with pytest.raises(PilotGateError, match="must be HUMAN"):
        service.record_final_decision(
            book_id,
            pilot.pilot_id,
            decision="GO",
            actor="system",
            actor_kind=cast("HUMAN", "SYSTEM"),
            reason="Invalid actor.",
        )

    completed = service.record_final_decision(
        book_id,
        pilot.pilot_id,
        decision="CONDITIONAL_GO",
        actor="Elena",
        actor_kind="HUMAN",
        reason="Synthetic evidence-complete fixture.",
    )
    assert completed.status == "COMPLETED"
    assert completed.final_decision == "CONDITIONAL_GO"

    with pytest.raises(PilotGateError, match="already immutable"):
        service.record_final_decision(
            book_id,
            pilot.pilot_id,
            decision="GO",
            actor="Elena",
            actor_kind="HUMAN",
            reason="Cannot overwrite.",
        )

    database = data_dir / "projects" / book_id / "project.sqlite"
    engine = create_database(database)
    try:
        with pytest.raises(DatabaseError):
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "UPDATE pilot_runs SET final_decision='GO' WHERE pilot_id=:pilot_id"
                    ),
                    {"pilot_id": pilot.pilot_id},
                )
    finally:
        engine.dispose()
