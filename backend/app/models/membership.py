"""
Membership Model.

Represents the relationship between User and Organization/Team with roles.
"""

import enum

from sqlalchemy import Enum, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class MemberRole(str, enum.Enum):
    """Role levels for organization/team membership."""

    OWNER = "owner"  # Full control, billing
    ADMIN = "admin"  # Manage org/team settings
    MEMBER = "member"  # Full access to repos
    VIEWER = "viewer"  # Read-only, business summaries


class Membership(Base, UUIDMixin, TimestampMixin):
    """Membership model.

    Links users to organizations and optionally to specific teams.
    If team_id is NULL, the membership is at the organization level.
    """

    __tablename__ = "memberships"

    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    team_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    role: Mapped[MemberRole] = mapped_column(
        Enum(MemberRole),
        default=MemberRole.MEMBER,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", "team_id", name="uq_membership"),
    )

    # Relationships
    organization = relationship("Organization", back_populates="memberships")
    user = relationship("User", back_populates="memberships")
    team = relationship("Team", back_populates="memberships")
