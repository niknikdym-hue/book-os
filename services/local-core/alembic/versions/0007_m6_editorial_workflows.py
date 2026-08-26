"""Create M6 Editorial Workflow persistence.

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-26
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

EDITORIAL_ROLES = (
    "'DEVELOPMENTAL_EDITOR','CROSS_BOOK_AUDITOR','FACT_CHECKER','LITERARY_EDITOR','STYLE_GUARDIAN'"
)
FINDING_STATES = "'OPEN','RESOLVED','WAIVED','SUPERSEDED'"
FINDING_SEVERITIES = "'INFO','MINOR','MAJOR','CRITICAL'"
ACTOR_KINDS = "'HUMAN','SYSTEM','AI'"
RUN_STATES = "'RUNNING','SUCCEEDED','FAILED'"


def upgrade() -> None:
    op.create_table(
        "editorial_runs",
        sa.Column("run_id", sa.String(26), primary_key=True),
        sa.Column("book_id", sa.String(26), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("runner_id", sa.String(128), nullable=False),
        sa.Column("runner_version", sa.String(32), nullable=False),
        sa.Column("scope_kind", sa.String(32), nullable=False),
        sa.Column("chapter_id", sa.String(26), nullable=True),
        sa.Column("unit_id", sa.String(26), nullable=True),
        sa.Column("input_snapshot_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.Column("completed_at", sa.String(32), nullable=True),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"]),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.chapter_id"]),
        sa.ForeignKeyConstraint(["unit_id"], ["manuscript_units.unit_id"]),
        sa.CheckConstraint(f"role IN ({EDITORIAL_ROLES})", name="ck_editorial_run_role"),
        sa.CheckConstraint(
            "scope_kind IN ('BOOK','CHAPTER','MANUSCRIPT_UNIT')",
            name="ck_editorial_run_scope",
        ),
        sa.CheckConstraint(f"status IN ({RUN_STATES})", name="ck_editorial_run_status"),
    )
    op.create_index(
        "ix_editorial_runs_book_role_created",
        "editorial_runs",
        ["book_id", "role", "created_at"],
    )

    op.create_table(
        "editorial_findings",
        sa.Column("finding_id", sa.String(26), primary_key=True),
        sa.Column("run_id", sa.String(26), nullable=True),
        sa.Column("book_id", sa.String(26), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("category", sa.String(96), nullable=False),
        sa.Column("target_kind", sa.String(32), nullable=False),
        sa.Column("target_entity_id", sa.String(26), nullable=False),
        sa.Column("chapter_id", sa.String(26), nullable=True),
        sa.Column("unit_id", sa.String(26), nullable=True),
        sa.Column("base_revision_id", sa.String(26), nullable=False),
        sa.Column("base_revision_hash", sa.String(64), nullable=False),
        sa.Column("diagnosis", sa.Text(), nullable=False),
        sa.Column("why", sa.Text(), nullable=False),
        sa.Column("evidence_json", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("expected_effect", sa.Text(), nullable=False),
        sa.Column("risks", sa.Text(), nullable=False),
        sa.Column("actor", sa.String(128), nullable=False),
        sa.Column("actor_kind", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.Column("resolved_at", sa.String(32), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["editorial_runs.run_id"]),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"]),
        sa.ForeignKeyConstraint(["target_entity_id"], ["authority_entities.entity_id"]),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.chapter_id"]),
        sa.ForeignKeyConstraint(["unit_id"], ["manuscript_units.unit_id"]),
        sa.ForeignKeyConstraint(
            ["base_revision_id", "base_revision_hash"],
            ["revisions.revision_id", "revisions.content_hash"],
            name="fk_editorial_finding_base_revision_hash",
        ),
        sa.CheckConstraint(f"role IN ({EDITORIAL_ROLES})", name="ck_editorial_finding_role"),
        sa.CheckConstraint(
            "target_kind IN ('MANUSCRIPT_UNIT','CHAPTER_CONTRACT','BOOK_CONTRACT')",
            name="ck_editorial_finding_target_kind",
        ),
        sa.CheckConstraint(
            f"severity IN ({FINDING_SEVERITIES})", name="ck_editorial_finding_severity"
        ),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_finding_confidence"),
        sa.CheckConstraint(f"actor_kind IN ({ACTOR_KINDS})", name="ck_finding_actor_kind"),
        sa.CheckConstraint(f"status IN ({FINDING_STATES})", name="ck_editorial_finding_status"),
    )
    op.create_index(
        "ix_editorial_findings_inbox",
        "editorial_findings",
        ["book_id", "status", "severity", "created_at"],
    )
    op.create_index(
        "ix_editorial_findings_target",
        "editorial_findings",
        ["book_id", "target_entity_id", "base_revision_id"],
    )

    op.create_table(
        "editorial_finding_state_history",
        sa.Column("state_event_id", sa.String(26), primary_key=True),
        sa.Column("finding_id", sa.String(26), nullable=False),
        sa.Column("prior_state", sa.String(16), nullable=True),
        sa.Column("new_state", sa.String(16), nullable=False),
        sa.Column("actor", sa.String(128), nullable=False),
        sa.Column("actor_kind", sa.String(16), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["finding_id"], ["editorial_findings.finding_id"]),
        sa.CheckConstraint(
            f"prior_state IS NULL OR prior_state IN ({FINDING_STATES})",
            name="ck_editorial_finding_prior_state",
        ),
        sa.CheckConstraint(
            f"new_state IN ({FINDING_STATES})", name="ck_editorial_finding_new_state"
        ),
        sa.CheckConstraint(f"actor_kind IN ({ACTOR_KINDS})", name="ck_editorial_state_actor_kind"),
    )
    op.create_index(
        "ix_editorial_finding_state_history",
        "editorial_finding_state_history",
        ["finding_id", "created_at"],
    )

    op.create_table(
        "editorial_finding_proposals",
        sa.Column("finding_id", sa.String(26), nullable=False),
        sa.Column("proposal_id", sa.String(26), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.PrimaryKeyConstraint("finding_id", "proposal_id"),
        sa.UniqueConstraint("proposal_id", name="uq_editorial_finding_proposal"),
        sa.ForeignKeyConstraint(["finding_id"], ["editorial_findings.finding_id"]),
        sa.ForeignKeyConstraint(["proposal_id"], ["change_proposals.proposal_id"]),
    )
    op.create_index(
        "ix_editorial_finding_proposals_finding",
        "editorial_finding_proposals",
        ["finding_id", "created_at"],
    )

    op.execute("INSERT INTO schema_metadata (version) VALUES ('0007')")

    # Diagnostic content is immutable; only workflow state/resolution timestamp may change.
    op.execute(
        """
        CREATE TRIGGER editorial_findings_immutable_content
        BEFORE UPDATE ON editorial_findings
        WHEN NEW.run_id IS NOT OLD.run_id
          OR NEW.book_id != OLD.book_id
          OR NEW.role != OLD.role
          OR NEW.category != OLD.category
          OR NEW.target_kind != OLD.target_kind
          OR NEW.target_entity_id != OLD.target_entity_id
          OR NEW.chapter_id IS NOT OLD.chapter_id
          OR NEW.unit_id IS NOT OLD.unit_id
          OR NEW.base_revision_id != OLD.base_revision_id
          OR NEW.base_revision_hash != OLD.base_revision_hash
          OR NEW.diagnosis != OLD.diagnosis
          OR NEW.why != OLD.why
          OR NEW.evidence_json != OLD.evidence_json
          OR NEW.severity != OLD.severity
          OR NEW.confidence != OLD.confidence
          OR NEW.expected_effect != OLD.expected_effect
          OR NEW.risks != OLD.risks
          OR NEW.actor != OLD.actor
          OR NEW.actor_kind != OLD.actor_kind
          OR NEW.created_at != OLD.created_at
        BEGIN
            SELECT RAISE(ABORT, 'editorial finding diagnostic content is immutable');
        END
        """
    )
    for table in ("editorial_finding_state_history", "editorial_finding_proposals"):
        op.execute(
            f"""
            CREATE TRIGGER {table}_no_update
            BEFORE UPDATE ON {table}
            BEGIN
                SELECT RAISE(ABORT, '{table} is append-only');
            END
            """
        )
        op.execute(
            f"""
            CREATE TRIGGER {table}_no_delete
            BEFORE DELETE ON {table}
            BEGIN
                SELECT RAISE(ABORT, '{table} is append-only');
            END
            """
        )


def downgrade() -> None:
    for table in ("editorial_finding_state_history", "editorial_finding_proposals"):
        op.execute(f"DROP TRIGGER IF EXISTS {table}_no_delete")
        op.execute(f"DROP TRIGGER IF EXISTS {table}_no_update")
    op.execute("DROP TRIGGER IF EXISTS editorial_findings_immutable_content")
    op.drop_index(
        "ix_editorial_finding_proposals_finding", table_name="editorial_finding_proposals"
    )
    op.drop_table("editorial_finding_proposals")
    op.drop_index(
        "ix_editorial_finding_state_history", table_name="editorial_finding_state_history"
    )
    op.drop_table("editorial_finding_state_history")
    op.drop_index("ix_editorial_findings_target", table_name="editorial_findings")
    op.drop_index("ix_editorial_findings_inbox", table_name="editorial_findings")
    op.drop_table("editorial_findings")
    op.drop_index("ix_editorial_runs_book_role_created", table_name="editorial_runs")
    op.drop_table("editorial_runs")
    op.execute("DELETE FROM schema_metadata WHERE version = '0007'")
