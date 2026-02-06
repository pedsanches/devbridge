"""
Authentication Service.

Business logic for magic link authentication and user session management.
"""

import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token
from app.models.magic_link import MagicLink
from app.models.membership import MemberRole, Membership
from app.models.organization import Organization, PlanType
from app.models.user import User
from app.services.email_service import send_magic_link_email


async def request_magic_link(db: AsyncSession, email: str) -> bool:
    """
    Request a magic link for authentication.

    Creates a magic link token, stores it in the database, and sends an email.
    If the user doesn't exist, they will be created on verification.

    Args:
        db: Database session.
        email: User's email address.

    Returns:
        True if magic link was sent successfully.
    """
    # Generate secure token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.MAGIC_LINK_EXPIRE_MINUTES)

    # Check if user exists
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    # Create magic link
    magic_link = MagicLink(
        email=email,
        token=token,
        expires_at=expires_at,
        user_id=user.id if user else None,
    )

    db.add(magic_link)
    await db.flush()

    # Send email
    success = send_magic_link_email(
        to_email=email,
        token=token,
        expires_in_minutes=settings.MAGIC_LINK_EXPIRE_MINUTES,
    )

    return success


async def verify_magic_link(db: AsyncSession, token: str) -> dict | None:
    """
    Verify a magic link token and return JWT.

    If user doesn't exist, creates user and personal organization.

    Args:
        db: Database session.
        token: Magic link token from email.

    Returns:
        Dict with access_token and user info, or None if invalid.
    """
    # Find magic link
    result = await db.execute(
        select(MagicLink).where(
            MagicLink.token == token,
            MagicLink.used_at.is_(None),
            MagicLink.expires_at > datetime.now(UTC),
        )
    )
    magic_link = result.scalar_one_or_none()

    if not magic_link:
        return None

    # Mark as used
    magic_link.used_at = datetime.now(UTC)

    # Get or create user
    result = await db.execute(select(User).where(User.email == magic_link.email))
    user = result.scalar_one_or_none()

    if not user:
        # Create new user
        user = User(
            email=magic_link.email,
            email_verified_at=datetime.now(UTC),
        )
        db.add(user)
        await db.flush()

        # Create personal organization
        org_slug = magic_link.email.split("@")[0].lower().replace(".", "-")[:50]
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
    else:
        # Update email verification if not already verified
        if not user.email_verified_at:
            user.email_verified_at = datetime.now(UTC)

    # Get user's default organization (first one they own or belong to)
    result = await db.execute(
        select(Membership)
        .where(Membership.user_id == user.id)
        .order_by(Membership.created_at.asc())
        .limit(1)
    )
    membership = result.scalar_one_or_none()

    if not membership:
        return None

    # Create JWT
    access_token = create_access_token(
        data={
            "sub": user.id,
            "email": user.email,
            "org_id": membership.organization_id,
            "role": membership.role.value,
        }
    )

    await db.refresh(user)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
        },
        "organization_id": membership.organization_id,
        "role": membership.role.value,
    }


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    """
    Get a user by ID.

    Args:
        db: Database session.
        user_id: User UUID.

    Returns:
        User if found, None otherwise.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
