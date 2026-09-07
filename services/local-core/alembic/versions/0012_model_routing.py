"""Persist provider/model routing choices.

Revision ID: 0012
Revises: 0011
Create Date: 2026-09-06
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("planning_runs") as batch:
        batch.add_column(
            sa.Column("selection_mode", sa.String(16), nullable=False, server_default="AUTO")
        )
        batch.add_column(sa.Column("selection_scope", sa.String(16), nullable=True))
        batch.add_column(sa.Column("routing_rationale", sa.Text(), nullable=True))
        batch.create_check_constraint(
            "ck_planning_selection_mode", "selection_mode IN ('AUTO','MANUAL')"
        )
        batch.create_check_constraint(
            "ck_planning_selection_scope",
            "selection_scope IS NULL OR selection_scope IN ('OPERATION','BOOK')",
        )

    op.create_table(
        "book_model_pins",
        sa.Column("book_id", sa.String(26), primary_key=True),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("model", sa.String(160), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.Column("updated_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"]),
    )
    op.execute("INSERT INTO schema_metadata (version) VALUES ('0012')")


def downgrade() -> None:
    op.drop_table("book_model_pins")
    with op.batch_alter_table("planning_runs") as batch:
        batch.drop_constraint("ck_planning_selection_scope", type_="check")
        batch.drop_constraint("ck_planning_selection_mode", type_="check")
        batch.drop_column("routing_rationale")
        batch.drop_column("selection_scope")
        batch.drop_column("selection_mode")
    op.execute("DELETE FROM schema_metadata WHERE version = '0012'")
