"""
Settings/Integrations Schemas.

Schemas for organization settings and data source integrations.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class IntegrationStatus(str, Enum):
    """Status of an integration connection."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class GitHubIntegration(BaseModel):
    """GitHub integration status."""

    status: IntegrationStatus = Field(default=IntegrationStatus.DISCONNECTED)
    connected_at: datetime | None = Field(None, description="When GitHub was connected")
    organization_name: str | None = Field(None, description="GitHub org/user connected")
    repositories_count: int = Field(0, description="Number of repositories synced")


class SlackIntegration(BaseModel):
    """Slack integration status (future)."""

    status: IntegrationStatus = Field(default=IntegrationStatus.DISCONNECTED)
    connected_at: datetime | None = None
    channel_name: str | None = None


class IntegrationsResponse(BaseModel):
    """Response with all integration statuses."""

    github: GitHubIntegration
    slack: SlackIntegration


class ConnectGitHubRequest(BaseModel):
    """Request to connect GitHub via PAT."""

    token: str = Field(..., min_length=10, description="GitHub Personal Access Token")


class ConnectGitHubResponse(BaseModel):
    """Response after connecting GitHub."""

    status: IntegrationStatus
    organization_name: str | None = None
    message: str


class DataSourceSummary(BaseModel):
    """Summary of a data source (repository) for the UI."""

    id: str
    name: str
    url: str
    is_active: bool
    activities_count: int = 0
    last_synced_at: datetime | None = None
    indexing_status: str = "pending"  # pending, indexing, indexed, error
    vectors_count: int = 0


class DataSourcesResponse(BaseModel):
    """List of data sources with metadata."""

    sources: list[DataSourceSummary]
    total: int
    github_connected: bool
