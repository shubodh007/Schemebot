from __future__ import annotations

import json
import uuid as uuid_pkg
from typing import AsyncGenerator, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from app.ai.agents.orchestrator import OrchestratorAgent
from app.ai.memory import ConversationMemory
from app.ai.providers.base import Message as AIMessage
from app.ai.rag.pipeline import RAGPipeline
from app.api.middleware.auth_middleware import current_user
from app.core.database import get_session
from app.core.logging import logger
from app.models.user import User
from app.repositories.conversation_repo import ConversationRepository, MessageRepository
from app.repositories.user_repo import ProfileRepository
from app.schemas.chat import (
    ConversationListResponse,
    ConversationSummary,
    CreateConversationRequest,
    FeedbackRequest,
    MessageRequest,
    MessageResponse,
)
from app.schemas.chat import ConversationSession

router = APIRouter(prefix="/chat", tags=["chat"])

rag = RAGPipeline()
orchestrator = OrchestratorAgent(rag_pipeline=rag)
memory = ConversationMemory()


@router.get("/sessions")
async def list_sessions(
    page: int = 1,
    limit: int = 20,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    repo = ConversationRepository(session)
    skip = (page - 1) * limit
    conversations, total = await repo.get_user_conversations(
        user_id=user.id,
        skip=skip,
        limit=limit,
    )
    return ConversationListResponse(
        sessions=[ConversationSummary.model_validate(c) for c in conversations],
        total=total,
    )


@router.post("/sessions", status_code=201)
async def create_session(
    body: CreateConversationRequest,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    repo = ConversationRepository(session)
    conv = await repo.create(
        user_id=user.id,
        title="New conversation",
        ai_provider=body.provider or "openrouter",
    )
    return {"session": ConversationSummary.model_validate(conv)}


@router.get("/sessions/{session_id}")
async def get_conversation(
    session_id: UUID,
    user: User = Depends(current_user),
    db_session: AsyncSession = Depends(get_session),
):
    repo = ConversationRepository(db_session)
    conv = await repo.get_conversation_with_messages(session_id, user.id)
    if conv is None:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Conversation not found")
    return {"session": ConversationSession.model_validate(conv)}


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: UUID,
    user: User = Depends(current_user),
    db_session: AsyncSession = Depends(get_session),
):
    repo = ConversationRepository(db_session)
    conv = await repo.get_by_id(session_id)
    if conv is None or str(conv.user_id) != str(user.id):
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Conversation not found")
    await repo.delete(session_id)
    return None


@router.post("/sessions/{session_id}/messages")
async def stream_message(
    session_id: UUID,
    body: MessageRequest,
    request: Request,
    user: User = Depends(current_user),
    db_session: AsyncSession = Depends(get_session),
):
    conv_repo = ConversationRepository(db_session)
    msg_repo = MessageRepository(db_session)
    profile_repo = ProfileRepository(db_session)

    conv = await conv_repo.get_by_id(session_id)
    if conv is None or str(conv.user_id) != str(user.id):
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Conversation not found")

    await msg_repo.create(
        conversation_id=session_id,
        role="user",
        content=body.content,
    )
    await conv_repo.update_message_count(session_id)

    recent_messages = await msg_repo.get_recent_messages(session_id, 20)
    ai_history = [AIMessage(role=m.role, content=m.content) for m in recent_messages]

    profile = await profile_repo.get_by_user_id(user.id)
    user_context = {}
    if profile:
        user_context = {
            "state_code": profile.state_code,
            "caste_category": profile.caste_category.value if profile.caste_category else None,
            "annual_income": float(profile.annual_income) if profile.annual_income else None,
            "gender": profile.gender.value if profile.gender else None,
        }

    async def generate() -> AsyncGenerator[str, None]:
        yield f"data: {json.dumps({'status': 'processing'})}\n\n"

        collected_tokens: list[str] = []

        async for chunk in orchestrator.stream(
            user_message=body.content,
            conversation_id=session_id,
            user_id=user.id,
            language=body.language or "en",
            user_profile=user_context,
            conversation_history=ai_history,
        ):
            if chunk.token:
                collected_tokens.append(chunk.token)
                yield f"data: {json.dumps({'token': chunk.token})}\n\n"
            if chunk.finish_reason == "citations" and chunk.usage:
                citations = chunk.usage.get("citations", [])
                yield f"data: {json.dumps({'citations': citations})}\n\n"
            if chunk.finish_reason == "stop":
                break

        full_response = "".join(collected_tokens)
        new_msg = await msg_repo.create(
            conversation_id=session_id,
            role="assistant",
            content=full_response,
            ai_provider="openrouter",
        )
        await conv_repo.update_message_count(session_id)

        yield f"data: {json.dumps({'done': True, 'message_id': str(new_msg.id)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("/messages/{message_id}/feedback")
async def add_feedback(
    message_id: UUID,
    body: FeedbackRequest,
    user: User = Depends(current_user),
    db_session: AsyncSession = Depends(get_session),
):
    msg_repo = MessageRepository(db_session)
    updated = await msg_repo.add_feedback(
        message_id=message_id,
        score=body.score,
        comment=body.comment,
    )
    if updated is None:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Message not found")
    return {"detail": "Feedback recorded"}
