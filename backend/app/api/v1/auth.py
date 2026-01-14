"""
Authentication Endpoints.

Magic link login with httpOnly cookie session management.
"""

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, EmailStr

from app.api.deps import CurrentUserRequired, DbSession
from app.core.config import settings
from app.services import auth_service

router = APIRouter()


class MagicLinkRequest(BaseModel):
    """Request schema for magic link."""

    email: EmailStr


class MagicLinkResponse(BaseModel):
    """Response schema for magic link request."""

    message: str
    email: str


class VerifyRequest(BaseModel):
    """Request schema for token verification."""

    token: str


class UserResponse(BaseModel):
    """Response schema for current user."""

    id: str
    email: str
    name: str | None
    organization_id: str


@router.post("/magic", response_model=MagicLinkResponse)
async def request_magic_link(db: DbSession, request: MagicLinkRequest) -> MagicLinkResponse:
    """
    Request a magic link for passwordless authentication.

    A magic link will be sent to the provided email address.
    The link expires in 15 minutes.
    """
    success = await auth_service.request_magic_link(db, request.email)

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to send magic link email",
        )

    return MagicLinkResponse(
        message="Magic link sent! Check your email.",
        email=request.email,
    )


@router.post("/verify")
async def verify_magic_link(
    db: DbSession,
    request: VerifyRequest,
    response: Response,
) -> UserResponse:
    """
    Verify a magic link token and set httpOnly cookie.

    If the user doesn't exist, a new account and personal organization
    will be created automatically.
    """
    result = await auth_service.verify_magic_link(db, request.token)

    if not result:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired magic link",
        )

    # Set httpOnly cookie instead of returning token in body
    response.set_cookie(
        key="session",
        value=result["access_token"],
        httponly=True,
        secure=settings.ENVIRONMENT != "development",
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 7 days
    )

    return UserResponse(
        id=result["user"]["id"],
        email=result["user"]["email"],
        name=result["user"]["name"],
        organization_id=result["organization_id"],
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(user: CurrentUserRequired, db: DbSession) -> UserResponse:
    """
    Get the current authenticated user.
    """
    # Get user's default organization
    from sqlalchemy import select

    from app.models import Membership

    result = await db.execute(
        select(Membership)
        .where(Membership.user_id == user.id)
        .order_by(Membership.created_at.asc())
        .limit(1)
    )
    membership = result.scalar_one_or_none()

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        organization_id=membership.organization_id if membership else "",
    )


@router.post("/logout")
async def logout(response: Response) -> dict:
    """
    Logout by clearing the session cookie.
    """
    response.delete_cookie(
        key="session",
        httponly=True,
        secure=settings.ENVIRONMENT != "development",
        samesite="lax",
    )
    return {"message": "Logged out successfully"}


class DevLoginRequest(BaseModel):
    """Request schema for dev login (development only)."""

    email: EmailStr = "test@example.com"


@router.post("/dev-login")
async def dev_login(
    db: DbSession,
    response: Response,
    request: DevLoginRequest = DevLoginRequest(),
) -> UserResponse:
    """
    Development-only login endpoint.

    Bypasses magic link email for faster testing.
    Only works when ENVIRONMENT=development.

    Default test email: test@devbridge.local
    """
    if settings.ENVIRONMENT != "development":
        raise HTTPException(
            status_code=403,
            detail="Dev login is only available in development environment",
        )

    # Use the auth service to create/get user and generate token
    # We'll create a simplified version that doesn't require email
    import secrets
    from datetime import UTC, datetime

    from sqlalchemy import select

    from app.core.security import create_access_token
    from app.models.membership import MemberRole, Membership
    from app.models.organization import Organization, PlanType
    from app.models.user import User

    email = request.email

    # Get or create user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        # Create new user
        user = User(
            email=email,
            name="Test User",
            email_verified_at=datetime.now(UTC),
        )
        db.add(user)
        await db.flush()

        # Create personal organization
        org_slug = email.split("@")[0].lower().replace(".", "-")[:50]
        org = Organization(
            name=f"{org_slug}'s Organization",
            slug=f"{org_slug}-{secrets.token_hex(4)}",
            plan=PlanType.FREE,
        )
        db.add(org)
        await db.flush()

        # Create owner membership
        membership = Membership(
            organization_id=org.id,
            user_id=user.id,
            role=MemberRole.OWNER,
        )
        db.add(membership)
        await db.flush()

    # Get user's membership
    result = await db.execute(
        select(Membership)
        .where(Membership.user_id == user.id)
        .order_by(Membership.created_at.asc())
        .limit(1)
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=500,
            detail="Failed to create user membership",
        )

    # Create JWT
    access_token = create_access_token(
        data={
            "sub": user.id,
            "email": user.email,
            "org_id": membership.organization_id,
            "role": membership.role.value,
        }
    )

    # Set httpOnly cookie
    response.set_cookie(
        key="session",
        value=access_token,
        httponly=True,
        secure=False,  # Dev only
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 7 days
    )

    await db.commit()
    await db.refresh(user)

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        organization_id=membership.organization_id,
    )
