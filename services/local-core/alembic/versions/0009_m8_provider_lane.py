"""Add M8 provider-lane evidence tables.

Revision ID: 0009
Revises: 0008
"""

from alembic import op
import sqlalchemy as sa

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("provider_capabilities", sa.Column("capability_id", sa.String(26), primary_key=True), sa.Column("provider", sa.String(64), nullable=False), sa.Column("model", sa.String(128), nullable=False), sa.Column("config_id", sa.String(128), nullable=False), sa.Column("matrix_version", sa.String(64), nullable=False), sa.Column("matrix_hash", sa.String(64), nullable=False), sa.Column("region", sa.String(16), nullable=False), sa.Column("policy_json", sa.Text(), nullable=False), sa.Column("capabilities_json", sa.Text(), nullable=False), sa.Column("privacy_json", sa.Text(), nullable=False), sa.Column("sources_json", sa.Text(), nullable=False), sa.Column("verified_at", sa.String(32), nullable=False), sa.Column("health_state", sa.String(32), nullable=False), sa.Column("cost_json", sa.Text(), nullable=False), sa.Column("current_state", sa.String(32), nullable=False), sa.Column("superseded_at", sa.String(32)))
    op.create_index("ix_provider_capability_identity", "provider_capabilities", ["provider", "model", "config_id", "region", "matrix_version"])
    op.create_table("provider_probe_runs", sa.Column("probe_id", sa.String(26), primary_key=True), sa.Column("provider", sa.String(64), nullable=False), sa.Column("model", sa.String(128), nullable=False), sa.Column("config_id", sa.String(128), nullable=False), sa.Column("matrix_hash", sa.String(64), nullable=False), sa.Column("probe_type", sa.String(8), nullable=False), sa.Column("region", sa.String(16), nullable=False), sa.Column("capability", sa.String(64), nullable=False), sa.Column("latency_ms", sa.Integer(), nullable=True), sa.Column("usage_json", sa.Text(), nullable=False), sa.Column("cost_json", sa.Text(), nullable=False), sa.Column("outcome", sa.String(32), nullable=False), sa.Column("external_request_id", sa.String(256)), sa.Column("created_at", sa.String(32), nullable=False), sa.CheckConstraint("probe_type IN ('MOCK','LIVE')", name="ck_provider_probe_type"))
    op.create_table("provider_role_promotions", sa.Column("promotion_id", sa.String(26), primary_key=True), sa.Column("provider", sa.String(64), nullable=False), sa.Column("model", sa.String(128), nullable=False), sa.Column("config_id", sa.String(128), nullable=False), sa.Column("region", sa.String(16), nullable=False), sa.Column("role", sa.String(64), nullable=False), sa.Column("dataset_snapshot_id", sa.String(26), nullable=True), sa.Column("dataset_hash", sa.String(64), nullable=False), sa.Column("scorecard_ref", sa.String(256), nullable=False), sa.Column("decision", sa.String(16), nullable=False), sa.Column("reason", sa.Text(), nullable=False), sa.Column("independence_state", sa.String(32), nullable=False), sa.Column("matrix_hash", sa.String(64), nullable=False), sa.Column("actor", sa.String(128), nullable=False), sa.Column("created_at", sa.String(32), nullable=False), sa.Column("superseded_at", sa.String(32)), sa.CheckConstraint("decision IN ('PROMOTED','REJECTED','EXPIRED')", name="ck_provider_promotion_decision"))
    op.execute("INSERT INTO schema_metadata (version) VALUES ('0009')")


def downgrade() -> None:
    op.drop_table("provider_role_promotions")
    op.drop_table("provider_probe_runs")
    op.drop_index("ix_provider_capability_identity", table_name="provider_capabilities")
    op.drop_table("provider_capabilities")
