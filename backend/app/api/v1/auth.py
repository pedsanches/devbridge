"""
Authentication Endpoints.

Magic link login with httpOnly cookie session management.
"""

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, EmailStr

from app.api.deps import CurrentOrgId, CurrentUserRequired, DbSession
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
    role: str


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
        role=result.get("role", "member"),
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    user: CurrentUserRequired,
    db: DbSession,
    current_org_id: CurrentOrgId,
) -> UserResponse:
    """
    Get the current authenticated user.
    """
    from sqlalchemy import select

    from app.models import Membership

    # Get membership for the current context (from token)
    result = await db.execute(
        select(Membership).where(
            Membership.user_id == user.id,
            Membership.organization_id == current_org_id,
            Membership.team_id.is_(None),
        )
    )
    membership = result.scalar_one_or_none()

    # If for some reason the context org is invalid (e.g. removed), fallback to first org
    if not membership:
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
        role=membership.role.value if membership else "member",
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
        role=membership.role.value,
    )


class InviteAcceptRequest(BaseModel):
    """Request schema for accepting an invitation."""

    token: str


class InviteAcceptResponse(BaseModel):
    """Response schema for accepted invitation."""

    id: str
    email: str
    name: str | None
    organization_id: str
    organization_name: str
    teams: list[str]


@router.post("/invite/accept", response_model=InviteAcceptResponse)
async def accept_invitation(
    db: DbSession,
    request: InviteAcceptRequest,
    response: Response,
) -> InviteAcceptResponse:
    """
    Accept an invitation to join an organization.

    This endpoint:
    1. Validates the invitation token (with FOR UPDATE lock)
    2. Creates or retrieves the user
    3. Creates the membership(s)
    4. Marks the invitation as accepted
    5. Sets the session cookie
    """
    from datetime import UTC, datetime

    from sqlalchemy import select, text

    from app.core.security import create_access_token
    from app.models import Organization, PendingInvitation, Team, User
    from app.models.invitation import InvitationStatus, hash_token
    from app.models.membership import MemberRole, Membership

    # Hash the token to find the invitation
    token_hashed = hash_token(request.token)

    # Lock the invitation row (FOR UPDATE) to prevent double-accept race condition
    result = await db.execute(
        select(PendingInvitation)
        .where(
            PendingInvitation.token_hash == token_hashed,
            PendingInvitation.status == InvitationStatus.PENDING,
            PendingInvitation.expires_at > datetime.now(UTC),
        )
        .with_for_update()
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=401,
            detail="Invalid, expired, or already used invitation",
        )

    # Get or create user
    user_result = await db.execute(select(User).where(User.email == invitation.email))
    user = user_result.scalar_one_or_none()

    if not user:
        # Create new user
        user = User(
            email=invitation.email,
            email_verified_at=datetime.now(UTC),
        )
        db.add(user)
        await db.flush()

    # Get organization
    org_result = await db.execute(
        select(Organization).where(Organization.id == invitation.organization_id)
    )
    org = org_result.scalar_one()

    # Determine role
    member_role = MemberRole.ADMIN if invitation.role == "admin" else MemberRole.MEMBER

    # Set RLS context for the organization we are joining
    # This is critical because RLS policies on 'memberships' will hide rows
    # if app.current_org_id does not match.
    await db.execute(
        text("SELECT set_config('app.current_org_id', :org_id, true)"),
        {"org_id": str(invitation.organization_id)},
    )

    # Create org-level membership (check if not already member)
    existing_membership = await db.execute(
        select(Membership).where(
            Membership.organization_id == invitation.organization_id,
            Membership.user_id == user.id,
            Membership.team_id.is_(None),
        )
    )
    if not existing_membership.scalar_one_or_none():
        org_membership = Membership(
            organization_id=invitation.organization_id,
            user_id=user.id,
            role=member_role,
        )
        db.add(org_membership)
        await db.flush()  # Ensure it is sent to DB (RLS checked here)

    # Create team memberships if specified
    team_names = []
    if invitation.team_ids:
        teams_result = await db.execute(select(Team).where(Team.id.in_(invitation.team_ids)))
        teams = list(teams_result.scalars().all())
        team_names = [t.name for t in teams]

        for team in teams:
            # Check if not already a member
            existing_team_membership = await db.execute(
                select(Membership).where(
                    Membership.organization_id == invitation.organization_id,
                    Membership.user_id == user.id,
                    Membership.team_id == team.id,
                )
            )
            if not existing_team_membership.scalar_one_or_none():
                team_membership = Membership(
                    organization_id=invitation.organization_id,
                    user_id=user.id,
                    team_id=team.id,
                    role=member_role,
                )
                db.add(team_membership)

    # Mark invitation as accepted
    invitation.accept(user.id)

    # Get the membership for the token
    membership_result = await db.execute(
        select(Membership).where(
            Membership.organization_id == invitation.organization_id,
            Membership.user_id == user.id,
            Membership.team_id.is_(None),
        )
    )
    membership = membership_result.scalar_one()

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
        secure=settings.ENVIRONMENT != "development",
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 7 days
    )

    await db.commit()
    await db.refresh(user)

    return InviteAcceptResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        organization_id=org.id,
        organization_name=org.name,
        teams=team_names,
    )


# ============================================================
# Organization Listing and Switching Endpoints
# ============================================================


class OrganizationSummary(BaseModel):
    """Summary of an organization the user belongs to."""

    id: str
    name: str
    slug: str
    role: str


class OrganizationsListResponse(BaseModel):
    """List of organizations for the current user."""

    organizations: list[OrganizationSummary]
    current_organization_id: str


class SwitchOrganizationRequest(BaseModel):
    """Request to switch organization context."""

    organization_id: str


@router.get("/organizations", response_model=OrganizationsListResponse)
async def list_user_organizations(
    user: CurrentUserRequired,
    db: DbSession,
    current_org_id: CurrentOrgId,
) -> OrganizationsListResponse:
    """
    List organizations the current user is a member of.
    """
    from sqlalchemy import select

    from app.models import Membership, Organization

    # Get all memberships for this user (org-level only, team_id is NULL)
    result = await db.execute(
        select(Membership, Organization)
        .join(Organization, Membership.organization_id == Organization.id)
        .where(
            Membership.user_id == user.id,
            Membership.team_id.is_(None),  # Only org-level memberships
        )
        .order_by(Membership.created_at.asc())
    )
    rows = result.all()

    organizations = [
        OrganizationSummary(
            id=org.id,
            name=org.name,
            slug=org.slug,
            role=membership.role.value,
        )
        for membership, org in rows
    ]

    return OrganizationsListResponse(
        organizations=organizations,
        current_organization_id=current_org_id,
    )


@router.post("/switch-org", response_model=UserResponse)
async def switch_organization(
    user: CurrentUserRequired,
    db: DbSession,
    request: SwitchOrganizationRequest,
    response: Response,
) -> UserResponse:
    """
    Switch the user's active organization context.

    Issues a new JWT scoped to the selected organization and sets the session cookie.
    """
    from sqlalchemy import select

    from app.core.security import create_access_token
    from app.models import Membership, Organization

    # Verify user is a member of the target organization
    result = await db.execute(
        select(Membership).where(
            Membership.user_id == user.id,
            Membership.organization_id == request.organization_id,
            Membership.team_id.is_(None),
        )
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this organization",
        )

    # Get org details for response
    org_result = await db.execute(
        select(Organization).where(Organization.id == request.organization_id)
    )
    org = org_result.scalar_one_or_none()

    if not org:
        raise HTTPException(
            status_code=404,
            detail="Organization not found",
        )

    # Create new JWT scoped to the new organization
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
        secure=settings.ENVIRONMENT != "development",
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 7 days
    )

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        organization_id=org.id,
        role=membership.role.value,
    )
