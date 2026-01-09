"""
Code Review Model.

Represents a code review on a GitHub pull request.
"""

import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ReviewState(str, enum.Enum):
    """State of a GitHub code review."""

    APPROVED = "APPROVED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    COMMENTED = "COMMENTED"
    PENDING = "PENDING"
    DISMISSED = "DISMISSED"


class CodeReview(Base, UUIDMixin, TimestampMixin):
    """Code Review model.

    Represents a review on a pull request.
    """

    __tablename__ = "code_reviews"

    # Foreign key to Activity (PR)
    activity_id: Mapped[str] = Column(
        UUID(as_uuid=False),
        ForeignKey("activities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # GitHub data
    review_id = Column(Integer, nullable=False, index=True)  # GitHub review ID
    reviewer = Column(String(255), nullable=False)
    state: Mapped[ReviewState] = Column(Enum(ReviewState), nullable=False)  # type: ignore[assignment]
    body = Column(Text, nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=False)

    # Metrics
    comments_count = Column(Integer, default=0)

    # Relationships
    activity = relationship("Activity", back_populates="reviews")

    def __repr__(self) -> str:
        return f"<CodeReview by {self.reviewer}: {self.state.value}>"
