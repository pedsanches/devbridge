"""
API Dependencies.

Shared dependencies for FastAPI endpoints.
Uses Dependency Injection pattern for database sessions, auth, etc.
"""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import async_session_factory
from app.models import User
from app.services import auth_service
from app.services.repository_service import DEFAULT_ORG_ID


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


async def get_session_token(
    request: Request,
    session: str | None = Cookie(default=None),
) -> str | None:
    """
    Get session token from httpOnly cookie or Authorization header.

    Supports both cookie-based (browser) and header-based (API) auth.
    """
    # First try httpOnly cookie
    if session:
        return session

    # Fallback to Authorization header for API clients
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]

    return None


async def get_current_user(
    db: DbSession,
    token: str | None = Depends(get_session_token),
) -> User | None:
    """
    Get current authenticated user from session cookie or JWT header.

    Returns:
        User if authenticated, None otherwise.
    """
    if not token:
        return None

    payload = decode_access_token(token)
    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    user = await auth_service.get_user_by_id(db, user_id)
    return user


async def get_current_user_required(
    user: User | None = Depends(get_current_user),
) -> User:
    """
    Require authenticated user. Raises 401 if not authenticated.

    Returns:
        Authenticated User.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_org_id(
    token: str | None = Depends(get_session_token),
) -> str:
    """
    Get current organization ID from session.

    Falls back to DEFAULT_ORG_ID if not authenticated (for development).

    Returns:
        Organization UUID string.
    """
    if not token:
        return DEFAULT_ORG_ID

    payload = decode_access_token(token)
    if not payload:
        return DEFAULT_ORG_ID

    return payload.get("org_id", DEFAULT_ORG_ID)


# Type aliases
CurrentUser = Annotated[User | None, Depends(get_current_user)]
CurrentUserRequired = Annotated[User, Depends(get_current_user_required)]
CurrentOrgId = Annotated[str, Depends(get_current_org_id)]
