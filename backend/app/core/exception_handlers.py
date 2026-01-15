"""
Exception Handlers for FastAPI.

Centralizes exception handling to ensure consistent error responses.
"""

import uuid
from typing import Any

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from app.core.errors import (
    DevBridgeError,
    ErrorCategory,
    ErrorResponse,
)

logger = structlog.get_logger(__name__)


def get_trace_id(request: Request) -> str:
    """Get trace_id from request state or generate one."""
    # Try to get from request state (set by middleware)
    if hasattr(request.state, "trace_id"):
        return str(request.state.trace_id)
    # Fallback to X-Request-ID header
    return request.headers.get("X-Request-ID", str(uuid.uuid4()))


def create_error_response(
    request: Request,
    error_code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> ErrorResponse:
    """Create standardized error response."""
    return ErrorResponse(
        error_id=str(uuid.uuid4()),
        trace_id=get_trace_id(request),
        error_code=error_code,
        message=message,
        details=details,
        path=str(request.url.path),
    )


async def devbridge_error_handler(
    request: Request,
    exc: DevBridgeError,
) -> JSONResponse:
    """Handle DevBridge custom exceptions."""
    error_response = create_error_response(
        request=request,
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
    )

    logger.warning(
        "DevBridge error",
        error_code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        trace_id=error_response.trace_id,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode="json"),
        headers={"X-Trace-ID": error_response.trace_id},
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException | StarletteHTTPException,
) -> JSONResponse:
    """Handle FastAPI/Starlette HTTPException with standardized format."""
    # Map HTTP status to error code
    error_code_map = {
        400: ErrorCategory.VALIDATION_FAILED.value,
        401: ErrorCategory.AUTH_UNAUTHORIZED.value,
        403: ErrorCategory.AUTH_FORBIDDEN.value,
        404: ErrorCategory.RESOURCE_NOT_FOUND.value,
        422: ErrorCategory.VALIDATION_FAILED.value,
        429: ErrorCategory.RATE_LIMIT_EXCEEDED.value,
        500: ErrorCategory.INTERNAL_ERROR.value,
        502: ErrorCategory.INTERNAL_ERROR.value,
        503: ErrorCategory.INTERNAL_ERROR.value,
    }

    error_code = error_code_map.get(exc.status_code, ErrorCategory.INTERNAL_ERROR.value)

    error_response = create_error_response(
        request=request,
        error_code=error_code,
        message=str(exc.detail),
    )

    if exc.status_code >= 500:
        logger.error(
            "HTTP error",
            error_code=error_code,
            message=str(exc.detail),
            status_code=exc.status_code,
            trace_id=error_response.trace_id,
        )
    else:
        logger.warning(
            "HTTP error",
            error_code=error_code,
            message=str(exc.detail),
            status_code=exc.status_code,
            trace_id=error_response.trace_id,
        )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode="json"),
        headers={"X-Trace-ID": error_response.trace_id},
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle Pydantic validation errors with standardized format."""
    # Extract validation errors
    errors = exc.errors()
    details = {
        "validation_errors": [
            {
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
            for error in errors
        ]
    }

    error_response = create_error_response(
        request=request,
        error_code=ErrorCategory.VALIDATION_FAILED.value,
        message="Request validation failed",
        details=details,
    )

    logger.warning(
        "Validation error",
        error_count=len(errors),
        trace_id=error_response.trace_id,
    )

    return JSONResponse(
        status_code=422,
        content=error_response.model_dump(mode="json"),
        headers={"X-Trace-ID": error_response.trace_id},
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle unexpected exceptions with standardized format."""
    error_response = create_error_response(
        request=request,
        error_code=ErrorCategory.INTERNAL_ERROR.value,
        message="An unexpected error occurred",
    )

    logger.exception(
        "Unhandled exception",
        error_type=type(exc).__name__,
        error_message=str(exc),
        trace_id=error_response.trace_id,
    )

    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(mode="json"),
        headers={"X-Trace-ID": error_response.trace_id},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI app."""
    app.add_exception_handler(DevBridgeError, devbridge_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)
