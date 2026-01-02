"""
Activity Endpoints.

API for viewing activities and business updates.
"""

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import DbSession
from app.schemas import (
    ActivityWithUpdate,
    PaginatedResponse,
)
from app.services import activity_service

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_activities(
    db: DbSession,
    repository_id: str | None = Query(None, description="Filter by repository"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> PaginatedResponse:
    """
    List all activities with optional filtering.

    Args:
        db: Database session.
        repository_id: Filter by repository ID.
        page: Page number (1-indexed).
        page_size: Number of items per page.

    Returns:
        Paginated list of activities.
    """
    skip = (page - 1) * page_size
    activities, total = await activity_service.get_activities(
        db,
        repository_id=repository_id,
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
    activity = await activity_service.get_activity_by_id(db, activity_id, include_update=True)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    return ActivityWithUpdate.model_validate(activity)
