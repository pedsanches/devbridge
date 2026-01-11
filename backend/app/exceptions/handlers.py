"""
Exception Handlers Module.

FastAPI exception handlers for unified error responses.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.exceptions.base import DevBridgeError

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all exception handlers for the FastAPI application.

    Args:
        app: FastAPI application instance.
    """

    @app.exception_handler(DevBridgeError)
    async def devbridge_exception_handler(
        req: Request,
        exc: DevBridgeError,
    ) -> JSONResponse:
        """
        Handle all DevBridge custom exceptions.

        Returns a standardized error response with error code and details.
        """
        logger.warning(
            f"DevBridge error: {exc.code.value} - {exc.message}",
            extra={
                "error_code": exc.code.value,
                "status_code": exc.status_code,
                "path": req.url.path,
                "details": exc.details,
            },
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        req: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """
        Handle Pydantic validation errors.

        Formats validation errors in a user-friendly way.
        """
        errors = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            errors.append(
                {
                    "field": field,
                    "message": error["msg"],
                    "type": error["type"],
                }
            )

        logger.info(
            f"Validation error on {req.url.path}",
            extra={"errors": errors},
        )

        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "E1001",
                    "message": "Validation error",
                    "details": {"errors": errors},
                }
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        _req: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        """
        Handle standard HTTP exceptions.

        Wraps them in our standard error format.
        """
        # Map common status codes to error codes
        error_codes: dict[int, str] = {
            400: "E1001",
            401: "E2000",
            403: "E1003",
            404: "E1002",
            405: "E1001",
            429: "E1004",
            500: "E1000",
            502: "E1000",
            503: "E1000",
        }

        code = error_codes.get(exc.status_code, "E1000")

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": code,
                    "message": exc.detail or "An error occurred",
                    "details": {},
                }
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        req: Request,
        exc: Exception,
    ) -> JSONResponse:
        """
        Handle all unhandled exceptions.

        Logs the full exception and returns a generic error response.
        This prevents internal details from leaking to clients.
        """
        logger.exception(
            f"Unhandled exception on {req.url.path}: {exc!s}",
            extra={"path": req.url.path, "method": req.method},
        )

        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "E1000",
                    "message": "An internal error occurred. Please try again later.",
                    "details": {},
                }
            },
        )


# =============================================================================
# Utility Functions
# =============================================================================


def error_response(
    code: str,
    message: str,
    status_code: int = 400,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    """
    Create a standardized error response.

    Args:
        code: Error code (e.g., "E1001").
        message: Human-readable error message.
        status_code: HTTP status code.
        details: Additional error details.

    Returns:
        JSONResponse with standardized error format.
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            }
        },
    )
