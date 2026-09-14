"""Complete durable nonfiction-series governance.

Revision ID: 0028
Revises: 0027
Create Date: 2026-09-14
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0028"
down_revision: str | None = "0027"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "series_topic_ownership",
        sa.Column("ownership_id", sa.String(26), primary_key=True),
        sa.Column("series_profile_id", sa.String(26), nullable=False),
        sa.Column("topic_key", sa.String(64), nullable=False),
        sa.Column("topic_label", sa.Text(), nullable=False),
        sa.Column("owner_book_id", sa.String(26), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("actor", sa.String(255), nullable=False),
        sa.Column("supersedes_ownership_id", sa.String(26), nullable=True),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(
            ["supersedes_ownership_id"],
            ["series_topic_ownership.ownership_id"],
        ),
    )
    op.create_index(
        "ix_series_topic_ownership_series_topic",
        "series_topic_ownership",
        ["series_profile_id", "topic_key", "created_at"],
    )
    op.execute(
        "CREATE TRIGGER protect_series_topic_ownership_update BEFORE UPDATE ON "
        "series_topic_ownership BEGIN SELECT RAISE(ABORT, "
        "'series_topic_ownership is append-only'); END"
    )
    op.execute(
        "CREATE TRIGGER protect_series_topic_ownership_delete BEFORE DELETE ON "
        "series_topic_ownership BEGIN SELECT RAISE(ABORT, "
        "'series_topic_ownership is append-only'); END"
    )
    op.execute("INSERT INTO schema_metadata (version) VALUES ('0028')")


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS protect_series_topic_ownership_delete")
    op.execute("DROP TRIGGER IF EXISTS protect_series_topic_ownership_update")
    op.drop_index(
        "ix_series_topic_ownership_series_topic",
        table_name="series_topic_ownership",
    )
    op.drop_table("series_topic_ownership")
    op.execute("DELETE FROM schema_metadata WHERE version='0028'")
