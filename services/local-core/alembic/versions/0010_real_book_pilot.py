"""Create real-book pilot evidence persistence.

Revision ID: 0010
Revises: 0009
Create Date: 2026-08-29
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

PILOT_STAGES = (
    "'IDEA','BOOK_DEFINITION','RESEARCH','BOOK_CONTRACT','ARCHITECTURE',"
    "'CHAPTER_CONTRACTS','DRAFTING','BOOK_MEMORY','EDITORIAL','BOOKBENCH',"
    "'FINAL_REVIEW','LITERARY_MASTER'"
)
EVENT_KINDS = (
    "'STARTED','COMPLETED','CHECKPOINT','HUMAN_REVIEW','NOT_APPLICABLE',"
    "'LITERARY_QUALITY_JUDGMENT','COST_CHECKPOINT','DEFECT_REVIEW'"
)
OBSERVATION_CATEGORIES = (
    "'PRODUCT_DEFECT','WORKFLOW_FRICTION','MISSED_ERROR','BOOKBENCH_FALSE_POSITIVE',"
    "'BOOKBENCH_FALSE_NEGATIVE','MODEL_QUALITY_FAILURE','VOICE_FAILURE',"
    "'RESEARCH_TRACEABILITY_FAILURE','HUMAN_DECISION_REASON','OTHER'"
)


def upgrade() -> None:
    op.create_table(
        "pilot_runs",
        sa.Column("pilot_id", sa.String(26), primary_key=True),
        sa.Column("book_id", sa.String(26), nullable=False),
        sa.Column("profile_version", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("human_actor", sa.String(255), nullable=False),
        sa.Column("started_at", sa.String(32), nullable=False),
        sa.Column("completed_at", sa.String(32), nullable=True),
        sa.Column("final_decision", sa.String(24), nullable=True),
        sa.Column("final_reason", sa.Text(), nullable=True),
        sa.Column("decision_actor", sa.String(255), nullable=True),
        sa.Column("decision_actor_kind", sa.String(16), nullable=True),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"]),
        sa.CheckConstraint(
            "status IN ('ACTIVE','COMPLETED','ABORTED')", name="ck_pilot_run_status"
        ),
        sa.CheckConstraint(
            "final_decision IS NULL OR final_decision IN ('GO','CONDITIONAL_GO','NO_GO')",
            name="ck_pilot_final_decision",
        ),
        sa.CheckConstraint(
            "decision_actor_kind IS NULL OR decision_actor_kind='HUMAN'",
            name="ck_pilot_decision_human",
        ),
        sa.CheckConstraint(
            "final_decision IS NULL OR (status='COMPLETED' AND completed_at IS NOT NULL "
            "AND final_reason IS NOT NULL AND length(trim(final_reason))>0 "
            "AND decision_actor IS NOT NULL AND length(trim(decision_actor))>0 "
            "AND decision_actor_kind='HUMAN')",
            name="ck_pilot_final_decision_complete",
        ),
    )
    op.create_index("ix_pilot_runs_book_started", "pilot_runs", ["book_id", "started_at"])
    op.execute(
        "CREATE UNIQUE INDEX uq_pilot_active_per_book ON pilot_runs(book_id) WHERE status='ACTIVE'"
    )

    op.create_table(
        "pilot_stage_events",
        sa.Column("event_id", sa.String(26), primary_key=True),
        sa.Column("pilot_id", sa.String(26), nullable=False),
        sa.Column("stage", sa.String(32), nullable=False),
        sa.Column("event_kind", sa.String(40), nullable=False),
        sa.Column("actor", sa.String(255), nullable=False),
        sa.Column("actor_kind", sa.String(16), nullable=False),
        sa.Column("elapsed_seconds", sa.Integer(), nullable=True),
        sa.Column("human_minutes", sa.Integer(), nullable=True),
        sa.Column("provider_cost_usd", sa.Float(), nullable=True),
        sa.Column("model_run_count", sa.Integer(), nullable=True),
        sa.Column("outcome", sa.String(24), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["pilot_id"], ["pilot_runs.pilot_id"]),
        sa.CheckConstraint(f"stage IN ({PILOT_STAGES})", name="ck_pilot_stage"),
        sa.CheckConstraint(f"event_kind IN ({EVENT_KINDS})", name="ck_pilot_event_kind"),
        sa.CheckConstraint("actor_kind IN ('HUMAN','AI','SYSTEM')", name="ck_pilot_event_actor"),
        sa.CheckConstraint(
            "event_kind NOT IN ('HUMAN_REVIEW','LITERARY_QUALITY_JUDGMENT','DEFECT_REVIEW') "
            "OR actor_kind='HUMAN'",
            name="ck_pilot_human_review_actor",
        ),
        sa.CheckConstraint(
            "outcome IN ('SUCCESS','ATTENTION','BLOCKED','NOT_APPLICABLE')",
            name="ck_pilot_event_outcome",
        ),
        sa.CheckConstraint(
            "elapsed_seconds IS NULL OR elapsed_seconds >= 0", name="ck_pilot_elapsed_nonnegative"
        ),
        sa.CheckConstraint(
            "human_minutes IS NULL OR human_minutes >= 0", name="ck_pilot_human_nonnegative"
        ),
        sa.CheckConstraint(
            "provider_cost_usd IS NULL OR provider_cost_usd >= 0",
            name="ck_pilot_cost_nonnegative",
        ),
        sa.CheckConstraint(
            "model_run_count IS NULL OR model_run_count >= 0", name="ck_pilot_runs_nonnegative"
        ),
    )
    op.create_index(
        "ix_pilot_stage_events_pilot_stage",
        "pilot_stage_events",
        ["pilot_id", "stage", "created_at"],
    )

    op.create_table(
        "pilot_observations",
        sa.Column("observation_id", sa.String(26), primary_key=True),
        sa.Column("pilot_id", sa.String(26), nullable=False),
        sa.Column("stage", sa.String(32), nullable=False),
        sa.Column("category", sa.String(48), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("actor", sa.String(255), nullable=False),
        sa.Column("actor_kind", sa.String(16), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("artifact_ref", sa.String(255), nullable=True),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.Column("resolved_at", sa.String(32), nullable=True),
        sa.Column("resolution_actor", sa.String(255), nullable=True),
        sa.Column("resolution_actor_kind", sa.String(16), nullable=True),
        sa.Column("resolution_reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["pilot_id"], ["pilot_runs.pilot_id"]),
        sa.CheckConstraint(f"stage IN ({PILOT_STAGES})", name="ck_pilot_observation_stage"),
        sa.CheckConstraint(
            f"category IN ({OBSERVATION_CATEGORIES})", name="ck_pilot_observation_category"
        ),
        sa.CheckConstraint(
            "severity IN ('INFO','ATTENTION','BLOCKING')", name="ck_pilot_observation_severity"
        ),
        sa.CheckConstraint(
            "actor_kind IN ('HUMAN','AI','SYSTEM')", name="ck_pilot_observation_actor"
        ),
        sa.CheckConstraint(
            "resolution_actor_kind IS NULL OR resolution_actor_kind IN ('HUMAN','SYSTEM')",
            name="ck_pilot_resolution_actor",
        ),
        sa.CheckConstraint(
            "resolved_at IS NULL OR (resolution_actor IS NOT NULL "
            "AND length(trim(resolution_actor))>0 AND resolution_actor_kind IS NOT NULL "
            "AND resolution_reason IS NOT NULL AND length(trim(resolution_reason))>0)",
            name="ck_pilot_resolution_complete",
        ),
        sa.CheckConstraint(
            "severity!='BLOCKING' OR resolved_at IS NULL OR resolution_actor_kind='HUMAN'",
            name="ck_pilot_blocking_resolution_human",
        ),
    )
    op.create_index(
        "ix_pilot_observations_open",
        "pilot_observations",
        ["pilot_id", "severity", "resolved_at"],
    )

    op.execute("INSERT INTO schema_metadata (version) VALUES ('0010')")

    op.execute(
        "CREATE TRIGGER protect_pilot_runs_delete BEFORE DELETE ON pilot_runs "
        "BEGIN SELECT RAISE(ABORT, 'pilot_runs cannot be deleted'); END"
    )
    op.execute(
        "CREATE TRIGGER protect_final_pilot_update BEFORE UPDATE ON pilot_runs "
        "WHEN OLD.status!='ACTIVE' BEGIN SELECT RAISE(ABORT, 'final pilot decision is immutable'); END"
    )
    op.execute(
        "CREATE TRIGGER protect_pilot_stage_events_update BEFORE UPDATE ON pilot_stage_events "
        "BEGIN SELECT RAISE(ABORT, 'pilot stage events are append-only'); END"
    )
    op.execute(
        "CREATE TRIGGER protect_pilot_stage_events_delete BEFORE DELETE ON pilot_stage_events "
        "BEGIN SELECT RAISE(ABORT, 'pilot stage events are append-only'); END"
    )
    op.execute(
        "CREATE TRIGGER protect_pilot_observations_delete BEFORE DELETE ON pilot_observations "
        "BEGIN SELECT RAISE(ABORT, 'pilot observations cannot be deleted'); END"
    )
    op.execute(
        "CREATE TRIGGER protect_resolved_observation_update BEFORE UPDATE ON pilot_observations "
        "WHEN OLD.resolved_at IS NOT NULL "
        "BEGIN SELECT RAISE(ABORT, 'resolved pilot observation is immutable'); END"
    )


def downgrade() -> None:
    for trigger in (
        "protect_resolved_observation_update",
        "protect_pilot_observations_delete",
        "protect_pilot_stage_events_delete",
        "protect_pilot_stage_events_update",
        "protect_final_pilot_update",
        "protect_pilot_runs_delete",
    ):
        op.execute(f"DROP TRIGGER IF EXISTS {trigger}")
    op.drop_index("ix_pilot_observations_open", table_name="pilot_observations")
    op.drop_table("pilot_observations")
    op.drop_index("ix_pilot_stage_events_pilot_stage", table_name="pilot_stage_events")
    op.drop_table("pilot_stage_events")
    op.execute("DROP INDEX IF EXISTS uq_pilot_active_per_book")
    op.drop_index("ix_pilot_runs_book_started", table_name="pilot_runs")
    op.drop_table("pilot_runs")
    op.execute("DELETE FROM schema_metadata WHERE version = '0010'")
