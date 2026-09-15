"""Make nonfiction bibliography automatic and preserve explicit future omission.

Revision ID: 0025
Revises: 0024
Create Date: 2026-09-13
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0025"
down_revision: str | None = "0024"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("planning_runs") as batch:
        batch.drop_constraint("ck_planning_run_kind", type_="check")
        batch.create_check_constraint(
            "ck_planning_run_kind",
            "run_kind IN ('BOOK_CONCEPT_PROPOSAL','BOOK_CONTRACT_PROPOSAL',"
            "'ARCHITECTURE_PROPOSAL','CHAPTER_CONTRACT_PROPOSAL')",
        )
    op.add_column(
        "book_context_settings",
        sa.Column(
            "bibliography_preference",
            sa.String(24),
            nullable=False,
            server_default="AUTO_INCLUDED",
        ),
    )
    # Before this revision FALSE was the product default and therefore cannot prove an explicit
    # author choice. Existing nonfiction projects are migrated to the safe automatic default.
    op.execute(
        "UPDATE book_context_settings SET include_bibliography=1, "
        "bibliography_preference='AUTO_INCLUDED'"
    )
    op.execute("INSERT INTO schema_metadata (version) VALUES ('0025')")


def downgrade() -> None:
    with op.batch_alter_table("planning_runs") as batch:
        batch.drop_constraint("ck_planning_run_kind", type_="check")
        batch.create_check_constraint(
            "ck_planning_run_kind",
            "run_kind IN ('BOOK_CONTRACT_PROPOSAL','ARCHITECTURE_PROPOSAL',"
            "'CHAPTER_CONTRACT_PROPOSAL')",
        )
    op.drop_column("book_context_settings", "bibliography_preference")
    op.execute("DELETE FROM schema_metadata WHERE version='0025'")
