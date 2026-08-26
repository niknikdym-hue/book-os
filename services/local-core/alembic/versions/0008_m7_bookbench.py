"""Create M7 BookBench evaluation persistence.

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-26
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

DIMENSIONS = (
    "'BOOK_CONTRACT_FULFILLMENT','CHAPTER_CONTRACT_FULFILLMENT','SEMANTIC_NOVELTY',"
    "'IDEA_REPETITION','CONTRADICTION_INCONSISTENCY','THOUGHT_DENSITY',"
    "'SPECIFICITY_GENERICNESS','EVIDENCE_UNSUPPORTED_CLAIMS','AUTHOR_VOICE',"
    "'AI_PROSE_PATHOLOGY','OPENING_ENDING_TRANSITION','CROSS_BOOK_COHERENCE'"
)
EVALUATOR_CLASSES = "'DETERMINISTIC','SEMANTIC','LLM_JUDGE','PAIRWISE','HUMAN_LABEL'"
RUN_STATES = "'RUNNING','SUCCEEDED','FAILED'"
FINDING_SEVERITIES = "'INFO','ATTENTION','BLOCKING'"
INDEPENDENCE_STATES = "'INDEPENDENT','SAME_CONFIG','UNKNOWN','NOT_APPLICABLE'"
SNAPSHOT_SCOPES = "'MANUSCRIPT_UNIT','CHAPTER','BOOK'"
TARGET_KINDS = "'MANUSCRIPT_UNIT','BOOK_CONTRACT','CHAPTER_CONTRACT','CLAIM','BOOK'"


def upgrade() -> None:
    op.create_table(
        "evaluation_snapshots",
        sa.Column("snapshot_id", sa.String(26), primary_key=True),
        sa.Column("book_id", sa.String(26), nullable=False),
        sa.Column("scope", sa.String(32), nullable=False),
        sa.Column("chapter_id", sa.String(26), nullable=True),
        sa.Column("unit_id", sa.String(26), nullable=True),
        sa.Column("snapshot_json", sa.Text(), nullable=False),
        sa.Column("snapshot_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"]),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.chapter_id"]),
        sa.ForeignKeyConstraint(["unit_id"], ["manuscript_units.unit_id"]),
        sa.CheckConstraint(f"scope IN ({SNAPSHOT_SCOPES})", name="ck_eval_snapshot_scope"),
        sa.UniqueConstraint("book_id", "snapshot_hash", name="uq_eval_snapshot_hash"),
    )
    op.create_index(
        "ix_evaluation_snapshots_book_created",
        "evaluation_snapshots",
        ["book_id", "created_at"],
    )

    op.create_table(
        "evaluation_snapshot_targets",
        sa.Column("snapshot_id", sa.String(26), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("target_kind", sa.String(32), nullable=False),
        sa.Column("target_id", sa.String(26), nullable=False),
        sa.Column("chapter_id", sa.String(26), nullable=True),
        sa.Column("unit_id", sa.String(26), nullable=True),
        sa.Column("revision_id", sa.String(26), nullable=False),
        sa.Column("revision_hash", sa.String(64), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("source_status", sa.String(32), nullable=False),
        sa.PrimaryKeyConstraint("snapshot_id", "ordinal"),
        sa.ForeignKeyConstraint(["snapshot_id"], ["evaluation_snapshots.snapshot_id"]),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.chapter_id"]),
        sa.ForeignKeyConstraint(["unit_id"], ["manuscript_units.unit_id"]),
        sa.ForeignKeyConstraint(
            ["revision_id", "revision_hash"],
            ["revisions.revision_id", "revisions.content_hash"],
            name="fk_eval_snapshot_target_revision_hash",
        ),
        sa.CheckConstraint(f"target_kind IN ({TARGET_KINDS})", name="ck_eval_target_kind"),
    )
    op.create_index(
        "ix_eval_snapshot_targets_identity",
        "evaluation_snapshot_targets",
        ["snapshot_id", "target_kind", "target_id"],
    )

    op.create_table(
        "evaluation_runs",
        sa.Column("evaluation_id", sa.String(26), primary_key=True),
        sa.Column("book_id", sa.String(26), nullable=False),
        sa.Column("snapshot_id", sa.String(26), nullable=False),
        sa.Column("check_id", sa.String(128), nullable=False),
        sa.Column("check_version", sa.String(32), nullable=False),
        sa.Column("registry_hash", sa.String(64), nullable=False),
        sa.Column("dimension", sa.String(64), nullable=False),
        sa.Column("evaluator_class", sa.String(32), nullable=False),
        sa.Column("evaluator_id", sa.String(128), nullable=False),
        sa.Column("evaluator_version", sa.String(64), nullable=False),
        sa.Column("provider", sa.String(64), nullable=True),
        sa.Column("model", sa.String(128), nullable=True),
        sa.Column("config_id", sa.String(128), nullable=True),
        sa.Column("prompt_id", sa.String(128), nullable=True),
        sa.Column("prompt_version", sa.String(32), nullable=True),
        sa.Column("prompt_hash", sa.String(64), nullable=True),
        sa.Column("dataset_snapshot_id", sa.String(26), nullable=True),
        sa.Column("independence_state", sa.String(32), nullable=False),
        sa.Column("input_hash", sa.String(64), nullable=False),
        sa.Column("output_json", sa.Text(), nullable=False),
        sa.Column("usage_json", sa.Text(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("cost_usd", sa.Float(), nullable=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.Column("completed_at", sa.String(32), nullable=True),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"]),
        sa.ForeignKeyConstraint(["snapshot_id"], ["evaluation_snapshots.snapshot_id"]),
        sa.CheckConstraint(f"dimension IN ({DIMENSIONS})", name="ck_evaluation_dimension"),
        sa.CheckConstraint(f"evaluator_class IN ({EVALUATOR_CLASSES})", name="ck_evaluator_class"),
        sa.CheckConstraint(
            f"independence_state IN ({INDEPENDENCE_STATES})",
            name="ck_evaluation_independence",
        ),
        sa.CheckConstraint(f"status IN ({RUN_STATES})", name="ck_evaluation_run_status"),
        sa.CheckConstraint("latency_ms >= 0", name="ck_evaluation_latency"),
    )
    op.create_index(
        "ix_evaluation_runs_book_dimension",
        "evaluation_runs",
        ["book_id", "dimension", "created_at"],
    )
    op.create_index(
        "ix_evaluation_runs_snapshot",
        "evaluation_runs",
        ["snapshot_id", "created_at"],
    )

    op.create_table(
        "evaluation_findings",
        sa.Column("finding_id", sa.String(26), primary_key=True),
        sa.Column("evaluation_id", sa.String(26), nullable=False),
        sa.Column("dimension", sa.String(64), nullable=False),
        sa.Column("category", sa.String(128), nullable=False),
        sa.Column("target_kind", sa.String(32), nullable=False),
        sa.Column("target_id", sa.String(26), nullable=False),
        sa.Column("chapter_id", sa.String(26), nullable=True),
        sa.Column("unit_id", sa.String(26), nullable=True),
        sa.Column("revision_id", sa.String(26), nullable=False),
        sa.Column("revision_hash", sa.String(64), nullable=False),
        sa.Column("location", sa.Text(), nullable=False),
        sa.Column("evidence_json", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("recommended_action", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["evaluation_id"], ["evaluation_runs.evaluation_id"]),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.chapter_id"]),
        sa.ForeignKeyConstraint(["unit_id"], ["manuscript_units.unit_id"]),
        sa.ForeignKeyConstraint(
            ["revision_id", "revision_hash"],
            ["revisions.revision_id", "revisions.content_hash"],
            name="fk_evaluation_finding_revision_hash",
        ),
        sa.CheckConstraint(f"dimension IN ({DIMENSIONS})", name="ck_eval_finding_dimension"),
        sa.CheckConstraint(f"target_kind IN ({TARGET_KINDS})", name="ck_eval_finding_target_kind"),
        sa.CheckConstraint(f"severity IN ({FINDING_SEVERITIES})", name="ck_eval_finding_severity"),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_eval_confidence"),
    )
    op.create_index(
        "ix_evaluation_findings_run",
        "evaluation_findings",
        ["evaluation_id", "severity", "finding_id"],
    )

    op.create_table(
        "evaluation_metrics",
        sa.Column("metric_id", sa.String(26), primary_key=True),
        sa.Column("evaluation_id", sa.String(26), nullable=False),
        sa.Column("metric_name", sa.String(128), nullable=False),
        sa.Column("metric_value_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["evaluation_id"], ["evaluation_runs.evaluation_id"]),
        sa.UniqueConstraint("evaluation_id", "metric_name", name="uq_evaluation_metric_name"),
    )

    op.create_table(
        "voice_fingerprints",
        sa.Column("fingerprint_id", sa.String(26), primary_key=True),
        sa.Column("book_id", sa.String(26), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("extractor_id", sa.String(128), nullable=False),
        sa.Column("extractor_version", sa.String(32), nullable=False),
        sa.Column("extractor_hash", sa.String(64), nullable=False),
        sa.Column("reference_snapshot_id", sa.String(26), nullable=False),
        sa.Column("features_json", sa.Text(), nullable=False),
        sa.Column("fingerprint_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"]),
        sa.ForeignKeyConstraint(["reference_snapshot_id"], ["evaluation_snapshots.snapshot_id"]),
        sa.UniqueConstraint("book_id", "fingerprint_hash", name="uq_voice_fingerprint_hash"),
    )

    op.create_table(
        "evaluation_dataset_snapshots",
        sa.Column("dataset_snapshot_id", sa.String(26), primary_key=True),
        sa.Column("book_id", sa.String(26), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("dataset_hash", sa.String(64), nullable=False),
        sa.Column("case_count", sa.Integer(), nullable=False),
        sa.Column("source_cutoff_at", sa.String(32), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"]),
        sa.UniqueConstraint("book_id", "name", "version", name="uq_eval_dataset_version"),
        sa.UniqueConstraint("book_id", "dataset_hash", name="uq_eval_dataset_hash"),
        sa.CheckConstraint("version > 0", name="ck_eval_dataset_version_positive"),
        sa.CheckConstraint("case_count >= 0", name="ck_eval_dataset_case_count"),
    )

    op.create_table(
        "evaluation_dataset_cases",
        sa.Column("case_id", sa.String(26), primary_key=True),
        sa.Column("dataset_snapshot_id", sa.String(26), nullable=False),
        sa.Column("role", sa.String(64), nullable=False),
        sa.Column("dimension", sa.String(64), nullable=False),
        sa.Column("base_revision_id", sa.String(26), nullable=False),
        sa.Column("base_revision_hash", sa.String(64), nullable=False),
        sa.Column("proposal_id", sa.String(26), nullable=True),
        sa.Column("proposed_content_hash", sa.String(64), nullable=True),
        sa.Column("human_decision", sa.String(32), nullable=False),
        sa.Column("human_reason", sa.Text(), nullable=False),
        sa.Column("final_revision_id", sa.String(26), nullable=True),
        sa.Column("final_revision_hash", sa.String(64), nullable=True),
        sa.Column("case_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(
            ["dataset_snapshot_id"], ["evaluation_dataset_snapshots.dataset_snapshot_id"]
        ),
        sa.ForeignKeyConstraint(
            ["base_revision_id", "base_revision_hash"],
            ["revisions.revision_id", "revisions.content_hash"],
            name="fk_eval_case_base_revision_hash",
        ),
        sa.ForeignKeyConstraint(["proposal_id"], ["change_proposals.proposal_id"]),
        sa.ForeignKeyConstraint(["final_revision_id"], ["revisions.revision_id"]),
        sa.CheckConstraint(f"dimension IN ({DIMENSIONS})", name="ck_eval_case_dimension"),
        sa.CheckConstraint(
            "human_decision IN ('ACCEPT','REJECT','REQUEST_REVISION','WAIVE')",
            name="ck_eval_case_decision",
        ),
        sa.UniqueConstraint("dataset_snapshot_id", "case_hash", name="uq_eval_case_hash"),
    )

    op.create_table(
        "role_scorecards",
        sa.Column("scorecard_id", sa.String(26), primary_key=True),
        sa.Column("book_id", sa.String(26), nullable=False),
        sa.Column("dataset_snapshot_id", sa.String(26), nullable=False),
        sa.Column("role", sa.String(64), nullable=False),
        sa.Column("config_id", sa.String(128), nullable=False),
        sa.Column("provider", sa.String(64), nullable=True),
        sa.Column("model", sa.String(128), nullable=True),
        sa.Column("config_hash", sa.String(64), nullable=False),
        sa.Column("metrics_json", sa.Text(), nullable=False),
        sa.Column("severe_failure_count", sa.Integer(), nullable=False),
        sa.Column("pass_count", sa.Integer(), nullable=False),
        sa.Column("attention_count", sa.Integer(), nullable=False),
        sa.Column("blocking_count", sa.Integer(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("cost_usd", sa.Float(), nullable=True),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"]),
        sa.ForeignKeyConstraint(
            ["dataset_snapshot_id"], ["evaluation_dataset_snapshots.dataset_snapshot_id"]
        ),
        sa.CheckConstraint("severe_failure_count >= 0", name="ck_scorecard_severe_count"),
        sa.CheckConstraint("pass_count >= 0", name="ck_scorecard_pass_count"),
        sa.CheckConstraint("attention_count >= 0", name="ck_scorecard_attention_count"),
        sa.CheckConstraint("blocking_count >= 0", name="ck_scorecard_blocking_count"),
        sa.CheckConstraint("latency_ms >= 0", name="ck_scorecard_latency"),
    )
    op.create_index(
        "ix_role_scorecards_dataset_role",
        "role_scorecards",
        ["dataset_snapshot_id", "role", "created_at"],
    )

    op.execute("INSERT INTO schema_metadata (version) VALUES ('0008')")

    # Evaluation artifacts are immutable derived evidence. Reruns create new rows.
    for table in (
        "evaluation_snapshots",
        "evaluation_snapshot_targets",
        "evaluation_runs",
        "evaluation_findings",
        "evaluation_metrics",
        "voice_fingerprints",
        "evaluation_dataset_snapshots",
        "evaluation_dataset_cases",
        "role_scorecards",
    ):
        op.execute(
            f"""
            CREATE TRIGGER {table}_no_update
            BEFORE UPDATE ON {table}
            BEGIN
                SELECT RAISE(ABORT, '{table} is immutable; create a new evaluation artifact');
            END
            """
        )
        op.execute(
            f"""
            CREATE TRIGGER {table}_no_delete
            BEFORE DELETE ON {table}
            BEGIN
                SELECT RAISE(ABORT, '{table} is immutable; preserve evaluation history');
            END
            """
        )


def downgrade() -> None:
    for table in (
        "evaluation_snapshots",
        "evaluation_snapshot_targets",
        "evaluation_runs",
        "evaluation_findings",
        "evaluation_metrics",
        "voice_fingerprints",
        "evaluation_dataset_snapshots",
        "evaluation_dataset_cases",
        "role_scorecards",
    ):
        op.execute(f"DROP TRIGGER IF EXISTS {table}_no_delete")
        op.execute(f"DROP TRIGGER IF EXISTS {table}_no_update")

    op.drop_index("ix_role_scorecards_dataset_role", table_name="role_scorecards")
    op.drop_table("role_scorecards")
    op.drop_table("evaluation_dataset_cases")
    op.drop_table("evaluation_dataset_snapshots")
    op.drop_table("voice_fingerprints")
    op.drop_table("evaluation_metrics")
    op.drop_index("ix_evaluation_findings_run", table_name="evaluation_findings")
    op.drop_table("evaluation_findings")
    op.drop_index("ix_evaluation_runs_snapshot", table_name="evaluation_runs")
    op.drop_index("ix_evaluation_runs_book_dimension", table_name="evaluation_runs")
    op.drop_table("evaluation_runs")
    op.drop_index("ix_eval_snapshot_targets_identity", table_name="evaluation_snapshot_targets")
    op.drop_table("evaluation_snapshot_targets")
    op.drop_index("ix_evaluation_snapshots_book_created", table_name="evaluation_snapshots")
    op.drop_table("evaluation_snapshots")
    op.execute("DELETE FROM schema_metadata WHERE version = '0008'")
