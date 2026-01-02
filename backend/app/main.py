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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events for the application.
    Use this for database connections, cache initialization, etc.
    """
    # Startup
    print(f"🚀 Starting DevBridge API v{settings.VERSION}")
    print(f"📍 Environment: {settings.ENVIRONMENT}")

    yield

    # Shutdown
    print("👋 Shutting down DevBridge API")


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

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API router
    app.include_router(api_router, prefix=settings.API_PREFIX)

    return app


# Create application instance
app = create_app()
