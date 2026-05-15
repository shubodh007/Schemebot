from __future__ import annotations

import asyncio
from typing import Any, AsyncGenerator, Dict, List, Optional
from unittest.mock import AsyncMock

from app.ai.providers.base import (
    BaseProvider,
    CompletionResult,
    Message,
    ProviderHealth,
    StreamChunk,
)


class MockLLMProvider(BaseProvider):
    """Deterministic mock with configurable failure modes."""

    def __init__(
        self,
        responses: Optional[List[str]] = None,
        fail_on_complete: Optional[List[int]] = None,
        fail_on_stream: Optional[List[int]] = None,
        latency_ms: int = 0,
        name: str = "mock",
        model: str = "mock-model",
    ) -> None:
        super().__init__(api_key="mock-key", model=model)
        self.name = name
        self._responses = responses or ["This is a mock response."]
        self._fail_on_complete = set(fail_on_complete or [])
        self._fail_on_stream = set(fail_on_stream or [])
        self._call_count = 0
        self._latency = latency_ms / 1000

    async def complete(
        self,
        messages: List[Message],
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> CompletionResult:
        self._call_count += 1
        if self._call_count in self._fail_on_complete:
            raise RuntimeError(f"Mock failure on call {self._call_count}")
        await asyncio.sleep(self._latency)
        idx = min(self._call_count - 1, len(self._responses) - 1)
        return CompletionResult(
            content=self._responses[idx],
            model=self.model,
            provider=self.name,
            prompt_tokens=10,
            completion_tokens=len(self._responses[idx].split()),
            latency_ms=int(self._latency * 1000),
        )

    async def stream(
        self,
        messages: List[Message],
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[StreamChunk, None]:
        self._call_count += 1
        if self._call_count in self._fail_on_stream:
            yield StreamChunk(token="", finish_reason="error")
            return
        await asyncio.sleep(self._latency)
        idx = min(self._call_count - 1, len(self._responses) - 1)
        for word in self._responses[idx].split():
            yield StreamChunk(token=word + " ")
            await asyncio.sleep(0.001)
        yield StreamChunk(token="", finish_reason="stop")

    async def count_tokens(self, messages: List[Message]) -> int:
        return sum(len(m.content) // 4 for m in messages)

    async def embed(self, texts: List[str]) -> List[List[float]]:
        return [[0.1] * 128 for _ in texts]

    async def health_check(self) -> ProviderHealth:
        return ProviderHealth(healthy=True, latency_ms=0)
