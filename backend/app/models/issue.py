"""
Issue Model.

Represents a GitHub issue tracked by DevBridge.
"""

import enum

from sqlalchemy import (
    ARRAY,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class IssueState(str, enum.Enum):
    """State of a GitHub issue."""

    OPEN = "open"
    CLOSED = "closed"


class Issue(Base, UUIDMixin, TimestampMixin):
    """Issue model.

    Represents a GitHub issue in a repository.
    """

    __tablename__ = "issues"

    # Foreign keys
    repository_id: Mapped[str] = Column(
        UUID(as_uuid=False),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # GitHub data
    issue_number = Column(Integer, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    body = Column(Text, nullable=True)
    state: Mapped[IssueState] = Column(Enum(IssueState), nullable=False)  # type: ignore[assignment]
    author = Column(String(255), nullable=False)
    assignees = Column(ARRAY(String), nullable=True)
    labels = Column(ARRAY(String), nullable=True)
    milestone = Column(String(255), nullable=True)

    # Timestamps from GitHub
    opened_at = Column(DateTime(timezone=True), nullable=False)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    closed_by = Column(String(255), nullable=True)

    # Calculated metrics
    time_to_close_hours = Column(Float, nullable=True)

    # Links to PRs
    linked_pr_numbers = Column(ARRAY(Integer), nullable=True)

    # Relationships
    repository = relationship("Repository", back_populates="issues")

    def __repr__(self) -> str:
        return f"<Issue #{self.issue_number}: {self.title[:30]}>"
