"""
Repository Schemas.

Pydantic schemas for Repository model request/response validation.
"""

from pydantic import HttpUrl

from app.schemas.common import BaseSchema, TimestampSchema


class RepositoryCreate(BaseSchema):
    """Schema for creating a new repository."""

    url: str | HttpUrl
    name: str | None = None  # Will be extracted from URL if not provided
    owner: str | None = None  # Will be extracted from URL if not provided


class RepositoryUpdate(BaseSchema):
    """Schema for updating a repository."""

    is_active: bool | None = None


class RepositoryResponse(TimestampSchema):
    """Schema for repository response."""

    id: str
    name: str
    owner: str
    url: str
    is_active: bool


class RepositoryWithStats(RepositoryResponse):
    """Repository response with activity statistics."""

    total_activities: int = 0
    total_business_updates: int = 0
