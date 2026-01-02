"""
Exception Handlers.

Custom exception handlers for the FastAPI application.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class DevBridgeException(Exception):
    """Base exception for DevBridge."""

    def __init__(
        self,
        message: str,
        code: str = "DEVBRIDGE_ERROR",
        status_code: int = 500,
    ) -> None:
        """Initialize exception."""
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(DevBridgeException):
    """Resource not found."""

    def __init__(self, resource: str, resource_id: str) -> None:
        """Initialize not found error."""
        super().__init__(
            message=f"{resource} with id '{resource_id}' not found",
            code="NOT_FOUND",
            status_code=404,
        )


class ValidationError(DevBridgeException):
    """Validation error."""

    def __init__(self, message: str) -> None:
        """Initialize validation error."""
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
        )


class AuthenticationError(DevBridgeException):
    """Authentication failed."""

    def __init__(self, message: str = "Authentication required") -> None:
        """Initialize auth error."""
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=401,
        )


class AuthorizationError(DevBridgeException):
    """Authorization failed."""

    def __init__(self, message: str = "Permission denied") -> None:
        """Initialize authz error."""
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            status_code=403,
        )


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register custom exception handlers.

    Args:
        app: FastAPI application instance.
    """

    @app.exception_handler(DevBridgeException)
    async def devbridge_exception_handler(
        request: Request,
        exc: DevBridgeException,
    ) -> JSONResponse:
        """Handle DevBridge exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.message,
                "code": exc.code,
            },
        )
