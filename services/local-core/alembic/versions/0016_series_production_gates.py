"""Add executable series-production gates.

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

_CANON_STATUSES = (
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
        "definition_packs",
        sa.Column("definition_id", sa.String(26), primary_key=True),
        sa.Column("book_id", sa.String(26), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("content_json", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.Column("approved_by", sa.String(255), nullable=True),
        sa.Column("approved_at", sa.String(32), nullable=True),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"]),
        sa.UniqueConstraint(
            "book_id",
            "revision",
            name="uq_definition_pack_book_revision",
        ),
        sa.CheckConstraint(
            "revision > 0",
            name="ck_definition_pack_revision_positive",
        ),
        sa.CheckConstraint(
            "status IN ('DRAFT','APPROVED','SUPERSEDED')",
            name="ck_definition_pack_status",
        ),
        sa.CheckConstraint(
            "status != 'APPROVED' OR "
            "(approved_by IS NOT NULL AND approved_at IS NOT NULL)",
            name="ck_definition_pack_approved_actor",
        ),
    )
    op.create_index(
        "ix_definition_packs_book_status",
        "definition_packs",
        ["book_id", "status", "revision"],
    )

    op.create_table(
        "series_canon_assets",
        sa.Column("asset_id", sa.String(26), primary_key=True),
        sa.Column("series_profile_id", sa.String(26), nullable=False),
        sa.Column("book_id", sa.String(26), nullable=True),
        sa.Column("asset_type", sa.String(64), nullable=False),
        sa.Column("asset_key", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("source_revision_id", sa.String(26), nullable=True),
        sa.Column("source_revision_hash", sa.String(64), nullable=True),
        sa.Column("provenance_json", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.Column("updated_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"]),
        sa.UniqueConstraint(
            "series_profile_id",
            "asset_key",
            name="uq_series_canon_asset_key",
        ),
        sa.CheckConstraint(
            "status IN ('" + "','".join(_CANON_STATUSES) + "')",
            name="ck_series_canon_status",
        ),
    )
    op.create_index(
        "ix_series_canon_series_status",
        "series_canon_assets",
        ["series_profile_id", "status"],
    )

    op.create_table(
        "chapter_production_contracts",
        sa.Column("production_contract_id", sa.String(26), primary_key=True),
        sa.Column("book_id", sa.String(26), nullable=False),
        sa.Column("chapter_id", sa.String(26), nullable=False),
        sa.Column("architecture_revision_id", sa.String(26), nullable=False),
        sa.Column("architecture_revision_hash", sa.String(64), nullable=False),
        sa.Column("chapter_contract_revision_id", sa.String(26), nullable=False),
        sa.Column("chapter_contract_revision_hash", sa.String(64), nullable=False),
        sa.Column("content_json", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.Column("approved_by", sa.String(255), nullable=True),
        sa.Column("approved_at", sa.String(32), nullable=True),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"]),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.chapter_id"]),
        sa.ForeignKeyConstraint(
            ["architecture_revision_id"],
            ["revisions.revision_id"],
            name="fk_prod_contract_architecture",
        ),
        sa.ForeignKeyConstraint(
            ["chapter_contract_revision_id"],
            ["revisions.revision_id"],
            name="fk_prod_contract_chapter_contract",
        ),
        sa.CheckConstraint(
            "status IN ('DRAFT','APPROVED','SUPERSEDED')",
            name="ck_production_contract_status",
        ),
        sa.CheckConstraint(
            "status != 'APPROVED' OR "
            "(approved_by IS NOT NULL AND approved_at IS NOT NULL)",
            name="ck_production_contract_approved_actor",
        ),
    )
    op.create_index(
        "ix_prod_contract_chapter_status",
        "chapter_production_contracts",
        ["book_id", "chapter_id", "status"],
    )

    op.create_table(
        "book_uniqueness_ledger",
        sa.Column("ledger_id", sa.String(26), primary_key=True),
        sa.Column("book_id", sa.String(26), nullable=False),
        sa.Column("chapter_id", sa.String(26), nullable=False),
        sa.Column("architecture_revision_id", sa.String(26), nullable=False),
        sa.Column("architecture_revision_hash", sa.String(64), nullable=False),
        sa.Column("chapter_contract_revision_id", sa.String(26), nullable=False),
        sa.Column("chapter_contract_revision_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("evidence_json", sa.Text(), nullable=False),
        sa.Column("actor_kind", sa.String(16), nullable=False),
        sa.Column("actor", sa.String(255), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"]),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.chapter_id"]),
        sa.ForeignKeyConstraint(
            ["architecture_revision_id"],
            ["revisions.revision_id"],
            name="fk_uniqueness_architecture",
        ),
        sa.ForeignKeyConstraint(
            ["chapter_contract_revision_id"],
            ["revisions.revision_id"],
            name="fk_uniqueness_chapter_contract",
        ),
        sa.CheckConstraint(
            "status IN ('PASS','ATTENTION','BLOCKING')",
            name="ck_uniqueness_status",
        ),
        sa.CheckConstraint(
            "actor_kind IN ('HUMAN','OWNER','AI','SYSTEM')",
            name="ck_uniqueness_actor_kind",
        ),
    )
    op.create_index(
        "ix_uniqueness_chapter_created",
        "book_uniqueness_ledger",
        ["book_id", "chapter_id", "created_at"],
    )

    op.create_table(
        "chapter_admissions",
        sa.Column("admission_id", sa.String(26), primary_key=True),
        sa.Column("book_id", sa.String(26), nullable=False),
        sa.Column("chapter_id", sa.String(26), nullable=False),
        sa.Column("definition_id", sa.String(26), nullable=False),
        sa.Column("definition_hash", sa.String(64), nullable=False),
        sa.Column("architecture_revision_id", sa.String(26), nullable=False),
        sa.Column("architecture_revision_hash", sa.String(64), nullable=False),
        sa.Column("chapter_contract_revision_id", sa.String(26), nullable=False),
        sa.Column("chapter_contract_revision_hash", sa.String(64), nullable=False),
        sa.Column("production_contract_id", sa.String(26), nullable=False),
        sa.Column("production_contract_hash", sa.String(64), nullable=False),
        sa.Column("checks_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("actor_kind", sa.String(16), nullable=False),
        sa.Column("actor", sa.String(255), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"]),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.chapter_id"]),
        sa.ForeignKeyConstraint(
            ["definition_id"],
            ["definition_packs.definition_id"],
        ),
        sa.ForeignKeyConstraint(
            ["architecture_revision_id"],
            ["revisions.revision_id"],
            name="fk_admission_architecture",
        ),
        sa.ForeignKeyConstraint(
            ["chapter_contract_revision_id"],
            ["revisions.revision_id"],
            name="fk_admission_chapter_contract",
        ),
        sa.ForeignKeyConstraint(
            ["production_contract_id"],
            ["chapter_production_contracts.production_contract_id"],
        ),
        sa.CheckConstraint(
            "status IN ('WRITING_ALLOWED','REVOKED')",
            name="ck_admission_status",
        ),
        sa.CheckConstraint(
            "actor_kind IN ('HUMAN','OWNER')",
            name="ck_admission_human_actor",
        ),
    )
    op.create_index(
        "ix_admissions_chapter_created",
        "chapter_admissions",
        ["book_id", "chapter_id", "created_at"],
    )

    op.create_table(
        "production_checkpoints",
        sa.Column("checkpoint_id", sa.String(26), primary_key=True),
        sa.Column("book_id", sa.String(26), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("progress_percent", sa.Float(), nullable=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("findings_json", sa.Text(), nullable=False),
        sa.Column("actor_kind", sa.String(16), nullable=False),
        sa.Column("actor", sa.String(255), nullable=False),
        sa.Column("executor_identity", sa.String(255), nullable=True),
        sa.Column("snapshot_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"]),
        sa.CheckConstraint(
            "kind IN ('MID_BOOK','ADVERSARIAL_REVIEW')",
            name="ck_production_checkpoint_kind",
        ),
        sa.CheckConstraint(
            "status IN ('PASS','ATTENTION','BLOCKING')",
            name="ck_production_checkpoint_status",
        ),
        sa.CheckConstraint(
            "actor_kind IN ('HUMAN','OWNER','AI','SYSTEM')",
            name="ck_production_checkpoint_actor",
        ),
        sa.CheckConstraint(
            "progress_percent IS NULL OR "
            "(progress_percent >= 0 AND progress_percent <= 100)",
            name="ck_production_checkpoint_progress",
        ),
        sa.CheckConstraint(
            "kind != 'MID_BOOK' OR "
            "(progress_percent >= 40 AND progress_percent <= 60)",
            name="ck_mid_book_checkpoint_range",
        ),
    )
    op.create_index(
        "ix_production_checkpoints_book_kind",
        "production_checkpoints",
        ["book_id", "kind", "created_at"],
    )

    op.create_table(
        "series_closures",
        sa.Column("closure_id", sa.String(26), primary_key=True),
        sa.Column("book_id", sa.String(26), nullable=False),
        sa.Column("series_profile_id", sa.String(26), nullable=False),
        sa.Column("master_id", sa.String(64), nullable=False),
        sa.Column("master_manifest_hash", sa.String(64), nullable=False),
        sa.Column("used_asset_ids_json", sa.Text(), nullable=False),
        sa.Column("released_asset_ids_json", sa.Text(), nullable=False),
        sa.Column("evidence_json", sa.Text(), nullable=False),
        sa.Column("human_actor", sa.String(255), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"]),
        sa.ForeignKeyConstraint(["master_id"], ["literary_masters.master_id"]),
        sa.UniqueConstraint(
            "book_id",
            "master_id",
            name="uq_series_closure_master",
        ),
    )

    op.execute("INSERT INTO schema_metadata (version) VALUES ('0016')")

    op.execute(
        "CREATE TRIGGER protect_used_accepted_asset_status "
        "BEFORE UPDATE OF status ON series_canon_assets "
        "WHEN OLD.status = 'USED_ACCEPTED' AND NEW.status != 'USED_ACCEPTED' "
        "BEGIN SELECT RAISE(ABORT, 'USED_ACCEPTED series asset is immutable'); END"
    )
    op.execute(
        "CREATE TRIGGER protect_used_accepted_asset_delete "
        "BEFORE DELETE ON series_canon_assets "
        "WHEN OLD.status = 'USED_ACCEPTED' "
        "BEGIN SELECT RAISE(ABORT, 'USED_ACCEPTED series asset is immutable'); END"
    )
    for table in ("chapter_admissions", "series_closures"):
        op.execute(
            f"CREATE TRIGGER protect_{table}_update "
            f"BEFORE UPDATE ON {table} "
            f"BEGIN SELECT RAISE(ABORT, '{table} is append-only'); END"
        )
        op.execute(
            f"CREATE TRIGGER protect_{table}_delete "
            f"BEFORE DELETE ON {table} "
            f"BEGIN SELECT RAISE(ABORT, '{table} is append-only'); END"
        )
    op.execute(
        "CREATE TRIGGER protect_approved_definition_update "
        "BEFORE UPDATE ON definition_packs WHEN OLD.status = 'APPROVED' "
        "BEGIN SELECT RAISE(ABORT, 'approved definition pack is immutable'); END"
    )
    op.execute(
        "CREATE TRIGGER protect_approved_prod_contract_update "
        "BEFORE UPDATE ON chapter_production_contracts "
        "WHEN OLD.status = 'APPROVED' "
        "BEGIN SELECT RAISE(ABORT, 'approved production contract is immutable'); END"
    )

    op.execute(
        "CREATE TRIGGER require_current_writing_admission "
        "BEFORE INSERT ON bounded_tasks WHEN NEW.task_type = 'SECTION_DRAFT' "
        "BEGIN "
        "SELECT CASE WHEN NOT EXISTS ("
        "SELECT 1 FROM chapter_admissions a "
        "JOIN definition_packs d ON d.definition_id=a.definition_id "
        "JOIN chapter_production_contracts pc "
        "ON pc.production_contract_id=a.production_contract_id "
        "WHERE a.book_id=NEW.book_id AND a.chapter_id=NEW.chapter_id "
        "AND a.status='WRITING_ALLOWED' "
        "AND a.admission_id=(SELECT a2.admission_id FROM chapter_admissions a2 "
        "WHERE a2.book_id=NEW.book_id AND a2.chapter_id=NEW.chapter_id "
        "ORDER BY a2.created_at DESC LIMIT 1) "
        "AND d.book_id=NEW.book_id AND d.status='APPROVED' "
        "AND d.definition_id=(SELECT d2.definition_id FROM definition_packs d2 "
        "WHERE d2.book_id=NEW.book_id AND d2.status='APPROVED' "
        "ORDER BY d2.revision DESC LIMIT 1) "
        "AND d.content_hash=a.definition_hash "
        "AND a.architecture_revision_id=(SELECT h.revision_id FROM book_projects b "
        "JOIN authority_heads h ON h.entity_id=b.architecture_entity_id "
        "WHERE b.book_id=NEW.book_id) "
        "AND a.architecture_revision_hash=(SELECT h.revision_hash FROM book_projects b "
        "JOIN authority_heads h ON h.entity_id=b.architecture_entity_id "
        "WHERE b.book_id=NEW.book_id) "
        "AND (SELECT s.status FROM revision_status_history s "
        "WHERE s.revision_id=a.architecture_revision_id "
        "ORDER BY s.created_at DESC, s.status_event_id DESC LIMIT 1) "
        "IN ('APPROVED','LOCKED') "
        "AND a.chapter_contract_revision_id=(SELECT h.revision_id FROM chapters c "
        "JOIN authority_heads h ON h.entity_id=c.chapter_contract_entity_id "
        "WHERE c.book_id=NEW.book_id AND c.chapter_id=NEW.chapter_id) "
        "AND a.chapter_contract_revision_hash=(SELECT h.revision_hash FROM chapters c "
        "JOIN authority_heads h ON h.entity_id=c.chapter_contract_entity_id "
        "WHERE c.book_id=NEW.book_id AND c.chapter_id=NEW.chapter_id) "
        "AND (SELECT s.status FROM revision_status_history s "
        "WHERE s.revision_id=a.chapter_contract_revision_id "
        "ORDER BY s.created_at DESC, s.status_event_id DESC LIMIT 1) "
        "IN ('APPROVED','LOCKED') "
        "AND pc.book_id=NEW.book_id AND pc.chapter_id=NEW.chapter_id "
        "AND pc.status='APPROVED' AND pc.content_hash=a.production_contract_hash "
        "AND pc.production_contract_id=(SELECT pc2.production_contract_id "
        "FROM chapter_production_contracts pc2 "
        "WHERE pc2.book_id=NEW.book_id AND pc2.chapter_id=NEW.chapter_id "
        "AND pc2.status='APPROVED' ORDER BY pc2.created_at DESC LIMIT 1) "
        "AND pc.architecture_revision_id=a.architecture_revision_id "
        "AND pc.architecture_revision_hash=a.architecture_revision_hash "
        "AND pc.chapter_contract_revision_id=a.chapter_contract_revision_id "
        "AND pc.chapter_contract_revision_hash=a.chapter_contract_revision_hash "
        "AND EXISTS (SELECT 1 FROM book_uniqueness_ledger u "
        "WHERE u.ledger_id=(SELECT u2.ledger_id FROM book_uniqueness_ledger u2 "
        "WHERE u2.book_id=NEW.book_id AND u2.chapter_id=NEW.chapter_id "
        "ORDER BY u2.created_at DESC LIMIT 1) "
        "AND u.status='PASS' "
        "AND u.architecture_revision_id=a.architecture_revision_id "
        "AND u.architecture_revision_hash=a.architecture_revision_hash "
        "AND u.chapter_contract_revision_id=a.chapter_contract_revision_id "
        "AND u.chapter_contract_revision_hash=a.chapter_contract_revision_hash)"
        ") THEN RAISE(ABORT, 'WRITING_NOT_ALLOWED') END; "
        "SELECT CASE WHEN "
        "COALESCE((SELECT target_characters FROM book_context_settings "
        "WHERE book_id=NEW.book_id),0) > 0 "
        "AND COALESCE((SELECT SUM(LENGTH(COALESCE(json_extract(r.content_json,'$.text'),''))) "
        "FROM manuscript_units u JOIN authority_heads h "
        "ON h.entity_id=u.authority_entity_id JOIN revisions r "
        "ON r.revision_id=h.revision_id WHERE u.book_id=NEW.book_id),0) >= "
        "0.4 * (SELECT target_characters FROM book_context_settings "
        "WHERE book_id=NEW.book_id) "
        "AND NOT EXISTS (SELECT 1 FROM production_checkpoints p "
        "WHERE p.checkpoint_id=(SELECT p2.checkpoint_id FROM production_checkpoints p2 "
        "WHERE p2.book_id=NEW.book_id AND p2.kind='MID_BOOK' "
        "ORDER BY p2.created_at DESC LIMIT 1) "
        "AND p.kind='MID_BOOK' AND p.status!='BLOCKING') "
        "THEN RAISE(ABORT, 'WRITING_NOT_ALLOWED: MID_BOOK_AUDIT_REQUIRED') END; "
        "END"
    )

    op.execute(
        "CREATE TRIGGER require_adversarial_review_before_master "
        "BEFORE INSERT ON literary_masters BEGIN "
        "SELECT CASE WHEN NOT EXISTS ("
        "SELECT 1 FROM production_checkpoints p "
        "WHERE p.checkpoint_id=(SELECT p2.checkpoint_id FROM production_checkpoints p2 "
        "WHERE p2.book_id=NEW.book_id AND p2.kind='ADVERSARIAL_REVIEW' "
        "ORDER BY p2.created_at DESC LIMIT 1) "
        "AND p.kind='ADVERSARIAL_REVIEW' AND p.status!='BLOCKING' "
        "AND p.executor_identity IS NOT NULL "
        "AND json_extract(p.findings_json,'$.independent')=1"
        ") THEN RAISE(ABORT, 'ADVERSARIAL_REVIEW_REQUIRED') END; "
        "END"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS require_adversarial_review_before_master")
    op.execute("DROP TRIGGER IF EXISTS require_current_writing_admission")
    op.execute("DROP TRIGGER IF EXISTS protect_approved_prod_contract_update")
    op.execute("DROP TRIGGER IF EXISTS protect_approved_definition_update")
    for table in ("series_closures", "chapter_admissions"):
        op.execute(f"DROP TRIGGER IF EXISTS protect_{table}_delete")
        op.execute(f"DROP TRIGGER IF EXISTS protect_{table}_update")
    op.execute("DROP TRIGGER IF EXISTS protect_used_accepted_asset_delete")
    op.execute("DROP TRIGGER IF EXISTS protect_used_accepted_asset_status")

    op.drop_table("series_closures")
    op.drop_index(
        "ix_production_checkpoints_book_kind",
        table_name="production_checkpoints",
    )
    op.drop_table("production_checkpoints")
    op.drop_index(
        "ix_admissions_chapter_created",
        table_name="chapter_admissions",
    )
    op.drop_table("chapter_admissions")
    op.drop_index(
        "ix_uniqueness_chapter_created",
        table_name="book_uniqueness_ledger",
    )
    op.drop_table("book_uniqueness_ledger")
    op.drop_index(
        "ix_prod_contract_chapter_status",
        table_name="chapter_production_contracts",
    )
    op.drop_table("chapter_production_contracts")
    op.drop_index(
        "ix_series_canon_series_status",
        table_name="series_canon_assets",
    )
    op.drop_table("series_canon_assets")
    op.drop_index(
        "ix_definition_packs_book_status",
        table_name="definition_packs",
    )
    op.drop_table("definition_packs")
    op.execute("DELETE FROM schema_metadata WHERE version = '0016'")
