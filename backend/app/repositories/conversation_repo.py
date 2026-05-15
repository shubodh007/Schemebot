from __future__ import annotations

import uuid
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.conversation import Conversation, Message
from app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Conversation, session)

    async def get_user_conversations(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
        include_archived: bool = False,
    ) -> Tuple[List[Conversation], int]:
        conditions = [Conversation.user_id == user_id]
        if not include_archived:
            conditions.append(Conversation.is_archived == False)
        return await self.get_many(
            *conditions,
            skip=skip,
            limit=limit,
            sort_by="updated_at",
            sort_desc=True,
        )

    async def get_conversation_with_messages(
        self,
        conversation_id: UUID,
        user_id: UUID,
    ) -> Optional[Conversation]:
        stmt = (
            select(Conversation)
            .options(joinedload(Conversation.messages))
            .where(
                and_(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user_id,
                )
            )
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def update_message_count(
        self, conversation_id: UUID
    ) -> None:
        count_stmt = (
            select(func.count())
            .select_from(Message)
            .where(Message.conversation_id == conversation_id)
        )
        count_result = await self.session.execute(count_stmt)
        count = count_result.scalar() or 0

        conv = await self.get_by_id_or_fail(conversation_id)
        conv.message_count = count
        await self.session.flush()


class MessageRepository(BaseRepository[Message]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Message, session)

    async def get_conversation_messages(
        self,
        conversation_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Message]:
        stmt = (
            select(Message)
            .where(
                and_(
                    Message.conversation_id == conversation_id,
                    Message.is_partial == False,
                )
            )
            .order_by(Message.created_at)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_recent_messages(
        self,
        conversation_id: UUID,
        count: int = 10,
    ) -> List[Message]:
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(count)
        )
        result = await self.session.execute(stmt)
        messages = list(result.scalars().all())
        messages.reverse()
        return messages

    async def add_feedback(
        self,
        message_id: UUID,
        score: int,
        comment: Optional[str] = None,
    ) -> Optional[Message]:
        msg = await self.get_by_id(message_id)
        if msg is None:
            return None
        msg.feedback_score = score
        await self.session.flush()
        return msg
