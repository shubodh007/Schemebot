from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    id: UUID
    original_filename: str
    mime_type: str
    file_size_bytes: int
    document_type: str
    status: str
    page_count: Optional[int] = None
    ocr_confidence: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentDetail(DocumentResponse):
    extracted_fields: dict = {}
    extracted_text: Optional[str] = None
    scheme_matches: list[dict] = []
    error_message: Optional[str] = None
    processing_started: Optional[datetime] = None
    processing_finished: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int


class SchemeMatchResult(BaseModel):
    scheme_id: UUID
    scheme_title: str
    match_confidence: float = Field(..., ge=0, le=1)
    matched_fields: list[str]


class DocumentAnalysis(BaseModel):
    document_id: UUID
    document_type: str
    extracted_fields: dict
    ocr_confidence: Optional[float] = None
    scheme_matches: list[SchemeMatchResult] = []


class ErrorResponse(BaseModel):
    code: str
    detail: str
    errors: Optional[list[dict]] = None
    metadata: Optional[dict] = None


class SearchResult(BaseModel):
    id: UUID
    title: str
    title_hi: Optional[str] = None
    title_te: Optional[str] = None
    description: str
    type: str  # 'scheme', 'document', 'legal'
    score: float
    url: Optional[str] = None
    metadata: dict = {}


class SearchResponse(BaseModel):
    results: list[SearchResult]
    suggestions: list[str]
    elapsed_ms: int
    total: int
