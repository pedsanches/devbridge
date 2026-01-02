"""
Pytest Configuration and Fixtures.

Shared fixtures for all tests.
"""

from collections.abc import AsyncGenerator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def anyio_backend() -> str:
    """Specify asyncio backend for pytest-anyio."""
    return "asyncio"


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create async test client.

    Yields:
        AsyncClient: HTTP client for testing.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.fixture
def sample_repo_data() -> dict[str, Any]:
    """Sample repository creation data."""
    return {
        "url": "https://github.com/example/repo",
        "name": "Example Repo",
        "description": "A sample repository for testing",
    }
