import enum

from sqlalchemy import (
    ARRAY,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
)
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

    # === State Machine (ADR-012) ===
    github_node_id = Column(String(100), unique=True, nullable=True)
    state = Column(String(20), nullable=True)  # open, closed, merged
    state_updated_at = Column(DateTime(timezone=True), nullable=True)
    last_event_at = Column(DateTime(timezone=True), nullable=True)

    # Context enrichment fields (Phase 1)
    files_touched = Column(ARRAY(String), nullable=True)  # List of filenames changed
    labels = Column(ARRAY(String), nullable=True)  # PR labels (bug, feature, etc.)
    linked_issues = Column(ARRAY(String), nullable=True)  # Issue refs (#123, closes #456)

    # Value Tagging (Phase 2)
    value_tags = Column(ARRAY(String), nullable=True)  # RISK_MITIGATION, VELOCITY_ENABLER, etc.

    # === Code Metrics (ADR-009) ===
    lines_added = Column(Integer, nullable=True)
    lines_deleted = Column(Integer, nullable=True)
    files_changed_count = Column(Integer, nullable=True)

    # === PR Lifecycle Timestamps (SPACE-Efficiency) ===
    first_review_at = Column(DateTime(timezone=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    merged_at = Column(DateTime(timezone=True), nullable=True)

    # === Calculated Time Metrics (in hours) ===
    pickup_time_hours = Column(Float, nullable=True)  # first_review - created
    review_time_hours = Column(Float, nullable=True)  # approved - first_review
    merge_time_hours = Column(Float, nullable=True)  # merged - approved
    cycle_time_hours = Column(Float, nullable=True)  # merged - created

    # === Review Quality Metrics ===
    review_count = Column(Integer, default=0)
    rework_iterations = Column(Integer, default=0)  # Count of CHANGES_REQUESTED
    comments_received = Column(Integer, default=0)
    is_reverted = Column(Boolean, default=False)  # For DORA CFR calculation
    reverted_by_pr = Column(String(50), nullable=True)

    # Relationships
    repository = relationship("Repository", back_populates="activities")
    business_update = relationship(
        "BusinessUpdate", uselist=False, back_populates="activity", cascade="all, delete-orphan"
    )
    reviews = relationship("CodeReview", back_populates="activity", cascade="all, delete-orphan")


class BusinessUpdate(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "business_updates"

    activity_id = Column(Uuid, ForeignKey("activities.id"), unique=True, nullable=False)
    summary = Column(Text, nullable=False)  # The translated business value
    impact_level: Mapped[ImpactLevel | None] = Column(Enum(ImpactLevel), default=ImpactLevel.LOW)  # type: ignore[assignment]
    category = Column(String, nullable=True)  # e.g. "Performance", "Feature"

    # Relationships
    activity = relationship("Activity", back_populates="business_update")
