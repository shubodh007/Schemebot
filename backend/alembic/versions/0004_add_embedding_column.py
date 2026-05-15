"""Add embedding column to document_chunks + HNSW index

Revision ID: 0004
Revises: 0003
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("document_chunks", sa.Column("embedding", Vector(768), nullable=True))
    op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chunks_embedding ON document_chunks USING hnsw (embedding vector_cosine_ops)")


def downgrade() -> None:
    op.drop_index("idx_chunks_embedding", table_name="document_chunks", if_exists=True)
    op.drop_column("document_chunks", "embedding")
