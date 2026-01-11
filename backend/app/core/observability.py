"""
Observability Module.

Configures OpenTelemetry tracing and Prometheus metrics for the application.
"""

import logging
from collections.abc import Callable, Generator
from contextlib import contextmanager
from functools import wraps
from typing import Any, TypeVar

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from prometheus_client import Counter, Gauge, Histogram, Info, generate_latest
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# OpenTelemetry Configuration
# =============================================================================

_tracer_provider: TracerProvider | None = None


def setup_tracing(service_name: str = "devbridge-backend") -> TracerProvider:
    """
    Configure OpenTelemetry tracing.

    Args:
        service_name: Name of the service for tracing.

    Returns:
        Configured TracerProvider.
    """
    global _tracer_provider

    if _tracer_provider is not None:
        return _tracer_provider

    # Create resource with service information
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": settings.VERSION if hasattr(settings, "VERSION") else "0.1.0",
            "deployment.environment": settings.ENVIRONMENT
            if hasattr(settings, "ENVIRONMENT")
            else "development",
        }
    )

    # Create tracer provider
    _tracer_provider = TracerProvider(resource=resource)

    # Configure exporters based on environment
    otlp_endpoint = getattr(settings, "OTLP_ENDPOINT", None)

    if otlp_endpoint:
        # Production: Export to OTLP collector (Jaeger, Tempo, etc.)
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        _tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        logger.info(f"Tracing configured with OTLP exporter to {otlp_endpoint}")
    else:
        # Development: Log to console
        if settings.DEBUG if hasattr(settings, "DEBUG") else False:
            console_exporter = ConsoleSpanExporter()
            _tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))
            logger.info("Tracing configured with console exporter (DEBUG mode)")

    # Set as global tracer provider
    trace.set_tracer_provider(_tracer_provider)

    return _tracer_provider


def instrument_app(app: Any) -> None:
    """
    Instrument FastAPI application with OpenTelemetry.

    Args:
        app: FastAPI application instance.
    """
    # Ensure tracing is set up
    setup_tracing()

    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)

    # Instrument HTTP client (httpx)
    HTTPXClientInstrumentor().instrument()

    logger.info("FastAPI and HTTPX instrumented for tracing")


def instrument_database(engine: Any) -> None:
    """
    Instrument SQLAlchemy engine for tracing.

    Args:
        engine: SQLAlchemy engine instance.
    """
    SQLAlchemyInstrumentor().instrument(engine=engine)
    logger.info("SQLAlchemy instrumented for tracing")


def get_tracer(name: str = "devbridge") -> trace.Tracer:
    """Get a tracer for the given name."""
    return trace.get_tracer(name)


# =============================================================================
# Custom Span Helpers
# =============================================================================

T = TypeVar("T")


def traced(
    span_name: str | None = None,
    attributes: dict[str, Any] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to add tracing to a function.

    Args:
        span_name: Name of the span (defaults to function name).
        attributes: Additional attributes to add to the span.

    Usage:
        @traced("my_operation")
        def my_function():
            ...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            tracer = get_tracer()
            name = span_name or func.__name__
            with tracer.start_as_current_span(name) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                return await func(*args, **kwargs)  # type: ignore[misc]

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            tracer = get_tracer()
            name = span_name or func.__name__
            with tracer.start_as_current_span(name) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                return func(*args, **kwargs)

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator


@contextmanager
def span(name: str, attributes: dict[str, Any] | None = None) -> Generator[trace.Span, None, None]:
    """
    Context manager for creating a span.

    Usage:
        with span("my_operation", {"key": "value"}) as s:
            s.set_attribute("result", "success")
    """
    tracer = get_tracer()
    with tracer.start_as_current_span(name) as s:
        if attributes:
            for key, value in attributes.items():
                s.set_attribute(key, value)
        yield s


# =============================================================================
# Prometheus Metrics
# =============================================================================

# Application info
APP_INFO = Info("devbridge", "DevBridge application information")

# Request metrics
REQUEST_COUNT = Counter(
    "devbridge_requests_total",
    "Total number of requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "devbridge_request_duration_seconds",
    "Request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# Business metrics
SYNC_OPERATIONS = Counter(
    "devbridge_sync_operations_total",
    "Total sync operations",
    ["operation", "status"],
)

AI_GENERATIONS = Counter(
    "devbridge_ai_generations_total",
    "Total AI generation requests",
    ["operation", "status"],
)

AI_GENERATION_LATENCY = Histogram(
    "devbridge_ai_generation_duration_seconds",
    "AI generation latency in seconds",
    ["operation"],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
)

ACTIVE_USERS = Gauge(
    "devbridge_active_users",
    "Number of active users",
    ["organization"],
)

ACTIVITIES_PROCESSED = Counter(
    "devbridge_activities_processed_total",
    "Total activities processed",
    ["type", "repository"],
)


def setup_metrics() -> None:
    """Initialize application metrics with info."""
    APP_INFO.info(
        {
            "version": settings.VERSION if hasattr(settings, "VERSION") else "0.1.0",
            "environment": settings.ENVIRONMENT
            if hasattr(settings, "ENVIRONMENT")
            else "development",
        }
    )


async def metrics_endpoint(_request: Request) -> Response:
    """Prometheus metrics endpoint handler."""
    return Response(
        content=generate_latest(),
        media_type="text/plain; charset=utf-8",
    )


# =============================================================================
# Convenience Functions for Business Metrics
# =============================================================================


def record_sync_operation(operation: str, success: bool = True) -> None:
    """Record a sync operation metric."""
    SYNC_OPERATIONS.labels(operation=operation, status="success" if success else "error").inc()


def record_ai_generation(operation: str, duration_seconds: float, success: bool = True) -> None:
    """Record an AI generation metric."""
    AI_GENERATIONS.labels(operation=operation, status="success" if success else "error").inc()
    AI_GENERATION_LATENCY.labels(operation=operation).observe(duration_seconds)


def record_activity_processed(activity_type: str, repository: str) -> None:
    """Record an activity processing metric."""
    ACTIVITIES_PROCESSED.labels(type=activity_type, repository=repository).inc()
