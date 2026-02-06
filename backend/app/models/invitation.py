"""
Pending Invitation Model.

Stores invitations for users to join an organization/team.
Implements a secure state machine for invite lifecycle.
"""

import enum
import hashlib
import secrets
from datetime import datetime, timedelta

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class InvitationStatus(str, enum.Enum):
    """Status of an invitation."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"


def generate_invite_token() -> str:
    """Generate a secure random token for invitation links."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Hash a token using SHA-256 for secure storage."""
    return hashlib.sha256(token.encode()).hexdigest()


class PendingInvitation(Base, UUIDMixin, TimestampMixin):
    """Pending Invitation model.

    Stores invitations for users to join an organization.
    Security features:
    - Token is hashed (original only sent via email)
    - 48-hour expiration by default
    - Single-use (status transitions to ACCEPTED)
    - Audit trail (invited_by_id, accepted_by_id)
    """

    __tablename__ = "pending_invitations"

    # Target
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Organization & Teams
    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    team_ids: Mapped[list[str] | None] = mapped_column(
        ARRAY(UUID(as_uuid=False)),
        nullable=True,
    )

    # Role assigned upon acceptance
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="member",
    )

    # Security
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # State Machine
    status: Mapped[InvitationStatus] = mapped_column(
        Enum(InvitationStatus),
        nullable=False,
        default=InvitationStatus.PENDING,
    )

    # Audit
    invited_by_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    accepted_by_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    organization = relationship("Organization")
    invited_by = relationship("User", foreign_keys=[invited_by_id])
    accepted_by = relationship("User", foreign_keys=[accepted_by_id])

    # Indexes
    __table_args__ = (
        # Partial unique index: only one pending invite per org+email
        Index(
            "ix_pending_invite_unique",
            "organization_id",
            "email",
            unique=True,
            postgresql_where=(status == InvitationStatus.PENDING),
        ),
        # Index for cleanup jobs
        Index("ix_pending_invite_expires", "expires_at", "status"),
    )

    @classmethod
    def create(
        cls,
        email: str,
        organization_id: str,
        invited_by_id: str,
        team_ids: list[str] | None = None,
        role: str = "member",
        expires_in_hours: int = 48,
    ) -> tuple["PendingInvitation", str]:
        """
        Factory method to create a new invitation.

        Returns:
            Tuple of (invitation_instance, raw_token).
            The raw_token must be sent via email; only the hash is stored.
        """
        raw_token = generate_invite_token()
        token_hashed = hash_token(raw_token)

        invitation = cls(
            email=email.lower().strip(),
            organization_id=organization_id,
            team_ids=team_ids,
            role=role,
            token_hash=token_hashed,
            expires_at=datetime.now() + timedelta(hours=expires_in_hours),
            status=InvitationStatus.PENDING,
            invited_by_id=invited_by_id,
        )

        return invitation, raw_token

    def is_valid(self) -> bool:
        """Check if the invitation is still valid (pending and not expired)."""
        return self.status == InvitationStatus.PENDING and self.expires_at > datetime.now()

    def accept(self, user_id: str) -> None:
        """Mark the invitation as accepted."""
        self.status = InvitationStatus.ACCEPTED
        self.accepted_at = datetime.now()
        self.accepted_by_id = user_id

    def revoke(self) -> None:
        """Revoke the invitation."""
        self.status = InvitationStatus.REVOKED

    def __repr__(self) -> str:
        return f"<PendingInvitation {self.email} -> {self.organization_id} ({self.status.value})>"
