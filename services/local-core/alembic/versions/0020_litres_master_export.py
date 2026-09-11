"""Allow LitRes DOCX as a Literary Master export.

Revision ID: 0020
Revises: 0019
Create Date: 2026-09-11
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0020"
down_revision: str | None = "0019"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _create_exports_table() -> None:
    op.create_table(
        "literary_master_exports",
        sa.Column("export_id", sa.String(64), primary_key=True),
        sa.Column("master_id", sa.String(64), nullable=False),
        sa.Column("format", sa.String(32), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("byte_length", sa.Integer(), nullable=False),
        sa.Column("relative_path", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["master_id"], ["literary_masters.master_id"]),
        sa.UniqueConstraint("master_id", "format", name="uq_literary_master_export_format"),
        sa.CheckConstraint(
            "format IN ('MARKDOWN','AUDIOBOOK_HANDOFF_JSON','LITRES_DOCX')",
            name="ck_literary_master_export_format",
        ),
        sa.CheckConstraint("byte_length >= 0", name="ck_literary_master_export_length"),
    )


def _create_append_only_triggers() -> None:
    op.execute(
        "CREATE TRIGGER protect_literary_master_exports_update "
        "BEFORE UPDATE ON literary_master_exports "
        "BEGIN SELECT RAISE(ABORT, 'literary_master_exports is append-only'); END"
    )
    op.execute(
        "CREATE TRIGGER protect_literary_master_exports_delete "
        "BEFORE DELETE ON literary_master_exports "
        "BEGIN SELECT RAISE(ABORT, 'literary_master_exports is append-only'); END"
    )


def upgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS protect_literary_master_exports_update")
    op.execute("DROP TRIGGER IF EXISTS protect_literary_master_exports_delete")
    op.rename_table("literary_master_exports", "literary_master_exports_0019")
    _create_exports_table()
    op.execute(
        "INSERT INTO literary_master_exports("
        "export_id,master_id,format,content_hash,byte_length,relative_path,created_at) "
        "SELECT export_id,master_id,format,content_hash,byte_length,relative_path,created_at "
        "FROM literary_master_exports_0019"
    )
    op.drop_table("literary_master_exports_0019")
    _create_append_only_triggers()
    op.execute("INSERT INTO schema_metadata (version) VALUES ('0020')")


def downgrade() -> None:
    connection = op.get_bind()
    litres_count = int(
        connection.exec_driver_sql(
            "SELECT COUNT(*) FROM literary_master_exports WHERE format='LITRES_DOCX'"
        ).scalar_one()
    )
    if litres_count:
        raise RuntimeError("cannot downgrade 0020 while LITRES_DOCX exports exist")

    op.execute("DROP TRIGGER IF EXISTS protect_literary_master_exports_update")
    op.execute("DROP TRIGGER IF EXISTS protect_literary_master_exports_delete")
    op.rename_table("literary_master_exports", "literary_master_exports_0020")
    op.create_table(
        "literary_master_exports",
        sa.Column("export_id", sa.String(64), primary_key=True),
        sa.Column("master_id", sa.String(64), nullable=False),
        sa.Column("format", sa.String(32), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("byte_length", sa.Integer(), nullable=False),
        sa.Column("relative_path", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["master_id"], ["literary_masters.master_id"]),
        sa.UniqueConstraint("master_id", "format", name="uq_literary_master_export_format"),
        sa.CheckConstraint(
            "format IN ('MARKDOWN','AUDIOBOOK_HANDOFF_JSON')",
            name="ck_literary_master_export_format",
        ),
        sa.CheckConstraint("byte_length >= 0", name="ck_literary_master_export_length"),
    )
    op.execute(
        "INSERT INTO literary_master_exports("
        "export_id,master_id,format,content_hash,byte_length,relative_path,created_at) "
        "SELECT export_id,master_id,format,content_hash,byte_length,relative_path,created_at "
        "FROM literary_master_exports_0020"
    )
    op.drop_table("literary_master_exports_0020")
    _create_append_only_triggers()
    op.execute("DELETE FROM schema_metadata WHERE version='0020'")
