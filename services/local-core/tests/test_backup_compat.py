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
            == "0010"
        )
    assert AuthorityService(upgraded).get_head(original.entity_id) == original
