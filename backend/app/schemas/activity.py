"""
Activity Schemas.

Pydantic schemas for Activity and BusinessUpdate models.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from app.schemas.common import BaseSchema, TimestampSchema


class ActivityType(str, Enum):
    """Type of activity from GitHub."""

    COMMIT = "COMMIT"
    PULL_REQUEST = "PULL_REQUEST"


class ImpactLevel(str, Enum):
    """Business impact level of an activity."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


# --- Activity Schemas ---


class ActivityCreate(BaseSchema):
    """Schema for creating an activity."""

    repository_id: UUID
    external_id: str  # GitHub SHA or PR number
    type: ActivityType
    title: str
    content: str | None = None
    author: str
    occurred_at: datetime | None = None
    # Context enrichment fields
    files_touched: list[str] | None = None
    labels: list[str] | None = None
    linked_issues: list[str] | None = None
    # Value Tagging (Phase 2)
    value_tags: list[str] | None = None


class ActivityResponse(TimestampSchema):
    """Schema for activity response."""

    id: UUID
    repository_id: UUID
    external_id: str
    type: ActivityType
    title: str
    content: str | None
    author: str
    occurred_at: datetime | None
    # Context enrichment fields
    files_touched: list[str] | None = None
    labels: list[str] | None = None
    linked_issues: list[str] | None = None
    # Value Tagging (Phase 2)
    value_tags: list[str] | None = None


class ActivityWithUpdate(ActivityResponse):
    """Activity response including business update if available."""

    business_update: "BusinessUpdateResponse | None" = None


# --- BusinessUpdate Schemas ---


class BusinessUpdateCreate(BaseSchema):
    """Schema for creating a business update."""

    activity_id: UUID
    summary: str
    impact_level: ImpactLevel = ImpactLevel.LOW
    category: str | None = None


class BusinessUpdateResponse(TimestampSchema):
    """Schema for business update response."""

    id: UUID
    activity_id: UUID
    summary: str
    impact_level: ImpactLevel
    category: str | None


# Forward reference resolution
ActivityWithUpdate.model_rebuild()
