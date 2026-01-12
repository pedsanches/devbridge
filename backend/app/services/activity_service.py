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
    team_id: str | int | None = None,
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
        team_id: Filter by Team ID (includes direct and grouped repositories).
        activity_type: Filter by activity type (COMMIT/PULL_REQUEST).
        skip: Number of records to skip.
        limit: Maximum number of records to return.
        include_updates: Whether to eager load business updates.

    Returns:
        Tuple of (activities list, total count).
    """
    from sqlalchemy import or_

    from app.models import Repository
    from app.models.team import team_repositories

    query = select(Activity).join(Repository)

    # Multi-tenant: filter by organization through repository
    if organization_id:
        query = query.where(Repository.organization_id == organization_id)

    if repository_id:
        query = query.where(Activity.repository_id == repository_id)

    if team_id:
        # Filter by team: either direct ownership (team_id) or via group association
        query = query.outerjoin(
            team_repositories, Repository.id == team_repositories.c.repository_id
        ).where(
            or_(Repository.team_id == str(team_id), team_repositories.c.team_id == str(team_id))
        )

    if activity_type:
        query = query.where(Activity.type == activity_type)
    if include_updates:
        query = query.options(selectinload(Activity.business_update))

    # Get total count
    count_query = select(Activity.id).join(Repository)
    if organization_id:
        count_query = count_query.where(Repository.organization_id == organization_id)
    if repository_id:
        count_query = count_query.where(Activity.repository_id == repository_id)

    if team_id:
        count_query = count_query.outerjoin(
            team_repositories, Repository.id == team_repositories.c.repository_id
        ).where(
            or_(Repository.team_id == str(team_id), team_repositories.c.team_id == str(team_id))
        )

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

    # Manually load business_updates due to UUID/str type mismatch in relationships
    if include_updates and activities:
        from uuid import UUID as PyUUID

        activity_ids = [PyUUID(a.id) for a in activities]
        bu_query = select(BusinessUpdate).where(BusinessUpdate.activity_id.in_(activity_ids))
        bu_result = await db.execute(bu_query)
        bu_map = {str(bu.activity_id): bu for bu in bu_result.scalars().all()}

        for activity in activities:
            activity.business_update = bu_map.get(activity.id)

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
    query = select(Activity).where(Activity.id == str(activity_id))

    result = await db.execute(query)
    activity = result.scalar_one_or_none()

    # Manually load business_update due to UUID/str type mismatch
    if activity and include_update:
        bu_query = select(BusinessUpdate).where(BusinessUpdate.activity_id == activity_id)
        bu_result = await db.execute(bu_query)
        activity.business_update = bu_result.scalar_one_or_none()

    return activity


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


async def _calculate_metrics(activity: Activity) -> None:
    """Calculate time-based metrics for an activity."""
    if not activity.occurred_at:
        return

    # Cycle Time: Time from creation to merge
    if activity.merged_at:
        delta = activity.merged_at - activity.occurred_at
        activity.cycle_time_hours = delta.total_seconds() / 3600

    # Pickup Time: Time from creation to first review
    if activity.first_review_at:
        delta = activity.first_review_at - activity.occurred_at
        activity.pickup_time_hours = delta.total_seconds() / 3600

    # Review Time: Time from first review to approval
    if activity.first_review_at and activity.approved_at:
        delta = activity.approved_at - activity.first_review_at
        activity.review_time_hours = delta.total_seconds() / 3600

    # Merge Time: Time from approval to merge
    if activity.approved_at and activity.merged_at:
        delta = activity.merged_at - activity.approved_at
        activity.merge_time_hours = delta.total_seconds() / 3600


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
        files_touched=activity_in.files_touched,
        labels=activity_in.labels,
        linked_issues=activity_in.linked_issues,
        value_tags=activity_in.value_tags,
        # Code Metrics
        lines_added=activity_in.lines_added,
        lines_deleted=activity_in.lines_deleted,
        files_changed_count=activity_in.files_changed_count,
        # PR Lifecycle
        first_review_at=activity_in.first_review_at,
        approved_at=activity_in.approved_at,
        merged_at=activity_in.merged_at,
    )

    await _calculate_metrics(activity)

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
    Get existing activity (and update it) or create new one.

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
        # Update fields if provided (Context Enrichment & Metrics)
        changed = False

        # Helper to update field if changed
        for field in [
            "files_touched",
            "labels",
            "linked_issues",
            "value_tags",
            "lines_added",
            "lines_deleted",
            "files_changed_count",
            "first_review_at",
            "approved_at",
            "merged_at",
        ]:
            new_val = getattr(activity_in, field)
            if new_val is not None and getattr(existing, field) != new_val:
                setattr(existing, field, new_val)
                changed = True

        if changed:
            await _calculate_metrics(existing)
            db.add(existing)
            await db.flush()
            await db.refresh(existing)

        return existing, False

    activity = await create_activity(db, activity_in)
    return activity, True
