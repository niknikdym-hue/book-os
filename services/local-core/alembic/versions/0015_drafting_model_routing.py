"""Persist Writer model-routing provenance.

Revision ID: 0015
Revises: 0014
Create Date: 2026-09-06
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("model_runs") as batch:
        batch.add_column(
            sa.Column("selection_mode", sa.String(16), nullable=False, server_default="AUTO")
        )
        batch.add_column(sa.Column("selection_scope", sa.String(16), nullable=True))
        batch.add_column(sa.Column("routing_rationale", sa.Text(), nullable=True))
        batch.create_check_constraint(
            "ck_model_runs_selection_mode", "selection_mode IN ('AUTO','MANUAL')"
        )
        batch.create_check_constraint(
            "ck_model_runs_selection_scope",
            "selection_scope IS NULL OR selection_scope IN ('OPERATION','BOOK')",
        )
    op.execute("INSERT INTO schema_metadata (version) VALUES ('0015')")


def downgrade() -> None:
    with op.batch_alter_table("model_runs") as batch:
        batch.drop_constraint("ck_model_runs_selection_scope", type_="check")
        batch.drop_constraint("ck_model_runs_selection_mode", type_="check")
        batch.drop_column("routing_rationale")
        batch.drop_column("selection_scope")
        batch.drop_column("selection_mode")
    op.execute("DELETE FROM schema_metadata WHERE version = '0015'")
