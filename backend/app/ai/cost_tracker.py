from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ProviderUsageRecord:
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    success: bool
    timestamp: float = field(default_factory=time.monotonic)


COST_PER_1K_TOKENS: Dict[str, Dict[str, float]] = {
    "openrouter": {
        "anthropic/claude-sonnet-4-20250514": {"prompt": 0.003, "completion": 0.015},
        "google/gemini-2.0-flash-lite-preview-02-05": {"prompt": 0.000, "completion": 0.000},
        "google/gemini-2.0-flash-001": {"prompt": 0.000, "completion": 0.000},
        "groq/llama-3.1-70b-versatile": {"prompt": 0.000, "completion": 0.000},
        "deepseek/deepseek-chat": {"prompt": 0.00014, "completion": 0.00028},
        "openai/gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
    },
    "anthropic": {
        "claude-sonnet-4-20250514": {"prompt": 0.003, "completion": 0.015},
        "claude-haiku-3-5-20241022": {"prompt": 0.0008, "completion": 0.004},
    },
    "google": {
        "gemini-2.0-flash": {"prompt": 0.0, "completion": 0.0},
        "gemini-2.0-flash-lite": {"prompt": 0.0, "completion": 0.0},
        "text-embedding-004": {"prompt": 0.0, "completion": 0.0},
    },
    "openai": {
        "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
        "gpt-4o": {"prompt": 0.0025, "completion": 0.01},
        "text-embedding-3-small": {"prompt": 0.00002, "completion": 0.0},
    },
    "groq": {
        "llama-3.1-70b-versatile": {"prompt": 0.0, "completion": 0.0},
        "llama-3.1-8b-instant": {"prompt": 0.0, "completion": 0.0},
    },
    "deepseek": {
        "deepseek-chat": {"prompt": 0.00014, "completion": 0.00028},
    },
}


class CostTracker:
    _records: List[ProviderUsageRecord] = []

    @classmethod
    def record(
        cls,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: int,
        success: bool = True,
    ) -> None:
        cls._records.append(
            ProviderUsageRecord(
                provider=provider,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                latency_ms=latency_ms,
                success=success,
            )
        )

    @classmethod
    def calculate_cost(cls, provider: str, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        pricing = COST_PER_1K_TOKENS.get(provider, {}).get(model, {"prompt": 0.001, "completion": 0.002})
        prompt_cost = (prompt_tokens / 1000) * pricing["prompt"]
        completion_cost = (completion_tokens / 1000) * pricing["completion"]
        return round(prompt_cost + completion_cost, 6)

    @classmethod
    def get_session_cost(cls, window_minutes: int = 60) -> float:
        cutoff = time.monotonic() - (window_minutes * 60)
        recent = [r for r in cls._records if r.timestamp > cutoff]
        total = 0.0
        for r in recent:
            total += cls.calculate_cost(r.provider, r.model, r.prompt_tokens, r.completion_tokens)
        return round(total, 6)

    @classmethod
    def get_provider_summary(cls) -> Dict[str, Any]:
        summary: Dict[str, Any] = {}
        for record in cls._records:
            if record.provider not in summary:
                summary[record.provider] = {
                    "total_requests": 0,
                    "successful": 0,
                    "failed": 0,
                    "total_prompt_tokens": 0,
                    "total_completion_tokens": 0,
                    "total_cost": 0.0,
                    "avg_latency_ms": 0.0,
                    "latencies": [],
                }
            s = summary[record.provider]
            s["total_requests"] += 1
            if record.success:
                s["successful"] += 1
            else:
                s["failed"] += 1
            s["total_prompt_tokens"] += record.prompt_tokens
            s["total_completion_tokens"] += record.completion_tokens
            s["total_cost"] += cls.calculate_cost(record.provider, record.model, record.prompt_tokens, record.completion_tokens)
            s["latencies"].append(record.latency_ms)

        for provider, s in summary.items():
            if s["latencies"]:
                s["avg_latency_ms"] = round(sum(s["latencies"]) / len(s["latencies"]), 1)
            s["total_cost"] = round(s["total_cost"], 6)
            del s["latencies"]

        return summary

    @classmethod
    def reset(cls) -> None:
        cls._records.clear()
