"""
API Dependencies.

Shared dependencies for FastAPI endpoints.
Uses Dependency Injection pattern for database sessions, auth, etc.
"""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session.

    Yields:
        AsyncSession: Database session for the request.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Type alias for dependency injection
DbSession = Annotated[AsyncSession, Depends(get_db)]


# Placeholder for future auth dependency
async def get_current_user() -> dict[str, str]:
    """
    Get current authenticated user.

    Returns:
        User info dict (placeholder).
    """
    # TODO: Implement JWT validation
    return {"id": "placeholder", "email": "user@example.com"}


CurrentUser = Annotated[dict, Depends(get_current_user)]
