"""Persist bounded disposable style-preview evidence.

Revision ID: 0014
Revises: 0013
Create Date: 2026-09-06
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "style_preview_runs",
        sa.Column("preview_id", sa.String(26), primary_key=True),
        sa.Column("batch_id", sa.String(26), nullable=False),
        sa.Column("book_id", sa.String(26), nullable=False),
        sa.Column("author_profile_id", sa.String(26), nullable=False),
        sa.Column("author_profile_hash", sa.String(64), nullable=False),
        sa.Column("style_profile_id", sa.String(26), nullable=False),
        sa.Column("style_profile_hash", sa.String(64), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("model", sa.String(160), nullable=False),
        sa.Column("selection_mode", sa.String(16), nullable=False),
        sa.Column("selection_scope", sa.String(16), nullable=True),
        sa.Column("routing_rationale", sa.Text(), nullable=False),
        sa.Column("prompt_id", sa.String(128), nullable=False),
        sa.Column("prompt_version", sa.String(32), nullable=False),
        sa.Column("prompt_hash", sa.String(64), nullable=False),
        sa.Column("brief_hash", sa.String(64), nullable=False),
        sa.Column("content_brief", sa.Text(), nullable=False),
        sa.Column("max_output_tokens", sa.Integer(), nullable=False),
        sa.Column("max_cost_usd", sa.Float(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("provider_run_id", sa.String(255), nullable=True),
        sa.Column("output_text", sa.Text(), nullable=True),
        sa.Column("usage_json", sa.Text(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.Column("completed_at", sa.String(32), nullable=True),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"]),
        sa.CheckConstraint(
            "selection_mode IN ('AUTO','MANUAL')", name="ck_style_preview_selection_mode"
        ),
        sa.CheckConstraint(
            "selection_scope IS NULL OR selection_scope IN ('OPERATION','BOOK')",
            name="ck_style_preview_selection_scope",
        ),
        sa.CheckConstraint(
            "status IN ('RUNNING','SUCCEEDED','FAILED')", name="ck_style_preview_status"
        ),
        sa.CheckConstraint("max_output_tokens > 0", name="ck_style_preview_tokens_positive"),
        sa.CheckConstraint("max_cost_usd > 0", name="ck_style_preview_cost_positive"),
    )
    op.create_index(
        "ix_style_preview_batch",
        "style_preview_runs",
        ["book_id", "batch_id", "created_at"],
    )
    op.execute("INSERT INTO schema_metadata (version) VALUES ('0014')")


def downgrade() -> None:
    op.drop_index("ix_style_preview_batch", table_name="style_preview_runs")
    op.drop_table("style_preview_runs")
    op.execute("DELETE FROM schema_metadata WHERE version = '0014'")
