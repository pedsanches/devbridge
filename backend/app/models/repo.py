"""
Repository Model.

Represents a GitHub repository monitored by DevBridge.
"""

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Repository(Base, UUIDMixin, TimestampMixin):
    """Repository model.

    Repositories belong to an organization and optionally to a team.
    """

    __tablename__ = "repositories"

    # Multi-tenancy: organization is required, team is optional
    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    team_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(String, index=True, nullable=False)  # "owner/repo"
    owner: Mapped[str] = mapped_column(String, index=True, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (UniqueConstraint("organization_id", "name", name="uq_repo_org_name"),)

    # Relationships
    organization = relationship("Organization", back_populates="repositories")
    team = relationship("Team", back_populates="repositories")
    activities = relationship("Activity", back_populates="repository", cascade="all, delete-orphan")
