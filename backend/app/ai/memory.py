from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from app.ai.providers.base import Message
from app.ai.providers.factory import ProviderFactory
from app.core.logging import logger


class ConversationMemory:
    def __init__(self, max_history: int = 20) -> None:
        self.max_history = max_history

    def compress_history(
        self,
        messages: List[Message],
    ) -> List[Message]:
        if len(messages) <= self.max_history:
            return messages

        recent = messages[-self.max_history:]
        older = messages[:-self.max_history]

        summary = self._summarize(older)
        if summary:
            return [Message(role="system", content=f"[Previous conversation summary]: {summary}"), *recent]

        return recent

    async def summarize_conversation(
        self,
        messages: List[Message],
        existing_summary: Optional[str] = None,
    ) -> str:
        return await self._summarize_async(messages, existing_summary)

    def _summarize(
        self,
        messages: List[Message],
    ) -> str:
        text = " | ".join(
            f"{m.role}: {m.content[:200]}"
            for m in messages
            if m.content
        )
        return f"Conversation summary ({len(messages)} messages): {text[:1000]}"

    async def _summarize_async(
        self,
        messages: List[Message],
        existing_summary: Optional[str] = None,
    ) -> str:
        try:
            context = existing_summary or "No prior summary"
            text = "\n".join(
                f"{m.role}: {m.content[:300]}"
                for m in messages[-30:]
                if m.content
            )

            provider = await ProviderFactory.get_provider_for_use_case("chat")
            result = await provider.complete(
                messages=[Message(
                    role="user",
                    content=f"Previous summary: {context}\n\nNew messages:\n{text}\n\nGenerate a concise 2-3 sentence summary of this conversation.",
                )],
                system="You summarize conversations concisely. Output only the summary.",
                temperature=0.3,
                max_tokens=200,
            )
            return result.content.strip()
        except Exception as exc:
            logger.warning("memory.summarization_failed", error=str(exc))
            return self._summarize(messages[-10:])
