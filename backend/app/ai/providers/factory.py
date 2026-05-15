from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from app.ai.circuit_breaker import CircuitBreakerRegistry
from app.ai.cost_tracker import CostTracker
from app.ai.providers.base import BaseProvider
from app.ai.providers.anthropic_claude import AnthropicClaudeProvider
from app.ai.providers.openrouter_provider import OpenRouterProvider
from app.core.config import AIProvider, settings
from app.core.exceptions import AIProviderUnavailableError
from app.core.logging import logger

MODEL_USE_CASE_MAP: Dict[str, str] = {
    "eligibility": settings.ai_eligibility_model,
    "legal": settings.ai_legal_model,
    "chat": settings.ai_chat_model,
    "search": settings.ai_search_model,
    "classifier": settings.ai_classifier_model,
    "document": settings.ai_document_model,
}

FALLBACK_CHAIN: List[str] = [
    AIProvider.OPENROUTER.value,
    AIProvider.GOOGLE.value,
]

MODEL_FALLBACK_CHAIN: List[str] = [
    "use_case_model",
    "chat",
    "google_fallback",
]


class ProviderFactory:
    _instances: Dict[str, BaseProvider] = {}

    @classmethod
    def get_provider(
        cls,
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
    ) -> BaseProvider:
        provider = provider_name or settings.ai_primary_provider.value
        cache_key = f"{provider}:{model or 'default'}"

        if cache_key in cls._instances:
            return cls._instances[cache_key]

        instance = cls._create_provider(provider, model)
        cls._instances[cache_key] = instance
        return instance

    @classmethod
    def _create_provider(cls, provider: str, model: Optional[str] = None) -> BaseProvider:
        provider_enum = AIProvider(provider)

        if provider_enum == AIProvider.OPENROUTER:
            cls._require_key("openrouter", settings.openrouter_api_key, "OPENROUTER_API_KEY")
            return OpenRouterProvider(
                api_key=settings.openrouter_api_key,
                model=model or settings.ai_chat_model,
            )

        elif provider_enum == AIProvider.ANTHROPIC:
            cls._require_key("anthropic", settings.anthropic_api_key, "ANTHROPIC_API_KEY")
            return AnthropicClaudeProvider(
                api_key=settings.anthropic_api_key,
                model=model or settings.ai_legal_model,
            )

        elif provider_enum == AIProvider.GOOGLE:
            return cls._create_google_provider(model)

        elif provider_enum == AIProvider.OPENAI:
            cls._require_key("openai", settings.openai_api_key, "OPENAI_API_KEY")
            from app.ai.providers.openai_gpt import OpenAIProvider
            return OpenAIProvider(api_key=settings.openai_api_key, model=model or "gpt-4o-mini")

        elif provider_enum == AIProvider.DEEPSEEK:
            cls._require_key("deepseek", settings.deepseek_api_key, "DEEPSEEK_API_KEY")
            from app.ai.providers.deepseek import DeepSeekProvider
            return DeepSeekProvider(api_key=settings.deepseek_api_key, model=model or "deepseek-chat")

        elif provider_enum == AIProvider.GROQ:
            cls._require_key("groq", settings.groq_api_key, "GROQ_API_KEY")
            from app.ai.providers.groq_llama import GroqProvider
            return GroqProvider(api_key=settings.groq_api_key, model=model or "llama-3.1-70b-versatile")

        raise AIProviderUnavailableError(
            provider=provider,
            model=model or "default",
            original_error=f"Unknown provider: {provider}",
        )

    @classmethod
    def _require_key(cls, provider: str, key: str, env_var: str) -> None:
        if not key:
            raise AIProviderUnavailableError(
                provider=provider,
                model="default",
                original_error=f"{env_var} not configured",
            )

    @classmethod
    def _create_google_provider(cls, model: Optional[str] = None) -> BaseProvider:
        from app.ai.providers.google_gemini import GeminiProvider
        api_key = settings.google_ai_studio_api_key or settings.google_ai_api_key
        if not api_key:
            raise AIProviderUnavailableError(
                provider="google",
                model=model or "default",
                original_error="GOOGLE_AI_STUDIO_API_KEY not configured",
            )
        return GeminiProvider(
            api_key=api_key,
            model=model or "gemini-3-flash-preview",
        )

    @classmethod
    async def get_provider_for_use_case(
        cls,
        use_case: str,
    ) -> BaseProvider:
        model = MODEL_USE_CASE_MAP.get(use_case, settings.ai_chat_model)
        primary = settings.ai_primary_provider.value

        breaker = CircuitBreakerRegistry.get(f"provider:{primary}")
        if not breaker.allow_request():
            logger.warning("circuit_breaker.blocking_request", provider=primary)
            fallback = settings.ai_fallback_provider.value
            return cls.get_provider(fallback, model)

        try:
            return cls.get_provider(primary, model)
        except AIProviderUnavailableError:
            logger.warning("provider.fallback", primary=primary, fallback=settings.ai_fallback_provider.value)
            return cls.get_provider(settings.ai_fallback_provider.value, model)

    @classmethod
    async def with_fallback(
        cls,
        use_case: str,
        messages: list,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> Any:
        use_case_model = MODEL_USE_CASE_MAP.get(use_case, settings.ai_chat_model)
        models_to_try = [
            use_case_model,
            settings.ai_chat_model,
        ]
        errors: List[str] = []

        for model in models_to_try:
            for provider_name in FALLBACK_CHAIN:
                breaker = CircuitBreakerRegistry.get(f"provider:{provider_name}")
                if not breaker.allow_request():
                    errors.append(f"{provider_name}/{model}: circuit open")
                    continue

                try:
                    provider = cls.get_provider(provider_name, model)
                    start = time.monotonic()

                    result = await provider.complete(
                        messages=messages,
                        system=system,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )

                    latency = int((time.monotonic() - start) * 1000)
                    breaker.record_success()

                    CostTracker.record(
                        provider=provider_name,
                        model=provider.model,
                        prompt_tokens=result.prompt_tokens,
                        completion_tokens=result.completion_tokens,
                        latency_ms=latency,
                        success=True,
                    )

                    return result

                except Exception as exc:
                    latency = int((time.monotonic() - start) * 1000) if 'start' in dir() else 0
                    breaker.record_failure()

                    CostTracker.record(
                        provider=provider_name,
                        model=model,
                        prompt_tokens=0,
                        completion_tokens=0,
                        latency_ms=latency,
                        success=False,
                    )

                    errors.append(f"{provider_name}/{model}: {str(exc)}")
                    logger.warning("provider.fallback.attempt_failed", provider=provider_name, model=model, error=str(exc))
                    continue

        raise AIProviderUnavailableError(
            provider=",".join(FALLBACK_CHAIN),
            model=use_case,
            original_error=f"All fallbacks failed: {'; '.join(errors)}",
        )

    @classmethod
    async def health_check_all(cls) -> Dict[str, Any]:
        results = {}
        for provider_name in ["openrouter", "google", "groq", "deepseek"]:
            try:
                provider = cls.get_provider(provider_name)
                health = await provider.health_check()
                results[provider_name] = {
                    "healthy": health.healthy,
                    "latency_ms": health.latency_ms,
                    "error": health.error,
                }
            except Exception as exc:
                results[provider_name] = {
                    "healthy": False,
                    "latency_ms": 0,
                    "error": str(exc),
                }
        return results
