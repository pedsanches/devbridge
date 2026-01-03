"""
Repository Service.

Business logic for Repository CRUD operations with multi-tenant isolation.
"""

from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Repository
from app.schemas import RepositoryCreate, RepositoryUpdate

# Default organization ID for backwards compatibility
DEFAULT_ORG_ID = "00000000-0000-0000-0000-000000000001"


async def get_repositories(
    db: AsyncSession,
    organization_id: str,
    *,
    skip: int = 0,
    limit: int = 20,
    is_active: bool | None = None,
) -> tuple[list[Repository], int]:
    """
    Get list of repositories for an organization.

    Args:
        db: Database session.
        organization_id: Organization UUID (tenant isolation).
        skip: Number of records to skip.
        limit: Maximum number of records to return.
        is_active: Filter by active status.

    Returns:
        Tuple of (repositories list, total count).
    """
    # Base query with tenant isolation
    query = select(Repository).where(Repository.organization_id == organization_id)

    if is_active is not None:
        query = query.where(Repository.is_active == is_active)

    # Get total count
    count_query = select(func.count(Repository.id)).where(
        Repository.organization_id == organization_id
    )
    if is_active is not None:
        count_query = count_query.where(Repository.is_active == is_active)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Get paginated results
    query = query.offset(skip).limit(limit).order_by(Repository.created_at.desc())
    result = await db.execute(query)
    repositories = list(result.scalars().all())

    return repositories, total


async def get_repository_by_id(
    db: AsyncSession,
    organization_id: str,
    repo_id: str,
) -> Repository | None:
    """
    Get a repository by ID within an organization.

    Args:
        db: Database session.
        organization_id: Organization UUID (tenant isolation).
        repo_id: Repository UUID.

    Returns:
        Repository if found, None otherwise.
    """
    result = await db.execute(
        select(Repository).where(
            Repository.id == repo_id,
            Repository.organization_id == organization_id,
        )
    )
    return result.scalar_one_or_none()


async def get_repository_by_name(
    db: AsyncSession,
    organization_id: str,
    name: str,
) -> Repository | None:
    """
    Get a repository by name within an organization.

    Args:
        db: Database session.
        organization_id: Organization UUID (tenant isolation).
        name: Repository name in owner/repo format.

    Returns:
        Repository if found, None otherwise.
    """
    result = await db.execute(
        select(Repository).where(
            Repository.name == name,
            Repository.organization_id == organization_id,
        )
    )
    return result.scalar_one_or_none()


async def create_repository(
    db: AsyncSession,
    organization_id: str,
    repo_in: RepositoryCreate,
    team_id: str | None = None,
) -> Repository:
    """
    Create a new repository within an organization.

    Args:
        db: Database session.
        organization_id: Organization UUID (tenant isolation).
        repo_in: Repository creation data.
        team_id: Optional team UUID.

    Returns:
        Created repository.
    """
    # Extract owner/name from URL if not provided
    url_str = str(repo_in.url)
    parts = url_str.rstrip("/").split("/")

    owner = repo_in.owner or parts[-2] if len(parts) >= 2 else "unknown"
    name = repo_in.name or f"{owner}/{parts[-1]}" if parts else "unknown/repo"

    repository = Repository(
        id=str(uuid4()),
        organization_id=organization_id,
        team_id=team_id,
        name=name,
        owner=owner,
        url=url_str,
        is_active=True,
    )

    db.add(repository)
    await db.flush()
    await db.refresh(repository)

    return repository


async def update_repository(
    db: AsyncSession,
    repo: Repository,
    repo_in: RepositoryUpdate,
) -> Repository:
    """
    Update a repository.

    Args:
        db: Database session.
        repo: Existing repository (already verified for tenant access).
        repo_in: Update data.

    Returns:
        Updated repository.
    """
    update_data = repo_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(repo, field, value)

    await db.flush()
    await db.refresh(repo)

    return repo


async def delete_repository(db: AsyncSession, repo: Repository) -> None:
    """
    Delete a repository.

    Args:
        db: Database session.
        repo: Repository to delete (already verified for tenant access).
    """
    await db.delete(repo)
    await db.flush()
