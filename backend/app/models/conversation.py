from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    TIMESTAMP,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class AIProviderType(str, enum.Enum):
    CLAUDE = "claude"
    OPENAI = "openai"
    GEMINI = "gemini"
    DEEPSEEK = "deepseek"
    GROQ = "groq"
    OPENROUTER = "openrouter"


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ai_provider: Mapped[AIProviderType | None] = mapped_column(
        Enum(AIProviderType, name="ai_provider_type", create_constraint=True, values_callable=lambda x: x.value if isinstance(x, enum.Enum) else x),
        nullable=True,
    )
    model_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="conversations")

    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan",
        order_by="Message.created_at",
    )

    __table_args__ = (
        Index("idx_conversations_user_id", "user_id"),
        Index("idx_conversations_created_at", "created_at", postgresql_using="btree"),
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[MessageRole] = mapped_column(
        Enum(MessageRole, name="message_role", create_constraint=True, values_callable=lambda x: x.value if isinstance(x, enum.Enum) else x),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hi: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_te: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_provider: Mapped[AIProviderType | None] = mapped_column(
        Enum(AIProviderType, name="ai_provider_type", create_constraint=True, values_callable=lambda x: x.value if isinstance(x, enum.Enum) else x),
        nullable=True,
    )
    model_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(
        Numeric(4, 3), nullable=True
    )
    citations: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    is_partial: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    feedback_score: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    conversation: Mapped[Conversation] = relationship("Conversation", back_populates="messages")

    __table_args__ = (
        CheckConstraint(
            "confidence_score BETWEEN 0 AND 1", name="messages_confidence_score_check"
        ),
        CheckConstraint(
            "feedback_score BETWEEN 1 AND 5", name="messages_feedback_score_check"
        ),
        Index("idx_messages_conversation", "conversation_id"),
        Index("idx_messages_role", "role"),
        Index("idx_messages_created_at", "created_at"),
    )
