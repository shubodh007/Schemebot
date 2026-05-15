from __future__ import annotations

from typing import Any, AsyncGenerator, Dict, List, Optional

from openai import AsyncOpenAI

from app.ai.providers.base import (
    BaseProvider,
    CompletionResult,
    Message,
    ProviderHealth,
    StreamChunk,
)
from app.core.logging import logger


class OpenAIProvider(BaseProvider):
    name = "openai"
    model: str

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        **kwargs: Any,
    ) -> None:
        super().__init__(api_key, model)
        self.client = AsyncOpenAI(api_key=api_key)

    async def stream(
        self,
        messages: List[Message],
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[StreamChunk, None]:
        formatted = self._format_messages(messages, system)
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=formatted,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield StreamChunk(token=delta.content)

    async def complete(
        self,
        messages: List[Message],
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> CompletionResult:
        import time
        start = time.monotonic()
        formatted = self._format_messages(messages, system)
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=formatted,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        latency = int((time.monotonic() - start) * 1000)
        return CompletionResult(
            content=response.choices[0].message.content or "",
            model=self.model,
            provider=self.name,
            prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
            completion_tokens=response.usage.completion_tokens if response.usage else 0,
            latency_ms=latency,
        )

    async def count_tokens(self, messages: List[Message]) -> int:
        return sum(len(m.content) // 4 for m in messages)

    async def embed(self, texts: List[str]) -> List[List[float]]:
        response = await self.client.embeddings.create(
            model="text-embedding-3-small", input=texts
        )
        return [d.embedding for d in response.data]

    async def health_check(self) -> ProviderHealth:
        import time
        start = time.monotonic()
        try:
            await self.client.models.list()
            latency = int((time.monotonic() - start) * 1000)
            return ProviderHealth(healthy=True, latency_ms=latency)
        except Exception as exc:
            latency = int((time.monotonic() - start) * 1000)
            return ProviderHealth(healthy=False, latency_ms=latency, error=str(exc))
