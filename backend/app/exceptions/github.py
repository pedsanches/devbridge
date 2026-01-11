"""
GitHub Exceptions Module.

Exceptions specific to GitHub integration errors.
"""

from typing import Any

from app.exceptions.base import DevBridgeError, ErrorCode


class GitHubError(DevBridgeError):
    """Base exception for GitHub-related errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.GITHUB_API_ERROR,
        status_code: int = 502,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=status_code,
            details=details,
        )


class GitHubAuthenticationError(GitHubError):
    """GitHub authentication failed (invalid or expired token)."""

    def __init__(
        self,
        message: str = "GitHub authentication failed. Please reconnect your GitHub account.",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            code=ErrorCode.GITHUB_AUTHENTICATION_FAILED,
            status_code=401,
            details=details,
        )


class GitHubRateLimitError(GitHubError):
    """GitHub API rate limit exceeded."""

    def __init__(
        self,
        reset_at: str | None = None,
        remaining: int = 0,
    ):
        message = "GitHub API rate limit exceeded"
        details: dict[str, Any] = {"remaining": remaining}
        if reset_at:
            message += f". Resets at {reset_at}"
            details["reset_at"] = reset_at

        super().__init__(
            message=message,
            code=ErrorCode.GITHUB_RATE_LIMITED,
            status_code=429,
            details=details,
        )


class GitHubNotFoundError(GitHubError):
    """GitHub resource not found."""

    def __init__(
        self,
        resource_type: str = "resource",
        resource_id: str | None = None,
    ):
        message = f"GitHub {resource_type} not found"
        details: dict[str, Any] = {"resource_type": resource_type}
        if resource_id:
            message += f": {resource_id}"
            details["resource_id"] = resource_id

        super().__init__(
            message=message,
            code=ErrorCode.GITHUB_NOT_FOUND,
            status_code=404,
            details=details,
        )


class GitHubSyncError(GitHubError):
    """Error during GitHub data synchronization."""

    def __init__(
        self,
        repository: str,
        operation: str = "sync",
        reason: str | None = None,
    ):
        message = f"Failed to {operation} repository '{repository}'"
        details: dict[str, Any] = {
            "repository": repository,
            "operation": operation,
        }
        if reason:
            message += f": {reason}"
            details["reason"] = reason

        super().__init__(
            message=message,
            code=ErrorCode.GITHUB_SYNC_FAILED,
            status_code=502,
            details=details,
        )
