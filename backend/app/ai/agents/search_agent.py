from __future__ import annotations

import asyncio
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

from app.ai.agents.base_agent import BaseAgent
from app.ai.providers.base import StreamChunk
from app.core.logging import logger
from app.ai.rag.pipeline import RAGPipeline

SEARCH_AGENT_SYSTEM_PROMPT = """
You are the GovScheme Search Agent — you provide timely, accurate information about
Indian government schemes by combining real-time web search results with our database.

RULES:
1. Always cite your sources with the URL when providing scheme information.
2. Clearly distinguish between "from our database" and "from web search" information.
3. If search results are empty or unreliable, say so. Never fabricate information.
4. Focus on: scheme deadlines, application window changes, new scheme launches,
   budget announcements, policy changes.
5. For eligibility questions — defer to our scheme database. Use web only for timing/deadlines.
"""


class SearchAgent(BaseAgent):
    name = "search_agent"
    system_prompt = SEARCH_AGENT_SYSTEM_PROMPT

    def __init__(
        self,
        rag_pipeline: Optional[RAGPipeline] = None,
    ) -> None:
        super().__init__(rag_pipeline=rag_pipeline, use_case="search")

    async def stream_response(
        self,
        user_message: str,
        conversation_history: Optional[List] = None,
        context: Optional[Dict[str, Any]] = None,
        language: str = "en",
    ) -> AsyncGenerator[StreamChunk, None]:
        db_context = ""
        citations: List[Dict[str, Any]] = []

        if self.rag:
            retrieval = await self.rag.retrieve(query=user_message, filter_context=context or {})
            db_context = retrieval.get("context", "")
            citations = retrieval.get("citations", [])

        web_results = await self._search_web(user_message)

        context_parts = [f"User query: {user_message}"]
        if db_context:
            context_parts.append(f"<database_context>\n{db_context}\n</database_context>")
        if web_results:
            context_parts.append(f"<web_search_results>\n{web_results}\n</web_search_results>")
        context_parts.append(f"Language: {language}")

        from app.ai.providers.factory import ProviderFactory
        provider = await ProviderFactory.get_provider_for_use_case("search")

        messages = [__import__("app.ai.providers.base", fromlist=["Message"]).Message(
            role="user",
            content="\n\n".join(context_parts),
        )]

        async for chunk in provider.stream(
            messages=messages,
            system=self._build_system_prompt(language),
        ):
            if chunk.finish_reason == "stop" and citations:
                yield StreamChunk(token="", finish_reason="citations", usage={"citations": citations})
            yield chunk

    async def _search_web(self, query: str) -> str:
        try:
            from duckduckgo_search import DDGS
            loop = asyncio.get_running_loop()

            def _sync_search(q: str) -> str:
                with DDGS() as ddgs:
                    results = list(ddgs.text(q, max_results=5))
                    if not results:
                        return ""
                    formatted = []
                    for i, r in enumerate(results, 1):
                        formatted.append(
                            f"[{i}] {r.get('title', '')}\n"
                            f"    URL: {r.get('href', '')}\n"
                            f"    Snippet: {r.get('body', '')}"
                        )
                    return "\n\n".join(formatted)

            return await loop.run_in_executor(None, _sync_search, query)
        except Exception as exc:
            logger.warning("search.web_search_failed", error=str(exc))
            return ""

    async def complete(
        self,
        user_message: str,
        conversation_history: Optional[List] = None,
        context: Optional[Dict[str, Any]] = None,
        language: str = "en",
    ) -> Tuple[str, List[Dict[str, Any]]]:
        web_results = await self._search_web(user_message)
        context_parts = [f"User query: {user_message}"]
        if web_results:
            context_parts.append(f"<web_search_results>\n{web_results}\n</web_search_results>")
        context_parts.append(f"Language: {language}")

        from app.ai.providers.base import Message
        from app.ai.providers.factory import ProviderFactory
        provider = await ProviderFactory.get_provider_for_use_case("search")
        result = await provider.complete(
            messages=[Message(role="user", content="\n\n".join(context_parts))],
            system=self._build_system_prompt(language),
        )
        return result.content, []
