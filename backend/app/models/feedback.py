"""
Feedback Models.

Stores user feedback on AI-generated responses for continuous learning.
Implements v1.2 schema with append-only history, lineage, and weighted scoring.

Key design decisions (see ADR-011):
- Append-only: Feedback is never updated; vote changes create new records
- Supersedes chain: New feedback references previous via supersedes_id
- Lineage: generation_id and prompt_version_id required for ML traceability

Reference: docs/architecture/continuous-learning-execution-plan.md
"""

import enum
import hashlib
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, event, func
from sqlalchemy.dialects.postgresql import ENUM, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class FeedbackType(str, enum.Enum):
    """Type of feedback signal."""

    # Explicit (user-initiated)
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"

    # Implicit (system-detected)
    REGENERATION = "regeneration"
    EDIT = "edit"
    COPY = "copy"
    ABANDON = "abandon"


class FeedbackSource(str, enum.Enum):
    """Source classification of the feedback."""

    EXPLICIT = "explicit"  # Deliberate user action (thumbs, rating)
    IMPLICIT = "implicit"  # Inferred by system behavior


# Mapping: FeedbackType -> raw score
FEEDBACK_SCORE_MAP: dict[FeedbackType, float] = {
    FeedbackType.THUMBS_UP: 1.0,
    FeedbackType.THUMBS_DOWN: -1.0,
    FeedbackType.REGENERATION: -0.5,
    FeedbackType.EDIT: -0.3,
    FeedbackType.COPY: 0.3,
    FeedbackType.ABANDON: -0.7,
}

# Mapping: FeedbackType -> source
FEEDBACK_SOURCE_MAP: dict[FeedbackType, FeedbackSource] = {
    FeedbackType.THUMBS_UP: FeedbackSource.EXPLICIT,
    FeedbackType.THUMBS_DOWN: FeedbackSource.EXPLICIT,
    FeedbackType.REGENERATION: FeedbackSource.IMPLICIT,
    FeedbackType.EDIT: FeedbackSource.IMPLICIT,
    FeedbackType.COPY: FeedbackSource.IMPLICIT,
    FeedbackType.ABANDON: FeedbackSource.IMPLICIT,
}


def generate_idempotency_key(
    user_id: str | None,
    message_id: str,
    feedback_type: str,
) -> str:
    """
    Generate an idempotency key for deduplication within a request window.

    Hash of: user_id + message_id + feedback_type
    Returns a 64-char hex string (SHA-256).

    Note: This key is used to detect duplicate submissions of the SAME feedback
    (e.g., network retries). Different feedback types create different keys,
    allowing the append-only model to track vote changes.
    """
    key_parts = f"{user_id or 'anonymous'}:{message_id}:{feedback_type}"
    return hashlib.sha256(key_parts.encode()).hexdigest()


class Feedback(Base, UUIDMixin, TimestampMixin):
    """
    Feedback model for continuous learning.

    Stores user feedback (explicit and implicit) on AI-generated responses.
    Designed as append-only: feedback is never updated, only superseded.

    Key Features:
    - Append-only: Vote changes create new records with supersedes_id link
    - Idempotency: Same feedback_type for same user+message is deduplicated
    - Lineage: Requires generation_id and prompt_version_id for traceability
    - Weighted Scoring: Separates raw score from trust weight

    Multi-tenant: Isolated by organization_id.
    """

    __tablename__ = "feedback"

    # === Idempotency ===
    # Key for deduplication: hash(user_id + message_id + feedback_type)
    # Not unique - allows multiple feedbacks per user+message (vote changes)
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # === History Tracking ===
    # Reference to previous feedback this one supersedes (for vote changes)
    supersedes_id: Mapped[str | None] = mapped_column(
        ForeignKey("feedback.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # === Multi-tenancy ===
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # === Context ===
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Note: message_id is NOT a FK because frontend generates IDs with suffixes like "-assistant"
    message_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # === Lineage (Required for Learning) ===
    # ID of the specific LLM generation that produced the response
    generation_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # Version of the prompt used (git hash, semver, or tag)
    prompt_version_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # Request trace ID for E2E debugging
    trace_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # === Feedback Type ===
    feedback_type: Mapped[FeedbackType] = mapped_column(
        ENUM(
            "thumbs_up",
            "thumbs_down",
            "regeneration",
            "edit",
            "copy",
            "abandon",
            name="feedbacktype",
            create_type=False,
        ),
        nullable=False,
    )
    source: Mapped[FeedbackSource] = mapped_column(
        ENUM(
            "explicit",
            "implicit",
            name="feedbacksource",
            create_type=False,
        ),
        nullable=False,
    )

    # === Scoring System ===
    # Raw score from the feedback type (-1.0 to +1.0)
    score_raw: Mapped[float] = mapped_column(Float, nullable=False)
    # Trust weight based on user history/reliability (0.0 to 1.0)
    # Default 1.0 = full trust. Reduced for anomalous users.
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    # Effective score = score_raw * weight (persisted for query efficiency)
    score_effective: Mapped[float] = mapped_column(Float, nullable=False)

    # === Metadata ===
    # Persona used when generating the response
    persona: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Additional metadata (model version, latency, tokens, etc.)
    extra_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # === Relationships ===
    organization = relationship("Organization")
    user = relationship("User")
    # Note: message relationship removed - message_id is not a FK (supports frontend IDs with suffixes)
    conversation = relationship("Conversation")
    supersedes = relationship("Feedback", remote_side="Feedback.id", uselist=False)

    # === Indexes ===
    __table_args__ = (
        # Composite index for quality score queries
        Index("ix_feedback_org_created", "organization_id", "created_at"),
        # Index for lineage queries
        Index("ix_feedback_generation", "generation_id"),
        Index("ix_feedback_prompt_version", "prompt_version_id"),
        # Index for feedback analysis by type
        Index("ix_feedback_type_source", "feedback_type", "source"),
        # Index for finding latest feedback per user+message
        Index("ix_feedback_user_message_created", "user_id", "message_id", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<Feedback(id={self.id}, type={self.feedback_type.value}, "
            f"score_effective={self.score_effective})>"
        )


# === Event Listeners ===
@event.listens_for(Feedback, "before_insert")
def calculate_effective_score(_mapper, _connection, target: Feedback) -> None:  # noqa: ARG001
    """Calculate score_effective before insert."""
    target.score_effective = target.score_raw * target.weight


class EventLog(Base, UUIDMixin):
    """
    Minimal event log for traceability and debugging.

    Stores key system events for the feedback funnel:
    - chat.response.generated
    - chat.response.displayed
    - feedback.received
    - feedback.persisted

    This is a lightweight append-only log, NOT for analytics.
    """

    __tablename__ = "event_log"

    # Event identification
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
        nullable=False,
    )

    # Correlation IDs
    trace_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    generation_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    message_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    organization_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    # Event payload (lightweight)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # === Indexes ===
    __table_args__ = (
        Index("ix_event_log_org_type_time", "organization_id", "event_type", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<EventLog(type={self.event_type}, trace_id={self.trace_id})>"
