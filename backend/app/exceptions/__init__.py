"""
DevBridge Exceptions Package.

Provides a standardized exception hierarchy for the application.
"""

from app.exceptions.ai import (
    AIContextTooLongError,
    AIGenerationError,
    AIInvalidResponseError,
    AIRateLimitError,
    AIServiceError,
)
from app.exceptions.base import (
    BusinessRuleError,
    ConflictError,
    DevBridgeError,
    ErrorCode,
    NotFoundError,
    PermissionDeniedError,
    RateLimitedError,
    ValidationError,
)
from app.exceptions.github import (
    GitHubAuthenticationError,
    GitHubError,
    GitHubNotFoundError,
    GitHubRateLimitError,
    GitHubSyncError,
)
from app.exceptions.handlers import error_response, register_exception_handlers

__all__ = [
    # Base
    "DevBridgeError",
    "ErrorCode",
    "NotFoundError",
    "ValidationError",
    "PermissionDeniedError",
    "RateLimitedError",
    "ConflictError",
    "BusinessRuleError",
    # GitHub
    "GitHubError",
    "GitHubAuthenticationError",
    "GitHubRateLimitError",
    "GitHubNotFoundError",
    "GitHubSyncError",
    # AI
    "AIServiceError",
    "AIRateLimitError",
    "AIInvalidResponseError",
    "AIContextTooLongError",
    "AIGenerationError",
    # Handlers
    "register_exception_handlers",
    "error_response",
]
