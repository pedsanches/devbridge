"""
Health Endpoint Tests.

Tests for the health check endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient) -> None:
    """Test main health check endpoint."""
    response = await async_client.get("/api/v1/health")

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data
    assert "services" in data


@pytest.mark.asyncio
async def test_readiness_probe(async_client: AsyncClient) -> None:
    """Test Kubernetes readiness probe."""
    response = await async_client.get("/api/v1/health/ready")

    assert response.status_code == 200
    assert response.json()["ready"] is True


@pytest.mark.asyncio
async def test_liveness_probe(async_client: AsyncClient) -> None:
    """Test Kubernetes liveness probe."""
    response = await async_client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json()["alive"] is True
