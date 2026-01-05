"""
Activity Service.

Business logic for Activity and BusinessUpdate operations.
"""

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Activity, ActivityType, BusinessUpdate
from app.schemas import ActivityCreate, BusinessUpdateCreate


async def get_activities(
    db: AsyncSession,
    *,
    organization_id: str | None = None,
    repository_id: UUID | None = None,
    activity_type: ActivityType | None = None,
    skip: int = 0,
    limit: int = 20,
    include_updates: bool = False,
) -> tuple[list[Activity], int]:
    """
    Get list of activities with optional filtering.

    Args:
        db: Database session.
        organization_id: Filter by organization ID (multi-tenant).
        repository_id: Filter by repository ID.
        activity_type: Filter by activity type (COMMIT/PULL_REQUEST).
        skip: Number of records to skip.
        limit: Maximum number of records to return.
        include_updates: Whether to eager load business updates.

    Returns:
        Tuple of (activities list, total count).
    """
    from app.models import Repository

    query = select(Activity)

    # Multi-tenant: filter by organization through repository
    if organization_id:
        query = query.join(Repository).where(Repository.organization_id == organization_id)

    if repository_id:
        query = query.where(Activity.repository_id == repository_id)
    if activity_type:
        query = query.where(Activity.type == activity_type)
    if include_updates:
        query = query.options(selectinload(Activity.business_update))

    # Get total count
    count_query = select(Activity.id)
    if organization_id:
        count_query = count_query.join(Repository).where(
            Repository.organization_id == organization_id
        )
    if repository_id:
        count_query = count_query.where(Activity.repository_id == repository_id)
    if activity_type:
        count_query = count_query.where(Activity.type == activity_type)

    count_result = await db.execute(count_query)
    total = len(count_result.all())

    from sqlalchemy import func

    # Get paginated results
    query = (
        query.offset(skip)
        .limit(limit)
        .order_by(func.coalesce(Activity.occurred_at, Activity.created_at).desc())
    )
    result = await db.execute(query)
    activities = list(result.scalars().all())

    return activities, total


async def get_activity_by_id(
    db: AsyncSession,
    activity_id: UUID,
    include_update: bool = False,
) -> Activity | None:
    """
    Get an activity by ID.

    Args:
        db: Database session.
        activity_id: Activity UUID.
        include_update: Whether to eager load business update.

    Returns:
        Activity if found, None otherwise.
    """
    query = select(Activity).where(Activity.id == activity_id)
    if include_update:
        query = query.options(selectinload(Activity.business_update))

    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_activity_by_external_id(
    db: AsyncSession,
    repository_id: UUID,
    external_id: str,
) -> Activity | None:
    """
    Get an activity by external ID (SHA or PR number).

    Args:
        db: Database session.
        repository_id: Repository UUID.
        external_id: GitHub SHA or PR number.

    Returns:
        Activity if found, None otherwise.
    """
    result = await db.execute(
        select(Activity).where(
            Activity.repository_id == repository_id,
            Activity.external_id == external_id,
        )
    )
    return result.scalar_one_or_none()


async def create_activity(db: AsyncSession, activity_in: ActivityCreate) -> Activity:
    """
    Create a new activity.

    Args:
        db: Database session.
        activity_in: Activity creation data.

    Returns:
        Created activity.
    """
    activity = Activity(
        id=str(uuid4()),
        repository_id=activity_in.repository_id,
        external_id=activity_in.external_id,
        type=activity_in.type,
        title=activity_in.title,
        content=activity_in.content,
        author=activity_in.author,
        occurred_at=activity_in.occurred_at,
    )

    db.add(activity)
    await db.flush()
    await db.refresh(activity)

    return activity


async def create_business_update(
    db: AsyncSession,
    update_in: BusinessUpdateCreate,
) -> BusinessUpdate:
    """
    Create a business update for an activity.

    Args:
        db: Database session.
        update_in: Business update creation data.

    Returns:
        Created business update.
    """
    business_update = BusinessUpdate(
        id=str(uuid4()),
        activity_id=update_in.activity_id,
        summary=update_in.summary,
        impact_level=update_in.impact_level,
        category=update_in.category,
    )

    db.add(business_update)
    await db.flush()
    await db.refresh(business_update)

    return business_update


async def get_or_create_activity(
    db: AsyncSession,
    activity_in: ActivityCreate,
) -> tuple[Activity, bool]:
    """
    Get existing activity or create new one.

    Args:
        db: Database session.
        activity_in: Activity data.

    Returns:
        Tuple of (activity, created_flag).
    """
    existing = await get_activity_by_external_id(
        db,
        activity_in.repository_id,
        activity_in.external_id,
    )

    if existing:
        return existing, False

    activity = await create_activity(db, activity_in)
    return activity, True
