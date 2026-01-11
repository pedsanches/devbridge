"""
Team Model.

Represents a team within an organization for grouping repositories.
Enhanced for data sources organization (inspired by Waydev/Swarmia patterns).
"""

from sqlalchemy import Boolean, Column, ForeignKey, String, Table, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

# Many-to-many association table for Team <-> Repository
team_repositories = Table(
    "team_repositories",
    Base.metadata,
    Column(
        "team_id", UUID(as_uuid=False), ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "repository_id",
        UUID(as_uuid=False),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Team(Base, UUIDMixin, TimestampMixin):
    """Team model.

    Teams are the primary organizational unit for grouping repositories.
    They serve as the default scope for:
    - Chat conversations (context filtering)
    - Report generation (mandatory selection)
    - Metrics aggregation (DORA/SPACE per team)

    Design inspired by:
    - Waydev: Groups = Repos + Team + Board
    - Swarmia: Teams as fundamental unit with GitHub sync
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

    # New fields for data sources organization
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    color: Mapped[str | None] = mapped_column(
        String(7), nullable=True
    )  # Hex color, e.g., "#4F46E5"
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    github_team_slug: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # For GitHub Teams sync

    __table_args__ = ({"extend_existing": True},)

    # Relationships
    organization = relationship("Organization", back_populates="teams")

    # Legacy 1:N relationship (maintained for backward compatibility)
    # This is the direct team_id FK on repositories
    repositories = relationship(
        "Repository", back_populates="team", foreign_keys="Repository.team_id"
    )

    # New many-to-many relationship for flexible grouping
    # A repository can belong to multiple teams via this relationship
    grouped_repositories = relationship(
        "Repository",
        secondary=team_repositories,
        backref="teams_grouped",
        lazy="selectin",
    )

    memberships = relationship("Membership", back_populates="team")
    team_metrics = relationship("TeamMetrics", back_populates="team", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Team {self.name} ({self.slug})>"
