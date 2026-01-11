"""
AI Service Exceptions Module.

Exceptions specific to AI/LLM service errors.
"""

from typing import Any

from app.exceptions.base import DevBridgeError, ErrorCode


class AIServiceError(DevBridgeError):
    """Base exception for AI service-related errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.AI_SERVICE_ERROR,
        status_code: int = 502,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=status_code,
            details=details,
        )


class AIRateLimitError(AIServiceError):
    """AI service rate limit exceeded."""

    def __init__(
        self,
        provider: str = "AI",
        retry_after: int | None = None,
    ):
        message = f"{provider} service rate limit exceeded"
        details: dict[str, Any] = {"provider": provider}
        if retry_after:
            message += f". Retry after {retry_after} seconds"
            details["retry_after_seconds"] = retry_after

        super().__init__(
            message=message,
            code=ErrorCode.AI_RATE_LIMITED,
            status_code=429,
            details=details,
        )


class AIInvalidResponseError(AIServiceError):
    """AI service returned an invalid or unparseable response."""

    def __init__(
        self,
        operation: str,
        reason: str | None = None,
    ):
        message = f"AI service returned invalid response for '{operation}'"
        details: dict[str, Any] = {"operation": operation}
        if reason:
            message += f": {reason}"
            details["reason"] = reason

        super().__init__(
            message=message,
            code=ErrorCode.AI_INVALID_RESPONSE,
            status_code=502,
            details=details,
        )


class AIContextTooLongError(AIServiceError):
    """Input context exceeds AI model's maximum token limit."""

    def __init__(
        self,
        tokens_provided: int | None = None,
        max_tokens: int | None = None,
    ):
        message = "Input context exceeds maximum length for AI model"
        details: dict[str, Any] = {}
        if tokens_provided:
            details["tokens_provided"] = tokens_provided
        if max_tokens:
            details["max_tokens"] = max_tokens

        super().__init__(
            message=message,
            code=ErrorCode.AI_CONTEXT_TOO_LONG,
            status_code=400,
            details=details,
        )


class AIGenerationError(AIServiceError):
    """AI content generation failed."""

    def __init__(
        self,
        operation: str,
        reason: str | None = None,
        model: str | None = None,
    ):
        message = f"AI generation failed for '{operation}'"
        details: dict[str, Any] = {"operation": operation}
        if reason:
            message += f": {reason}"
            details["reason"] = reason
        if model:
            details["model"] = model

        super().__init__(
            message=message,
            code=ErrorCode.AI_GENERATION_FAILED,
            status_code=502,
            details=details,
        )
