"""Add durable nonfiction series workspace records.

Revision ID: 0022
Revises: 0021
Create Date: 2026-09-13
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0022"
down_revision: str | None = "0021"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "series_books",
        sa.Column("series_book_id", sa.String(26), primary_key=True),
        sa.Column("series_profile_id", sa.String(26), nullable=False),
        sa.Column("book_id", sa.String(26), nullable=False, unique=True),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("unique_idea", sa.Text(), nullable=False),
        sa.Column("reader_problem", sa.Text(), nullable=False),
        sa.Column("reader_result", sa.Text(), nullable=False),
        sa.Column("unique_mechanism", sa.Text(), nullable=False),
        sa.Column("excluded_topics_json", sa.Text(), nullable=False),
        sa.Column("source_kind", sa.String(16), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.Column("updated_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"]),
        sa.CheckConstraint("ordinal > 0"),
        sa.CheckConstraint("source_kind IN ('BOOK_OS','IMPORTED','PLANNED')"),
        sa.CheckConstraint(
            "status IN ('IDEA','DEFINITION','ARCHITECTURE','WRITING','EDITING',"
            "'FINAL_REVIEW','READY','ARCHIVED')"
        ),
    )
    op.create_index(
        "ix_series_books_profile_ordinal",
        "series_books",
        ["series_profile_id", "ordinal"],
    )
    op.create_table(
        "series_imported_sources",
        sa.Column("source_id", sa.String(26), primary_key=True),
        sa.Column("series_profile_id", sa.String(26), nullable=False),
        sa.Column("book_id", sa.String(26), nullable=False),
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column("format", sa.String(16), nullable=False),
        sa.Column("relative_path", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("rights_status", sa.String(32), nullable=False),
        sa.Column("analysis_status", sa.String(24), nullable=False),
        sa.Column("analysis_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"]),
        sa.UniqueConstraint("book_id", "content_hash"),
        sa.CheckConstraint("format IN ('DOCX','TXT','PDF','EPUB','MARKDOWN')"),
        sa.CheckConstraint(
            "rights_status IN ('AUTHOR_MANUSCRIPT','PUBLISHED_OWN_BOOK',"
            "'LICENSED_MATERIAL','REFERENCE_ONLY')"
        ),
        sa.CheckConstraint("analysis_status IN ('PARSED','PARTIAL','FAILED')"),
    )
    op.create_table(
        "series_similarity_findings",
        sa.Column("finding_id", sa.String(26), primary_key=True),
        sa.Column("series_profile_id", sa.String(26), nullable=False),
        sa.Column("book_id", sa.String(26), nullable=False),
        sa.Column("compared_book_id", sa.String(26), nullable=False),
        sa.Column("dimension", sa.String(32), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("evidence_json", sa.Text(), nullable=False),
        sa.Column("map_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"]),
        sa.CheckConstraint(
            "dimension IN ('THESIS','ARCHITECTURE','EXAMPLE','METAPHOR','TOOL','LANGUAGE',"
            "'VISUAL','SOURCE_QUALITY')"
        ),
        sa.CheckConstraint("severity IN ('ATTENTION','BLOCKING')"),
        sa.CheckConstraint("status IN ('OPEN','RESOLVED','ACCEPTED_EXCEPTION')"),
    )
    op.create_index(
        "ix_series_similarity_map",
        "series_similarity_findings",
        ["series_profile_id", "map_hash", "status"],
    )
    op.create_table(
        "series_author_decisions",
        sa.Column("decision_id", sa.String(26), primary_key=True),
        sa.Column("series_profile_id", sa.String(26), nullable=False),
        sa.Column("book_id", sa.String(26), nullable=False),
        sa.Column("decision_kind", sa.String(32), nullable=False),
        sa.Column("input_hash", sa.String(64), nullable=False),
        sa.Column("decision", sa.String(32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("actor", sa.String(255), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"]),
        sa.CheckConstraint(
            "decision_kind IN ('SERIES_BIBLE','BOOK_PASSPORT','OVERLAP_MAP','EXCEPTION')"
        ),
        sa.CheckConstraint("decision IN ('APPROVED','REJECTED','REVISE')"),
    )
    op.create_table(
        "series_map_runs",
        sa.Column("map_run_id", sa.String(26), primary_key=True),
        sa.Column("series_profile_id", sa.String(26), nullable=False),
        sa.Column("book_id", sa.String(26), nullable=False),
        sa.Column("map_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("finding_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"]),
        sa.CheckConstraint("status IN ('PASS','ATTENTION','BLOCKING')"),
    )
    op.execute("INSERT INTO schema_metadata (version) VALUES ('0022')")
    op.execute(
        "CREATE TRIGGER protect_series_import_identity BEFORE UPDATE OF relative_path,content_hash "
        "ON series_imported_sources BEGIN SELECT RAISE(ABORT, "
        "'imported series source bytes are immutable'); END"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS protect_series_import_identity")
    op.drop_table("series_map_runs")
    op.drop_table("series_author_decisions")
    op.drop_index("ix_series_similarity_map", table_name="series_similarity_findings")
    op.drop_table("series_similarity_findings")
    op.drop_table("series_imported_sources")
    op.drop_index("ix_series_books_profile_ordinal", table_name="series_books")
    op.drop_table("series_books")
    op.execute("DELETE FROM schema_metadata WHERE version='0022'")
