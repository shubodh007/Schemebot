from __future__ import annotations

from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

from app.ai.input_sanitizer import InputSanitizer
from app.ai.providers.base import Message, StreamChunk
from app.ai.providers.factory import ProviderFactory
from app.ai.rag.pipeline import RAGPipeline
from app.core.logging import logger


class BaseAgent:
    name: str = "base"
    system_prompt: str = ""

    def __init__(
        self,
        rag_pipeline: Optional[RAGPipeline] = None,
        use_case: str = "chat",
    ) -> None:
        self.rag = rag_pipeline
        self.use_case = use_case

    async def stream_response(
        self,
        user_message: str,
        conversation_history: Optional[List[Message]] = None,
        context: Optional[Dict[str, Any]] = None,
        language: str = "en",
    ) -> AsyncGenerator[StreamChunk, None]:
        sanitized = InputSanitizer.process(user_message)
        retrieved_context = ""
        citations: List[Dict[str, Any]] = []

        if self.rag:
            retrieval_result = await self.rag.retrieve(
                query=sanitized,
                filter_context=context or {},
            )
            retrieved_context = retrieval_result.get("context", "")
            citations = retrieval_result.get("citations", [])

        messages = self._build_messages(
            user_message=sanitized,
            retrieved_context=retrieved_context,
            conversation_history=conversation_history or [],
            language=language,
        )

        provider = await ProviderFactory.get_provider_for_use_case(self.use_case)

        logger.info(
            "agent.stream.start",
            agent=self.name,
            provider=provider.name,
            model=provider.model,
        )

        async for chunk in provider.stream(
            messages=messages,
            system=self._build_system_prompt(language),
        ):
            if chunk.finish_reason == "stop" and citations:
                yield StreamChunk(
                    token="",
                    finish_reason="citations",
                    usage={"citations": citations},
                )
            yield chunk

    async def complete(
        self,
        user_message: str,
        conversation_history: Optional[List[Message]] = None,
        context: Optional[Dict[str, Any]] = None,
        language: str = "en",
    ) -> Tuple[str, List[Dict[str, Any]]]:
        sanitized = InputSanitizer.process(user_message)
        retrieved_context = ""
        citations: List[Dict[str, Any]] = []

        if self.rag:
            retrieval_result = await self.rag.retrieve(
                query=sanitized,
                filter_context=context or {},
            )
            retrieved_context = retrieval_result.get("context", "")
            citations = retrieval_result.get("citations", [])

        messages = self._build_messages(
            user_message=sanitized,
            retrieved_context=retrieved_context,
            conversation_history=conversation_history or [],
            language=language,
        )

        provider = await ProviderFactory.get_provider_for_use_case(self.use_case)

        result = await provider.complete(
            messages=messages,
            system=self._build_system_prompt(language),
        )

        logger.info(
            "agent.complete",
            agent=self.name,
            provider=provider.name,
            tokens=result.completion_tokens,
            latency_ms=result.latency_ms,
        )

        return result.content, citations

    def _build_messages(
        self,
        user_message: str,
        retrieved_context: str,
        conversation_history: List[Message],
        language: str,
    ) -> List[Message]:
        messages: List[Message] = []

        for msg in conversation_history[-20:]:
            messages.append(msg)

        context_parts = []
        if retrieved_context:
            context_parts.append(f"<retrieved_context>\n{retrieved_context}\n</retrieved_context>")
        context_parts.append(f"User language: {language}")
        context_parts.append(f"User query: {user_message}")

        messages.append(Message(role="user", content="\n\n".join(context_parts)))
        return messages

    def _build_system_prompt(self, language: str = "en") -> str:
        lang_instruction = ""
        if language == "hi":
            lang_instruction = "\n\nCRITICAL: Respond in Hindi (Devanagari script). Use formal Hindi appropriate for government communication."
        elif language == "te":
            lang_instruction = "\n\nCRITICAL: Respond in Telugu (Telugu script). Use formal Telugu appropriate for government communication."

        return self.system_prompt + lang_instruction
