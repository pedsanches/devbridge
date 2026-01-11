"""
Observability Middleware.

Request tracing and metrics middleware for FastAPI.
"""

import time
import uuid
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import bind_request_context, clear_context, get_logger
from app.core.observability import REQUEST_COUNT, REQUEST_LATENCY

logger = get_logger(__name__)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Middleware that adds request tracing and metrics."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with tracing and metrics."""
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Extract user/org context from request state if available
        user_id = getattr(request.state, "user_id", None) if hasattr(request, "state") else None
        org_id = getattr(request.state, "org_id", None) if hasattr(request, "state") else None

        # Bind logging context
        bind_request_context(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            user_id=user_id,
            org_id=org_id,
        )

        # Start timing
        start_time = time.perf_counter()

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.perf_counter() - start_time

            # Record metrics
            endpoint = self._normalize_endpoint(request.url.path)
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=endpoint,
                status=str(response.status_code),
            ).inc()
            REQUEST_LATENCY.labels(
                method=request.method,
                endpoint=endpoint,
            ).observe(duration)

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            # Log request completion
            if response.status_code >= 400:
                logger.warning(
                    "Request completed with error",
                    status_code=response.status_code,
                    duration_ms=round(duration * 1000, 2),
                )
            else:
                logger.info(
                    "Request completed",
                    status_code=response.status_code,
                    duration_ms=round(duration * 1000, 2),
                )

            return response

        except Exception as e:
            # Record error metrics
            duration = time.perf_counter() - start_time
            endpoint = self._normalize_endpoint(request.url.path)
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=endpoint,
                status="500",
            ).inc()
            REQUEST_LATENCY.labels(
                method=request.method,
                endpoint=endpoint,
            ).observe(duration)

            logger.exception(
                "Request failed with exception",
                error=str(e),
                duration_ms=round(duration * 1000, 2),
            )
            raise

        finally:
            # Clear logging context
            clear_context()

    def _normalize_endpoint(self, path: str) -> str:
        """
        Normalize endpoint path for metrics.

        Replaces dynamic segments (UUIDs, numbers) with placeholders
        to prevent metric cardinality explosion.
        """
        import re

        # Replace UUIDs
        path = re.sub(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "{id}",
            path,
            flags=re.IGNORECASE,
        )
        # Replace numeric IDs
        path = re.sub(r"/\d+", "/{id}", path)
        return path
