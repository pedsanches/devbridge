"""
Repository Schemas.

Pydantic schemas for Repository model request/response validation.
"""

from datetime import datetime

from pydantic import HttpUrl, computed_field

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

    @computed_field  # type: ignore[prop-decorator]
    @property
    def last_synced_at(self) -> datetime | None:
        return self.updated_at


class RepositoryWithStats(RepositoryResponse):
    """Repository response with activity statistics."""

    total_activities: int = 0
    total_business_updates: int = 0
