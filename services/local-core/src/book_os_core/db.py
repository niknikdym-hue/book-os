from pathlib import Path
from typing import Any
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine


def create_database(path: Path) -> Engine:
    engine = create_engine(f"sqlite:///{path}")

    @event.listens_for(engine, "connect")
    def configure_sqlite(connection: Any, _: Any) -> None:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    with engine.begin() as connection:
        connection.execute(
            text("CREATE TABLE IF NOT EXISTS schema_metadata (version TEXT PRIMARY KEY NOT NULL)")
        )
        connection.execute(text("INSERT OR IGNORE INTO schema_metadata(version) VALUES ('0001')"))
    return engine
