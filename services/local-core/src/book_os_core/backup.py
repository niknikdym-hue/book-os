from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any

SUPPORTED_ALEMBIC_REVISION = "0006"
MIN_RESTORABLE_ALEMBIC_REVISION = "0002"
BACKUP_FORMAT_VERSION = 1
DOWNGRADE_POLICY = (
    "No silent automatic downgrade. Older supported backups restore at their recorded schema and "
    "are migrated forward by normal application migrations when opened."
)


class BackupError(RuntimeError):
    pass


class BackupIntegrityError(BackupError):
    pass


class SchemaCompatibilityError(BackupError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _alembic_revision(connection: sqlite3.Connection) -> str:
    row = connection.execute("SELECT version_num FROM alembic_version").fetchone()
    if row is None:
        raise BackupIntegrityError("database has no Alembic revision")
    return str(row[0])


def _integrity_check(connection: sqlite3.Connection) -> None:
    row = connection.execute("PRAGMA integrity_check").fetchone()
    if row is None or row[0] != "ok":
        raise BackupIntegrityError(f"SQLite integrity check failed: {row}")


def create_backup(
    source_database: Path,
    backup_directory: Path,
    *,
    app_version: str = "0.1.0",
) -> tuple[Path, Path]:
    """Create a consistent SQLite backup using SQLite's online backup API."""
    backup_directory.mkdir(parents=True, exist_ok=True)
    database_backup = backup_directory / "project.sqlite"
    manifest_path = backup_directory / "manifest.json"
    if database_backup.exists() or manifest_path.exists():
        raise BackupError("backup destination must be empty")

    source = sqlite3.connect(source_database)
    destination = sqlite3.connect(database_backup)
    try:
        source.execute("PRAGMA foreign_keys=ON")
        _integrity_check(source)
        schema_revision = _alembic_revision(source)
        source.backup(destination)
        destination.commit()
        _integrity_check(destination)
    finally:
        destination.close()
        source.close()

    checksum = _sha256(database_backup)
    manifest: dict[str, Any] = {
        "backup_format_version": BACKUP_FORMAT_VERSION,
        "created_at": _utc_now(),
        "app_version": app_version,
        "alembic_revision": schema_revision,
        "supported_schema_revision": SUPPORTED_ALEMBIC_REVISION,
        "minimum_restorable_schema_revision": MIN_RESTORABLE_ALEMBIC_REVISION,
        "database_sha256": checksum,
        "database_file": database_backup.name,
        "downgrade_policy": DOWNGRADE_POLICY,
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return database_backup, manifest_path


def restore_backup(
    backup_directory: Path,
    destination_database: Path,
    *,
    supported_revision: str = SUPPORTED_ALEMBIC_REVISION,
    minimum_revision: str = MIN_RESTORABLE_ALEMBIC_REVISION,
) -> None:
    """Validate a backup before restoring its exact recorded schema into a fresh path."""
    manifest_path = backup_directory / "manifest.json"
    if not manifest_path.is_file():
        raise BackupIntegrityError("backup manifest is missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("backup_format_version") != BACKUP_FORMAT_VERSION:
        raise BackupIntegrityError("unsupported backup format version")

    schema_revision = str(manifest.get("alembic_revision", ""))
    if schema_revision > supported_revision:
        raise SchemaCompatibilityError(
            f"backup schema {schema_revision} is newer than supported {supported_revision}"
        )
    if schema_revision < minimum_revision:
        raise SchemaCompatibilityError(
            f"backup schema {schema_revision} is older than minimum restorable {minimum_revision}"
        )

    database_backup = backup_directory / str(manifest.get("database_file", "project.sqlite"))
    if not database_backup.is_file():
        raise BackupIntegrityError("backup database file is missing")
    expected_checksum = str(manifest.get("database_sha256", ""))
    actual_checksum = _sha256(database_backup)
    if not expected_checksum or actual_checksum != expected_checksum:
        raise BackupIntegrityError("backup database checksum mismatch")
    if destination_database.exists():
        raise BackupError("restore destination must not already exist")
    destination_database.parent.mkdir(parents=True, exist_ok=True)

    source = sqlite3.connect(database_backup)
    try:
        _integrity_check(source)
        actual_schema = _alembic_revision(source)
        if actual_schema != schema_revision:
            raise BackupIntegrityError("manifest schema revision does not match backup database")
        destination = sqlite3.connect(destination_database)
        try:
            source.backup(destination)
            destination.commit()
            destination.execute("PRAGMA foreign_keys=ON")
            _integrity_check(destination)
            restored_schema = _alembic_revision(destination)
            if restored_schema != schema_revision:
                raise BackupIntegrityError(
                    "restored database schema does not match the backup manifest"
                )
        except Exception:
            destination.close()
            destination_database.unlink(missing_ok=True)
            raise
        else:
            destination.close()
    finally:
        source.close()
