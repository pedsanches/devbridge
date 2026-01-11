"""
Teams API Routes.

CRUD operations for team management and data sources organization.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_org_id, get_current_user, get_db
from app.models import User
from app.schemas.team import (
    SetDefaultTeamRequest,
    TeamAddRepositories,
    TeamCreate,
    TeamDetailResponse,
    TeamListResponse,
    TeamRemoveRepositories,
    TeamResponse,
    TeamUpdate,
)
from app.services.settings_service import get_github_token
from app.services.team_service import team_service
from app.services.team_sync_service import team_sync_service

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("", response_model=TeamListResponse)
async def list_teams(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_org_id),
) -> TeamListResponse:
    """
    List all teams for the current organization.

    Teams are returned ordered by:
    1. Default team first
    2. Alphabetically by name
    """
    return await team_service.list_teams(db, org_id, page, page_size)


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    data: TeamCreate,
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_org_id),
    _user: User = Depends(get_current_user),
) -> TeamResponse:
    """
    Create a new team.

    Optionally include repository_ids to add repositories during creation.
    """
    team = await team_service.create_team(db, org_id, data)
    await db.commit()
    return team


@router.get("/default", response_model=TeamResponse | None)
async def get_default_team(
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_org_id),
) -> TeamResponse | None:
    """
    Get the default team for the current organization.

    Returns null if no default team is set.
    """
    return await team_service.get_default_team(db, org_id)


@router.post("/default", response_model=TeamResponse)
async def ensure_default_team(
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_org_id),
    _user: User = Depends(get_current_user),
) -> TeamResponse:
    """
    Ensure a default team exists.

    If no default team exists, creates one called "Meus Repositórios"
    with all active repositories. This is typically called during onboarding.
    """
    team = await team_service.create_default_team_if_needed(db, org_id)
    await db.commit()
    return team


@router.post("/sync", response_model=dict)
async def sync_github_teams(
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_org_id),
    _user: User = Depends(get_current_user),
) -> dict:
    """
    Synchronize GitHub Teams with DevBridge Teams.

    This endpoint fetches the user's GitHub teams and creates/updates
    corresponding DevBridge teams, linking repositories automatically.

    Requires GitHub integration to be connected.
    """
    # Get GitHub token from settings
    github_token = await get_github_token(db, org_id)
    if not github_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub integration not connected. Please connect GitHub first.",
        )

    result = await team_sync_service.sync_github_teams(db, org_id, github_token)
    await db.commit()
    return result


@router.put("/default", response_model=TeamResponse)
async def set_default_team(
    data: SetDefaultTeamRequest,
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_org_id),
    _user: User = Depends(get_current_user),
) -> TeamResponse:
    """
    Set a team as the default.

    Only one team can be default per organization.
    """
    team = await team_service.update_team(db, data.team_id, org_id, TeamUpdate(is_default=True))
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )
    await db.commit()
    return team


@router.get("/{team_id}", response_model=TeamDetailResponse)
async def get_team(
    team_id: str,
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_org_id),
) -> TeamDetailResponse:
    """
    Get a team by ID with full details including repositories.
    """
    team = await team_service.get_team(db, team_id, org_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )
    return team


@router.patch("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: str,
    data: TeamUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_org_id),
    _user: User = Depends(get_current_user),
) -> TeamResponse:
    """
    Update a team.

    All fields are optional. Only provided fields will be updated.
    """
    team = await team_service.update_team(db, team_id, org_id, data)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )
    await db.commit()
    return team


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: str,
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_org_id),
    _user: User = Depends(get_current_user),
) -> None:
    """
    Delete a team.

    This removes the team and all its repository associations.
    The repositories themselves are NOT deleted.
    """
    deleted = await team_service.delete_team(db, team_id, org_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )
    await db.commit()


@router.post("/{team_id}/repositories", response_model=dict)
async def add_repositories(
    team_id: str,
    data: TeamAddRepositories,
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_org_id),
    _user: User = Depends(get_current_user),
) -> dict:
    """
    Add repositories to a team.

    A repository can belong to multiple teams (many-to-many).
    """
    count = await team_service.add_repositories(db, team_id, org_id, data.repository_ids)
    if count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found or no valid repositories provided",
        )
    await db.commit()
    return {"added": count, "message": f"Added {count} repositories to team"}


@router.delete("/{team_id}/repositories", response_model=dict)
async def remove_repositories(
    team_id: str,
    data: TeamRemoveRepositories,
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_org_id),
    _user: User = Depends(get_current_user),
) -> dict:
    """
    Remove repositories from a team.

    The repositories themselves are NOT deleted, only the association.
    """
    count = await team_service.remove_repositories(db, team_id, org_id, data.repository_ids)
    if count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found or no repositories to remove",
        )
    await db.commit()
    return {"removed": count, "message": f"Removed {count} repositories from team"}
