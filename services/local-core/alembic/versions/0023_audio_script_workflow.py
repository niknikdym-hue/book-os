"""Add versioned AudioScript editorial workflow records.

Revision ID: 0023
Revises: 0022
Create Date: 2026-09-13
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0023"
down_revision: str | None = "0022"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audio_scripts",
        sa.Column("audio_script_id", sa.String(26), primary_key=True),
        sa.Column("book_id", sa.String(26), nullable=False),
        sa.Column("source_kind", sa.String(24), nullable=False),
        sa.Column("source_identity", sa.Text(), nullable=False),
        sa.Column("source_hash", sa.String(64), nullable=False),
        sa.Column("adaptation_mode", sa.String(32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("content_json", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("transformation_json", sa.Text(), nullable=False),
        sa.Column("provenance_json", sa.Text(), nullable=False),
        sa.Column("approval_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.Column("updated_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"]),
        sa.UniqueConstraint("book_id", "version"),
        sa.CheckConstraint("version > 0"),
        sa.CheckConstraint("source_kind IN ('LITERARY_MASTER','IMPORTED_SOURCE')"),
        sa.CheckConstraint(
            "adaptation_mode IN ('SOURCE_FAITHFUL','LISTENING_ADAPTATION','AUDIO_NATIVE')"
        ),
        sa.CheckConstraint("status IN ('DRAFT','PROPOSED','APPROVED','SUPERSEDED')"),
    )
    op.create_index(
        "ix_audio_scripts_book_created",
        "audio_scripts",
        ["book_id", "created_at"],
    )
    op.create_table(
        "audio_script_quality_checks",
        sa.Column("check_id", sa.String(26), primary_key=True),
        sa.Column("audio_script_id", sa.String(26), nullable=False),
        sa.Column("source_hash", sa.String(64), nullable=False),
        sa.Column("script_hash", sa.String(64), nullable=False),
        sa.Column("check_kind", sa.String(48), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("findings_json", sa.Text(), nullable=False),
        sa.Column("evaluator_kind", sa.String(16), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["audio_script_id"], ["audio_scripts.audio_script_id"]),
        sa.UniqueConstraint("audio_script_id", "check_kind"),
        sa.CheckConstraint("state IN ('PASS','ATTENTION','BLOCKING')"),
        sa.CheckConstraint("evaluator_kind IN ('SYSTEM','MODEL','HUMAN')"),
    )
    op.create_table(
        "audio_pronunciation_entries",
        sa.Column("entry_id", sa.String(26), primary_key=True),
        sa.Column("audio_script_id", sa.String(26), nullable=False),
        sa.Column("term", sa.Text(), nullable=False),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("origin", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["audio_script_id"], ["audio_scripts.audio_script_id"]),
        sa.UniqueConstraint("audio_script_id", "term"),
        sa.CheckConstraint(
            "category IN ('PERSON','PLACE','COMPANY_OR_PRODUCT','ACRONYM','FOREIGN',"
            "'PROFESSIONAL_TERM','AMBIGUOUS_STRESS','AUTHOR_WORD')"
        ),
        sa.CheckConstraint("status IN ('NEEDS_REVIEW','VERIFIED','REJECTED')"),
    )
    op.create_table(
        "audio_production_handoffs",
        sa.Column("handoff_id", sa.String(26), primary_key=True),
        sa.Column("audio_script_id", sa.String(26), nullable=False),
        sa.Column("script_hash", sa.String(64), nullable=False),
        sa.Column("manifest_json", sa.Text(), nullable=False),
        sa.Column("text_relative_path", sa.Text(), nullable=False),
        sa.Column("text_content_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["audio_script_id"], ["audio_scripts.audio_script_id"]),
        sa.UniqueConstraint("audio_script_id", "script_hash"),
    )
    op.execute("INSERT INTO schema_metadata (version) VALUES ('0023')")
    op.execute(
        "UPDATE auto_book_runtime_runs SET status='PACKAGE_READY' "
        "WHERE current_stage='MASTER_AND_EXPORTS' AND status='RUNNING'"
    )


def downgrade() -> None:
    op.drop_table("audio_production_handoffs")
    op.drop_table("audio_pronunciation_entries")
    op.drop_table("audio_script_quality_checks")
    op.drop_index("ix_audio_scripts_book_created", table_name="audio_scripts")
    op.drop_table("audio_scripts")
    op.execute("DELETE FROM schema_metadata WHERE version='0023'")
