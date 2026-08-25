"""Create the M1 authority and persistence kernel.

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-25
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

AUTHORITY_STATUSES = "'DRAFT','PROPOSED','REVIEWED','APPROVED','LOCKED','SUPERSEDED'"
PROPOSAL_STATUSES = "'OPEN','ACCEPTED','REJECTED','SUPERSEDED'"
DECISIONS = "'ACCEPT','REJECT','REQUEST_REVISION','WAIVE'"
ORIGINS = "'HUMAN_WRITTEN','AI_ASSISTED','AI_GENERATED','IMPORTED','SYSTEM_DERIVED'"


def upgrade() -> None:
    op.create_table(
        "provenance_records",
        sa.Column("provenance_id", sa.String(26), primary_key=True),
        sa.Column("origin", sa.String(32), nullable=False),
        sa.Column("actor", sa.String(255), nullable=False),
        sa.Column("task_id", sa.String(255), nullable=True),
        sa.Column("provider", sa.String(255), nullable=True),
        sa.Column("model", sa.String(255), nullable=True),
        sa.Column("model_version", sa.String(255), nullable=True),
        sa.Column("transformation_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.CheckConstraint(f"origin IN ({ORIGINS})", name="ck_provenance_origin"),
    )

    op.create_table(
        "authority_entities",
        sa.Column("entity_id", sa.String(26), primary_key=True),
        sa.Column("entity_type", sa.String(128), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
    )
    op.create_index("ix_authority_entities_type", "authority_entities", ["entity_type"])

    op.create_table(
        "revisions",
        sa.Column("revision_id", sa.String(26), primary_key=True),
        sa.Column("entity_id", sa.String(26), nullable=False),
        sa.Column("entity_type", sa.String(128), nullable=False),
        sa.Column("schema_name", sa.String(128), nullable=False),
        sa.Column("schema_version", sa.String(32), nullable=False),
        sa.Column("content_json", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("provenance_id", sa.String(26), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["entity_id"], ["authority_entities.entity_id"]),
        sa.ForeignKeyConstraint(["provenance_id"], ["provenance_records.provenance_id"]),
        sa.UniqueConstraint("revision_id", "content_hash", name="uq_revision_id_hash"),
    )
    op.create_index("ix_revisions_entity_created", "revisions", ["entity_id", "created_at"])
    op.create_index("ix_revisions_hash", "revisions", ["content_hash"])

    op.create_table(
        "revision_parents",
        sa.Column("revision_id", sa.String(26), nullable=False),
        sa.Column("parent_revision_id", sa.String(26), nullable=False),
        sa.ForeignKeyConstraint(["revision_id"], ["revisions.revision_id"]),
        sa.ForeignKeyConstraint(["parent_revision_id"], ["revisions.revision_id"]),
        sa.PrimaryKeyConstraint("revision_id", "parent_revision_id"),
    )

    op.create_table(
        "provenance_inputs",
        sa.Column("provenance_id", sa.String(26), nullable=False),
        sa.Column("revision_id", sa.String(26), nullable=False),
        sa.ForeignKeyConstraint(["provenance_id"], ["provenance_records.provenance_id"]),
        sa.ForeignKeyConstraint(["revision_id"], ["revisions.revision_id"]),
        sa.PrimaryKeyConstraint("provenance_id", "revision_id"),
    )

    op.create_table(
        "revision_status_history",
        sa.Column("status_event_id", sa.String(26), primary_key=True),
        sa.Column("revision_id", sa.String(26), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("actor", sa.String(255), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["revision_id"], ["revisions.revision_id"]),
        sa.CheckConstraint(f"status IN ({AUTHORITY_STATUSES})", name="ck_revision_status"),
    )
    op.create_index(
        "ix_revision_status_history_revision_created",
        "revision_status_history",
        ["revision_id", "created_at"],
    )

    op.create_table(
        "authority_heads",
        sa.Column("entity_id", sa.String(26), primary_key=True),
        sa.Column("revision_id", sa.String(26), nullable=False),
        sa.Column("revision_hash", sa.String(64), nullable=False),
        sa.Column("updated_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["entity_id"], ["authority_entities.entity_id"]),
        sa.ForeignKeyConstraint(
            ["revision_id", "revision_hash"],
            ["revisions.revision_id", "revisions.content_hash"],
            name="fk_authority_head_revision_hash",
        ),
    )

    op.create_table(
        "change_proposals",
        sa.Column("proposal_id", sa.String(26), primary_key=True),
        sa.Column("entity_id", sa.String(26), nullable=False),
        sa.Column("base_revision_id", sa.String(26), nullable=False),
        sa.Column("base_revision_hash", sa.String(64), nullable=False),
        sa.Column("proposed_schema_name", sa.String(128), nullable=False),
        sa.Column("proposed_schema_version", sa.String(32), nullable=False),
        sa.Column("proposed_content_json", sa.Text(), nullable=False),
        sa.Column("proposed_content_hash", sa.String(64), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="OPEN"),
        sa.Column("provenance_id", sa.String(26), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.Column("resolved_at", sa.String(32), nullable=True),
        sa.ForeignKeyConstraint(["entity_id"], ["authority_entities.entity_id"]),
        sa.ForeignKeyConstraint(
            ["base_revision_id", "base_revision_hash"],
            ["revisions.revision_id", "revisions.content_hash"],
            name="fk_proposal_base_revision_hash",
        ),
        sa.ForeignKeyConstraint(["provenance_id"], ["provenance_records.provenance_id"]),
        sa.CheckConstraint(f"status IN ({PROPOSAL_STATUSES})", name="ck_proposal_status"),
    )
    op.create_index(
        "ix_change_proposals_entity_status", "change_proposals", ["entity_id", "status"]
    )

    op.create_table(
        "decisions",
        sa.Column("decision_id", sa.String(26), primary_key=True),
        sa.Column("proposal_id", sa.String(26), nullable=True),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("actor", sa.String(255), nullable=False),
        sa.Column("actor_kind", sa.String(16), nullable=False),
        sa.Column("decision", sa.String(32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["proposal_id"], ["change_proposals.proposal_id"]),
        sa.CheckConstraint(f"decision IN ({DECISIONS})", name="ck_decision_value"),
        sa.CheckConstraint("actor_kind IN ('HUMAN','SYSTEM','AI')", name="ck_decision_actor_kind"),
    )

    op.create_table(
        "approvals",
        sa.Column("approval_id", sa.String(26), primary_key=True),
        sa.Column("proposal_id", sa.String(26), nullable=False),
        sa.Column("decision_id", sa.String(26), nullable=False),
        sa.Column("approved_revision_id", sa.String(26), nullable=False),
        sa.Column("prior_revision_id", sa.String(26), nullable=True),
        sa.Column("approving_actor", sa.String(255), nullable=False),
        sa.Column("approving_actor_kind", sa.String(16), nullable=False),
        sa.Column("gates_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["proposal_id"], ["change_proposals.proposal_id"]),
        sa.ForeignKeyConstraint(["decision_id"], ["decisions.decision_id"]),
        sa.ForeignKeyConstraint(["approved_revision_id"], ["revisions.revision_id"]),
        sa.ForeignKeyConstraint(["prior_revision_id"], ["revisions.revision_id"]),
        sa.CheckConstraint(
            "approving_actor_kind IN ('HUMAN','SYSTEM','AI')", name="ck_approval_actor_kind"
        ),
    )

    op.execute("INSERT INTO schema_metadata (version) VALUES ('0002')")

    # Immutable / append-only authority history is protected in the database, not only in UI code.
    for table in (
        "revisions",
        "revision_parents",
        "provenance_records",
        "provenance_inputs",
        "revision_status_history",
        "decisions",
        "approvals",
    ):
        op.execute(
            f"CREATE TRIGGER protect_{table}_update BEFORE UPDATE ON {table} "
            f"BEGIN SELECT RAISE(ABORT, '{table} is append-only'); END"
        )
        op.execute(
            f"CREATE TRIGGER protect_{table}_delete BEFORE DELETE ON {table} "
            f"BEGIN SELECT RAISE(ABORT, '{table} is append-only'); END"
        )


def downgrade() -> None:
    # M1 policy is no silent automatic downgrade. This function exists for developer migration tooling only.
    for table in (
        "revisions",
        "revision_parents",
        "provenance_records",
        "provenance_inputs",
        "revision_status_history",
        "decisions",
        "approvals",
    ):
        op.execute(f"DROP TRIGGER IF EXISTS protect_{table}_update")
        op.execute(f"DROP TRIGGER IF EXISTS protect_{table}_delete")
    op.drop_table("approvals")
    op.drop_table("decisions")
    op.drop_index("ix_change_proposals_entity_status", table_name="change_proposals")
    op.drop_table("change_proposals")
    op.drop_table("authority_heads")
    op.drop_index(
        "ix_revision_status_history_revision_created", table_name="revision_status_history"
    )
    op.drop_table("revision_status_history")
    op.drop_table("provenance_inputs")
    op.drop_table("revision_parents")
    op.drop_index("ix_revisions_hash", table_name="revisions")
    op.drop_index("ix_revisions_entity_created", table_name="revisions")
    op.drop_table("revisions")
    op.drop_index("ix_authority_entities_type", table_name="authority_entities")
    op.drop_table("authority_entities")
    op.drop_table("provenance_records")
    op.execute("DELETE FROM schema_metadata WHERE version = '0002'")
