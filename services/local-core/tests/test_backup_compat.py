from __future__ import annotations

from pathlib import Path

from alembic import command
from sqlalchemy import create_engine, event, text

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
            == "0025"
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
