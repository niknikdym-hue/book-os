from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DatabaseError

from book_os_core.authority import AuthorityService, new_ulid
from book_os_core.authority_types import utc_now
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
    return (
        ProjectService(data_dir)
        .create_project(
            NewBookRequest(working_title="Private Pilot Book", primary_subtype="Strategy")
        )
        .book_id
    )


def test_fresh_project_migrates_to_0010_and_only_one_active_pilot(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    book_id = _project(data_dir)
    database = data_dir / "projects" / book_id / "project.sqlite"
    engine = create_database(database)
    try:
        with engine.connect() as connection:
            assert (
                connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                == "0010"
            )
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
            revisions_before = connection.execute(
                text("SELECT COUNT(*) FROM revisions")
            ).scalar_one()
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
    with pytest.raises(PilotGateError, match="requires HUMAN resolution"):
        service.resolve_observation(
            book_id,
            pilot.pilot_id,
            observation.observation_id,
            actor="system",
            actor_kind="SYSTEM",
            reason="Automation cannot clear blocking evidence.",
        )
    assert "PILOT_BLOCKING_OBSERVATIONS:1" in summary.go_no_go.blockers

    all_observations = service.list_observations(book_id, pilot.pilot_id)
    open_observations = service.list_observations(book_id, pilot.pilot_id, open_only=True)
    assert [item.observation_id for item in all_observations] == [observation.observation_id]
    assert [item.observation_id for item in open_observations] == [observation.observation_id]

    resolved = service.resolve_observation(
        book_id,
        pilot.pilot_id,
        observation.observation_id,
        actor="Elena",
        actor_kind="HUMAN",
        reason="Synthetic resolution fixture.",
    )
    assert resolved.resolved_at is not None
    assert service.list_observations(book_id, pilot.pilot_id, open_only=True) == []
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
            revisions_after = connection.execute(
                text("SELECT COUNT(*) FROM revisions")
            ).scalar_one()
    finally:
        engine.dispose()
    assert revisions_after == revisions_before


def test_openai_preflight_is_zero_call_and_secret_safe() -> None:
    secret = "SENTINEL_OPENAI_SECRET_DO_NOT_LEAK"
    available = PilotService.openai_preflight(
        DictSecretStore({"openai_api_key": secret}),
        book_id="BOOK1",
        pilot_id="PILOT1",
        writer_model="writer-model",
        evaluator_model="evaluator-model",
        max_requests=3,
        max_input_tokens=1000,
        max_output_tokens=500,
        max_cost_usd=1.25,
    )
    missing = PilotService.openai_preflight(
        DictSecretStore({}),
        book_id="BOOK1",
        pilot_id="PILOT1",
        writer_model="writer-model",
        evaluator_model="evaluator-model",
        max_requests=3,
        max_input_tokens=1000,
        max_output_tokens=500,
        max_cost_usd=1.25,
    )
    assert available.credential_state == "AVAILABLE"
    assert missing.credential_state == "NOT_AVAILABLE"
    assert available.external_calls == 0
    assert available.paid_calls == 0
    assert available.max_requests == 3
    assert len(available.plan_hash) == 64
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
            actor_kind=cast(Any, "SYSTEM"),
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
                    text("UPDATE pilot_runs SET final_decision='GO' WHERE pilot_id=:pilot_id"),
                    {"pilot_id": pilot.pilot_id},
                )
    finally:
        engine.dispose()


def test_checkpoint_does_not_complete_mandatory_stage(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    book_id = _project(data_dir)
    service = PilotService(data_dir)
    pilot = service.start(book_id, human_actor="Elena")
    service.record_stage_event(
        book_id,
        pilot.pilot_id,
        PilotStageEventRequest(
            stage="IDEA",
            event_kind="CHECKPOINT",
            actor="Elena",
            actor_kind="HUMAN",
            outcome="SUCCESS",
        ),
    )
    summary = service.summary(book_id, pilot.pilot_id)
    assert summary.stage_event_counts.get("IDEA", 0) == 0
    assert any(
        blocker.startswith("MISSING_STAGES:") and "IDEA" in blocker
        for blocker in summary.go_no_go.blockers
    )


def test_human_review_event_kinds_require_human_and_detail(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    book_id = _project(data_dir)
    service = PilotService(data_dir)
    pilot = service.start(book_id, human_actor="Elena")
    with pytest.raises(PilotGateError, match="must be HUMAN"):
        service.record_stage_event(
            book_id,
            pilot.pilot_id,
            PilotStageEventRequest(
                stage="BOOKBENCH",
                event_kind="DEFECT_REVIEW",
                actor="AI",
                actor_kind="AI",
                outcome="SUCCESS",
                metadata={"reason": "invalid"},
            ),
        )
    with pytest.raises(PilotGateError, match="requires nonblank judgment"):
        service.record_stage_event(
            book_id,
            pilot.pilot_id,
            PilotStageEventRequest(
                stage="FINAL_REVIEW",
                event_kind="LITERARY_QUALITY_JUDGMENT",
                actor="Elena",
                actor_kind="HUMAN",
                outcome="SUCCESS",
                metadata={},
            ),
        )


def test_db_rejects_nonhuman_review_and_incomplete_final_decision(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    book_id = _project(data_dir)
    service = PilotService(data_dir)
    pilot = service.start(book_id, human_actor="Elena")
    database = data_dir / "projects" / book_id / "project.sqlite"
    engine = create_database(database)
    try:
        with pytest.raises(DatabaseError):
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO pilot_stage_events("
                        "event_id,pilot_id,stage,event_kind,actor,actor_kind,outcome,metadata_json,created_at) "
                        "VALUES (:event_id,:pilot_id,'FINAL_REVIEW','LITERARY_QUALITY_JUDGMENT',"
                        "'AI','AI','SUCCESS','{\"judgment\":\"invalid\"}',:created_at)"
                    ),
                    {
                        "event_id": "E" * 26,
                        "pilot_id": pilot.pilot_id,
                        "created_at": "9999-01-01T00:00:00Z",
                    },
                )
        with pytest.raises(DatabaseError):
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "UPDATE pilot_runs SET final_decision='GO',decision_actor='Elena',"
                        "decision_actor_kind='HUMAN' WHERE pilot_id=:pilot_id"
                    ),
                    {"pilot_id": pilot.pilot_id},
                )
    finally:
        engine.dispose()


def test_db_rejects_system_resolution_of_blocking_observation(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    book_id = _project(data_dir)
    service = PilotService(data_dir)
    pilot = service.start(book_id, human_actor="Elena")
    observation = service.add_observation(
        book_id,
        pilot.pilot_id,
        PilotObservationRequest(
            stage="IDEA",
            category="PRODUCT_DEFECT",
            severity="BLOCKING",
            actor="Elena",
            actor_kind="HUMAN",
            description="Synthetic blocking fixture",
        ),
    )
    database = data_dir / "projects" / book_id / "project.sqlite"
    engine = create_database(database)
    try:
        with pytest.raises(DatabaseError):
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "UPDATE pilot_observations SET resolved_at='9999-01-01T00:00:00Z',"
                        "resolution_actor='system',resolution_actor_kind='SYSTEM',"
                        "resolution_reason='invalid' WHERE observation_id=:observation_id"
                    ),
                    {"observation_id": observation.observation_id},
                )
    finally:
        engine.dispose()


def test_material_claim_must_be_positively_supported_for_go_readiness(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    book_id = _project(data_dir)
    service = PilotService(data_dir)
    pilot = service.start(book_id, human_actor="Elena")
    database = data_dir / "projects" / book_id / "project.sqlite"
    engine = create_database(database)
    authority = AuthorityService(engine)
    manuscript = authority.register_entity(
        entity_type="manuscript.unit",
        payload={"text": "Synthetic claim source text."},
        schema_name="manuscript.unit.section.v0.1",
        schema_version="1",
        actor="Owner",
        initial_status="DRAFT",
    )
    chapter_id = new_ulid()
    unit_id = new_ulid()
    now = utc_now()
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO chapters("
                    "chapter_id,book_id,ordinal,working_title,architecture_role,workflow_state,"
                    "created_at,updated_at) VALUES "
                    "(:chapter_id,:book_id,1,'Synthetic Chapter','Evidence fixture','CURRENT',:now,:now)"
                ),
                {"chapter_id": chapter_id, "book_id": book_id, "now": now},
            )
            connection.execute(
                text(
                    "INSERT INTO manuscript_units("
                    "unit_id,book_id,chapter_id,unit_type,ordinal,authority_entity_id,created_at,updated_at) "
                    "VALUES (:unit_id,:book_id,:chapter_id,'SECTION',1,:entity_id,:now,:now)"
                ),
                {
                    "unit_id": unit_id,
                    "book_id": book_id,
                    "chapter_id": chapter_id,
                    "entity_id": manuscript.entity_id,
                    "now": now,
                },
            )
            connection.execute(
                text(
                    "INSERT INTO claims("
                    "claim_id,book_id,chapter_id,unit_id,manuscript_revision_id,manuscript_revision_hash,"
                    "normalized_text,claim_type,materiality,required_evidence_level,verification_state,"
                    "created_at,updated_at) VALUES "
                    "(:claim_id,:book_id,:chapter_id,:unit_id,:revision_id,:revision_hash,"
                    "'Material fact','EMPIRICAL','HIGH','TRACEABLE_SOURCE','UNREVIEWED',:now,:now)"
                ),
                {
                    "claim_id": new_ulid(),
                    "book_id": book_id,
                    "chapter_id": chapter_id,
                    "unit_id": unit_id,
                    "revision_id": manuscript.revision_id,
                    "revision_hash": manuscript.revision_hash,
                    "now": now,
                },
            )
    finally:
        engine.dispose()
    summary = service.summary(book_id, pilot.pilot_id)
    assert summary.material_claims_not_supported == 1
    assert "MATERIAL_RESEARCH_NOT_SUPPORTED:1" in summary.go_no_go.blockers
