"""
Issue Schemas.

Pydantic schemas for Issue model.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from app.schemas.common import BaseSchema, TimestampSchema


class IssueState(str, Enum):
    """State of a GitHub issue."""

    OPEN = "open"
    CLOSED = "closed"


class IssueCreate(BaseSchema):
    """Schema for creating an issue."""

    repository_id: UUID
    issue_number: int
    title: str
    body: str | None = None
    state: IssueState
    author: str
    assignees: list[str] | None = None
    labels: list[str] | None = None
    milestone: str | None = None
    opened_at: datetime
    closed_at: datetime | None = None
    closed_by: str | None = None
    time_to_close_hours: float | None = None
    linked_pr_numbers: list[int] | None = None


class IssueResponse(TimestampSchema):
    """Schema for issue response."""

    id: UUID
    repository_id: UUID
    issue_number: int
    title: str
    body: str | None
    state: IssueState
    author: str
    assignees: list[str] | None = None
    labels: list[str] | None = None
    milestone: str | None = None
    opened_at: datetime
    closed_at: datetime | None = None
    closed_by: str | None = None
    time_to_close_hours: float | None = None
    linked_pr_numbers: list[int] | None = None


class IssueUpdate(BaseSchema):
    """Schema for updating an issue."""

    state: IssueState | None = None
    closed_at: datetime | None = None
    closed_by: str | None = None
    time_to_close_hours: float | None = None
