from __future__ import annotations

from pathlib import Path

from alembic import command
import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import IntegrityError

from book_os_core.authority import AuthorityService
from book_os_core.backup import create_backup, restore_backup
from book_os_core.db import alembic_config, create_database


def test_m1_backup_restores_then_migrates_forward_to_current(tmp_path: Path) -> None:
    source_path = tmp_path / "m1.sqlite"
    command.upgrade(alembic_config(source_path), "0002")
    engine = create_engine(f"sqlite:///{source_path}")

    @event.listens_for(engine, "connect")
    def configure_sqlite(connection, _) -> None:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    service = AuthorityService(engine)
    original = service.register_entity(
        entity_type="compat.contract",
        payload={"title": "M1 authority survives forward migrations"},
        schema_name="compat.contract",
        schema_version="1",
        actor="owner",
    )
    engine.dispose()

    backup_dir = tmp_path / "backup"
    create_backup(source_path, backup_dir)
    restored_path = tmp_path / "restored.sqlite"
    restore_backup(backup_dir, restored_path)

    restored_engine = create_engine(f"sqlite:///{restored_path}")
    with restored_engine.connect() as connection:
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            == "0002"
        )
    restored_engine.dispose()

    upgraded = create_database(restored_path)
    with upgraded.connect() as connection:
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            == "0027"
        )
    assert AuthorityService(upgraded).get_head(original.entity_id) == original


def test_0024_migration_separates_series_origin_from_lifecycle(tmp_path: Path) -> None:
    database_path = tmp_path / "series-0023.sqlite"
    command.upgrade(alembic_config(database_path), "0023")
    engine = create_engine(f"sqlite:///{database_path}")
    now = "2026-09-13T00:00:00Z"
    rows = [
        ("B" * 26, "S" * 26, "IMPORTED", "IDEA"),
        ("C" * 26, "T" * 26, "BOOK_OS", "READY"),
        ("D" * 26, "U" * 26, "PLANNED", "WRITING"),
    ]
    with engine.begin() as connection:
        for ordinal, (book_id, membership_id, source_kind, status) in enumerate(rows, start=1):
            connection.execute(
                text(
                    "INSERT INTO book_projects(book_id,working_title,mode,domain,primary_subtype,"
                    "profile_version,workflow_stage,created_at,updated_at) VALUES "
                    "(:book,:title,'BOOK_FROM_ZERO','BUSINESS_NONFICTION','Strategy','0.1',"
                    "'BOOK_DEFINITION',:created,:updated)"
                ),
                {"book": book_id, "title": f"Book {ordinal}", "created": now, "updated": now},
            )
            connection.execute(
                text(
                    "INSERT INTO series_books(series_book_id,series_profile_id,book_id,ordinal,"
                    "unique_idea,reader_problem,reader_result,unique_mechanism,excluded_topics_json,"
                    "source_kind,status,created_at,updated_at) VALUES "
                    "(:membership,:series,:book,:ordinal,'idea','problem','result','mechanism','[]',"
                    ":source,:status,:created,:updated)"
                ),
                {
                    "membership": membership_id,
                    "series": "V" * 26,
                    "book": book_id,
                    "ordinal": ordinal,
                    "source": source_kind,
                    "status": status,
                    "created": now,
                    "updated": now,
                },
            )
    engine.dispose()

    command.upgrade(alembic_config(database_path), "0024")
    upgraded = create_engine(f"sqlite:///{database_path}")
    with upgraded.connect() as connection:
        migrated = connection.execute(
            text(
                "SELECT source_kind,origin_kind,lifecycle,legacy_content_allowed "
                "FROM series_books ORDER BY ordinal"
            )
        ).all()
    upgraded.dispose()

    assert migrated == [
        ("IMPORTED", "IMPORTED", "PLANNED", 1),
        ("BOOK_OS", "CURRENT_REWRITTEN", "COMPLETED", 0),
        ("PLANNED", "NEW", "WRITING", 0),
    ]


def test_0027_preserves_human_vs_delegated_master_history_and_append_only_guard(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "master-0026.sqlite"
    command.upgrade(alembic_config(database_path), "0026")
    engine = create_engine(f"sqlite:///{database_path}")
    now = "2026-09-14T00:00:00Z"
    book_id = "L" * 26
    contract_entity = "E" * 26
    architecture_entity = "F" * 26
    contract_revision = "R" * 26
    architecture_revision = "S" * 26
    contract_hash = "1" * 64
    architecture_hash = "2" * 64
    with engine.begin() as connection:
        # This fixture represents historical masters written before the adversarial-review release
        # gate existed. Disable that current insert guard only while constructing the legacy state.
        connection.execute(
            text("DROP TRIGGER IF EXISTS require_adversarial_review_for_literary_master")
        )
        connection.execute(
            text(
                "INSERT INTO book_projects(book_id,working_title,mode,domain,primary_subtype,"
                "profile_version,workflow_stage,created_at,updated_at) VALUES "
                "(:book,'Migration fixture','BOOK_FROM_ZERO','BUSINESS_NONFICTION','Strategy',"
                "'0.1','FINAL_REVIEW',:created,:updated)"
            ),
            {"book": book_id, "created": now, "updated": now},
        )
        for provenance_id, entity_id, revision_id, revision_hash, entity_type in (
            ("P" * 26, contract_entity, contract_revision, contract_hash, "book.contract"),
            (
                "Q" * 26,
                architecture_entity,
                architecture_revision,
                architecture_hash,
                "book.architecture",
            ),
        ):
            connection.execute(
                text(
                    "INSERT INTO provenance_records(provenance_id,origin,actor,created_at) "
                    "VALUES (:provenance,'HUMAN_WRITTEN','owner',:created)"
                ),
                {"provenance": provenance_id, "created": now},
            )
            connection.execute(
                text(
                    "INSERT INTO authority_entities(entity_id,entity_type,created_at) "
                    "VALUES (:entity,:entity_type,:created)"
                ),
                {"entity": entity_id, "entity_type": entity_type, "created": now},
            )
            connection.execute(
                text(
                    "INSERT INTO revisions(revision_id,entity_id,entity_type,schema_name,"
                    "schema_version,content_json,content_hash,provenance_id,created_at) VALUES "
                    "(:revision,:entity,:entity_type,:entity_type,'1','{}',:hash,:provenance,:created)"
                ),
                {
                    "revision": revision_id,
                    "entity": entity_id,
                    "entity_type": entity_type,
                    "hash": revision_hash,
                    "provenance": provenance_id,
                    "created": now,
                },
            )
        for master_id, manifest_hash, actor in (
            ("A" * 64, "3" * 64, "OWNER Auto Book 01JLEGACYRUN00000000000000"),
            ("B" * 64, "4" * 64, "Елена Дым"),
        ):
            connection.execute(
                text(
                    "INSERT INTO literary_masters(master_id,book_id,manifest_version,manifest_json,"
                    "manifest_hash,book_title,book_contract_revision_id,book_contract_revision_hash,"
                    "architecture_revision_id,architecture_revision_hash,ordered_manifest_json,"
                    "canonical_content_hash,release_gate_json,human_actor,created_at,status) VALUES "
                    "(:master,:book,'literary-master.v1','{}',:manifest,'Migration fixture',"
                    ":contract_revision,:contract_hash,:architecture_revision,:architecture_hash,"
                    "'[]',:canonical,'{}',:actor,:created,'LOCKED')"
                ),
                {
                    "master": master_id,
                    "book": book_id,
                    "manifest": manifest_hash,
                    "contract_revision": contract_revision,
                    "contract_hash": contract_hash,
                    "architecture_revision": architecture_revision,
                    "architecture_hash": architecture_hash,
                    "canonical": "5" * 64 if master_id.startswith("A") else "6" * 64,
                    "actor": actor,
                    "created": now,
                },
            )
    engine.dispose()

    command.upgrade(alembic_config(database_path), "0027")
    upgraded = create_engine(f"sqlite:///{database_path}")
    with upgraded.connect() as connection:
        rows = connection.execute(
            text(
                "SELECT human_actor,acceptance_actor_kind FROM literary_masters "
                "ORDER BY human_actor"
            )
        ).all()
    assert rows == [
        ("OWNER Auto Book 01JLEGACYRUN00000000000000", "DELEGATED"),
        ("Елена Дым", "HUMAN"),
    ]
    with pytest.raises(IntegrityError, match="append-only"):
        with upgraded.begin() as connection:
            connection.execute(
                text("UPDATE literary_masters SET book_title='forbidden' WHERE master_id=:master"),
                {"master": "A" * 64},
            )
    upgraded.dispose()
