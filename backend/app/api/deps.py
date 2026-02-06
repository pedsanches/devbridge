"""
API Dependencies.

Shared dependencies for FastAPI endpoints.
Uses Dependency Injection pattern for database sessions, auth, etc.
"""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlalchemy import text
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


async def get_db_with_rls(
    token: str | None = Depends(get_session_token),
) -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session with RLS context set.

    This sets the 'app.current_org_id' session variable that RLS policies use
    to filter rows by organization.

    Yields:
        AsyncSession: Database session with tenant context.
    """
    # Extract org_id from token
    org_id = DEFAULT_ORG_ID
    if token:
        payload = decode_access_token(token)
        if payload:
            org_id = payload.get("org_id", DEFAULT_ORG_ID)

    async with async_session_factory() as session:
        try:
            # Set the RLS session variable
            await session.execute(
                text("SET LOCAL app.current_org_id = :org_id"), {"org_id": org_id}
            )
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# RLS-aware type alias
DbSessionRLS = Annotated[AsyncSession, Depends(get_db_with_rls)]


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


async def get_current_user_with_role(
    db: DbSession,
    token: str | None = Depends(get_session_token),
) -> tuple[User, str, str] | None:
    """
    Get current user with their role in the current organization.

    Returns:
        Tuple of (User, org_id, role) if authenticated, None otherwise.
    """
    from app.models.membership import Membership

    if not token:
        return None

    payload = decode_access_token(token)
    if not payload:
        return None

    user_id = payload.get("sub")
    org_id = payload.get("org_id")
    if not user_id or not org_id:
        return None

    user = await auth_service.get_user_by_id(db, user_id)
    if not user:
        return None

    # Get the user's role in this org
    from sqlalchemy import select

    result = await db.execute(
        select(Membership).where(
            Membership.user_id == user_id,
            Membership.organization_id == org_id,
            Membership.team_id.is_(None),  # Org-level membership
        )
    )
    membership = result.scalar_one_or_none()

    if not membership:
        return None

    return (user, org_id, membership.role.value)


async def get_current_admin_required(
    user_with_role: tuple[User, str, str] | None = Depends(get_current_user_with_role),
) -> User:
    """
    Require authenticated user with ADMIN or OWNER role.

    Raises 401 if not authenticated, 403 if not admin/owner.

    Returns:
        Authenticated User with admin privileges.
    """
    if not user_with_role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user, _org_id, role = user_with_role

    if role not in ("admin", "owner"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    return user


# Type aliases
CurrentUser = Annotated[User | None, Depends(get_current_user)]
CurrentUserRequired = Annotated[User, Depends(get_current_user_required)]
CurrentOrgId = Annotated[str, Depends(get_current_org_id)]
CurrentAdminRequired = Annotated[User, Depends(get_current_admin_required)]
