"""
Structured Logging Module.

Configures structlog for structured JSON logging with context.
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor

from app.core.config import settings


def setup_logging(
    log_level: str | None = None,
    json_format: bool | None = None,
) -> None:
    """
    Configure structured logging for the application.

    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR). Defaults to settings.
        json_format: Whether to output JSON format. Defaults to non-DEBUG environments.
    """
    level = log_level or getattr(settings, "LOG_LEVEL", "INFO") or "INFO"
    is_json = json_format if json_format is not None else not getattr(settings, "DEBUG", False)

    # Shared processors for all logging
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if is_json:
        # Production: JSON output
        processors: list[Processor] = [
            *shared_processors,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Development: Colored console output
        processors = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard logging to use structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
    )

    # Set third-party loggers to WARNING to reduce noise
    for logger_name in ["httpx", "httpcore", "sqlalchemy.engine", "asyncio"]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger.

    Args:
        name: Logger name (defaults to caller's module).

    Returns:
        Configured structlog logger.
    """
    return structlog.get_logger(name)


def bind_context(**kwargs: Any) -> None:
    """
    Bind context variables to the current logging context.

    These will be included in all subsequent log entries.

    Args:
        **kwargs: Key-value pairs to bind.
    """
    structlog.contextvars.bind_contextvars(**kwargs)


def unbind_context(*keys: str) -> None:
    """
    Remove context variables from the current logging context.

    Args:
        *keys: Keys to unbind.
    """
    structlog.contextvars.unbind_contextvars(*keys)


def clear_context() -> None:
    """Clear all bound context variables."""
    structlog.contextvars.clear_contextvars()


# =============================================================================
# Request Context Middleware Helpers
# =============================================================================


def bind_request_context(
    request_id: str,
    method: str,
    path: str,
    user_id: str | None = None,
    org_id: str | None = None,
) -> None:
    """
    Bind request context for logging.

    Args:
        request_id: Unique request identifier.
        method: HTTP method.
        path: Request path.
        user_id: Optional user ID.
        org_id: Optional organization ID.
    """
    ctx: dict[str, Any] = {
        "request_id": request_id,
        "http_method": method,
        "http_path": path,
    }
    if user_id:
        ctx["user_id"] = user_id
    if org_id:
        ctx["org_id"] = org_id

    bind_context(**ctx)


# =============================================================================
# Logging Presets for Common Operations
# =============================================================================


class LogContext:
    """Context manager for scoped logging context."""

    def __init__(self, **kwargs: Any):
        self.context = kwargs

    def __enter__(self) -> "LogContext":
        bind_context(**self.context)
        return self

    def __exit__(self, *args: Any) -> None:
        unbind_context(*self.context.keys())


def log_operation(
    operation: str,
    repository: str | None = None,
    activity_id: str | None = None,
) -> LogContext:
    """
    Create a logging context for an operation.

    Usage:
        with log_operation("sync_repository", repository="owner/repo"):
            logger.info("Starting sync")
            ...
            logger.info("Sync complete")
    """
    ctx: dict[str, Any] = {"operation": operation}
    if repository:
        ctx["repository"] = repository
    if activity_id:
        ctx["activity_id"] = activity_id
    return LogContext(**ctx)
