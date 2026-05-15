from __future__ import annotations

from typing import AsyncGenerator, List

import pytest

from app.ai.providers.base import Message, StreamChunk
from app.ai.providers.factory import ProviderFactory
from app.tests.mocks import MockLLMProvider


class TestStreamingFallback:
    @pytest.mark.asyncio
    async def test_primary_succeeds(self):
        primary = MockLLMProvider(responses=["Primary response"], name="primary")
        ProviderFactory._instances["primary:default"] = primary

        chunks: List[str] = []
        async for chunk in ProviderFactory.stream_with_fallback(
            use_case="chat",
            messages=[Message(role="user", content="hello")],
        ):
            if chunk.token:
                chunks.append(chunk.token)

        assert "".join(chunks).strip() == "Primary response"

    @pytest.mark.asyncio
    async def test_fallback_on_primary_failure(self):
        primary = MockLLMProvider(
            responses=["Primary"],
            fail_on_complete=[1],
            name="primary",
        )
        fallback = MockLLMProvider(responses=["Fallback response"], name="fallback")
        ProviderFactory._instances["primary:default"] = primary
        ProviderFactory._instances["fallback:default"] = fallback

        chunks: List[str] = []
        async for chunk in ProviderFactory.stream_with_fallback(
            use_case="chat",
            messages=[Message(role="user", content="hello")],
        ):
            if chunk.token:
                chunks.append(chunk.token)

        assert "".join(chunks).strip() == "Fallback response"

    @pytest.mark.asyncio
    async def test_all_providers_fail_raises_error(self):
        primary = MockLLMProvider(
            responses=["Primary"],
            fail_on_complete=[1, 2, 3],
            name="primary",
        )
        ProviderFactory._instances["primary:default"] = primary

        from app.core.exceptions import AIProviderUnavailableError
        with pytest.raises(AIProviderUnavailableError):
            async for _ in ProviderFactory.stream_with_fallback(
                use_case="chat",
                messages=[Message(role="user", content="hello")],
            ):
                pass
