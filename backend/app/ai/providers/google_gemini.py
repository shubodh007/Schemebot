from __future__ import annotations

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


class GeminiProvider(BaseProvider):
    name = "google"
    model: str

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash",
        **kwargs: Any,
    ) -> None:
        super().__init__(api_key, model)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self._headers = {"X-Goog-Api-Key": api_key, "Content-Type": "application/json"}

    async def stream(
        self,
        messages: List[Message],
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[StreamChunk, None]:
        url = f"{self.base_url}/models/{self.model}:streamGenerateContent?alt=sse"
        body = self._build_body(messages, system, temperature, max_tokens)

        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            async with client.stream("POST", url, json=body, headers=self._headers) as response:
                if response.status_code != 200:
                    yield StreamChunk(token="", finish_reason="error")
                    return

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        import json
                        try:
                            data = json.loads(line[6:])
                            candidates = data.get("candidates", [])
                            if candidates:
                                content = candidates[0].get("content", {})
                                parts = content.get("parts", [])
                                for part in parts:
                                    yield StreamChunk(token=part.get("text", ""))
                        except json.JSONDecodeError:
                            continue

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def complete(
        self,
        messages: List[Message],
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> CompletionResult:
        start = time.monotonic()
        url = f"{self.base_url}/models/{self.model}:generateContent"
        body = self._build_body(messages, system, temperature, max_tokens)

        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0)) as client:
            response = await client.post(url, json=body, headers=self._headers)
            latency = int((time.monotonic() - start) * 1000)

            if response.status_code != 200:
                raise RuntimeError(f"Gemini API error: {response.status_code}: {response.text[:500]}")

            data = response.json()
            text = ""
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                text = "".join(p.get("text", "") for p in parts)

            usage = data.get("usageMetadata", {})
            return CompletionResult(
                content=text,
                model=self.model,
                provider=self.name,
                prompt_tokens=usage.get("promptTokenCount", 0),
                completion_tokens=usage.get("candidatesTokenCount", 0),
                latency_ms=latency,
            )

    async def count_tokens(self, messages: List[Message]) -> int:
        total = sum(len(m.content) for m in messages)
        return total // 4

    async def embed(self, texts: List[str]) -> List[List[float]]:
        url = "https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent"
        results = []
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            for text in texts:
                resp = await client.post(url, json={"model": "models/text-embedding-004", "content": {"parts": [{"text": text}]}}, headers=self._headers)
                data = resp.json()
                results.append(data.get("embedding", {}).get("values", []))
        return results

    async def health_check(self) -> ProviderHealth:
        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                resp = await client.get(f"{self.base_url}/models", headers=self._headers)
                latency = int((time.monotonic() - start) * 1000)
                return ProviderHealth(healthy=resp.status_code == 200, latency_ms=latency)
        except Exception as exc:
            latency = int((time.monotonic() - start) * 1000)
            return ProviderHealth(healthy=False, latency_ms=latency, error=str(exc))

    def _build_body(self, messages: List[Message], system: Optional[str], temperature: float, max_tokens: int) -> Dict:
        contents = []
        for m in messages:
            contents.append({"role": m.role, "parts": [{"text": m.content}]})
        body: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}
        return body
