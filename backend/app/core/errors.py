"""
Standardized Error Response Models.

Provides consistent error response format with tracing support.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ErrorCategory(str, Enum):
    """Error category codes for classification."""

    # Authentication & Authorization
    AUTH_INVALID_TOKEN = "AUTH_001"
    AUTH_EXPIRED_TOKEN = "AUTH_002"
    AUTH_UNAUTHORIZED = "AUTH_003"
    AUTH_FORBIDDEN = "AUTH_004"

    # Validation
    VALIDATION_FAILED = "VAL_001"
    VALIDATION_MISSING_FIELD = "VAL_002"
    VALIDATION_INVALID_FORMAT = "VAL_003"

    # Resource
    RESOURCE_NOT_FOUND = "RES_001"
    RESOURCE_ALREADY_EXISTS = "RES_002"
    RESOURCE_CONFLICT = "RES_003"

    # External Services
    EXTERNAL_GITHUB_ERROR = "EXT_001"
    EXTERNAL_LLM_ERROR = "EXT_002"
    EXTERNAL_DB_ERROR = "EXT_003"
    EXTERNAL_REDIS_ERROR = "EXT_004"

    # Rate Limiting
    RATE_LIMIT_EXCEEDED = "RATE_001"

    # Internal
    INTERNAL_ERROR = "INT_001"
    INTERNAL_TIMEOUT = "INT_002"


class ErrorResponse(BaseModel):
    """
    Standardized error response format.

    All API errors should use this format for consistency and traceability.
    """

    error_id: str = Field(
        description="Unique identifier for this error instance (UUID)",
    )
    trace_id: str = Field(
        description="Request trace ID for correlation across services",
    )
    error_code: str = Field(
        description="Semantic error code (e.g., AUTH_001, VAL_002)",
    )
    message: str = Field(
        description="Human-readable error message",
    )
    details: dict[str, Any] | None = Field(
        default=None,
        description="Additional technical context (optional)",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Error occurrence timestamp (UTC)",
    )
    path: str = Field(
        description="API endpoint that generated the error",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "error_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "trace_id": "req-xyz-123",
                "error_code": "AUTH_001",
                "message": "Invalid authentication token",
                "details": {"reason": "Token expired"},
                "timestamp": "2025-01-15T14:30:00Z",
                "path": "/api/v1/users/me",
            }
        }
    }


class DevBridgeError(Exception):
    """
    Base exception for DevBridge application errors.

    Provides structured error information for API responses.
    """

    def __init__(
        self,
        message: str,
        error_code: ErrorCategory | str = ErrorCategory.INTERNAL_ERROR,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.error_code = error_code.value if isinstance(error_code, ErrorCategory) else error_code
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class NotFoundError(DevBridgeError):
    """Resource not found error."""

    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: str | None = None,
        resource_id: str | None = None,
    ):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        super().__init__(
            message=message,
            error_code=ErrorCategory.RESOURCE_NOT_FOUND,
            status_code=404,
            details=details or None,
        )


class ValidationError(DevBridgeError):
    """Validation error."""

    def __init__(
        self,
        message: str = "Validation failed",
        field: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        error_details = details or {}
        if field:
            error_details["field"] = field
        super().__init__(
            message=message,
            error_code=ErrorCategory.VALIDATION_FAILED,
            status_code=422,
            details=error_details or None,
        )


class AuthenticationError(DevBridgeError):
    """Authentication error."""

    def __init__(
        self,
        message: str = "Authentication required",
        error_code: ErrorCategory = ErrorCategory.AUTH_UNAUTHORIZED,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=401,
        )


class AuthorizationError(DevBridgeError):
    """Authorization error."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(
            message=message,
            error_code=ErrorCategory.AUTH_FORBIDDEN,
            status_code=403,
        )


class ExternalServiceError(DevBridgeError):
    """External service error."""

    def __init__(
        self,
        message: str,
        service: str,
        error_code: ErrorCategory = ErrorCategory.INTERNAL_ERROR,
        details: dict[str, Any] | None = None,
    ):
        error_details = details or {}
        error_details["service"] = service
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=502,
            details=error_details,
        )
