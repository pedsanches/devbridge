"""
Code Review Service.

Service layer for CodeReview model operations.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.code_review import CodeReview
from app.schemas.code_review import CodeReviewCreate


async def get_or_create_review(
    db: AsyncSession, review_in: CodeReviewCreate
) -> tuple[CodeReview, bool]:
    """
    Get existing code review or create new.

    Args:
        db: Database session.
        review_in: Review data to create.

    Returns:
        Tuple of (CodeReview, created_flag).
    """
    query = select(CodeReview).where(
        CodeReview.activity_id == str(review_in.activity_id),
        CodeReview.review_id == review_in.review_id,
    )
    result = await db.execute(query)
    existing = result.scalar_one_or_none()

    if existing:
        return existing, False

    review = CodeReview(
        activity_id=str(review_in.activity_id),
        review_id=review_in.review_id,
        reviewer=review_in.reviewer,
        state=review_in.state,
        body=review_in.body,
        submitted_at=review_in.submitted_at,
        comments_count=review_in.comments_count,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review, True


async def get_reviews_by_activity(db: AsyncSession, activity_id: UUID) -> list[CodeReview]:
    """
    Get all reviews for a specific activity (PR).

    Args:
        db: Database session.
        activity_id: Activity UUID.

    Returns:
        List of CodeReview objects.
    """
    query = (
        select(CodeReview)
        .where(CodeReview.activity_id == str(activity_id))
        .order_by(CodeReview.submitted_at.asc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def count_reviews_by_reviewer(db: AsyncSession, reviewer: str) -> int:
    """Count total reviews given by a specific reviewer."""
    query = select(CodeReview).where(CodeReview.reviewer == reviewer)
    result = await db.execute(query)
    return len(list(result.scalars().all()))
