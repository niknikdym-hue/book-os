"""Persist the durable Auto Book complete-cycle runner.

Revision ID: 0021
Revises: 0020
Create Date: 2026-09-13
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0021"
down_revision: str | None = "0020"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "auto_book_authorizations",
        sa.Column("authorization_id", sa.String(26), primary_key=True),
        sa.Column("book_id", sa.String(26), nullable=False),
        sa.Column("run_id", sa.String(26), nullable=False, unique=True),
        sa.Column("scope_json", sa.Text(), nullable=False),
        sa.Column("input_revisions_json", sa.Text(), nullable=False),
        sa.Column("max_total_cost_usd", sa.Float(), nullable=False),
        sa.Column("max_requests", sa.Integer(), nullable=False),
        sa.Column("authorized_by", sa.String(255), nullable=False),
        sa.Column("authorized_by_kind", sa.String(16), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"]),
        sa.CheckConstraint("authorized_by_kind IN ('HUMAN','OWNER')"),
        sa.CheckConstraint("max_total_cost_usd > 0"),
        sa.CheckConstraint("max_requests > 0"),
    )
    op.create_table(
        "auto_book_runtime_runs",
        sa.Column("run_id", sa.String(26), primary_key=True),
        sa.Column("book_id", sa.String(26), nullable=False),
        sa.Column("intent_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("current_stage", sa.String(48), nullable=False),
        sa.Column("stage_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("progress_completed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("progress_total", sa.Integer(), nullable=False),
        sa.Column("estimated_cost_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("reserved_cost_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("confirmed_cost_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("unknown_cost_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("requests_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("worker_id", sa.String(100), nullable=True),
        sa.Column("lease_expires_at", sa.String(32), nullable=True),
        sa.Column("last_message", sa.Text(), nullable=False),
        sa.Column("error_code", sa.String(80), nullable=True),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.Column("updated_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"]),
        sa.CheckConstraint(
            "status IN ('QUEUED','RUNNING','PAUSED','AWAITING_CLARIFICATION',"
            "'BUDGET_REACHED','NEEDS_REVISION','UNKNOWN_OUTCOME','MANUSCRIPT_READY',"
            "'PACKAGE_READY','FAILED')"
        ),
        sa.CheckConstraint("progress_completed >= 0 AND progress_total > 0"),
        sa.CheckConstraint(
            "estimated_cost_usd >= 0 AND reserved_cost_usd >= 0 AND "
            "confirmed_cost_usd >= 0 AND unknown_cost_usd >= 0"
        ),
        sa.CheckConstraint("requests_used >= 0"),
    )
    op.create_table(
        "auto_book_operations",
        sa.Column("operation_id", sa.String(26), primary_key=True),
        sa.Column("run_id", sa.String(26), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("stage", sa.String(48), nullable=False),
        sa.Column("operation", sa.String(80), nullable=False),
        sa.Column("idempotency_key", sa.String(64), nullable=False),
        sa.Column("input_hash", sa.String(64), nullable=False),
        sa.Column("state", sa.String(24), nullable=False),
        sa.Column("provider", sa.String(64), nullable=True),
        sa.Column("model", sa.String(160), nullable=True),
        sa.Column("reasoning_effort", sa.String(16), nullable=True),
        sa.Column("provider_run_id", sa.String(255), nullable=True),
        sa.Column("estimated_cost_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("reserved_cost_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("confirmed_cost_usd", sa.Float(), nullable=True),
        sa.Column("output_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.Column("updated_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["auto_book_runtime_runs.run_id"]),
        sa.UniqueConstraint("run_id", "ordinal"),
        sa.UniqueConstraint("run_id", "idempotency_key"),
        sa.CheckConstraint(
            "state IN ('PENDING','RESERVED','RUNNING','SUCCEEDED','FAILED','UNKNOWN','STALE')"
        ),
    )
    op.create_table(
        "auto_book_output_artifacts",
        sa.Column("artifact_id", sa.String(26), primary_key=True),
        sa.Column("run_id", sa.String(26), nullable=False),
        sa.Column("output_kind", sa.String(48), nullable=False),
        sa.Column("master_hash", sa.String(64), nullable=False),
        sa.Column("profile_version", sa.String(64), nullable=False),
        sa.Column("exporter_version", sa.String(64), nullable=False),
        sa.Column("relative_path", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("byte_length", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("qa_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["auto_book_runtime_runs.run_id"]),
        sa.UniqueConstraint("run_id", "output_kind", "master_hash"),
        sa.CheckConstraint("status IN ('READY','FAILED','STALE')"),
        sa.CheckConstraint("byte_length >= 0"),
    )
    op.create_table(
        "auto_book_visual_assets",
        sa.Column("asset_id", sa.String(26), primary_key=True),
        sa.Column("run_id", sa.String(26), nullable=False),
        sa.Column("kind", sa.String(24), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("placement", sa.Text(), nullable=False),
        sa.Column("data_source", sa.Text(), nullable=True),
        sa.Column("caption", sa.Text(), nullable=False),
        sa.Column("origin", sa.String(32), nullable=False),
        sa.Column("rights_note", sa.Text(), nullable=False),
        sa.Column("alt_text", sa.Text(), nullable=False),
        sa.Column("audio_equivalent", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["auto_book_runtime_runs.run_id"]),
        sa.CheckConstraint("kind IN ('TABLE','CHART','SCHEME','ILLUSTRATION')"),
        sa.CheckConstraint("origin IN ('PROGRAMMATIC','GENERATIVE','OWNER_SUPPLIED')"),
    )
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
    op.execute("INSERT INTO schema_metadata (version) VALUES ('0021')")


def downgrade() -> None:
    op.drop_table("auto_book_change_requests")
    op.drop_table("auto_book_visual_assets")
    op.drop_table("auto_book_output_artifacts")
    op.drop_table("auto_book_operations")
    op.drop_table("auto_book_runtime_runs")
    op.drop_table("auto_book_authorizations")
    op.execute("DELETE FROM schema_metadata WHERE version='0021'")
