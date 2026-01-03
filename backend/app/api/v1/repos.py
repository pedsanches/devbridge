"""
Repository Endpoints.

CRUD operations for monitored repositories with multi-tenant isolation.
"""

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import DbSession
from app.schemas import (
    PaginatedResponse,
    RepositoryCreate,
    RepositoryResponse,
    RepositoryUpdate,
)
from app.services import repository_service
from app.services.repository_service import DEFAULT_ORG_ID

router = APIRouter()


# TODO: Replace with actual org_id from JWT/session after Auth implementation
def get_current_org_id() -> str:
    """Get current organization ID. Uses default until auth is implemented."""
    return DEFAULT_ORG_ID


@router.get("", response_model=PaginatedResponse)
async def list_repos(
    db: DbSession,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    is_active: bool | None = Query(None, description="Filter by active status"),
) -> PaginatedResponse:
    """
    List all monitored repositories for the current organization.

    Args:
        db: Database session.
        page: Page number (1-indexed).
        page_size: Number of items per page.
        is_active: Filter by active status.

    Returns:
        Paginated list of repositories.
    """
    org_id = get_current_org_id()
    skip = (page - 1) * page_size
    repositories, total = await repository_service.get_repositories(
        db,
        organization_id=org_id,
        skip=skip,
        limit=page_size,
        is_active=is_active,
    )

    return PaginatedResponse.create(
        data=[RepositoryResponse.model_validate(repo) for repo in repositories],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=RepositoryResponse, status_code=201)
async def create_repo(db: DbSession, repo: RepositoryCreate) -> RepositoryResponse:
    """
    Add a new repository to monitor.

    Args:
        db: Database session.
        repo: Repository creation data.

    Returns:
        Created repository.
    """
    org_id = get_current_org_id()

    # Check if repo already exists in this org
    url_str = str(repo.url)
    parts = url_str.rstrip("/").split("/")
    name = repo.name or f"{parts[-2]}/{parts[-1]}" if len(parts) >= 2 else None

    if name:
        existing = await repository_service.get_repository_by_name(db, org_id, name)
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Repository '{name}' already exists",
            )

    repository = await repository_service.create_repository(db, org_id, repo)
    return RepositoryResponse.model_validate(repository)


@router.get("/{repo_id}", response_model=RepositoryResponse)
async def get_repo(db: DbSession, repo_id: str) -> RepositoryResponse:
    """
    Get a specific repository by ID.

    Args:
        db: Database session.
        repo_id: Repository ID.

    Returns:
        Repository details.
    """
    org_id = get_current_org_id()
    repository = await repository_service.get_repository_by_id(db, org_id, repo_id)
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")

    return RepositoryResponse.model_validate(repository)


@router.patch("/{repo_id}", response_model=RepositoryResponse)
async def update_repo(
    db: DbSession,
    repo_id: str,
    repo_in: RepositoryUpdate,
) -> RepositoryResponse:
    """
    Update a repository.

    Args:
        db: Database session.
        repo_id: Repository ID.
        repo_in: Update data.

    Returns:
        Updated repository.
    """
    org_id = get_current_org_id()
    repository = await repository_service.get_repository_by_id(db, org_id, repo_id)
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")

    updated = await repository_service.update_repository(db, repository, repo_in)
    return RepositoryResponse.model_validate(updated)


@router.delete("/{repo_id}", status_code=204)
async def delete_repo(db: DbSession, repo_id: str) -> None:
    """
    Remove a repository from monitoring.

    Args:
        db: Database session.
        repo_id: Repository ID.
    """
    org_id = get_current_org_id()
    repository = await repository_service.get_repository_by_id(db, org_id, repo_id)
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")

    await repository_service.delete_repository(db, repository)
