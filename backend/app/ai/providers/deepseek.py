from __future__ import annotations

from typing import Any, AsyncGenerator, List, Optional

import httpx

from app.ai.providers.base import (
    BaseProvider,
    CompletionResult,
    Message,
    ProviderHealth,
    StreamChunk,
)


class DeepSeekProvider(BaseProvider):
    name = "deepseek"
    model: str

    def __init__(self, api_key: str, model: str = "deepseek-chat", **kwargs: Any) -> None:
        super().__init__(api_key, model)
        self.base_url = "https://api.deepseek.com/v1"

    async def stream(self, messages: List[Message], system: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 4096) -> AsyncGenerator[StreamChunk, None]:
        formatted = self._format_messages(messages, system)
        body = {"model": self.model, "messages": formatted, "temperature": temperature, "max_tokens": max_tokens, "stream": True}
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            async with client.stream("POST", f"{self.base_url}/chat/completions", json=body, headers=headers) as resp:
                if resp.status_code != 200:
                    yield StreamChunk(token="", finish_reason="error")
                    return
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        import json
                        d = json.loads(line[6:])
                        content = d.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if content:
                            yield StreamChunk(token=content)

    async def complete(self, messages: List[Message], system: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 4096) -> CompletionResult:
        import time
        start = time.monotonic()
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            resp = await client.post(f"{self.base_url}/chat/completions", json={"model": self.model, "messages": self._format_messages(messages, system), "temperature": temperature, "max_tokens": max_tokens}, headers={"Authorization": f"Bearer {self.api_key}"})
        latency = int((time.monotonic() - start) * 1000)
        data = resp.json()
        return CompletionResult(content=data["choices"][0]["message"]["content"], model=self.model, provider=self.name, prompt_tokens=data["usage"]["prompt_tokens"], completion_tokens=data["usage"]["completion_tokens"], latency_ms=latency)

    async def count_tokens(self, messages: List[Message]) -> int:
        return sum(len(m.content) // 4 for m in messages)

    async def embed(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

    async def health_check(self) -> ProviderHealth:
        import time
        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                await client.get(f"{self.base_url}/models", headers={"Authorization": f"Bearer {self.api_key}"})
            return ProviderHealth(healthy=True, latency_ms=int((time.monotonic() - start) * 1000))
        except Exception as exc:
            return ProviderHealth(healthy=False, latency_ms=int((time.monotonic() - start) * 1000), error=str(exc))
