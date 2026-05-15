from __future__ import annotations

import re
from enum import Enum
from typing import List

from pydantic import Field, field_validator, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class AIProvider(str, Enum):
    OPENROUTER = "openrouter"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    GROQ = "groq"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # General
    environment: Environment = Environment.DEVELOPMENT
    log_level: str = Field(default="INFO", pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    secret_key: str = Field(default="", min_length=32)
    api_v1_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000"
    app_base_url: str = "http://localhost:3000"

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if not v or len(v) < 32:
            import warnings
            warnings.warn("SECRET_KEY is too short or empty. Use a 64-char hex key in production.")
        return v

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, v: str) -> str:
        origins = [o.strip() for o in v.split(",") if o.strip()]
        for origin in origins:
            if origin != "*" and not re.match(r"^https?://", origin):
                raise ValueError(f"Invalid CORS origin: {origin}. Must start with http:// or https://")
        return v

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # Supabase
    supabase_url: str = Field(default="", description="https://your-project.supabase.co")
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_db_url: str = ""

    @field_validator("supabase_db_url")
    @classmethod
    def validate_db_url(cls, v: str) -> str:
        if v and not v.startswith("postgresql"):
            raise ValueError("supabase_db_url must start with postgresql:// or postgresql+asyncpg://")
        return v

    # Upstash Redis
    upstash_redis_url: str = ""
    upstash_redis_token: str = ""

    @field_validator("upstash_redis_url")
    @classmethod
    def validate_redis_url(cls, v: str) -> str:
        if v and not v.startswith("redis://") and not v.startswith("rediss://"):
            raise ValueError("upstash_redis_url must start with redis:// or rediss://")
        return v

    # OpenRouter
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_site_url: str = "https://govscheme.in"
    openrouter_site_name: str = "GovScheme AI"

    # Google AI
    google_ai_api_key: str = ""
    google_embedding_model: str = "text-embedding-004"

    # Optional Direct Provider Keys
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    deepseek_api_key: str = ""
    groq_api_key: str = ""

    # Email (SendGrid)
    sendgrid_api_key: str = ""
    sendgrid_from_email: str = "noreply@govscheme.in"

    # Monitoring
    sentry_dsn: str = ""
    sentry_environment: str = "development"
    sentry_traces_sample_rate: float = Field(default=0.1, ge=0.0, le=1.0)
    posthog_api_key: str = ""
    posthog_host: str = "https://us.i.posthog.com"

    # Arq Worker
    arq_queue_name: str = "govscheme-tasks"
    arq_max_jobs: int = Field(default=10, ge=1, le=50)
    arq_job_timeout: int = Field(default=300, ge=30, le=3600)

    # File Upload
    max_upload_size_mb: int = Field(default=10, ge=1, le=100)
    allowed_mime_types: str = "application/pdf,image/jpeg,image/png"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def allowed_mime_list(self) -> List[str]:
        return [m.strip() for m in self.allowed_mime_types.split(",") if m.strip()]

    # Rate Limiting
    rate_limit_window_seconds: int = Field(default=60, ge=1, le=3600)
    rate_limit_default_max: int = Field(default=60, ge=1, le=10000)
    rate_limit_auth_max: int = Field(default=10, ge=1, le=100)
    rate_limit_chat_max: int = Field(default=20, ge=1, le=100)

    # AI Provider Selection
    ai_primary_provider: AIProvider = AIProvider.OPENROUTER
    ai_fallback_provider: AIProvider = AIProvider.GOOGLE
    ai_eligibility_model: str = "arcee-ai/trinity-large-thinking:free"
    ai_legal_model: str = "arcee-ai/trinity-large-thinking:free"
    ai_chat_model: str = "nvidia/nemotron-3-super-120b-a12b:free"
    ai_search_model: str = "nvidia/nemotron-3-super-120b-a12b:free"
    ai_classifier_model: str = "openai/gpt-oss-20b:free"
    ai_document_model: str = "google/gemini-2.0-flash-001"
    google_ai_studio_api_key: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_required()

    def _validate_required(self) -> None:
        if self.environment == Environment.PRODUCTION:
            required = {
                "SUPABASE_URL": self.supabase_url,
                "SUPABASE_SERVICE_ROLE_KEY": self.supabase_service_role_key,
                "SUPABASE_DB_URL": self.supabase_db_url,
                "OPENROUTER_API_KEY": self.openrouter_api_key,
                "SECRET_KEY": self.secret_key,
            }
            missing = [k for k, v in required.items() if not v]
            if self.secret_key and len(self.secret_key) < 32:
                missing.append("SECRET_KEY (too short, min 32 chars)")
            if missing:
                raise ValueError(f"Missing required production environment variables: {', '.join(missing)}")


settings = Settings()
