"""
Repository Service.

Business logic for Repository CRUD operations.
"""

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Repository
from app.schemas import RepositoryCreate, RepositoryUpdate


async def get_repositories(
    db: AsyncSession,
    *,
    skip: int = 0,
    limit: int = 20,
    is_active: bool | None = None,
) -> tuple[list[Repository], int]:
    """
    Get list of repositories with optional filtering.

    Args:
        db: Database session.
        skip: Number of records to skip.
        limit: Maximum number of records to return.
        is_active: Filter by active status.

    Returns:
        Tuple of (repositories list, total count).
    """
    query = select(Repository)

    if is_active is not None:
        query = query.where(Repository.is_active == is_active)

    # Get total count
    count_query = select(Repository.id)
    if is_active is not None:
        count_query = count_query.where(Repository.is_active == is_active)
    count_result = await db.execute(count_query)
    total = len(count_result.all())

    # Get paginated results
    query = query.offset(skip).limit(limit).order_by(Repository.created_at.desc())
    result = await db.execute(query)
    repositories = list(result.scalars().all())

    return repositories, total


async def get_repository_by_id(db: AsyncSession, repo_id: str) -> Repository | None:
    """
    Get a repository by ID.

    Args:
        db: Database session.
        repo_id: Repository UUID.

    Returns:
        Repository if found, None otherwise.
    """
    result = await db.execute(select(Repository).where(Repository.id == repo_id))
    return result.scalar_one_or_none()


async def get_repository_by_name(db: AsyncSession, name: str) -> Repository | None:
    """
    Get a repository by name (owner/repo format).

    Args:
        db: Database session.
        name: Repository name in owner/repo format.

    Returns:
        Repository if found, None otherwise.
    """
    result = await db.execute(select(Repository).where(Repository.name == name))
    return result.scalar_one_or_none()


async def create_repository(db: AsyncSession, repo_in: RepositoryCreate) -> Repository:
    """
    Create a new repository.

    Args:
        db: Database session.
        repo_in: Repository creation data.

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
        repo: Existing repository.
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
        repo: Repository to delete.
    """
    await db.delete(repo)
    await db.flush()
