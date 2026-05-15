from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Dict, List, Optional


@dataclass
class Message:
    role: str  # "user" | "assistant" | "system"
    content: str


@dataclass
class CompletionResult:
    content: str
    model: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamChunk:
    token: str
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, int]] = None


@dataclass
class ProviderHealth:
    healthy: bool
    latency_ms: int
    error: Optional[str] = None


class BaseProvider(ABC):
    name: str = ""
    model: str = ""

    def __init__(self, api_key: str, model: str, **kwargs: Any) -> None:
        self.api_key = api_key
        self.model = model

    @abstractmethod
    async def stream(
        self,
        messages: List[Message],
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[StreamChunk, None]:
        ...

    @abstractmethod
    async def complete(
        self,
        messages: List[Message],
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> CompletionResult:
        ...

    @abstractmethod
    async def count_tokens(self, messages: List[Message]) -> int:
        ...

    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        ...

    @abstractmethod
    async def health_check(self) -> ProviderHealth:
        ...

    def _format_messages(
        self, messages: List[Message], system: Optional[str] = None
    ) -> List[Dict[str, str]]:
        result: List[Dict[str, str]] = []
        if system:
            result.append({"role": "system", "content": system})
        for msg in messages:
            result.append({"role": msg.role, "content": msg.content})
        return result
