"""Separate series book origin from production lifecycle.

Revision ID: 0024
Revises: 0023
Create Date: 2026-09-13
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0024"
down_revision: str | None = "0023"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "series_books",
        sa.Column("origin_kind", sa.String(32), nullable=False, server_default="NEW"),
    )
    op.add_column(
        "series_books",
        sa.Column("lifecycle", sa.String(24), nullable=False, server_default="PLANNED"),
    )
    op.add_column(
        "series_books",
        sa.Column("legacy_content_allowed", sa.Boolean(), nullable=False, server_default="0"),
    )
    op.add_column(
        "series_books",
        sa.Column("superseded_by_book_id", sa.String(26), nullable=True),
    )
    op.execute(
        "UPDATE series_books SET origin_kind=CASE source_kind "
        "WHEN 'IMPORTED' THEN 'IMPORTED' WHEN 'BOOK_OS' THEN 'CURRENT_REWRITTEN' "
        "ELSE 'NEW' END"
    )
    op.execute(
        "UPDATE series_books SET lifecycle=CASE status "
        "WHEN 'IDEA' THEN 'PLANNED' WHEN 'DEFINITION' THEN 'DEFINITION' "
        "WHEN 'ARCHITECTURE' THEN 'ARCHITECTURE' WHEN 'WRITING' THEN 'WRITING' "
        "WHEN 'EDITING' THEN 'EDITING' WHEN 'FINAL_REVIEW' THEN 'EDITING' "
        "WHEN 'READY' THEN 'COMPLETED' WHEN 'ARCHIVED' THEN 'ARCHIVED' "
        "ELSE 'PLANNED' END"
    )
    op.execute(
        "UPDATE series_books SET legacy_content_allowed=1 WHERE origin_kind='IMPORTED'"
    )
    op.execute("INSERT INTO schema_metadata (version) VALUES ('0024')")


def downgrade() -> None:
    op.drop_column("series_books", "superseded_by_book_id")
    op.drop_column("series_books", "legacy_content_allowed")
    op.drop_column("series_books", "lifecycle")
    op.drop_column("series_books", "origin_kind")
    op.execute("DELETE FROM schema_metadata WHERE version='0024'")
