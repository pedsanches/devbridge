"""
Observability Middleware.

Request tracing and metrics middleware for FastAPI.
"""

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.core.config import settings
from app.core.logging import bind_request_context, clear_context, get_logger
from app.core.observability import REQUEST_COUNT, REQUEST_LATENCY
from app.core.rate_limit import RateLimitResult, build_rate_limit_headers, rate_limiter

logger = get_logger(__name__)


class ObservabilityMiddleware(BaseHTTPMiddleware):  # type: ignore[misc]
    """Middleware that adds request tracing and metrics."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
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


class RateLimitMiddleware(BaseHTTPMiddleware):  # type: ignore[misc]
    """Middleware that enforces API rate limiting."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        api_prefix = settings.API_PREFIX
        self._exempt_prefixes = (
            "/metrics",
            "/health",
            "/ready",
            "/live",
            f"{api_prefix}/health",
            f"{api_prefix}/health/ready",
            f"{api_prefix}/health/live",
            f"{api_prefix}/docs",
            f"{api_prefix}/redoc",
            f"{api_prefix}/openapi.json",
        )

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Apply rate limiting before processing the request."""
        if request.method == "OPTIONS" or self._is_exempt(request.url.path):
            return await call_next(request)

        if settings.RATE_LIMIT_PER_MINUTE <= 0:
            return await call_next(request)

        client_id = self._get_client_id(request)
        key = f"rate_limit:global:{client_id}"
        result = await rate_limiter.check(key, settings.RATE_LIMIT_PER_MINUTE, 60)

        if not result.allowed:
            logger.warning("Rate limit exceeded", client_id=client_id, path=request.url.path)
            response = JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
            )
            self._apply_headers(response, result)
            retry_after = max(result.reset_at - int(time.time()), 0)
            response.headers["Retry-After"] = str(retry_after)
            return response

        response = await call_next(request)
        self._apply_headers(response, result)
        return response

    def _apply_headers(self, response: Response, result: RateLimitResult) -> None:
        response.headers.update(build_rate_limit_headers(result))

    def _is_exempt(self, path: str) -> bool:
        return any(path.startswith(prefix) for prefix in self._exempt_prefixes)

    @staticmethod
    def _get_client_id(request: Request) -> str:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return str(forwarded_for.split(",")[0].strip())
        if request.client:
            return str(request.client.host)
        return "unknown"
