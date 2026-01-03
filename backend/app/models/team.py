"""
Team Model.

Represents a team within an organization for grouping repositories.
"""

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Team(Base, UUIDMixin, TimestampMixin):
    """Team model.

    Teams group repositories within an organization.
    Users can be members of specific teams with different roles.
    """

    __tablename__ = "teams"

    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)

    __table_args__ = (UniqueConstraint("organization_id", "slug", name="uq_team_org_slug"),)

    # Relationships
    organization = relationship("Organization", back_populates="teams")
    repositories = relationship("Repository", back_populates="team")
    memberships = relationship("Membership", back_populates="team")
