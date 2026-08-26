"""Create M5 rebuildable Book Memory persistence.

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-26
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "memory_documents",
        sa.Column("memory_id", sa.String(26), primary_key=True),
        sa.Column("book_id", sa.String(26), nullable=False),
        sa.Column("object_kind", sa.String(32), nullable=False),
        sa.Column("object_id", sa.String(26), nullable=False),
        sa.Column("chapter_id", sa.String(26), nullable=True),
        sa.Column("revision_id", sa.String(26), nullable=False),
        sa.Column("revision_hash", sa.String(64), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("source_status", sa.String(32), nullable=False),
        sa.Column("currentness", sa.String(16), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.Column("indexed_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"]),
        sa.CheckConstraint(
            "object_kind IN ('MANUSCRIPT_UNIT','BOOK_CONTRACT','CHAPTER_CONTRACT','CLAIM')",
            name="ck_memory_object_kind",
        ),
        sa.CheckConstraint("currentness IN ('CURRENT','HISTORY')", name="ck_memory_currentness"),
        sa.UniqueConstraint(
            "book_id",
            "object_kind",
            "object_id",
            "revision_id",
            "content_hash",
            name="uq_memory_document_identity",
        ),
    )
    op.create_index(
        "ix_memory_documents_book_current",
        "memory_documents",
        ["book_id", "currentness", "object_kind"],
    )
    op.create_index(
        "ix_memory_documents_object",
        "memory_documents",
        ["book_id", "object_kind", "object_id"],
    )

    op.execute(
        "CREATE VIRTUAL TABLE memory_fts USING fts5("
        "memory_id UNINDEXED, text, object_kind UNINDEXED, chapter_id UNINDEXED, "
        "tokenize='unicode61')"
    )

    op.create_table(
        "memory_embeddings",
        sa.Column("embedding_id", sa.String(26), primary_key=True),
        sa.Column("memory_id", sa.String(26), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("model", sa.String(128), nullable=False),
        sa.Column("model_version", sa.String(128), nullable=False),
        sa.Column("config_hash", sa.String(64), nullable=False),
        sa.Column("dimension", sa.Integer(), nullable=False),
        sa.Column("vector_blob", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["memory_id"], ["memory_documents.memory_id"]),
        sa.CheckConstraint("dimension > 0", name="ck_memory_embedding_dimension"),
        sa.UniqueConstraint("memory_id", "config_hash", name="uq_memory_embedding_config"),
    )
    op.create_index(
        "ix_memory_embeddings_config",
        "memory_embeddings",
        ["config_hash", "memory_id"],
    )

    op.create_table(
        "memory_index_state",
        sa.Column("book_id", sa.String(26), primary_key=True),
        sa.Column("provider", sa.String(64), nullable=True),
        sa.Column("model", sa.String(128), nullable=True),
        sa.Column("model_version", sa.String(128), nullable=True),
        sa.Column("config_hash", sa.String(64), nullable=True),
        sa.Column("dimension", sa.Integer(), nullable=True),
        sa.Column("document_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["book_projects.book_id"]),
        sa.CheckConstraint(
            "status IN ('EMPTY','LEXICAL_READY','SEMANTIC_READY','FAILED')",
            name="ck_memory_index_status",
        ),
    )

    op.execute("INSERT INTO schema_metadata (version) VALUES ('0006')")


def downgrade() -> None:
    op.drop_table("memory_index_state")
    op.drop_index("ix_memory_embeddings_config", table_name="memory_embeddings")
    op.drop_table("memory_embeddings")
    op.execute("DROP TABLE memory_fts")
    op.drop_index("ix_memory_documents_object", table_name="memory_documents")
    op.drop_index("ix_memory_documents_book_current", table_name="memory_documents")
    op.drop_table("memory_documents")
    op.execute("DELETE FROM schema_metadata WHERE version = '0006'")
