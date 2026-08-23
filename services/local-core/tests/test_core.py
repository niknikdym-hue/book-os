from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import text
from book_os_core.app import create_app
from book_os_core.db import create_database


def test_health_requires_session_token() -> None:
    client = TestClient(create_app("test-token"))
    assert client.get("/health").status_code == 401
    assert (
        client.get("/health", headers={"Authorization": "Bearer test-token"}).json()["status"]
        == "healthy"
    )


def test_database_enables_foreign_keys_and_wal(tmp_path: Path) -> None:
    engine = create_database(tmp_path / "fresh.sqlite")
    with engine.connect() as connection:
        assert connection.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
        assert connection.execute(text("PRAGMA journal_mode")).scalar_one() == "wal"
        assert (
            connection.execute(text("SELECT version FROM schema_metadata")).scalar_one() == "0001"
        )
