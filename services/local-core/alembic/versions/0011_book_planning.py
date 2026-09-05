"""Persist bounded Book/Architecture/Chapter planning runs.

Revision ID: 0011
Revises: 0010
Create Date: 2026-08-31
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "planning_runs",
        sa.Column("run_id", sa.String(26), primary_key=True),
        sa.Column("book_id", sa.String(26), nullable=False),
        sa.Column("chapter_id", sa.String(26), nullable=True),
        sa.Column("run_kind", sa.String(64), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("model", sa.String(128), nullable=False),
        sa.Column("provider_run_id", sa.String(255), nullable=True),
        sa.Column("prompt_id", sa.String(128), nullable=False),
        sa.Column("prompt_version", sa.String(32), nullable=False),
        sa.Column("prompt_hash", sa.String(64), nullable=False),
        sa.Column("request_json", sa.Text(), nullable=False),
        sa.Column("output_json", sa.Text(), nullable=True),
        sa.Column("usage_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("max_output_tokens", sa.Integer(), nullable=False),
        sa.Column("max_cost_usd", sa.Float(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.Column("completed_at", sa.String(32), nullable=True),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"]),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.chapter_id"]),
        sa.CheckConstraint(
            "run_kind IN ('BOOK_CONTRACT_PROPOSAL','ARCHITECTURE_PROPOSAL','CHAPTER_CONTRACT_PROPOSAL')",
            name="ck_planning_run_kind",
        ),
        sa.CheckConstraint(
            "status IN ('RUNNING','SUCCEEDED','FAILED')", name="ck_planning_run_status"
        ),
    )
    op.create_index("ix_planning_runs_book_created", "planning_runs", ["book_id", "created_at"])
    op.execute("INSERT INTO schema_metadata (version) VALUES ('0011')")


def downgrade() -> None:
    op.drop_index("ix_planning_runs_book_created", table_name="planning_runs")
    op.drop_table("planning_runs")
    op.execute("DELETE FROM schema_metadata WHERE version = '0011'")
