"""Allow simple author writing and bounded Auto Book admissions.

Revision ID: 0019
Revises: 0018
Create Date: 2026-09-11
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0019"
down_revision: str | None = "0018"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _full_series_admission_sql() -> str:
    return (
        "EXISTS (SELECT 1 FROM chapter_admissions a "
        "WHERE a.book_id=NEW.book_id AND a.chapter_id=NEW.chapter_id "
        "AND a.status='WRITING_ALLOWED' "
        "AND a.admission_id=(SELECT a2.admission_id FROM chapter_admissions a2 "
        "WHERE a2.book_id=NEW.book_id AND a2.chapter_id=NEW.chapter_id "
        "ORDER BY a2.created_at DESC,a2.admission_id DESC LIMIT 1) "
        "AND a.definition_id=(SELECT d.definition_id FROM definition_packs d "
        "WHERE d.book_id=NEW.book_id AND d.status='APPROVED' ORDER BY d.revision DESC LIMIT 1) "
        "AND a.production_contract_id=(SELECT pc.production_contract_id "
        "FROM chapter_production_contracts pc WHERE pc.book_id=NEW.book_id "
        "AND pc.chapter_id=NEW.chapter_id AND pc.status='APPROVED' "
        "ORDER BY pc.created_at DESC,pc.production_contract_id DESC LIMIT 1) "
        "AND a.architecture_revision_id=(SELECT h.revision_id FROM book_projects b "
        "JOIN authority_heads h ON h.entity_id=b.architecture_entity_id WHERE b.book_id=NEW.book_id) "
        "AND a.chapter_contract_revision_id=(SELECT h.revision_id FROM chapters c "
        "JOIN authority_heads h ON h.entity_id=c.chapter_contract_entity_id "
        "WHERE c.book_id=NEW.book_id AND c.chapter_id=NEW.chapter_id))"
    )


def _auto_book_admission_sql() -> str:
    return (
        "EXISTS (SELECT 1 FROM auto_book_writing_admissions a "
        "WHERE a.book_id=NEW.book_id AND a.chapter_id=NEW.chapter_id "
        "AND a.status='WRITING_ALLOWED' "
        "AND a.admission_id=(SELECT a2.admission_id FROM auto_book_writing_admissions a2 "
        "WHERE a2.book_id=NEW.book_id AND a2.chapter_id=NEW.chapter_id "
        "ORDER BY a2.created_at DESC,a2.admission_id DESC LIMIT 1) "
        "AND a.architecture_revision_id=(SELECT h.revision_id FROM book_projects b "
        "JOIN authority_heads h ON h.entity_id=b.architecture_entity_id WHERE b.book_id=NEW.book_id) "
        "AND a.chapter_contract_revision_id=(SELECT h.revision_id FROM chapters c "
        "JOIN authority_heads h ON h.entity_id=c.chapter_contract_entity_id "
        "WHERE c.book_id=NEW.book_id AND c.chapter_id=NEW.chapter_id))"
    )


def upgrade() -> None:
    op.create_table(
        "auto_book_writing_admissions",
        sa.Column("admission_id", sa.String(26), primary_key=True),
        sa.Column("run_id", sa.String(26), nullable=False),
        sa.Column("book_id", sa.String(26), nullable=False),
        sa.Column("chapter_id", sa.String(26), nullable=False),
        sa.Column("architecture_revision_id", sa.String(26), nullable=False),
        sa.Column("architecture_revision_hash", sa.String(64), nullable=False),
        sa.Column("chapter_contract_revision_id", sa.String(26), nullable=False),
        sa.Column("chapter_contract_revision_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("actor_kind", sa.String(16), nullable=False),
        sa.Column("actor", sa.String(255), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"]),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.chapter_id"]),
        sa.ForeignKeyConstraint(["architecture_revision_id"], ["revisions.revision_id"]),
        sa.ForeignKeyConstraint(["chapter_contract_revision_id"], ["revisions.revision_id"]),
        sa.CheckConstraint(
            "status IN ('WRITING_ALLOWED','REVOKED')",
            name="ck_auto_book_admission_status",
        ),
        sa.CheckConstraint("actor_kind='OWNER'", name="ck_auto_book_admission_owner"),
    )
    op.create_index(
        "ix_auto_book_admissions_chapter_created",
        "auto_book_writing_admissions",
        ["book_id", "chapter_id", "created_at"],
    )
    op.execute(
        "CREATE TRIGGER protect_auto_book_admissions_update "
        "BEFORE UPDATE ON auto_book_writing_admissions "
        "BEGIN SELECT RAISE(ABORT, 'auto_book_writing_admissions is append-only'); END"
    )
    op.execute(
        "CREATE TRIGGER protect_auto_book_admissions_delete "
        "BEFORE DELETE ON auto_book_writing_admissions "
        "BEGIN SELECT RAISE(ABORT, 'auto_book_writing_admissions is append-only'); END"
    )

    # Task 017's full production admission is a series-production gate. A standalone
    # author book already has the core BOOK OS authority gate in DraftingService:
    # current approved Architecture + current approved Chapter Contract. Series books
    # retain the full gate, except for a short-lived exact-revision admission created
    # by an owner-authorized Auto Book run.
    op.execute("DROP TRIGGER IF EXISTS require_current_writing_admission")
    full_series = _full_series_admission_sql()
    auto_book = _auto_book_admission_sql()
    op.execute(
        "CREATE TRIGGER require_current_writing_admission BEFORE INSERT ON bounded_tasks "
        "WHEN NEW.task_type='SECTION_DRAFT' BEGIN "
        "SELECT CASE WHEN NOT ("
        "NOT EXISTS (SELECT 1 FROM book_context_settings s "
        "WHERE s.book_id=NEW.book_id AND s.series_profile_id IS NOT NULL) "
        f"OR {full_series} OR {auto_book}"
        ") THEN RAISE(ABORT, 'WRITING_NOT_ALLOWED') END; END"
    )
    op.execute("INSERT INTO schema_metadata (version) VALUES ('0019')")


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS require_current_writing_admission")
    # Restoring the old universal Task 017 trigger on downgrade is intentionally
    # delegated to migration 0016 by a normal downgrade/upgrade cycle.
    op.execute("DROP TRIGGER IF EXISTS protect_auto_book_admissions_delete")
    op.execute("DROP TRIGGER IF EXISTS protect_auto_book_admissions_update")
    op.drop_index(
        "ix_auto_book_admissions_chapter_created",
        table_name="auto_book_writing_admissions",
    )
    op.drop_table("auto_book_writing_admissions")
    op.execute("DELETE FROM schema_metadata WHERE version='0019'")
