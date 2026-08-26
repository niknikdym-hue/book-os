"""Create M4 Research Engine and Claim Ledger persistence.

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-25
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

CLAIM_STATES = "'UNREVIEWED','SUPPORTED','PARTIALLY_SUPPORTED','DISPUTED','UNSUPPORTED','REJECTED'"


def upgrade() -> None:
    op.create_table(
        "claims",
        sa.Column("claim_id", sa.String(26), primary_key=True),
        sa.Column("book_id", sa.String(26), nullable=False),
        sa.Column("chapter_id", sa.String(26), nullable=False),
        sa.Column("unit_id", sa.String(26), nullable=False),
        sa.Column("manuscript_revision_id", sa.String(26), nullable=False),
        sa.Column("manuscript_revision_hash", sa.String(64), nullable=False),
        sa.Column("normalized_text", sa.Text(), nullable=False),
        sa.Column("claim_type", sa.String(32), nullable=False),
        sa.Column("materiality", sa.String(16), nullable=False),
        sa.Column("required_evidence_level", sa.String(128), nullable=False),
        sa.Column("verification_state", sa.String(32), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.Column("updated_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"]),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.chapter_id"]),
        sa.ForeignKeyConstraint(["unit_id"], ["manuscript_units.unit_id"]),
        sa.ForeignKeyConstraint(
            ["manuscript_revision_id", "manuscript_revision_hash"],
            ["revisions.revision_id", "revisions.content_hash"],
            name="fk_claim_manuscript_revision_hash",
        ),
        sa.CheckConstraint(
            "claim_type IN ('QUANTITATIVE','EMPIRICAL','CAUSAL','HISTORICAL','ATTRIBUTION',"
            "'CASE_ASSERTION','LEGAL_REGULATORY','CONSENSUS','INTERPRETIVE','AUTHORIAL')",
            name="ck_claim_type",
        ),
        sa.CheckConstraint(
            "materiality IN ('LOW','MEDIUM','HIGH','CRITICAL')", name="ck_claim_materiality"
        ),
        sa.CheckConstraint(
            f"verification_state IN ({CLAIM_STATES})", name="ck_claim_verification_state"
        ),
    )
    op.create_index("ix_claims_book_chapter", "claims", ["book_id", "chapter_id"])
    op.create_index("ix_claims_unit", "claims", ["unit_id", "manuscript_revision_id"])
    op.create_index("ix_claims_state", "claims", ["book_id", "verification_state"])

    op.create_table(
        "claim_state_history",
        sa.Column("state_event_id", sa.String(26), primary_key=True),
        sa.Column("claim_id", sa.String(26), nullable=False),
        sa.Column("prior_state", sa.String(32), nullable=True),
        sa.Column("new_state", sa.String(32), nullable=False),
        sa.Column("actor", sa.String(128), nullable=False),
        sa.Column("actor_kind", sa.String(16), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["claim_id"], ["claims.claim_id"]),
        sa.CheckConstraint(
            f"prior_state IS NULL OR prior_state IN ({CLAIM_STATES})", name="ck_claim_history_prior"
        ),
        sa.CheckConstraint(f"new_state IN ({CLAIM_STATES})", name="ck_claim_history_new"),
        sa.CheckConstraint("actor_kind IN ('HUMAN','SYSTEM')", name="ck_claim_history_actor_kind"),
    )
    op.create_index(
        "ix_claim_state_history_claim_created",
        "claim_state_history",
        ["claim_id", "created_at"],
    )

    op.create_table(
        "sources",
        sa.Column("source_id", sa.String(26), primary_key=True),
        sa.Column("canonical_key", sa.String(512), nullable=False, unique=True),
        sa.Column("source_type", sa.String(64), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("authors_json", sa.Text(), nullable=False),
        sa.Column("organization", sa.Text(), nullable=True),
        sa.Column("publication_date", sa.String(32), nullable=True),
        sa.Column("publication_year", sa.Integer(), nullable=True),
        sa.Column("doi", sa.String(512), nullable=True, unique=True),
        sa.Column("canonical_url", sa.Text(), nullable=True),
        sa.Column("container_title", sa.Text(), nullable=True),
        sa.Column("abstract", sa.Text(), nullable=True),
        sa.Column("citation_count", sa.Integer(), nullable=True),
        sa.Column("primary_secondary", sa.String(16), nullable=False),
        sa.Column("reliability_json", sa.Text(), nullable=False),
        sa.Column("access_status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.Column("updated_at", sa.String(32), nullable=False),
        sa.CheckConstraint(
            "primary_secondary IN ('PRIMARY','SECONDARY','UNCLASSIFIED')",
            name="ck_source_primary_secondary",
        ),
        sa.CheckConstraint(
            "access_status IN ('METADATA_ONLY','ABSTRACT_AVAILABLE','FULL_SOURCE_INSPECTED')",
            name="ck_source_access_status",
        ),
    )

    op.create_table(
        "source_access_history",
        sa.Column("access_event_id", sa.String(26), primary_key=True),
        sa.Column("source_id", sa.String(26), nullable=False),
        sa.Column("access_status", sa.String(32), nullable=False),
        sa.Column("actor", sa.String(128), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["sources.source_id"]),
        sa.CheckConstraint(
            "access_status IN ('METADATA_ONLY','ABSTRACT_AVAILABLE','FULL_SOURCE_INSPECTED')",
            name="ck_source_access_history_status",
        ),
    )
    op.create_index(
        "ix_source_access_history_source_created",
        "source_access_history",
        ["source_id", "created_at"],
    )

    op.create_table(
        "source_identifiers",
        sa.Column("source_id", sa.String(26), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("external_id", sa.String(512), nullable=False),
        sa.Column("provider_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.PrimaryKeyConstraint("source_id", "provider", "external_id"),
        sa.UniqueConstraint("provider", "external_id", name="uq_source_provider_external"),
        sa.ForeignKeyConstraint(["source_id"], ["sources.source_id"]),
    )

    op.create_table(
        "evidence",
        sa.Column("evidence_id", sa.String(26), primary_key=True),
        sa.Column("claim_id", sa.String(26), nullable=False),
        sa.Column("source_id", sa.String(26), nullable=False),
        sa.Column("relationship", sa.String(32), nullable=False),
        sa.Column("pointer", sa.Text(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("strength", sa.String(16), nullable=False),
        sa.Column("limitations", sa.Text(), nullable=False),
        sa.Column("actor", sa.String(128), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("supersedes_evidence_id", sa.String(26), nullable=True),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["claim_id"], ["claims.claim_id"]),
        sa.ForeignKeyConstraint(["source_id"], ["sources.source_id"]),
        sa.ForeignKeyConstraint(["supersedes_evidence_id"], ["evidence.evidence_id"]),
        sa.CheckConstraint(
            "relationship IN ('SUPPORTS','PARTIALLY_SUPPORTS','CONTRADICTS','CONTEXT_ONLY')",
            name="ck_evidence_relationship",
        ),
        sa.CheckConstraint("strength IN ('WEAK','MODERATE','STRONG')", name="ck_evidence_strength"),
        sa.CheckConstraint("status IN ('ACTIVE','SUPERSEDED')", name="ck_evidence_status"),
        sa.CheckConstraint("length(trim(pointer)) > 0", name="ck_evidence_pointer_nonblank"),
    )
    op.create_index("ix_evidence_claim", "evidence", ["claim_id", "status"])
    op.create_index("ix_evidence_source", "evidence", ["source_id"])

    op.execute("INSERT INTO schema_metadata (version) VALUES ('0005')")


def downgrade() -> None:
    op.drop_index("ix_evidence_source", table_name="evidence")
    op.drop_index("ix_evidence_claim", table_name="evidence")
    op.drop_table("evidence")
    op.drop_table("source_identifiers")
    op.drop_index("ix_source_access_history_source_created", table_name="source_access_history")
    op.drop_table("source_access_history")
    op.drop_table("sources")
    op.drop_index("ix_claim_state_history_claim_created", table_name="claim_state_history")
    op.drop_table("claim_state_history")
    op.drop_index("ix_claims_state", table_name="claims")
    op.drop_index("ix_claims_unit", table_name="claims")
    op.drop_index("ix_claims_book_chapter", table_name="claims")
    op.drop_table("claims")
    op.execute("DELETE FROM schema_metadata WHERE version = '0005'")
