from __future__ import annotations

import json
import time
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.ai.providers.base import (
    BaseProvider,
    CompletionResult,
    Message,
    ProviderHealth,
    StreamChunk,
)
from app.core.logging import logger


class AnthropicClaudeProvider(BaseProvider):
    name = "anthropic"
    model: str

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        **kwargs: Any,
    ) -> None:
        super().__init__(api_key, model)
        self.base_url = "https://api.anthropic.com/v1"

    async def stream(
        self,
        messages: List[Message],
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[StreamChunk, None]:
        body = self._build_body(messages, system, temperature, max_tokens, stream=True)

        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/messages",
                headers=self._headers(),
                json=body,
            ) as response:
                if response.status_code != 200:
                    error_body = await response.aread()
                    logger.error("anthropic.stream.error", status=response.status_code, body=error_body.decode()[:500])
                    yield StreamChunk(token="", finish_reason="error")
                    return

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            yield StreamChunk(token="", finish_reason="stop")
                            return
                        try:
                            data = json.loads(data_str)
                            if data.get("type") == "content_block_delta":
                                delta = data.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    yield StreamChunk(token=delta.get("text", ""))
                        except json.JSONDecodeError:
                            continue
                    elif line.startswith("event: message_stop"):
                        yield StreamChunk(token="", finish_reason="stop")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def complete(
        self,
        messages: List[Message],
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> CompletionResult:
        start = time.monotonic()
        body = self._build_body(messages, system, temperature, max_tokens, stream=False)

        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0)) as client:
            response = await client.post(
                f"{self.base_url}/messages",
                headers=self._headers(),
                json=body,
            )
            latency = int((time.monotonic() - start) * 1000)

            if response.status_code != 200:
                raise RuntimeError(f"Anthropic API error: {response.status_code}: {response.text[:500]}")

            data = response.json()
            content = "".join(
                block.get("text", "") for block in data.get("content", []) if block.get("type") == "text"
            )
            usage = data.get("usage", {})
            return CompletionResult(
                content=content,
                model=self.model,
                provider=self.name,
                prompt_tokens=usage.get("input_tokens", 0),
                completion_tokens=usage.get("output_tokens", 0),
                latency_ms=latency,
            )

    async def count_tokens(self, messages: List[Message]) -> int:
        total = 0
        for msg in messages:
            total += len(msg.content) // 4
        return total

    async def embed(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError("Anthropic does not provide embeddings via the Messages API")

    async def health_check(self) -> ProviderHealth:
        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers=self._headers(),
                )
                latency = int((time.monotonic() - start) * 1000)
                return ProviderHealth(healthy=response.status_code == 200, latency_ms=latency)
        except Exception as exc:
            latency = int((time.monotonic() - start) * 1000)
            return ProviderHealth(healthy=False, latency_ms=latency, error=str(exc))

    def _headers(self) -> Dict[str, str]:
        return {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

    def _build_body(
        self,
        messages: List[Message],
        system: Optional[str],
        temperature: float,
        max_tokens: int,
        stream: bool,
    ) -> Dict[str, Any]:
        formatted = [{"role": m.role, "content": m.content} for m in messages]
        body: Dict[str, Any] = {
            "model": self.model,
            "messages": formatted,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream,
        }
        if system:
            body["system"] = system
        return body
