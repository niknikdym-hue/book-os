from __future__ import annotations

import json
from pathlib import Path
import sqlite3

from alembic import command
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DatabaseError

from book_os_core.authority import (
    AuthorityService,
    HumanApprovalRequired,
    InvalidAuthorityOperation,
    StaleBaselineError,
    canonical_json,
    content_hash,
    new_ulid,
)
from book_os_core.backup import (
    BackupIntegrityError,
    SchemaCompatibilityError,
    create_backup,
    restore_backup,
)
from book_os_core.db import alembic_config, create_database


def _service(tmp_path: Path) -> tuple[AuthorityService, Path]:
    path = tmp_path / "project.sqlite"
    return AuthorityService(create_database(path)), path


def _initial(service: AuthorityService):
    return service.register_entity(
        entity_type="test.contract",
        payload={"title": "Initial", "nested": {"b": 2, "a": 1}},
        schema_name="test.contract",
        schema_version="1",
        actor="owner",
    )


def test_fresh_and_m0_upgrade_preserve_fk_and_wal(tmp_path: Path) -> None:
    fresh = tmp_path / "fresh.sqlite"
    engine = create_database(fresh)
    with engine.connect() as connection:
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "0002"
        assert connection.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
        assert connection.execute(text("PRAGMA journal_mode")).scalar_one().lower() == "wal"

    upgraded = tmp_path / "upgrade.sqlite"
    config = alembic_config(upgraded)
    command.upgrade(config, "0001")
    with sqlite3.connect(upgraded) as connection:
        assert connection.execute("SELECT version_num FROM alembic_version").fetchone() == ("0001",)
    command.upgrade(config, "head")
    with sqlite3.connect(upgraded) as connection:
        assert connection.execute("SELECT version_num FROM alembic_version").fetchone() == ("0002",)
        names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert "authority_entities" in names
        assert "approvals" in names


def test_ulid_style_ids_are_sortable_length() -> None:
    first = new_ulid()
    second = new_ulid()
    assert len(first) == 26
    assert len(second) == 26
    assert first <= second or first[:10] == second[:10]


def test_canonical_hash_key_order_and_unicode_stability() -> None:
    left = {"b": 2, "a": "café", "nested": {"y": 1, "x": 2}}
    right = {"nested": {"x": 2, "y": 1}, "a": "cafe\u0301", "b": 2}
    assert canonical_json(left) == canonical_json(right)
    assert content_hash(left) == content_hash(right)
    assert content_hash(left) != content_hash({**left, "b": 3})


def test_revision_content_and_history_are_append_only(tmp_path: Path) -> None:
    service, _ = _service(tmp_path)
    head = _initial(service)
    with service.engine.begin() as connection:
        with pytest.raises(DatabaseError):
            connection.execute(
                text("UPDATE revisions SET content_json='{}' WHERE revision_id=:revision_id"),
                {"revision_id": head.revision_id},
            )
    assert service.get_revision(head.revision_id)["content"]["title"] == "Initial"


def test_review_status_transitions_are_bounded(tmp_path: Path) -> None:
    service, _ = _service(tmp_path)
    initial = _initial(service)
    draft_revision = service.create_revision(
        entity_id=initial.entity_id,
        payload={"title": "Draft"},
        schema_name="test.contract",
        schema_version="1",
        actor="owner",
        origin="HUMAN_WRITTEN",
        parent_revision_ids=(initial.revision_id,),
    )
    service.advance_revision_status(
        draft_revision, new_status="PROPOSED", actor="owner", reason="submit"
    )
    service.advance_revision_status(
        draft_revision, new_status="REVIEWED", actor="owner", reason="reviewed"
    )
    with pytest.raises(InvalidAuthorityOperation):
        service.advance_revision_status(
            draft_revision, new_status="APPROVED", actor="owner", reason="bypass approval"
        )


def test_accept_reject_and_stale_proposals(tmp_path: Path) -> None:
    service, _ = _service(tmp_path)
    initial = _initial(service)
    proposal_one = service.create_proposal(
        entity_id=initial.entity_id,
        base_revision_id=initial.revision_id,
        base_revision_hash=initial.revision_hash,
        proposed_payload={"title": "Accepted"},
        schema_name="test.contract",
        schema_version="1",
        rationale="improve",
        actor="owner",
        input_revision_ids=(initial.revision_id,),
    )
    proposal_stale = service.create_proposal(
        entity_id=initial.entity_id,
        base_revision_id=initial.revision_id,
        base_revision_hash=initial.revision_hash,
        proposed_payload={"title": "Stale"},
        schema_name="test.contract",
        schema_version="1",
        rationale="parallel idea",
        actor="owner",
    )
    accepted = service.accept_proposal(
        proposal_one,
        actor="owner",
        actor_kind="HUMAN",
        reason="approved",
        gates={"human_review": True},
    )
    new_head = service.get_head(initial.entity_id)
    assert new_head.revision_id == accepted.revision_id
    assert new_head.status == "APPROVED"
    history = service.history(initial.entity_id)
    assert len(history["revisions"]) == 2
    assert len(history["decisions"]) == 1
    assert len(history["approvals"]) == 1
    assert service.get_revision(initial.revision_id)["content"]["title"] == "Initial"

    before = service.history(initial.entity_id)
    with pytest.raises(StaleBaselineError):
        service.accept_proposal(
            proposal_stale,
            actor="owner",
            actor_kind="HUMAN",
            reason="should be stale",
            gates={"human_review": True},
        )
    after = service.history(initial.entity_id)
    assert service.get_head(initial.entity_id) == new_head
    assert len(after["revisions"]) == len(before["revisions"])
    assert len(after["decisions"]) == len(before["decisions"])
    assert len(after["approvals"]) == len(before["approvals"])

    reject = service.create_proposal(
        entity_id=new_head.entity_id,
        base_revision_id=new_head.revision_id,
        base_revision_hash=new_head.revision_hash,
        proposed_payload={"title": "Rejected"},
        schema_name="test.contract",
        schema_version="1",
        rationale="not good enough",
        actor="owner",
    )
    service.reject_proposal(reject, actor="owner", actor_kind="HUMAN", reason="no")
    assert service.get_head(initial.entity_id) == new_head


def test_ai_cannot_approve_material_authority(tmp_path: Path) -> None:
    service, _ = _service(tmp_path)
    initial = _initial(service)
    proposal = service.create_proposal(
        entity_id=initial.entity_id,
        base_revision_id=initial.revision_id,
        base_revision_hash=initial.revision_hash,
        proposed_payload={"title": "AI proposal"},
        schema_name="test.contract",
        schema_version="1",
        rationale="candidate",
        actor="writer-model",
        origin="AI_GENERATED",
    )
    with pytest.raises(HumanApprovalRequired):
        service.accept_proposal(
            proposal,
            actor="writer-model",
            actor_kind="AI",
            reason="self approve",
            gates={},
        )
    assert service.get_head(initial.entity_id) == initial


def test_decision_approval_and_provenance_are_append_only(tmp_path: Path) -> None:
    service, _ = _service(tmp_path)
    initial = _initial(service)
    proposal = service.create_proposal(
        entity_id=initial.entity_id,
        base_revision_id=initial.revision_id,
        base_revision_hash=initial.revision_hash,
        proposed_payload={"title": "Accepted"},
        schema_name="test.contract",
        schema_version="1",
        rationale="append-only test",
        actor="owner",
    )
    accepted = service.accept_proposal(
        proposal,
        actor="owner",
        actor_kind="HUMAN",
        reason="yes",
        gates={"human_review": True},
    )
    revision = service.get_revision(accepted.revision_id)
    with service.engine.begin() as connection:
        with pytest.raises(DatabaseError):
            connection.execute(
                text("UPDATE decisions SET reason='rewritten' WHERE decision_id=:id"),
                {"id": accepted.decision_id},
            )
    with service.engine.begin() as connection:
        with pytest.raises(DatabaseError):
            connection.execute(
                text("DELETE FROM approvals WHERE approval_id=:id"),
                {"id": accepted.approval_id},
            )
    with service.engine.begin() as connection:
        with pytest.raises(DatabaseError):
            connection.execute(
                text("UPDATE provenance_records SET actor='other' WHERE provenance_id=:id"),
                {"id": revision["provenance_id"]},
            )


def test_acceptance_fault_rolls_back_everything(tmp_path: Path) -> None:
    service, _ = _service(tmp_path)
    initial = _initial(service)
    proposal = service.create_proposal(
        entity_id=initial.entity_id,
        base_revision_id=initial.revision_id,
        base_revision_hash=initial.revision_hash,
        proposed_payload={"title": "Candidate"},
        schema_name="test.contract",
        schema_version="1",
        rationale="candidate",
        actor="owner",
    )
    before = service.history(initial.entity_id)

    def fail(point: str) -> None:
        if point == "after_decision":
            raise RuntimeError("injected write failure")

    with pytest.raises(RuntimeError, match="injected write failure"):
        service.accept_proposal(
            proposal,
            actor="owner",
            actor_kind="HUMAN",
            reason="approved",
            gates={"human_review": True},
            fault_injector=fail,
        )
    after = service.history(initial.entity_id)
    assert service.get_head(initial.entity_id) == initial
    assert len(after["revisions"]) == len(before["revisions"])
    assert len(after["decisions"]) == len(before["decisions"])
    assert len(after["approvals"]) == len(before["approvals"])
    with service.engine.connect() as connection:
        status = connection.execute(
            text("SELECT status FROM change_proposals WHERE proposal_id=:proposal_id"),
            {"proposal_id": proposal},
        ).scalar_one()
    assert status == "OPEN"


def test_lock_is_status_history_not_content_mutation(tmp_path: Path) -> None:
    service, _ = _service(tmp_path)
    initial = _initial(service)
    before_hash = service.get_revision(initial.revision_id)["content_hash"]
    service.lock_authority(initial.entity_id, actor="owner", actor_kind="HUMAN", reason="freeze")
    locked = service.get_head(initial.entity_id)
    assert locked.status == "LOCKED"
    assert service.get_revision(initial.revision_id)["content_hash"] == before_hash


def test_backup_restore_preserves_authority_history_and_detects_tamper(tmp_path: Path) -> None:
    service, db_path = _service(tmp_path)
    initial = _initial(service)
    proposal = service.create_proposal(
        entity_id=initial.entity_id,
        base_revision_id=initial.revision_id,
        base_revision_hash=initial.revision_hash,
        proposed_payload={"title": "Backup me", "unicode": "Привет"},
        schema_name="test.contract",
        schema_version="1",
        rationale="backup fixture",
        actor="owner",
    )
    service.accept_proposal(
        proposal,
        actor="owner",
        actor_kind="HUMAN",
        reason="accepted",
        gates={"human_review": True},
    )
    expected_head = service.get_head(initial.entity_id)
    expected_history = service.history(initial.entity_id)

    # Leave committed WAL activity present; SQLite's online backup API must still produce a consistent copy.
    with service.engine.begin() as connection:
        connection.execute(text("INSERT OR IGNORE INTO schema_metadata(version) VALUES ('wal-evidence')"))

    backup_dir = tmp_path / "backup"
    create_backup(db_path, backup_dir)
    restored_path = tmp_path / "restored" / "project.sqlite"
    restore_backup(backup_dir, restored_path)
    restored = AuthorityService(create_database(restored_path))
    assert restored.get_head(initial.entity_id) == expected_head
    restored_history = restored.history(initial.entity_id)
    for key in ("revisions", "proposals", "decisions", "approvals", "provenance"):
        assert len(restored_history[key]) == len(expected_history[key])

    tampered = tmp_path / "tampered"
    tampered.mkdir()
    (tampered / "project.sqlite").write_bytes((backup_dir / "project.sqlite").read_bytes() + b"x")
    (tampered / "manifest.json").write_bytes((backup_dir / "manifest.json").read_bytes())
    with pytest.raises(BackupIntegrityError, match="checksum"):
        restore_backup(tampered, tmp_path / "should-not-exist.sqlite")


def test_newer_schema_backup_is_rejected_explicitly(tmp_path: Path) -> None:
    service, db_path = _service(tmp_path)
    _initial(service)
    backup_dir = tmp_path / "backup"
    create_backup(db_path, backup_dir)
    manifest_path = backup_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["alembic_revision"] = "9999"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(SchemaCompatibilityError, match="newer"):
        restore_backup(backup_dir, tmp_path / "newer.sqlite")
