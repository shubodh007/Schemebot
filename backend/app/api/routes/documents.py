from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.middleware.auth_middleware import current_user
from app.core.database import get_session
from app.core.logging import logger
from app.models.user import User
from app.repositories.conversation_repo import ConversationRepository
from app.schemas.document import (
    DocumentDetail,
    DocumentListResponse,
    DocumentResponse,
)
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    document_type: Optional[str] = Form(None),
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    content = await file.read()
    service = DocumentService(session)
    doc = await service.validate_and_upload(
        user_id=user.id,
        file_content=content,
        filename=file.filename or "document",
        mime_type=file.content_type or "application/octet-stream",
    )

    if doc.status == "failed":
        from app.core.exceptions import FileValidationError
        raise FileValidationError(doc.error_message or "Document processing failed")

    return {"document": DocumentResponse.model_validate(doc)}


@router.get("")
async def list_documents(
    page: int = 1,
    limit: int = 20,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    from app.repositories.conversation_repo import MessageRepository
    from app.models.document import Document
    from sqlalchemy import select, func

    count_stmt = select(func.count()).select_from(Document).where(Document.user_id == user.id)
    count_result = await session.execute(count_stmt)
    total = count_result.scalar() or 0

    list_stmt = (
        select(Document)
        .where(Document.user_id == user.id)
        .order_by(Document.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    result = await session.execute(list_stmt)
    docs = list(result.scalars().all())

    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(d) for d in docs],
        total=total,
    )


@router.get("/{document_id}")
async def get_document(
    document_id: UUID,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    from app.models.document import Document
    from sqlalchemy import select

    stmt = select(Document).where(
        Document.id == document_id,
        Document.user_id == user.id,
    )
    result = await session.execute(stmt)
    doc = result.scalar_one_or_none()

    if doc is None:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Document not found")

    return {"document": DocumentDetail.model_validate(doc)}


@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    from app.models.document import Document
    from app.core.exceptions import NotFoundError

    doc = await session.get(Document, document_id)
    if doc is None or str(doc.user_id) != str(user.id):
        raise NotFoundError("Document not found")

    from app.core.supabase_client import supabase_storage
    try:
        await supabase_storage.delete(doc.storage_key)
    except Exception as exc:
        logger.warning("document.storage_delete_failed", key=doc.storage_key, error=str(exc))

    from app.repositories.conversation_repo import MessageRepository
    await session.delete(doc)
    await session.flush()
    return None
