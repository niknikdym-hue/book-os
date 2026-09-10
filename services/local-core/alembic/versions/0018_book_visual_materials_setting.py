"""Persist the illustrations planning setting for each book.

Revision ID: 0018
Revises: 0017
Create Date: 2026-09-10
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0018"
down_revision: str | None = "0017"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "book_context_settings",
        sa.Column("plan_illustrations", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.execute("INSERT INTO schema_metadata (version) VALUES ('0018')")


def downgrade() -> None:
    op.drop_column("book_context_settings", "plan_illustrations")
    op.execute("DELETE FROM schema_metadata WHERE version = '0018'")
