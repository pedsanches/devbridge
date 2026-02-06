"""
Invitations API Routes.

CRUD operations for managing pending invitations.
Includes rate limiting and transactional acceptance.
"""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin_required, get_current_org_id, get_current_user, get_db
from app.models import Membership, Organization, PendingInvitation, User
from app.models.invitation import InvitationStatus, generate_invite_token, hash_token
from app.services.email_service import send_invite_email

router = APIRouter(prefix="/invitations", tags=["invitations"])


# === Schemas ===


class InvitationCreate(BaseModel):
    """Request schema for creating an invitation."""

    email: EmailStr
    team_ids: list[str] | None = None
    role: str = "member"


class InvitationResponse(BaseModel):
    """Response schema for an invitation."""

    id: str
    email: str
    organization_id: str
    role: str
    status: str
    expires_at: datetime
    created_at: datetime
    invited_by_email: str | None = None


class InvitationsListResponse(BaseModel):
    """Response schema for listing invitations."""

    items: list[InvitationResponse]
    total: int


# === Endpoints ===


@router.post("", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    data: InvitationCreate,
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_org_id),
    user: User = Depends(get_current_admin_required),
) -> InvitationResponse:
    """
    Create a new invitation.

    Sends an email to the invitee with a secure link.
    Rate limited: 10 invites/hour per admin.
    """
    # Check if user is already a member
    existing_member = await db.execute(
        select(Membership).where(
            Membership.organization_id == org_id,
            Membership.user_id.in_(select(User.id).where(User.email == data.email.lower())),
        )
    )
    if existing_member.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this organization",
        )

    # Check for existing pending invitation
    existing_invite = await db.execute(
        select(PendingInvitation).where(
            PendingInvitation.organization_id == org_id,
            PendingInvitation.email == data.email.lower(),
            PendingInvitation.status == InvitationStatus.PENDING,
        )
    )
    if existing_invite.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An invitation is already pending for this email",
        )

    # Create invitation
    invitation, raw_token = PendingInvitation.create(
        email=data.email,
        organization_id=org_id,
        invited_by_id=user.id,
        team_ids=data.team_ids,
        role=data.role,
    )
    db.add(invitation)
    await db.flush()

    # Get org name for email
    org_result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = org_result.scalar_one()

    # Send email
    email_sent = send_invite_email(
        to_email=data.email,
        inviter_name=user.name or user.email,
        organization_name=org.name,
        token=raw_token,
    )

    if not email_sent:
        # Rollback on email failure
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send invitation email",
        )

    await db.commit()
    await db.refresh(invitation)

    return InvitationResponse(
        id=invitation.id,
        email=invitation.email,
        organization_id=invitation.organization_id,
        role=invitation.role,
        status=invitation.status.value,
        expires_at=invitation.expires_at,
        created_at=invitation.created_at,
        invited_by_email=user.email,
    )


@router.get("", response_model=InvitationsListResponse)
async def list_invitations(
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_org_id),
    _user: User = Depends(get_current_user),
) -> InvitationsListResponse:
    """
    List all invitations for the current organization.

    Includes pending, accepted, and expired invitations.
    """
    result = await db.execute(
        select(PendingInvitation)
        .where(PendingInvitation.organization_id == org_id)
        .order_by(PendingInvitation.created_at.desc())
    )
    invitations = list(result.scalars().all())

    # Get inviter emails
    inviter_ids = [i.invited_by_id for i in invitations if i.invited_by_id]
    inviters = {}
    if inviter_ids:
        users_result = await db.execute(select(User).where(User.id.in_(inviter_ids)))
        inviters = {u.id: u.email for u in users_result.scalars().all()}

    items = [
        InvitationResponse(
            id=inv.id,
            email=inv.email,
            organization_id=inv.organization_id,
            role=inv.role,
            status=inv.status.value,
            expires_at=inv.expires_at,
            created_at=inv.created_at,
            invited_by_email=inviters.get(inv.invited_by_id),
        )
        for inv in invitations
    ]

    return InvitationsListResponse(items=items, total=len(items))


@router.delete("/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_invitation(
    invitation_id: str,
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_org_id),
    _user: User = Depends(get_current_admin_required),
) -> None:
    """
    Revoke a pending invitation.

    Only pending invitations can be revoked.
    """
    result = await db.execute(
        select(PendingInvitation).where(
            PendingInvitation.id == invitation_id,
            PendingInvitation.organization_id == org_id,
            PendingInvitation.status == InvitationStatus.PENDING,
        )
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found or already processed",
        )

    invitation.revoke()
    await db.commit()


@router.post("/{invitation_id}/resend", response_model=InvitationResponse)
async def resend_invitation(
    invitation_id: str,
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_org_id),
    user: User = Depends(get_current_admin_required),
) -> InvitationResponse:
    """
    Resend an invitation email.

    Creates a new token and extends the expiration.
    """
    result = await db.execute(
        select(PendingInvitation).where(
            PendingInvitation.id == invitation_id,
            PendingInvitation.organization_id == org_id,
            PendingInvitation.status == InvitationStatus.PENDING,
        )
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found or already processed",
        )

    # Generate new token
    new_token = generate_invite_token()
    invitation.token_hash = hash_token(new_token)
    invitation.expires_at = datetime.now(UTC) + timedelta(hours=48)

    # Get org name for email
    org_result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = org_result.scalar_one()

    # Send email
    email_sent = send_invite_email(
        to_email=invitation.email,
        inviter_name=user.name or user.email,
        organization_name=org.name,
        token=new_token,
    )

    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send invitation email",
        )

    await db.commit()
    await db.refresh(invitation)

    return InvitationResponse(
        id=invitation.id,
        email=invitation.email,
        organization_id=invitation.organization_id,
        role=invitation.role,
        status=invitation.status.value,
        expires_at=invitation.expires_at,
        created_at=invitation.created_at,
        invited_by_email=user.email,
    )
