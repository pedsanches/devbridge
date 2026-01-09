"""
Contributor Stats Model.

Weekly snapshots of contributor statistics for a repository.
"""

from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ContributorStats(Base, UUIDMixin, TimestampMixin):
    """Contributor Stats model.

    Weekly snapshot of a contributor's activity in a repository.
    """

    __tablename__ = "contributor_stats"

    # Foreign key
    repository_id: Mapped[str] = Column(
        UUID(as_uuid=False),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Contributor info
    author = Column(String(255), nullable=False, index=True)
    week_start = Column(Date, nullable=False, index=True)

    # SPACE-Activity metrics
    commits = Column(Integer, default=0)
    prs_created = Column(Integer, default=0)
    prs_merged = Column(Integer, default=0)
    reviews_given = Column(Integer, default=0)
    issues_closed = Column(Integer, default=0)

    # Code volume
    additions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)

    # SPACE-Efficiency (weekly averages)
    avg_pickup_time_hours = Column(Float, nullable=True)
    avg_cycle_time_hours = Column(Float, nullable=True)

    # SPACE-Communication
    comments_given = Column(Integer, default=0)

    # Relationships
    repository = relationship("Repository", back_populates="contributor_stats")

    __table_args__ = (
        UniqueConstraint(
            "repository_id", "author", "week_start", name="uq_contrib_repo_author_week"
        ),
    )

    def __repr__(self) -> str:
        return f"<ContributorStats {self.author} week={self.week_start}>"
