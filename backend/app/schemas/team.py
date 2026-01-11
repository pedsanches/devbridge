"""
Team Schemas.

Pydantic schemas for team CRUD operations.
Implements data sources organization (inspired by Waydev/Swarmia patterns).
"""

from datetime import datetime

from pydantic import BaseModel, Field


class TeamBase(BaseModel):
    """Base schema for team data."""

    name: str = Field(..., description="Team display name", min_length=1, max_length=255)
    description: str | None = Field(None, description="Team description")
    color: str | None = Field(
        None,
        description="Hex color for UI (e.g., '#4F46E5')",
        pattern=r"^#[0-9A-Fa-f]{6}$",
    )


class TeamCreate(TeamBase):
    """Schema for creating a new team."""

    repository_ids: list[str] | None = Field(None, description="Repository IDs to add to this team")
    github_team_slug: str | None = Field(
        None, description="GitHub Team slug for sync (e.g., 'engineering')"
    )


class TeamUpdate(BaseModel):
    """Schema for updating a team."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    is_default: bool | None = None
    github_team_slug: str | None = None


class TeamAddRepositories(BaseModel):
    """Schema for adding repositories to a team."""

    repository_ids: list[str] = Field(..., description="Repository IDs to add", min_length=1)


class TeamRemoveRepositories(BaseModel):
    """Schema for removing repositories from a team."""

    repository_ids: list[str] = Field(..., description="Repository IDs to remove", min_length=1)


class RepositorySummary(BaseModel):
    """Compact repository info for team responses."""

    id: str
    name: str
    url: str
    is_active: bool
    activities_count: int = 0

    model_config = {"from_attributes": True}


class TeamResponse(BaseModel):
    """Schema for team response."""

    id: str
    name: str
    slug: str
    description: str | None
    color: str | None
    is_default: bool
    github_team_slug: str | None
    repositories_count: int = Field(..., description="Number of repositories in this team")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TeamDetailResponse(TeamResponse):
    """Schema for detailed team response with repositories."""

    repositories: list[RepositorySummary] = Field(
        default_factory=list, description="Repositories in this team"
    )


class TeamListResponse(BaseModel):
    """Schema for paginated team list."""

    items: list[TeamResponse]
    total: int
    page: int = 1
    page_size: int = 20
    has_more: bool


class SetDefaultTeamRequest(BaseModel):
    """Schema for setting a team as default."""

    team_id: str = Field(..., description="Team ID to set as default")
