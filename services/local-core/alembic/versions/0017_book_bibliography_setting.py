"""Persist the bibliography-at-end setting for each book.

Revision ID: 0017
Revises: 0016
Create Date: 2026-09-10
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "book_context_settings",
        sa.Column("include_bibliography", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.execute("INSERT INTO schema_metadata (version) VALUES ('0017')")


def downgrade() -> None:
    op.drop_column("book_context_settings", "include_bibliography")
    op.execute("DELETE FROM schema_metadata WHERE version = '0017'")
