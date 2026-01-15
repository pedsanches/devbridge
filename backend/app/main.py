"""
DevBridge Backend API - Main Application Entry Point.

This module configures and creates the FastAPI application instance
with all routes, middleware, and lifecycle events.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.core.middleware import ObservabilityMiddleware, RateLimitMiddleware
from app.core.observability import (
    instrument_app,
    metrics_endpoint,
    setup_metrics,
    setup_tracing,
)

# Initialize structured logging early
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events for the application.
    Use this for database connections, cache initialization, etc.
    """
    # Startup
    logger.info(
        "Starting DevBridge API",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
    )

    # Initialize observability
    setup_tracing()
    setup_metrics()

    yield

    # Shutdown
    logger.info("Shutting down DevBridge API")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="Making Technical Work Visible to Non-Technical Stakeholders via AI Translation",
        version=settings.VERSION,
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        docs_url=f"{settings.API_PREFIX}/docs",
        redoc_url=f"{settings.API_PREFIX}/redoc",
        lifespan=lifespan,
    )

    # Observability Middleware (first in chain for accurate timing)
    app.add_middleware(ObservabilityMiddleware)

    # Rate Limiting Middleware
    app.add_middleware(RateLimitMiddleware)

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Instrument app for tracing
    instrument_app(app)

    # Register standardized exception handlers
    register_exception_handlers(app)

    # Include API router
    app.include_router(api_router, prefix=settings.API_PREFIX)

    # Metrics endpoint (outside API prefix for Prometheus scraping)
    app.add_route("/metrics", metrics_endpoint, methods=["GET"])

    # Health check endpoints
    @app.get("/health")
    async def health_check() -> dict:
        """Basic health check endpoint."""
        return {"status": "healthy", "version": settings.VERSION}

    @app.get("/ready")
    async def readiness_check() -> dict:
        """Readiness check endpoint."""
        # TODO: Add database connectivity check
        return {"status": "ready"}

    return app


# Create application instance
app = create_app()
