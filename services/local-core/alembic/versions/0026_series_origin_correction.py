"""Correct the historical BOOK_OS series-origin inference.

Revision ID: 0026
Revises: 0025
Create Date: 2026-09-14
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0026"
down_revision: str | None = "0025"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # source_kind records where the project originated, not whether it rewrote a legacy title.
    # The known rewritten first book is restored by the explicit services-series preset reconcile.
    # Lifecycle and every owner-authored field remain untouched.
    op.execute(
        "UPDATE series_books SET origin_kind='NEW' "
        "WHERE source_kind='BOOK_OS' AND origin_kind='CURRENT_REWRITTEN'"
    )
    op.execute("INSERT INTO schema_metadata (version) VALUES ('0026')")


def downgrade() -> None:
    # The old inference cannot be restored safely: BOOK_OS never proved a rewritten origin.
    op.execute("DELETE FROM schema_metadata WHERE version='0026'")
