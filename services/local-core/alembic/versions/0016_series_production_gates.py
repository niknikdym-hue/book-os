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
        sa.UniqueConstraint("book_id", "revision", name="uq_definition_pack_book_revision"),
        sa.CheckConstraint("revision > 0", name="ck_definition_pack_revision_positive"),
        sa.CheckConstraint(
            "status IN ('DRAFT','APPROVED','SUPERSEDED')",
            name="ck_definition_pack_status",
        ),
        sa.CheckConstraint(
            "status != 'APPROVED' OR (approved_by IS NOT NULL AND approved_at IS NOT NULL)",
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
        sa.UniqueConstraint("series_profile_id", "asset_key", name="uq_series_canon_asset_key"),
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
        sa.ForeignKeyConstraint(["architecture_revision_id"], ["revisions.revision_id"]),
        sa.ForeignKeyConstraint(["chapter_contract_revision_id"], ["revisions.revision_id"]),
        sa.CheckConstraint(
            "status IN ('DRAFT','APPROVED','SUPERSEDED')",
            name="ck_production_contract_status",
        ),
        sa.CheckConstraint(
            "status != 'APPROVED' OR (approved_by IS NOT NULL AND approved_at IS NOT NULL)",
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
        sa.ForeignKeyConstraint(["architecture_revision_id"], ["revisions.revision_id"]),
        sa.ForeignKeyConstraint(["chapter_contract_revision_id"], ["revisions.revision_id"]),
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
        sa.ForeignKeyConstraint(["definition_id"], ["definition_packs.definition_id"]),
        sa.ForeignKeyConstraint(["architecture_revision_id"], ["revisions.revision_id"]),
        sa.ForeignKeyConstraint(["chapter_contract_revision_id"], ["revisions.revision_id"]),
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
            "progress_percent IS NULL OR (progress_percent >= 0 AND progress_percent <= 100)",
            name="ck_production_checkpoint_progress",
        ),
        sa.CheckConstraint(
            "kind != 'MID_BOOK' OR (progress_percent >= 40 AND progress_percent <= 60)",
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
        sa.UniqueConstraint("book_id", "master_id", name="uq_series_closure_master"),
    )

    op.execute("INSERT INTO schema_metadata (version) VALUES ('0016')")

    op.execute(
        "CREATE TRIGGER protect_used_accepted_asset_status "
        "BEFORE UPDATE OF status ON series_canon_assets "
        "WHEN OLD.status='USED_ACCEPTED' AND NEW.status!='USED_ACCEPTED' "
        "BEGIN SELECT RAISE(ABORT, 'USED_ACCEPTED series asset is immutable'); END"
    )
    op.execute(
        "CREATE TRIGGER protect_used_accepted_asset_delete "
        "BEFORE DELETE ON series_canon_assets WHEN OLD.status='USED_ACCEPTED' "
        "BEGIN SELECT RAISE(ABORT, 'USED_ACCEPTED series asset is immutable'); END"
    )
    op.execute(
        "CREATE TRIGGER protect_chapter_admissions_update BEFORE UPDATE ON chapter_admissions "
        "BEGIN SELECT RAISE(ABORT, 'chapter_admissions is append-only'); END"
    )
    op.execute(
        "CREATE TRIGGER protect_chapter_admissions_delete BEFORE DELETE ON chapter_admissions "
        "BEGIN SELECT RAISE(ABORT, 'chapter_admissions is append-only'); END"
    )
    op.execute(
        "CREATE TRIGGER protect_series_closures_update BEFORE UPDATE ON series_closures "
        "BEGIN SELECT RAISE(ABORT, 'series_closures is append-only'); END"
    )
    op.execute(
        "CREATE TRIGGER protect_series_closures_delete BEFORE DELETE ON series_closures "
        "BEGIN SELECT RAISE(ABORT, 'series_closures is append-only'); END"
    )
    op.execute(
        "CREATE TRIGGER protect_approved_definition_update BEFORE UPDATE ON definition_packs "
        "WHEN OLD.status='APPROVED' "
        "BEGIN SELECT RAISE(ABORT, 'approved definition pack is immutable'); END"
    )
    op.execute(
        "CREATE TRIGGER protect_approved_prod_contract_update BEFORE UPDATE ON chapter_production_contracts "
        "WHEN OLD.status='APPROVED' "
        "BEGIN SELECT RAISE(ABORT, 'approved production contract is immutable'); END"
    )

    op.execute(
        "CREATE TRIGGER require_current_writing_admission BEFORE INSERT ON bounded_tasks "
        "WHEN NEW.task_type='SECTION_DRAFT' BEGIN "
        "SELECT CASE WHEN NOT EXISTS ("
        "SELECT 1 FROM chapter_admissions a "
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
        "WHERE c.book_id=NEW.book_id AND c.chapter_id=NEW.chapter_id)"
        ") THEN RAISE(ABORT, 'WRITING_NOT_ALLOWED') END; END"
    )
    op.get_bind().exec_driver_sql(
        "CREATE TRIGGER require_adversarial_review_for_literary_master "
        "BEFORE INSERT ON literary_masters BEGIN "
        "SELECT CASE WHEN NOT EXISTS ("
        "SELECT 1 FROM production_checkpoints p WHERE p.book_id=NEW.book_id "
        "AND p.kind='ADVERSARIAL_REVIEW' AND p.status!='BLOCKING' "
        "AND p.executor_identity IS NOT NULL AND p.executor_identity!='' "
        "AND p.findings_json LIKE '%\"independent\":true%' "
        "AND p.checkpoint_id=(SELECT p2.checkpoint_id FROM production_checkpoints p2 "
        "WHERE p2.book_id=NEW.book_id AND p2.kind='ADVERSARIAL_REVIEW' "
        "ORDER BY p2.created_at DESC,p2.checkpoint_id DESC LIMIT 1)"
        ") THEN RAISE(ABORT, 'ADVERSARIAL_REVIEW_REQUIRED') END; END"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS require_adversarial_review_for_literary_master")
    op.execute("DROP TRIGGER IF EXISTS require_current_writing_admission")
    op.execute("DROP TRIGGER IF EXISTS protect_approved_prod_contract_update")
    op.execute("DROP TRIGGER IF EXISTS protect_approved_definition_update")
    op.execute("DROP TRIGGER IF EXISTS protect_series_closures_delete")
    op.execute("DROP TRIGGER IF EXISTS protect_series_closures_update")
    op.execute("DROP TRIGGER IF EXISTS protect_chapter_admissions_delete")
    op.execute("DROP TRIGGER IF EXISTS protect_chapter_admissions_update")
    op.execute("DROP TRIGGER IF EXISTS protect_used_accepted_asset_delete")
    op.execute("DROP TRIGGER IF EXISTS protect_used_accepted_asset_status")
    op.drop_table("series_closures")
    op.drop_index("ix_production_checkpoints_book_kind", table_name="production_checkpoints")
    op.drop_table("production_checkpoints")
    op.drop_index("ix_admissions_chapter_created", table_name="chapter_admissions")
    op.drop_table("chapter_admissions")
    op.drop_index("ix_uniqueness_chapter_created", table_name="book_uniqueness_ledger")
    op.drop_table("book_uniqueness_ledger")
    op.drop_index("ix_prod_contract_chapter_status", table_name="chapter_production_contracts")
    op.drop_table("chapter_production_contracts")
    op.drop_index("ix_series_canon_series_status", table_name="series_canon_assets")
    op.drop_table("series_canon_assets")
    op.drop_index("ix_definition_packs_book_status", table_name="definition_packs")
    op.drop_table("definition_packs")
    op.execute("DELETE FROM schema_metadata WHERE version='0016'")
