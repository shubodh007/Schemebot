from __future__ import annotations

from typing import Any, Dict, List, Optional


class GovSchemeError(Exception):
    status_code: int = 500
    code: str = "INTERNAL_ERROR"
    detail: str = "An unexpected error occurred"

    def __init__(
        self,
        detail: Optional[str] = None,
        code: Optional[str] = None,
        status_code: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        if detail is not None:
            self.detail = detail
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        self.metadata = metadata or {}
        super().__init__(self.detail)


class NotFoundError(GovSchemeError):
    status_code = 404
    code = "NOT_FOUND"
    detail = "The requested resource was not found"


class ConflictError(GovSchemeError):
    status_code = 409
    code = "CONFLICT"
    detail = "The resource already exists"


class ValidationError(GovSchemeError):
    status_code = 422
    code = "VALIDATION_ERROR"
    detail = "Validation failed"

    def __init__(
        self,
        errors: List[Dict[str, Any]],
        detail: Optional[str] = None,
    ) -> None:
        super().__init__(detail=detail or "Validation failed", code="VALIDATION_ERROR")
        self.errors = errors


class AuthenticationError(GovSchemeError):
    status_code = 401
    code = "UNAUTHORIZED"
    detail = "Authentication required"


class ForbiddenError(GovSchemeError):
    status_code = 403
    code = "FORBIDDEN"
    detail = "You do not have permission to perform this action"


class RateLimitError(GovSchemeError):
    status_code = 429
    code = "RATE_LIMITED"
    detail = "Too many requests. Please try again later."


class AccountLockedError(GovSchemeError):
    status_code = 423
    code = "ACCOUNT_LOCKED"
    detail = "Account is temporarily locked due to too many failed attempts"

    def __init__(self, retry_after: str) -> None:
        super().__init__(
            detail=f"Account is locked until {retry_after}",
            metadata={"retry_after": retry_after},
        )


class TokenExpiredError(AuthenticationError):
    code = "TOKEN_EXPIRED"
    detail = "Token has expired. Please refresh."


class InvalidTokenError(AuthenticationError):
    code = "INVALID_TOKEN"
    detail = "Token is invalid or has been revoked"


class AIProviderError(GovSchemeError):
    status_code = 502
    code = "AI_PROVIDER_ERROR"
    detail = "AI provider returned an error"

    def __init__(
        self,
        provider: str,
        model: str,
        original_error: str,
    ) -> None:
        super().__init__(
            detail=f"AI provider {provider}/{model} failed: {original_error}",
            metadata={"provider": provider, "model": model, "original_error": original_error},
        )


class AIProviderUnavailableError(AIProviderError):
    code = "AI_PROVIDER_UNAVAILABLE"
    detail = "AI provider is currently unavailable"


class FileValidationError(GovSchemeError):
    status_code = 422
    code = "FILE_VALIDATION_ERROR"
    detail = "File failed validation"


class FileTooLargeError(FileValidationError):
    code = "FILE_TOO_LARGE"
    detail = "File exceeds maximum allowed size"


class FileTypeNotAllowedError(FileValidationError):
    code = "FILE_TYPE_NOT_ALLOWED"
    detail = "File type is not supported"


class ScrapingError(GovSchemeError):
    status_code = 502
    code = "SCRAPING_ERROR"
    detail = "Failed to scrape the source"


class DatabaseError(GovSchemeError):
    status_code = 500
    code = "DATABASE_ERROR"
    detail = "A database error occurred"


class EligibilityEngineError(GovSchemeError):
    status_code = 422
    code = "ELIGIBILITY_ERROR"
    detail = "Could not determine eligibility for the requested scheme"
