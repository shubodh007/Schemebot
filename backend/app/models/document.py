from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    TIMESTAMP,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.scheme import Scheme  # noqa: F401 — relationship reference

try:
    from sqlalchemy import types
    from pgvector.sqlalchemy import Vector
    _has_pgvector = True
except ImportError:
    Vector = None  # type: ignore
    _has_pgvector = False
class DocumentType(str, enum.Enum):
    AADHAAR = "aadhaar"
    PAN = "pan"
    VOTER_ID = "voter_id"
    RATION_CARD = "ration_card"
    INCOME_CERT = "income_cert"
    CASTE_CERT = "caste_cert"
    DISABILITY_CERT = "disability_cert"
    BANK_STATEMENT = "bank_statement"
    OTHER = "other"


class DocumentStatus(str, enum.Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    DELETED = "deleted"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    original_filename: Mapped[str] = mapped_column(Text, nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str] = mapped_column(Text, nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, name="document_type", create_constraint=True, values_callable=lambda x: x.value if isinstance(x, enum.Enum) else x),
        default=DocumentType.OTHER,
        nullable=False,
    )
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status", create_constraint=True, values_callable=lambda x: x.value if isinstance(x, enum.Enum) else x),
        default=DocumentStatus.UPLOADING,
        nullable=False,
    )
    ocr_confidence: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_fields: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    scheme_matches: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_started: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    processing_finished: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    chunks: Mapped[list["DocumentChunk"]] = relationship(
        "DocumentChunk", back_populates="document", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("file_size_bytes > 0", name="documents_file_size_positive"),
        CheckConstraint(
            "ocr_confidence BETWEEN 0 AND 1", name="documents_ocr_confidence_check"
        ),
        Index("idx_documents_user_id", "user_id"),
        Index("idx_documents_status", "status"),
        Index("idx_documents_type", "document_type"),
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    scheme_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schemes.id", ondelete="SET NULL"), nullable=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_metadata: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding: Mapped[Optional[list[float]]] = mapped_column(
        Vector(768) if _has_pgvector else JSONB, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    document: Mapped[Document] = relationship("Document", back_populates="chunks")

    __table_args__ = (
        Index("idx_chunks_document", "document_id"),
        Index("idx_chunks_scheme", "scheme_id"),
    )


class SavedScheme(Base):
    __tablename__ = "saved_schemes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    scheme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reminder_date: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    scheme: Mapped["Scheme"] = relationship("Scheme", lazy="joined")

    __table_args__ = (
        CheckConstraint(
            "scheme_id IS NOT NULL AND user_id IS NOT NULL",
            name="saved_schemes_valid_refs",
        ),
        Index("idx_saved_user_id", "user_id"),
        Index("idx_saved_scheme_id", "scheme_id"),
    )
