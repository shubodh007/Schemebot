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
from app.core.config import settings
from app.core.logging import logger


class OpenRouterProvider(BaseProvider):
    name = "openrouter"
    model: str

    def __init__(
        self,
        api_key: str,
        model: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(api_key, model)
        self.base_url = settings.openrouter_base_url
        self.site_url = settings.openrouter_site_url
        self.site_name = settings.openrouter_site_name

    async def stream(
        self,
        messages: List[Message],
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[StreamChunk, None]:
        formatted = self._format_messages(messages, system)

        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=self._payload(formatted, temperature, max_tokens, stream=True),
            ) as response:
                if response.status_code != 200:
                    error_body = await response.aread()
                    logger.error(
                        "openrouter.stream.error",
                        status=response.status_code,
                        body=error_body.decode()[:500],
                    )
                    yield StreamChunk(
                        token="",
                        finish_reason="error",
                    )
                    return

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        yield StreamChunk(token="", finish_reason="stop")
                        return
                    try:
                        data = json.loads(data_str)
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        finish = data.get("choices", [{}])[0].get("finish_reason")

                        chunk = StreamChunk(token=content or "")
                        if finish:
                            chunk.finish_reason = finish
                        if finish == "stop":
                            usage = data.get("usage")
                            if usage:
                                chunk.usage = {
                                    "prompt_tokens": usage.get("prompt_tokens", 0),
                                    "completion_tokens": usage.get("completion_tokens", 0),
                                }
                        yield chunk
                    except json.JSONDecodeError:
                        continue

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
    )
    async def complete(
        self,
        messages: List[Message],
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> CompletionResult:
        start = time.monotonic()
        formatted = self._format_messages(messages, system)

        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0)) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=self._payload(formatted, temperature, max_tokens, stream=False),
            )

            latency = int((time.monotonic() - start) * 1000)

            if response.status_code != 200:
                logger.error(
                    "openrouter.complete.error",
                    status=response.status_code,
                    body=response.text[:500],
                )
                raise RuntimeError(f"OpenRouter API error: {response.status_code}")

            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = data.get("usage", {})

            return CompletionResult(
                content=content or "",
                model=self.model,
                provider=self.name,
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                latency_ms=latency,
                metadata={"raw_response": data},
            )

    async def count_tokens(self, messages: List[Message]) -> int:
        formatted = self._format_messages(messages)
        total_chars = sum(len(m.get("content", "")) for m in formatted)
        return total_chars // 4

    async def embed(self, texts: List[str]) -> List[List[float]]:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            response = await client.post(
                "https://api.openrouter.ai/api/v1/embeddings",
                headers=self._headers(),
                json={"model": "openai/text-embedding-3-small", "input": texts},
            )
            if response.status_code != 200:
                raise RuntimeError(f"Embedding error: {response.status_code}")
            data = response.json()
            return [item["embedding"] for item in data.get("data", [])]

    async def health_check(self) -> ProviderHealth:
        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers=self._headers(),
                )
                latency = int((time.monotonic() - start) * 1000)
                return ProviderHealth(
                    healthy=response.status_code == 200,
                    latency_ms=latency,
                )
        except Exception as exc:
            latency = int((time.monotonic() - start) * 1000)
            return ProviderHealth(healthy=False, latency_ms=latency, error=str(exc))

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.site_url,
            "X-Title": self.site_name,
        }

    def _payload(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        stream: bool = False,
    ) -> Dict[str, Any]:
        return {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }
