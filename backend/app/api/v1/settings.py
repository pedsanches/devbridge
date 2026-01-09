"""
Settings Endpoints.

API for organization settings and data source integrations.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.deps import CurrentOrgId, CurrentUserRequired, DbSession
from app.schemas.settings import (
    ConnectGitHubRequest,
    ConnectGitHubResponse,
    DataSourcesResponse,
    IntegrationsResponse,
    IntegrationStatus,
)
from app.services import settings_service

router = APIRouter()


@router.get("/integrations", response_model=IntegrationsResponse)
async def get_integrations(
    db: DbSession,
    org_id: CurrentOrgId,
    _current_user: CurrentUserRequired,
) -> IntegrationsResponse:
    """
    Get status of all integrations for the current organization.

    Shows connection status for GitHub, Slack, and other data sources.

    Args:
        db: Database session.
        org_id: Current organization context.
        _current_user: Authenticated user.

    Returns:
        Integration statuses.
    """
    return await settings_service.get_integrations_status(db, org_id)


@router.post("/github/connect", response_model=ConnectGitHubResponse)
async def connect_github(
    db: DbSession,
    request: ConnectGitHubRequest,
    org_id: CurrentOrgId,
    _current_user: CurrentUserRequired,
) -> ConnectGitHubResponse:
    """
    Connect GitHub integration using a Personal Access Token.

    The token is encrypted before storage. After connecting,
    repositories can be synced to populate data sources.

    Args:
        db: Database session.
        request: GitHub PAT.
        org_id: Current organization context.
        _current_user: Authenticated user.

    Returns:
        Connection result with status.
    """
    result = await settings_service.connect_github(db, org_id, request.token)

    if result.status == IntegrationStatus.ERROR:
        raise HTTPException(status_code=400, detail=result.message)

    return result


@router.post("/github/disconnect", status_code=204)
async def disconnect_github(
    db: DbSession,
    org_id: CurrentOrgId,
    _current_user: CurrentUserRequired,
) -> None:
    """
    Disconnect GitHub integration.

    Removes the stored token but keeps existing repositories and activities.

    Args:
        db: Database session.
        org_id: Current organization context.
        _current_user: Authenticated user.
    """
    await settings_service.disconnect_github(db, org_id)


class RefreshRepositoriesResponse(BaseModel):
    """Response from refresh repositories operation."""

    status: str
    repositories_discovered: int
    message: str


@router.post("/github/refresh", response_model=RefreshRepositoriesResponse)
async def refresh_repositories(
    db: DbSession,
    org_id: CurrentOrgId,
    _current_user: CurrentUserRequired,
) -> RefreshRepositoriesResponse:
    """
    Refresh/rediscover GitHub repositories.

    Uses the existing stored token to fetch all accessible repositories
    and adds any new ones that weren't previously discovered.
    Existing repositories and their activities are not affected.

    Args:
        db: Database session.
        org_id: Current organization context.
        _current_user: Authenticated user.

    Returns:
        Number of new repositories discovered.
    """
    result = await settings_service.refresh_repositories(db, org_id)

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])

    return RefreshRepositoriesResponse(
        status=str(result["status"]),
        repositories_discovered=int(result["count"]),
        message=str(result["message"]),
    )


@router.get("/data-sources", response_model=DataSourcesResponse)
async def get_data_sources(
    db: DbSession,
    org_id: CurrentOrgId,
    _current_user: CurrentUserRequired,
) -> DataSourcesResponse:
    """
    Get all data sources (repositories) for the organization.

    Returns a list of connected repositories with their indexing status,
    activity counts, and sync information.

    Args:
        db: Database session.
        org_id: Current organization context.
        _current_user: Authenticated user.

    Returns:
        List of data sources with metadata.
    """
    return await settings_service.get_data_sources(db, org_id)
