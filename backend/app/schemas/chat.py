from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ConversationSummary(BaseModel):
    id: UUID
    title: Optional[str] = None
    summary: Optional[str] = None
    message_count: int
    ai_provider: Optional[str] = None
    model_name: Optional[str] = None
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationSession(BaseModel):
    id: UUID
    title: Optional[str] = None
    messages: list["MessageResponse"] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CreateConversationRequest(BaseModel):
    provider: Optional[str] = None


class MessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=50000)
    language: Optional[str] = "en"


class Citation(BaseModel):
    scheme_id: Optional[UUID] = None
    document_id: Optional[UUID] = None
    chunk_id: Optional[UUID] = None
    title: Optional[str] = None
    relevance: Optional[float] = None
    source_url: Optional[str] = None


class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    content_hi: Optional[str] = None
    content_te: Optional[str] = None
    ai_provider: Optional[str] = None
    model_name: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    latency_ms: Optional[int] = None
    confidence_score: Optional[float] = None
    citations: list[Citation] = []
    is_partial: bool
    feedback_score: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class FeedbackRequest(BaseModel):
    score: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class ConversationListResponse(BaseModel):
    sessions: list[ConversationSummary]
    total: int
