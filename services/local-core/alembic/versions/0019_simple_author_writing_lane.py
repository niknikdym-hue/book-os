"""Allow simple author writing and owner-authorized Auto Book series writing.

Revision ID: 0019
Revises: 0018
Create Date: 2026-09-11
"""

from collections.abc import Sequence

from alembic import op

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


def _owner_auto_book_authorization_sql() -> str:
    return (
        "EXISTS (SELECT 1 FROM chapters c "
        "JOIN authority_heads h ON h.entity_id=c.chapter_contract_entity_id "
        "JOIN approvals ap ON ap.approved_revision_id=h.revision_id "
        "WHERE c.book_id=NEW.book_id AND c.chapter_id=NEW.chapter_id "
        "AND ap.approving_actor='owner' AND ap.approving_actor_kind='HUMAN' "
        "AND ap.gates_json LIKE '%\"owner_auto_book_authorization\":true%')"
    )


def _create_trigger(*, allow_simple_author_lane: bool) -> None:
    full_series = _full_series_admission_sql()
    clauses = [full_series]
    if allow_simple_author_lane:
        clauses.insert(
            0,
            "NOT EXISTS (SELECT 1 FROM book_context_settings s "
            "WHERE s.book_id=NEW.book_id AND s.series_profile_id IS NOT NULL)",
        )
        clauses.append(_owner_auto_book_authorization_sql())
    allowed = " OR ".join(clauses)
    # Use the DBAPI driver's literal SQL path here. SQLAlchemy's text() parser treats
    # the JSON fragment `:true` inside the LIKE pattern as a bind parameter, which
    # breaks fresh/bundled database migrations before Local Core can start.
    op.get_bind().exec_driver_sql(
        "CREATE TRIGGER require_current_writing_admission BEFORE INSERT ON bounded_tasks "
        "WHEN NEW.task_type='SECTION_DRAFT' BEGIN "
        f"SELECT CASE WHEN NOT ({allowed}) "
        "THEN RAISE(ABORT, 'WRITING_NOT_ALLOWED') END; END"
    )


def upgrade() -> None:
    # Task 017 added a deep series-production admission gate to every book. That made
    # the normal standalone Author Studio impossible to use even after the human had
    # approved Architecture and Chapter Contract. Keep that deep gate for series work,
    # while the standalone lane relies on DraftingService's exact authority checks.
    #
    # A series Auto Book may also write when the current Chapter Contract was accepted
    # through the immutable HUMAN approval record created by the owner's one-run Auto
    # Book authorization. This does not synthesize production PASS results or weaken
    # manual series-production gates.
    op.execute("DROP TRIGGER IF EXISTS require_current_writing_admission")
    _create_trigger(allow_simple_author_lane=True)
    op.execute("INSERT INTO schema_metadata (version) VALUES ('0019')")


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS require_current_writing_admission")
    _create_trigger(allow_simple_author_lane=False)
    op.execute("DELETE FROM schema_metadata WHERE version='0019'")
