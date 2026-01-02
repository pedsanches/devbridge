"""
Health Check Endpoints.

Provides endpoints for monitoring application health.
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str
    version: str
    environment: str
    timestamp: str
    services: dict[str, str]


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns:
        HealthResponse: Current health status of the application.
    """
    # TODO: Add actual service health checks
    services = {
        "api": "healthy",
        "database": "unknown",  # Will be updated when DB is connected
        "redis": "unknown",
        "qdrant": "unknown",
    }

    return HealthResponse(
        status="healthy",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc).isoformat(),
        services=services,
    )


@router.get("/ready")
async def readiness_check() -> dict[str, Any]:
    """
    Kubernetes readiness probe.

    Returns:
        dict: Ready status for k8s.
    """
    return {"ready": True}


@router.get("/live")
async def liveness_check() -> dict[str, Any]:
    """
    Kubernetes liveness probe.

    Returns:
        dict: Alive status for k8s.
    """
    return {"alive": True}
