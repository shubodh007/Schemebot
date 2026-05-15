"""Add composite indexes for query performance + analytics partitioning

Revision ID: 0003
Revises: 0002
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_schemes_category_status
        ON schemes(category_id, status)
        WHERE status = 'active'
    """)
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_schemes_level_state
        ON schemes(level, state_code)
        WHERE status = 'active'
    """)
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_conversation_created
        ON messages(conversation_id, created_at)
    """)
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analytics_event_type_created
        ON analytics_events(event_type, created_at DESC)
    """)
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_user_status
        ON documents(user_id, status)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_schemes_category_status")
    op.execute("DROP INDEX IF EXISTS idx_schemes_level_state")
    op.execute("DROP INDEX IF EXISTS idx_messages_conversation_created")
    op.execute("DROP INDEX IF EXISTS idx_analytics_event_type_created")
    op.execute("DROP INDEX IF EXISTS idx_documents_user_status")
