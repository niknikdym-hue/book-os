"""Create M0 bootstrap metadata.

Revision ID: 0001
Revises:
Create Date: 2026-08-23
"""

from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "schema_metadata",
        sa.Column("version", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("version"),
    )
    op.execute("INSERT INTO schema_metadata (version) VALUES ('0001')")


def downgrade() -> None:
    op.drop_table("schema_metadata")
