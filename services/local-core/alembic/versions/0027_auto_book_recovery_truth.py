"""Close Auto Book recovery, acceptance, change, and visual audit gaps.

Revision ID: 0027
Revises: 0026
Create Date: 2026-09-14
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0027"
down_revision: str | None = "0026"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS require_current_writing_admission")
    op.execute("DROP TRIGGER IF EXISTS protect_chapter_admissions_update")
    op.execute("DROP TRIGGER IF EXISTS protect_chapter_admissions_delete")
    with op.batch_alter_table("chapter_admissions") as batch:
        batch.drop_constraint("ck_admission_human_actor", type_="check")
        batch.create_check_constraint(
            "ck_admission_authorized_actor",
            "actor_kind IN ('HUMAN','OWNER','SYSTEM')",
        )
    op.execute(
        "CREATE TRIGGER IF NOT EXISTS protect_chapter_admissions_update BEFORE UPDATE ON "
        "chapter_admissions BEGIN SELECT RAISE(ABORT, 'chapter_admissions is append-only'); END"
    )
    op.execute(
        "CREATE TRIGGER IF NOT EXISTS protect_chapter_admissions_delete BEFORE DELETE ON "
        "chapter_admissions BEGIN SELECT RAISE(ABORT, 'chapter_admissions is append-only'); END"
    )
    op.execute(
        "CREATE TRIGGER require_current_writing_admission BEFORE INSERT ON bounded_tasks "
        "WHEN NEW.task_type='SECTION_DRAFT' BEGIN SELECT CASE WHEN NOT EXISTS ("
        "SELECT 1 FROM chapter_admissions a WHERE a.book_id=NEW.book_id "
        "AND a.chapter_id=NEW.chapter_id AND a.status='WRITING_ALLOWED' "
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
        "JOIN authority_heads h ON h.entity_id=b.architecture_entity_id "
        "WHERE b.book_id=NEW.book_id) AND a.chapter_contract_revision_id="
        "(SELECT h.revision_id FROM chapters c JOIN authority_heads h "
        "ON h.entity_id=c.chapter_contract_entity_id WHERE c.book_id=NEW.book_id "
        "AND c.chapter_id=NEW.chapter_id)) THEN RAISE(ABORT, 'WRITING_NOT_ALLOWED') END; END"
    )
    # The v1 SQLite check was unnamed, so rebuild explicitly instead of pretending it can be
    # altered in place. Existing PROPOSED/APPLIED rows receive truthful v2 terminal states.
    op.rename_table("auto_book_change_requests", "auto_book_change_requests_v1")
    op.create_table(
        "auto_book_change_requests",
        sa.Column("change_id", sa.String(26), primary_key=True),
        sa.Column("run_id", sa.String(26), nullable=False),
        sa.Column("request_text", sa.Text(), nullable=False),
        sa.Column("affected_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("clarification_json", sa.Text(), nullable=True),
        sa.Column("audit_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.Column("updated_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["auto_book_runtime_runs.run_id"]),
        sa.CheckConstraint(
            "status IN ('QUEUED','ANALYZING','NEEDS_CLARIFICATION','RUNNING','DONE','FAILED')"
        ),
    )
    op.execute(
        "INSERT INTO auto_book_change_requests(change_id,run_id,request_text,affected_json,"
        "status,audit_json,created_at,updated_at) SELECT change_id,run_id,request_text,"
        "affected_json,CASE status WHEN 'PROPOSED' THEN 'QUEUED' WHEN 'APPLIED' THEN 'DONE' "
        "WHEN 'REJECTED' THEN 'FAILED' ELSE status END,'[]',created_at,updated_at "
        "FROM auto_book_change_requests_v1"
    )
    op.drop_table("auto_book_change_requests_v1")
    with op.batch_alter_table("auto_book_visual_assets") as batch:
        batch.add_column(sa.Column("chapter_id", sa.String(26), nullable=True))
        batch.add_column(sa.Column("source_revision_id", sa.String(26), nullable=True))
        batch.add_column(sa.Column("source_revision_hash", sa.String(64), nullable=True))
        batch.add_column(sa.Column("data_json", sa.Text(), nullable=False, server_default="{}"))
        batch.add_column(sa.Column("status", sa.String(16), nullable=False, server_default="READY"))
        batch.create_check_constraint(
            "ck_auto_book_visual_assets_status", "status IN ('READY','STALE','FAILED')"
        )

    # Literary Master is append-only in normal product operation. Temporarily remove its guards so
    # the migration can rebuild the SQLite table and truthfully classify legacy Auto Book masters.
    op.execute("DROP TRIGGER IF EXISTS protect_literary_masters_update")
    op.execute("DROP TRIGGER IF EXISTS protect_literary_masters_delete")
    with op.batch_alter_table("literary_masters") as batch:
        batch.add_column(
            sa.Column(
                "acceptance_actor_kind",
                sa.String(16),
                nullable=False,
                server_default="HUMAN",
            )
        )
        batch.create_check_constraint(
            "ck_literary_master_acceptance_actor_kind",
            "acceptance_actor_kind IN ('HUMAN','DELEGATED')",
        )
    # Older Auto Book code wrote a technical placeholder into human_actor. Preserve the record but
    # do not rewrite that system execution as a historical human click.
    op.execute(
        "UPDATE literary_masters SET acceptance_actor_kind='DELEGATED' "
        "WHERE human_actor LIKE 'OWNER Auto Book %' OR human_actor LIKE 'SYSTEM:%'"
    )
    op.execute(
        "CREATE TRIGGER protect_literary_masters_update BEFORE UPDATE ON literary_masters "
        "BEGIN SELECT RAISE(ABORT, 'literary_masters is append-only'); END"
    )
    op.execute(
        "CREATE TRIGGER protect_literary_masters_delete BEFORE DELETE ON literary_masters "
        "BEGIN SELECT RAISE(ABORT, 'literary_masters is append-only'); END"
    )

    op.add_column("sources", sa.Column("inspected_excerpt", sa.Text(), nullable=True))
    op.add_column("sources", sa.Column("inspected_pointer", sa.Text(), nullable=True))
    op.create_table(
        "auto_book_final_acceptances",
        sa.Column("candidate_id", sa.String(26), primary_key=True),
        sa.Column("run_id", sa.String(26), nullable=False),
        sa.Column("snapshot_hash", sa.String(64), nullable=False),
        sa.Column("candidate_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("actor", sa.String(255), nullable=True),
        sa.Column("actor_kind", sa.String(16), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.Column("updated_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["auto_book_runtime_runs.run_id"]),
        sa.UniqueConstraint("run_id", "snapshot_hash"),
        sa.CheckConstraint("status IN ('AWAITING','ACCEPTED','REWORK_REQUESTED','STALE')"),
        sa.CheckConstraint("actor_kind IS NULL OR actor_kind IN ('HUMAN','SYSTEM','DELEGATED')"),
    )
    op.execute("INSERT INTO schema_metadata (version) VALUES ('0027')")


def downgrade() -> None:
    op.drop_table("auto_book_final_acceptances")
    op.execute("DROP TRIGGER IF EXISTS require_current_writing_admission")
    op.execute("DROP TRIGGER IF EXISTS protect_chapter_admissions_update")
    op.execute("DROP TRIGGER IF EXISTS protect_chapter_admissions_delete")
    with op.batch_alter_table("chapter_admissions") as batch:
        batch.drop_constraint("ck_admission_authorized_actor", type_="check")
        batch.create_check_constraint(
            "ck_admission_human_actor",
            "actor_kind IN ('HUMAN','OWNER')",
        )
    op.execute(
        "CREATE TRIGGER IF NOT EXISTS protect_chapter_admissions_update BEFORE UPDATE ON "
        "chapter_admissions BEGIN SELECT RAISE(ABORT, 'chapter_admissions is append-only'); END"
    )
    op.execute(
        "CREATE TRIGGER IF NOT EXISTS protect_chapter_admissions_delete BEFORE DELETE ON "
        "chapter_admissions BEGIN SELECT RAISE(ABORT, 'chapter_admissions is append-only'); END"
    )
    op.execute(
        "CREATE TRIGGER require_current_writing_admission BEFORE INSERT ON bounded_tasks "
        "WHEN NEW.task_type='SECTION_DRAFT' BEGIN SELECT CASE WHEN NOT EXISTS ("
        "SELECT 1 FROM chapter_admissions a WHERE a.book_id=NEW.book_id "
        "AND a.chapter_id=NEW.chapter_id AND a.status='WRITING_ALLOWED' "
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
        "JOIN authority_heads h ON h.entity_id=b.architecture_entity_id "
        "WHERE b.book_id=NEW.book_id) AND a.chapter_contract_revision_id="
        "(SELECT h.revision_id FROM chapters c JOIN authority_heads h "
        "ON h.entity_id=c.chapter_contract_entity_id WHERE c.book_id=NEW.book_id "
        "AND c.chapter_id=NEW.chapter_id)) THEN RAISE(ABORT, 'WRITING_NOT_ALLOWED') END; END"
    )

    op.execute("DROP TRIGGER IF EXISTS protect_literary_masters_update")
    op.execute("DROP TRIGGER IF EXISTS protect_literary_masters_delete")
    with op.batch_alter_table("literary_masters") as batch:
        batch.drop_constraint("ck_literary_master_acceptance_actor_kind", type_="check")
        batch.drop_column("acceptance_actor_kind")
    op.execute(
        "CREATE TRIGGER protect_literary_masters_update BEFORE UPDATE ON literary_masters "
        "BEGIN SELECT RAISE(ABORT, 'literary_masters is append-only'); END"
    )
    op.execute(
        "CREATE TRIGGER protect_literary_masters_delete BEFORE DELETE ON literary_masters "
        "BEGIN SELECT RAISE(ABORT, 'literary_masters is append-only'); END"
    )

    op.drop_column("sources", "inspected_pointer")
    op.drop_column("sources", "inspected_excerpt")
    with op.batch_alter_table("auto_book_visual_assets") as batch:
        batch.drop_constraint("ck_auto_book_visual_assets_status", type_="check")
        batch.drop_column("status")
        batch.drop_column("data_json")
        batch.drop_column("source_revision_hash")
        batch.drop_column("source_revision_id")
        batch.drop_column("chapter_id")
    op.rename_table("auto_book_change_requests", "auto_book_change_requests_v2")
    op.create_table(
        "auto_book_change_requests",
        sa.Column("change_id", sa.String(26), primary_key=True),
        sa.Column("run_id", sa.String(26), nullable=False),
        sa.Column("request_text", sa.Text(), nullable=False),
        sa.Column("affected_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.Column("updated_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["auto_book_runtime_runs.run_id"]),
        sa.CheckConstraint("status IN ('PROPOSED','APPLIED','NEEDS_CLARIFICATION','REJECTED')"),
    )
    op.execute(
        "INSERT INTO auto_book_change_requests SELECT change_id,run_id,request_text,affected_json,"
        "CASE status WHEN 'DONE' THEN 'APPLIED' WHEN 'FAILED' THEN 'REJECTED' "
        "WHEN 'NEEDS_CLARIFICATION' THEN status ELSE 'PROPOSED' END,created_at,updated_at "
        "FROM auto_book_change_requests_v2"
    )
    op.drop_table("auto_book_change_requests_v2")
    op.execute("DELETE FROM schema_metadata WHERE version='0027'")
