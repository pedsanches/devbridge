"""
Feedback Schemas.

Pydantic schemas for feedback API request/response.
Implements v1.1 schema with idempotency and lineage validation.

Reference: docs/architecture/continuous-learning-execution-plan.md
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class FeedbackType(str, Enum):
    """Type of feedback signal."""

    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    REGENERATION = "regeneration"
    EDIT = "edit"
    COPY = "copy"
    ABANDON = "abandon"


class FeedbackSource(str, Enum):
    """Source classification."""

    EXPLICIT = "explicit"
    IMPLICIT = "implicit"


class FeedbackCreate(BaseModel):
    """Schema for creating new feedback."""

    # Required: Target message
    # Note: message_id is str (not UUID) to support frontend-generated IDs with suffixes like "-assistant"
    message_id: str = Field(
        ..., min_length=1, max_length=100, description="ID of the message being rated"
    )
    conversation_id: UUID = Field(..., description="ID of the conversation")

    # Required: Feedback type
    feedback_type: FeedbackType = Field(..., description="Type of feedback")

    # Required for learning: Lineage information
    generation_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="ID of the LLM generation that produced the response",
    )
    prompt_version_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Version of the prompt used (git hash or semver)",
    )

    # Optional: Request context
    trace_id: str | None = Field(None, max_length=100, description="Request trace ID")
    persona: str | None = Field(None, max_length=50, description="Persona used")

    # Optional: Additional metadata
    metadata: dict | None = Field(None, description="Additional context (model, latency, etc.)")

    @field_validator("generation_id", "prompt_version_id")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure lineage fields are not empty strings."""
        if not v.strip():
            raise ValueError("Lineage fields cannot be empty")
        return v.strip()


class FeedbackResponse(BaseModel):
    """Schema for feedback response."""

    id: UUID = Field(..., description="Feedback ID")
    message_id: str = Field(..., description="Message ID")
    conversation_id: UUID = Field(..., description="Conversation ID")
    feedback_type: FeedbackType
    source: FeedbackSource
    score_raw: float = Field(..., description="Raw score value")
    score_effective: float = Field(..., description="Weighted score")
    generation_id: str
    prompt_version_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FeedbackListResponse(BaseModel):
    """Schema for paginated feedback list."""

    items: list[FeedbackResponse]
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Items per page")
    has_more: bool = Field(..., description="Whether more items exist")


class FeedbackForConversationItem(BaseModel):
    """Minimal feedback projection for conversation hydration."""

    message_id: str
    feedback_type: FeedbackType
    created_at: datetime

    model_config = {"from_attributes": True}


class FeedbackForConversationResponse(BaseModel):
    """Feedback mapping for a specific conversation for the current user."""

    conversation_id: UUID
    items: list[FeedbackForConversationItem]


class FeedbackStats(BaseModel):
    """Schema for feedback statistics."""

    total_count: int = Field(..., description="Total feedbacks")
    explicit_count: int = Field(..., description="Explicit feedbacks (thumbs)")
    implicit_count: int = Field(..., description="Implicit feedbacks (system-detected)")
    positive_count: int = Field(..., description="Positive feedbacks")
    negative_count: int = Field(..., description="Negative feedbacks")
    average_score: float | None = Field(None, description="Average effective score")
    period_days: int = Field(..., description="Period in days")


class QualityScoreConfidence(str, Enum):
    """Confidence level for quality score."""

    LOW = "low"  # Not enough data
    MEDIUM = "medium"  # Moderate confidence
    HIGH = "high"  # Strong confidence


class QualityScore(BaseModel):
    """Schema for quality score calculation result."""

    value: float | None = Field(None, ge=0.0, le=1.0, description="Score (0-1)")
    confidence: QualityScoreConfidence = Field(..., description="Confidence level")
    sample_size: int = Field(..., description="Number of feedbacks used")
    explicit_score: float | None = Field(None, description="Score from explicit feedback only")
    implicit_score: float | None = Field(None, description="Score from implicit feedback only")
    period_days: int = Field(..., description="Period analyzed")
    reason: str | None = Field(None, description="Explanation if score is null")


class FeedbackFunnelStage(BaseModel):
    """Single stage in the feedback funnel."""

    stage: str = Field(..., description="Stage name")
    count: int = Field(..., description="Events at this stage")
    percentage: float = Field(..., description="Percentage of previous stage")


class FeedbackFunnel(BaseModel):
    """Schema for feedback funnel analysis."""

    period_start: datetime
    period_end: datetime
    stages: list[FeedbackFunnelStage]
    total_generated: int = Field(..., description="Total responses generated")
    total_persisted: int = Field(..., description="Total feedbacks persisted")
    conversion_rate: float = Field(..., description="End-to-end conversion rate")


class IdempotencyResult(BaseModel):
    """Result of idempotent feedback submission."""

    created: bool = Field(..., description="True if newly created, False if duplicate")
    feedback_id: UUID = Field(..., description="ID of the feedback (new or existing)")
    message: str = Field(..., description="Status message")
