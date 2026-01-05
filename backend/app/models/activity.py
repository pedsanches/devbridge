import enum

from sqlalchemy import ARRAY, Column, DateTime, Enum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ActivityType(str, enum.Enum):
    COMMIT = "COMMIT"
    PULL_REQUEST = "PULL_REQUEST"


class ImpactLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Activity(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "activities"

    repository_id = Column(Uuid, ForeignKey("repositories.id"), nullable=False)
    external_id = Column(String, index=True, nullable=False)  # sha or pr number
    type: Mapped[ActivityType] = Column(Enum(ActivityType), nullable=False)  # type: ignore[assignment]
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True)  # Commit message or PR body
    author = Column(String, nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=True)

    # Context enrichment fields (Phase 1)
    files_touched = Column(ARRAY(String), nullable=True)  # List of filenames changed
    labels = Column(ARRAY(String), nullable=True)  # PR labels (bug, feature, etc.)
    linked_issues = Column(ARRAY(String), nullable=True)  # Issue refs (#123, closes #456)

    # Value Tagging (Phase 2)
    value_tags = Column(ARRAY(String), nullable=True)  # RISK_MITIGATION, VELOCITY_ENABLER, etc.

    # Relationships
    repository = relationship("Repository", back_populates="activities")
    business_update = relationship(
        "BusinessUpdate", uselist=False, back_populates="activity", cascade="all, delete-orphan"
    )


class BusinessUpdate(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "business_updates"

    activity_id = Column(Uuid, ForeignKey("activities.id"), unique=True, nullable=False)
    summary = Column(Text, nullable=False)  # The translated business value
    impact_level: Mapped[ImpactLevel | None] = Column(Enum(ImpactLevel), default=ImpactLevel.LOW)  # type: ignore[assignment]
    category = Column(String, nullable=True)  # e.g. "Performance", "Feature"

    # Relationships
    activity = relationship("Activity", back_populates="business_update")
