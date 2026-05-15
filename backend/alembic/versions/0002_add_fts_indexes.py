"""Add full-text search indexes

Revision ID: 0002
Revises: 0001
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_schemes_fts
        ON schemes USING gin(
            to_tsvector('english', coalesce(title, '') || ' ' || coalesce(description, '') || ' ' || coalesce(title_hi, '') || ' ' || coalesce(title_te, ''))
        )
    """)
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_fts
        ON document_chunks USING gin(
            to_tsvector('english', content)
        )
    """)
    op.execute("""
        ALTER TABLE schemes ADD COLUMN IF NOT EXISTS fts_vector tsvector
        GENERATED ALWAYS AS (
            to_tsvector('english', coalesce(title, '') || ' ' || coalesce(description, ''))
        ) STORED
    """)
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_schemes_fts_vector
        ON schemes USING gin(fts_vector)
    """)
    op.execute("DROP INDEX IF EXISTS idx_users_email")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_schemes_fts")
    op.execute("DROP INDEX IF EXISTS idx_documents_fts")
    op.execute("DROP INDEX IF EXISTS idx_schemes_fts_vector")
    op.execute("ALTER TABLE schemes DROP COLUMN IF EXISTS fts_vector")
