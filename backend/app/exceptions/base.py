"""
Base Exceptions Module.

Defines the base exception hierarchy for the DevBridge application.
All application-specific exceptions should inherit from DevBridgeError.
"""

from enum import Enum
from typing import Any


class ErrorCode(str, Enum):
    """Standardized error codes for API responses."""

    # Generic errors (1xxx)
    INTERNAL_ERROR = "E1000"
    VALIDATION_ERROR = "E1001"
    NOT_FOUND = "E1002"
    PERMISSION_DENIED = "E1003"
    RATE_LIMITED = "E1004"

    # Authentication/Authorization errors (2xxx)
    AUTHENTICATION_REQUIRED = "E2000"
    INVALID_TOKEN = "E2001"  # nosec B105
    TOKEN_EXPIRED = "E2002"  # nosec B105
    INSUFFICIENT_PERMISSIONS = "E2003"  # nosec B105

    # GitHub integration errors (3xxx)
    GITHUB_API_ERROR = "E3000"
    GITHUB_RATE_LIMITED = "E3001"
    GITHUB_NOT_FOUND = "E3002"
    GITHUB_AUTHENTICATION_FAILED = "E3003"
    GITHUB_SYNC_FAILED = "E3004"

    # AI service errors (4xxx)
    AI_SERVICE_ERROR = "E4000"
    AI_RATE_LIMITED = "E4001"
    AI_INVALID_RESPONSE = "E4002"
    AI_CONTEXT_TOO_LONG = "E4003"
    AI_GENERATION_FAILED = "E4004"

    # Database errors (5xxx)
    DATABASE_ERROR = "E5000"
    CONSTRAINT_VIOLATION = "E5001"
    TRANSACTION_FAILED = "E5002"

    # Business logic errors (6xxx)
    BUSINESS_RULE_VIOLATION = "E6000"
    INVALID_OPERATION = "E6001"
    RESOURCE_CONFLICT = "E6002"


class DevBridgeError(Exception):
    """
    Base exception for all DevBridge application errors.

    All custom exceptions should inherit from this class to ensure
    consistent error handling and response formatting.
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize the exception.

        Args:
            message: Human-readable error message.
            code: Standardized error code for programmatic handling.
            status_code: HTTP status code to return.
            details: Additional context about the error.
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for API response."""
        return {
            "error": {
                "code": self.code.value,
                "message": self.message,
                "details": self.details,
            }
        }


# =============================================================================
# Common Exceptions
# =============================================================================


class NotFoundError(DevBridgeError):
    """Resource not found."""

    def __init__(
        self,
        resource: str,
        identifier: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} with id '{identifier}' not found"
        super().__init__(
            message=message,
            code=ErrorCode.NOT_FOUND,
            status_code=404,
            details=details,
        )


class ValidationError(DevBridgeError):
    """Validation error for invalid input."""

    def __init__(
        self,
        message: str = "Validation error",
        field: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        error_details = details or {}
        if field:
            error_details["field"] = field
        super().__init__(
            message=message,
            code=ErrorCode.VALIDATION_ERROR,
            status_code=422,
            details=error_details,
        )


class PermissionDeniedError(DevBridgeError):
    """User does not have permission for the requested operation."""

    def __init__(
        self,
        message: str = "Permission denied",
        resource: str | None = None,
        action: str | None = None,
    ):
        details = {}
        if resource:
            details["resource"] = resource
        if action:
            details["action"] = action
        super().__init__(
            message=message,
            code=ErrorCode.PERMISSION_DENIED,
            status_code=403,
            details=details,
        )


class RateLimitedError(DevBridgeError):
    """Rate limit exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
    ):
        details = {}
        if retry_after:
            details["retry_after_seconds"] = retry_after
        super().__init__(
            message=message,
            code=ErrorCode.RATE_LIMITED,
            status_code=429,
            details=details,
        )


class ConflictError(DevBridgeError):
    """Resource conflict error."""

    def __init__(
        self,
        message: str = "Resource conflict",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            code=ErrorCode.RESOURCE_CONFLICT,
            status_code=409,
            details=details,
        )


class BusinessRuleError(DevBridgeError):
    """Business rule violation."""

    def __init__(
        self,
        message: str,
        rule: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        error_details = details or {}
        if rule:
            error_details["rule"] = rule
        super().__init__(
            message=message,
            code=ErrorCode.BUSINESS_RULE_VIOLATION,
            status_code=400,
            details=error_details,
        )
