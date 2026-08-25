"""Create M2 book-project and contract workspace metadata.

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-25
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "book_projects",
        sa.Column("book_id", sa.String(26), primary_key=True),
        sa.Column("working_title", sa.String(300), nullable=False),
        sa.Column("mode", sa.String(32), nullable=False),
        sa.Column("domain", sa.String(64), nullable=False),
        sa.Column("primary_subtype", sa.String(80), nullable=False),
        sa.Column("secondary_subtype", sa.String(80), nullable=True),
        sa.Column("profile_version", sa.String(32), nullable=False),
        sa.Column("workflow_stage", sa.String(32), nullable=False),
        sa.Column("book_contract_entity_id", sa.String(26), nullable=True),
        sa.Column("architecture_entity_id", sa.String(26), nullable=True),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.Column("updated_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["book_contract_entity_id"], ["authority_entities.entity_id"]),
        sa.ForeignKeyConstraint(["architecture_entity_id"], ["authority_entities.entity_id"]),
        sa.CheckConstraint("mode = 'BOOK_FROM_ZERO'", name="ck_m2_book_mode"),
        sa.CheckConstraint("domain = 'BUSINESS_NONFICTION'", name="ck_m2_book_domain"),
    )

    op.create_table(
        "working_revisions",
        sa.Column("entity_id", sa.String(26), primary_key=True),
        sa.Column("revision_id", sa.String(26), nullable=False),
        sa.Column("updated_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["entity_id"], ["authority_entities.entity_id"]),
        sa.ForeignKeyConstraint(["revision_id"], ["revisions.revision_id"]),
    )

    op.create_table(
        "chapters",
        sa.Column("chapter_id", sa.String(26), primary_key=True),
        sa.Column("book_id", sa.String(26), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("working_title", sa.String(300), nullable=False),
        sa.Column("architecture_role", sa.Text(), nullable=False),
        sa.Column("chapter_contract_entity_id", sa.String(26), nullable=True),
        sa.Column("workflow_state", sa.String(32), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.Column("updated_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"]),
        sa.ForeignKeyConstraint(["chapter_contract_entity_id"], ["authority_entities.entity_id"]),
        sa.UniqueConstraint("book_id", "ordinal", name="uq_chapter_book_ordinal"),
    )
    op.create_index("ix_chapters_book", "chapters", ["book_id", "ordinal"])

    op.execute("INSERT INTO schema_metadata (version) VALUES ('0003')")


def downgrade() -> None:
    op.drop_index("ix_chapters_book", table_name="chapters")
    op.drop_table("chapters")
    op.drop_table("working_revisions")
    op.drop_table("book_projects")
    op.execute("DELETE FROM schema_metadata WHERE version = '0003'")
