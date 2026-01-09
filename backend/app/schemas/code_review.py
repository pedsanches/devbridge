"""
Code Review Schemas.

Pydantic schemas for CodeReview model.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from app.schemas.common import BaseSchema, TimestampSchema


class ReviewState(str, Enum):
    """State of a GitHub code review."""

    APPROVED = "APPROVED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    COMMENTED = "COMMENTED"
    PENDING = "PENDING"
    DISMISSED = "DISMISSED"


class CodeReviewCreate(BaseSchema):
    """Schema for creating a code review."""

    activity_id: UUID
    review_id: int
    reviewer: str
    state: ReviewState
    body: str | None = None
    submitted_at: datetime
    comments_count: int = 0


class CodeReviewResponse(TimestampSchema):
    """Schema for code review response."""

    id: UUID
    activity_id: UUID
    review_id: int
    reviewer: str
    state: ReviewState
    body: str | None
    submitted_at: datetime
    comments_count: int = 0
