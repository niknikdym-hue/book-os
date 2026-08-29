"""Create Literary Master and deterministic export persistence.

Revision ID: 0009
Revises: 0008
Create Date: 2026-08-29
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "literary_masters",
        sa.Column("master_id", sa.String(64), primary_key=True),
        sa.Column("book_id", sa.String(26), nullable=False),
        sa.Column("manifest_version", sa.String(32), nullable=False),
        sa.Column("manifest_json", sa.Text(), nullable=False),
        sa.Column("manifest_hash", sa.String(64), nullable=False),
        sa.Column("book_title", sa.String(300), nullable=False),
        sa.Column("book_contract_revision_id", sa.String(26), nullable=False),
        sa.Column("book_contract_revision_hash", sa.String(64), nullable=False),
        sa.Column("architecture_revision_id", sa.String(26), nullable=False),
        sa.Column("architecture_revision_hash", sa.String(64), nullable=False),
        sa.Column("ordered_manifest_json", sa.Text(), nullable=False),
        sa.Column("canonical_content_hash", sa.String(64), nullable=False),
        sa.Column("release_gate_json", sa.Text(), nullable=False),
        sa.Column("human_actor", sa.String(255), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"]),
        sa.ForeignKeyConstraint(
            ["book_contract_revision_id", "book_contract_revision_hash"],
            ["revisions.revision_id", "revisions.content_hash"],
            name="fk_literary_master_book_contract",
        ),
        sa.ForeignKeyConstraint(
            ["architecture_revision_id", "architecture_revision_hash"],
            ["revisions.revision_id", "revisions.content_hash"],
            name="fk_literary_master_architecture",
        ),
        sa.UniqueConstraint("book_id", "manifest_hash", name="uq_literary_master_manifest"),
        sa.CheckConstraint("status = 'LOCKED'", name="ck_literary_master_status"),
    )
    op.create_index(
        "ix_literary_masters_book_created",
        "literary_masters",
        ["book_id", "created_at"],
    )

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

    op.execute("INSERT INTO schema_metadata (version) VALUES ('0009')")

    for table in ("literary_masters", "literary_master_exports"):
        op.execute(
            f"CREATE TRIGGER protect_{table}_update BEFORE UPDATE ON {table} "
            f"BEGIN SELECT RAISE(ABORT, '{table} is append-only'); END"
        )
        op.execute(
            f"CREATE TRIGGER protect_{table}_delete BEFORE DELETE ON {table} "
            f"BEGIN SELECT RAISE(ABORT, '{table} is append-only'); END"
        )


def downgrade() -> None:
    for table in ("literary_master_exports", "literary_masters"):
        op.execute(f"DROP TRIGGER IF EXISTS protect_{table}_delete")
        op.execute(f"DROP TRIGGER IF EXISTS protect_{table}_update")
    op.drop_table("literary_master_exports")
    op.drop_index("ix_literary_masters_book_created", table_name="literary_masters")
    op.drop_table("literary_masters")
    op.execute("DELETE FROM schema_metadata WHERE version = '0009'")
