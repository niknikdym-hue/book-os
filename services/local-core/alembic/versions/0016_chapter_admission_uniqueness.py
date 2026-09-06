"""Add chapter admission and book uniqueness ledger.

Revision ID: 0016
Revises: 0015
Create Date: 2026-09-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


ASSET_STATUSES = (
    "PLANNED",
    "RESERVED",
    "USED_DRAFT",
    "USED_ACCEPTED",
    "CROSS_REFERENCE_ONLY",
    "LEGACY_PROTECTED",
    "RELEASED",
)


def upgrade() -> None:
    op.create_table(
        "chapter_admission",
        sa.Column("chapter_id", sa.String(26), primary_key=True),
        sa.Column("book_id", sa.String(26), nullable=False),
        sa.Column("contract_revision_id", sa.String(26), nullable=False),
        sa.Column("contract_revision_hash", sa.String(64), nullable=False),
        sa.Column("checks_json", sa.Text(), nullable=False),
        sa.Column("notes_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("writing_allowed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("actor", sa.String(300), nullable=False),
        sa.Column("actor_kind", sa.String(16), nullable=False),
        sa.Column("reviewed_at", sa.String(40), nullable=False),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.chapter_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"], ondelete="CASCADE"),
        sa.CheckConstraint("actor_kind = 'HUMAN'", name="ck_chapter_admission_human"),
    )
    op.create_index("ix_chapter_admission_book", "chapter_admission", ["book_id"])

    op.create_table(
        "book_uniqueness_assets",
        sa.Column("asset_id", sa.String(26), primary_key=True),
        sa.Column("book_id", sa.String(26), nullable=False),
        sa.Column("chapter_id", sa.String(26), nullable=True),
        sa.Column("asset_kind", sa.String(40), nullable=False),
        sa.Column("asset_text", sa.Text(), nullable=False),
        sa.Column("asset_function", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("source_revision_id", sa.String(26), nullable=False),
        sa.Column("source_revision_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.String(40), nullable=False),
        sa.Column("updated_at", sa.String(40), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.chapter_id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "status IN (" + ",".join(f"'{status}'" for status in ASSET_STATUSES) + ")",
            name="ck_uniqueness_asset_status",
        ),
        sa.UniqueConstraint(
            "book_id",
            "chapter_id",
            "asset_kind",
            "asset_text",
            name="uq_uniqueness_asset_identity",
        ),
    )
    op.create_index(
        "ix_uniqueness_assets_book_chapter",
        "book_uniqueness_assets",
        ["book_id", "chapter_id"],
    )
    op.create_index(
        "ix_uniqueness_assets_book_kind_status",
        "book_uniqueness_assets",
        ["book_id", "asset_kind", "status"],
    )
    op.execute("INSERT INTO schema_metadata (version) VALUES ('0016')")


def downgrade() -> None:
    op.drop_index("ix_uniqueness_assets_book_kind_status", table_name="book_uniqueness_assets")
    op.drop_index("ix_uniqueness_assets_book_chapter", table_name="book_uniqueness_assets")
    op.drop_table("book_uniqueness_assets")
    op.drop_index("ix_chapter_admission_book", table_name="chapter_admission")
    op.drop_table("chapter_admission")
    op.execute("DELETE FROM schema_metadata WHERE version = '0016'")
