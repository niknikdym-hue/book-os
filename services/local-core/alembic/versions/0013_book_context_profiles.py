"""Persist author/series/style bindings and target length.

Revision ID: 0013
Revises: 0012
Create Date: 2026-09-06
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "book_context_settings",
        sa.Column("book_id", sa.String(26), primary_key=True),
        sa.Column("author_profile_id", sa.String(26), nullable=True),
        sa.Column("author_profile_hash", sa.String(64), nullable=True),
        sa.Column("series_profile_id", sa.String(26), nullable=True),
        sa.Column("series_profile_hash", sa.String(64), nullable=True),
        sa.Column("style_profile_id", sa.String(26), nullable=True),
        sa.Column("style_profile_hash", sa.String(64), nullable=True),
        sa.Column("target_characters", sa.Integer(), nullable=True),
        sa.Column("min_characters", sa.Integer(), nullable=True),
        sa.Column("max_characters", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"]),
        sa.CheckConstraint(
            "target_characters IS NULL OR target_characters > 0",
            name="ck_context_target_positive",
        ),
        sa.CheckConstraint(
            "min_characters IS NULL OR min_characters > 0",
            name="ck_context_min_positive",
        ),
        sa.CheckConstraint(
            "max_characters IS NULL OR max_characters > 0",
            name="ck_context_max_positive",
        ),
        sa.CheckConstraint(
            "min_characters IS NULL OR max_characters IS NULL OR min_characters <= max_characters",
            name="ck_context_range_order",
        ),
        sa.CheckConstraint(
            "target_characters IS NULL OR min_characters IS NULL OR target_characters >= min_characters",
            name="ck_context_target_above_min",
        ),
        sa.CheckConstraint(
            "target_characters IS NULL OR max_characters IS NULL OR target_characters <= max_characters",
            name="ck_context_target_below_max",
        ),
    )
    op.execute("INSERT INTO schema_metadata (version) VALUES ('0013')")


def downgrade() -> None:
    op.drop_table("book_context_settings")
    op.execute("DELETE FROM schema_metadata WHERE version = '0013'")
