"""
Activity Endpoints.

API for viewing activities and business updates.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import CurrentOrgId, DbSession
from app.schemas import (
    ActivityWithUpdate,
    BusinessUpdateCreate,
    ImpactLevel,
    PaginatedResponse,
)
from app.services import activity_service
from app.services.ai_service import ai_service

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_activities(
    db: DbSession,
    org_id: CurrentOrgId,
    repository_id: str | None = Query(None, description="Filter by repository"),
    team_id: str | None = Query(None, description="Filter by team"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> PaginatedResponse:
    """
    List all activities with optional filtering.

    Args:
        db: Database session.
        org_id: Current organization ID (from session).
        repository_id: Filter by repository ID.
        team_id: Filter by team ID.
        page: Page number (1-indexed).
        page_size: Number of items per page.

    Returns:
        Paginated list of activities.
    """
    skip = (page - 1) * page_size
    activities, total = await activity_service.get_activities(
        db,
        organization_id=org_id,
        repository_id=UUID(repository_id) if repository_id else None,
        team_id=team_id,
        skip=skip,
        limit=page_size,
        include_updates=True,
    )

    return PaginatedResponse.create(
        data=[ActivityWithUpdate.model_validate(a) for a in activities],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{activity_id}", response_model=ActivityWithUpdate)
async def get_activity(db: DbSession, activity_id: str) -> ActivityWithUpdate:
    """
    Get a specific activity by ID.

    Args:
        db: Database session.
        activity_id: Activity ID.

    Returns:
        Activity with business update if available.
    """
    activity = await activity_service.get_activity_by_id(db, UUID(activity_id), include_update=True)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    return ActivityWithUpdate.model_validate(activity)


@router.post("/{activity_id}/generate-update", response_model=ActivityWithUpdate)
async def regenerate_business_update(
    db: DbSession,
    activity_id: str,
) -> ActivityWithUpdate:
    """
    Regenerate (or generate for the first time) the business update for an activity.

    Useful for:
    - Reprocessing activities that failed initial generation
    - Regenerating updates with improved AI models
    - Processing old activities that were synced before this feature

    Args:
        db: Database session.
        activity_id: Activity ID.

    Returns:
        Activity with newly generated business update.
    """
    activity = await activity_service.get_activity_by_id(db, UUID(activity_id), include_update=True)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Generate business update
    update_data = await ai_service.generate_business_update(
        {
            "type": activity.type.value if hasattr(activity.type, "value") else str(activity.type),
            "title": activity.title,
            "content": activity.content or "",
            "labels": activity.labels or [],
            "files_touched": activity.files_touched or [],
        }
    )

    # Delete existing update if present
    if activity.business_update:
        await db.delete(activity.business_update)
        await db.flush()

    # Create new update
    update_create = BusinessUpdateCreate(
        activity_id=activity.id,
        summary=update_data["summary"],
        impact_level=ImpactLevel(update_data["impact_level"]),
        category=update_data.get("category"),
    )
    await activity_service.create_business_update(db, update_create)
    await db.commit()

    # Refresh and return
    activity = await activity_service.get_activity_by_id(db, UUID(activity_id), include_update=True)
    return ActivityWithUpdate.model_validate(activity)


@router.post("/batch-generate-updates")
async def batch_regenerate_business_updates(
    db: DbSession,
    org_id: CurrentOrgId,
) -> dict:
    """
    Batch regenerate business updates for all activities without one.

    Use this to backfill existing activities that were synced before
    the automatic business update generation was implemented.

    Returns:
        Count of processed and failed activities.
    """
    import logging

    from sqlalchemy import select

    from app.models import BusinessUpdate

    logger = logging.getLogger(__name__)

    # Get all activities for this org
    activities, _ = await activity_service.get_activities(
        db,
        organization_id=org_id,
        skip=0,
        limit=500,  # Process up to 500 at a time
        include_updates=False,  # Don't rely on eager loading
    )

    processed = 0
    failed = 0
    skipped = 0

    for activity in activities:
        # Check if business_update exists in DB directly
        existing_check = await db.execute(
            select(BusinessUpdate.id).where(BusinessUpdate.activity_id == activity.id)
        )
        if existing_check.scalar_one_or_none():
            skipped += 1
            continue

        try:
            # Generate business update
            update_data = await ai_service.generate_business_update(
                {
                    "type": (
                        activity.type.value
                        if hasattr(activity.type, "value")
                        else str(activity.type)
                    ),
                    "title": activity.title,
                    "content": activity.content or "",
                    "labels": activity.labels or [],
                    "files_touched": activity.files_touched or [],
                }
            )

            # Create new update
            update_create = BusinessUpdateCreate(
                activity_id=activity.id,
                summary=update_data["summary"],
                impact_level=ImpactLevel(update_data["impact_level"]),
                category=update_data.get("category"),
            )
            await activity_service.create_business_update(db, update_create)
            await db.commit()  # Commit each successful one
            processed += 1
        except Exception as e:
            await db.rollback()  # Rollback on error to continue
            logger.warning(f"Failed to generate update for {activity.id}: {e}")
            failed += 1

    return {
        "processed": processed,
        "failed": failed,
        "skipped": skipped,
        "total": len(activities),
    }
