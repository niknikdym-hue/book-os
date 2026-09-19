from pathlib import Path
import sys
import threading
from typing import Any

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine


_MIGRATION_LOCK = threading.RLock()


def migration_root() -> Path:
    """Return the migration root for source and PyInstaller-frozen Local Core runtimes."""
    frozen_root = getattr(sys, "_MEIPASS", None)
    if isinstance(frozen_root, str) and frozen_root:
        return Path(frozen_root)
    return Path(__file__).parents[2]


def alembic_config(path: Path) -> Config:
    root = migration_root()
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{path}")
    return config


def create_database(path: Path) -> Engine:
    """Upgrade a local SQLite database to the current schema revision."""
    path.parent.mkdir(parents=True, exist_ok=True)
    # Alembic installs module-level proxy objects while a migration environment is active.
    # Local Core can serve UI reads while its durable Auto worker opens the same project, so
    # migration checks must be serialized even after a database has already reached head.
    with _MIGRATION_LOCK:
        command.upgrade(alembic_config(path), "head")

    engine = create_engine(f"sqlite:///{path}")

    @event.listens_for(engine, "connect")
    def configure_sqlite(connection: Any, _: Any) -> None:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    with engine.begin() as connection:
        connection.execute(text("PRAGMA foreign_keys=ON"))
        connection.execute(text("PRAGMA journal_mode=WAL"))
    return engine
