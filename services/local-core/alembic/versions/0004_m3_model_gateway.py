"""Create M3 bounded model-run and first manuscript-unit persistence.

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-25
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "bounded_tasks",
        sa.Column("task_id", sa.String(26), primary_key=True),
        sa.Column("book_id", sa.String(26), nullable=False),
        sa.Column("chapter_id", sa.String(26), nullable=False),
        sa.Column("task_type", sa.String(64), nullable=False),
        sa.Column("role", sa.String(64), nullable=False),
        sa.Column("input_revision_id", sa.String(26), nullable=False),
        sa.Column("input_revision_hash", sa.String(64), nullable=False),
        sa.Column("prompt_id", sa.String(128), nullable=False),
        sa.Column("prompt_version", sa.String(32), nullable=False),
        sa.Column("prompt_hash", sa.String(64), nullable=False),
        sa.Column("section_objective", sa.Text(), nullable=False),
        sa.Column("untrusted_context_json", sa.Text(), nullable=False),
        sa.Column("max_output_tokens", sa.Integer(), nullable=False),
        sa.Column("max_cost_usd", sa.Float(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("output_unit_id", sa.String(26), nullable=True),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.Column("started_at", sa.String(32), nullable=True),
        sa.Column("completed_at", sa.String(32), nullable=True),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"]),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.chapter_id"]),
        sa.ForeignKeyConstraint(
            ["input_revision_id", "input_revision_hash"],
            ["revisions.revision_id", "revisions.content_hash"],
            name="fk_bounded_task_input_revision_hash",
        ),
        sa.CheckConstraint(
            "status IN ('QUEUED','RUNNING','SUCCEEDED','FAILED')", name="ck_bounded_task_status"
        ),
    )
    op.create_index("ix_bounded_tasks_book_chapter", "bounded_tasks", ["book_id", "chapter_id"])

    op.create_table(
        "model_runs",
        sa.Column("run_id", sa.String(26), primary_key=True),
        sa.Column("task_id", sa.String(26), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("model", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("provider_run_id", sa.String(255), nullable=True),
        sa.Column("prompt_id", sa.String(128), nullable=False),
        sa.Column("prompt_version", sa.String(32), nullable=False),
        sa.Column("prompt_hash", sa.String(64), nullable=False),
        sa.Column("usage_json", sa.Text(), nullable=False),
        sa.Column("error_code", sa.String(128), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.Column("completed_at", sa.String(32), nullable=True),
        sa.ForeignKeyConstraint(["task_id"], ["bounded_tasks.task_id"]),
        sa.CheckConstraint(
            "status IN ('RUNNING','SUCCEEDED','FAILED')", name="ck_model_run_status"
        ),
    )
    op.create_index("ix_model_runs_task", "model_runs", ["task_id", "created_at"])

    op.create_table(
        "manuscript_units",
        sa.Column("unit_id", sa.String(26), primary_key=True),
        sa.Column("book_id", sa.String(26), nullable=False),
        sa.Column("chapter_id", sa.String(26), nullable=False),
        sa.Column("unit_type", sa.String(32), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("authority_entity_id", sa.String(26), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.Column("updated_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"]),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.chapter_id"]),
        sa.ForeignKeyConstraint(["authority_entity_id"], ["authority_entities.entity_id"]),
    )
    op.create_index(
        "ix_manuscript_units_chapter_order", "manuscript_units", ["chapter_id", "ordinal"]
    )

    op.execute("INSERT INTO schema_metadata (version) VALUES ('0004')")


def downgrade() -> None:
    op.drop_index("ix_manuscript_units_chapter_order", table_name="manuscript_units")
    op.drop_table("manuscript_units")
    op.drop_index("ix_model_runs_task", table_name="model_runs")
    op.drop_table("model_runs")
    op.drop_index("ix_bounded_tasks_book_chapter", table_name="bounded_tasks")
    op.drop_table("bounded_tasks")
    op.execute("DELETE FROM schema_metadata WHERE version = '0004'")
