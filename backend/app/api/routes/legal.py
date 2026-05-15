from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.middleware.auth_middleware import current_user
from app.core.database import get_session
from app.models.legal import LegalQuery
from app.models.user import User

router = APIRouter(prefix="/legal", tags=["legal"])


@router.post("/query")
async def submit_legal_query(
    body: dict,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    import json
    from app.ai.providers.base import Message
    from app.ai.providers.factory import ProviderFactory
    from app.core.logging import logger

    provider = await ProviderFactory.get_provider_for_use_case("legal")
    result = await provider.complete(
        messages=[Message(role="user", content=body.get("query", ""))],
        system="""You are the GovScheme Legal Guidance Agent.

CRITICAL: You provide LEGAL INFORMATION, not legal advice. Begin every response with this disclaimer.
Cite every legal claim with specific Act and Section references.
If the query involves criminal matters, property disputes over Rs. 10L, or family court — recommend professional help.
Explain legal concepts simply. Use examples.""",
    )

    legal_query = LegalQuery(
        user_id=user.id,
        conversation_id=UUID(body["conversation_id"]) if body.get("conversation_id") else None,
        query_text=body.get("query", ""),
        query_type=body.get("query_type", "general"),
        response_text=result.content,
    )
    session.add(legal_query)
    await session.flush()

    return {"response": result.content, "query_id": str(legal_query.id)}
