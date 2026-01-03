"""
Sync Endpoints.

API endpoints for synchronizing GitHub repository data.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import DbSession
from app.services.sync_service import sync_service

router = APIRouter()


class SyncRequest(BaseModel):
    """Request to sync a repository."""

    repo_name: str = Field(..., description="Repository name in 'owner/repo' format")
    max_commits: int = Field(50, ge=1, le=100, description="Max commits to sync")
    max_prs: int = Field(20, ge=1, le=50, description="Max PRs to sync")


class SyncResponse(BaseModel):
    """Response from sync operation."""

    status: str
    repo_name: str
    commits_synced: int
    prs_synced: int


@router.post("", response_model=SyncResponse)
async def sync_repository(db: DbSession, request: SyncRequest) -> SyncResponse:
    """
    Sync a GitHub repository to the local database.

    Fetches recent commits and PRs from GitHub API and creates
    Activity records for each.

    Args:
        db: Database session.
        request: Sync request with repo name and limits.

    Returns:
        Sync results with counts.
    """
    try:
        result = await sync_service.sync_repository(
            db,
            repo_name=request.repo_name,
            max_commits=request.max_commits,
            max_prs=request.max_prs,
        )

        return SyncResponse(
            status="success",
            repo_name=request.repo_name,
            commits_synced=result["commits_synced"],
            prs_synced=result["prs_synced"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
