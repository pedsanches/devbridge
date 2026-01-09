"""
Developer Profile Model.

Aggregated metrics and AI-generated insights for a developer.
"""

from sqlalchemy import BigInteger, Column, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class DeveloperProfile(Base, UUIDMixin, TimestampMixin):
    """Developer Profile model.

    Aggregated profile for each developer in an organization.
    """

    __tablename__ = "developer_profiles"

    # Foreign key
    organization_id: Mapped[str] = Column(
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Identity
    github_username = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # Aggregated metrics (updated by batch jobs)
    total_commits = Column(Integer, default=0)
    total_prs_created = Column(Integer, default=0)
    total_prs_merged = Column(Integer, default=0)
    total_reviews_given = Column(Integer, default=0)
    total_issues_closed = Column(Integer, default=0)
    total_lines_added = Column(BigInteger, default=0)
    total_lines_deleted = Column(BigInteger, default=0)

    # Time metrics (averages in hours)
    avg_review_time_hours = Column(Float, nullable=True)  # Avg time to give review
    avg_pr_merge_time_hours = Column(Float, nullable=True)  # Avg time for PRs to merge

    # AI-generated insights
    strength_tags = Column(ARRAY(String), nullable=True)  # ["frontend", "performance", "testing"]
    collaboration_score = Column(Float, nullable=True)  # 0-100

    # Relationships
    organization = relationship("Organization", back_populates="developer_profiles")

    __table_args__ = (
        UniqueConstraint("organization_id", "github_username", name="uq_dev_org_username"),
    )

    def __repr__(self) -> str:
        return f"<DeveloperProfile {self.github_username}>"
