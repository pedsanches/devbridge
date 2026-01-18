"""
Feedback API Router.

Endpoints for feedback collection and quality metrics.
Implements v1.2 with append-only history and lineage validation.

Reference: docs/architecture/continuous-learning-execution-plan.md
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentOrgId, get_current_user, get_current_user_required, get_db
from app.models.user import User
from app.schemas.feedback import (
    FeedbackCreate,
    FeedbackForConversationResponse,
    FeedbackFunnel,
    FeedbackStats,
    IdempotencyResult,
    QualityScore,
)
from app.services.feedback_service import FeedbackService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "",
    response_model=IdempotencyResult,
    status_code=status.HTTP_200_OK,
    summary="Submit feedback",
    description="""
    Submit feedback for a chat message.

    **Append-only Model**: Vote changes create new records with supersedes_id
    linking to the previous feedback. This preserves complete history for ML.

    **Idempotency**: If the same feedback (same user, message, type) is submitted
    multiple times, only the first submission is persisted. Subsequent calls
    return the existing feedback without errors.

    **Required Lineage**: `generation_id` and `prompt_version_id` are mandatory
    for traceability. Feedback without lineage is rejected.
    """,
)
async def submit_feedback(
    feedback: FeedbackCreate,
    org_id: CurrentOrgId,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
) -> IdempotencyResult:
    """
    Submit feedback with append-only semantics.

    Returns 200 whether the feedback was newly created or already existed.
    Check the `created` field to determine if it was a new submission.
    """
    service = FeedbackService(db)

    try:
        # Log feedback.received for funnel tracking (before processing)
        await service.log_feedback_received(
            feedback_data=feedback,
            organization_id=org_id,
            user_id=current_user.id,
            trace_id=feedback.trace_id,
        )

        result = await service.submit_feedback(
            feedback_data=feedback,
            organization_id=UUID(org_id),
            user_id=UUID(current_user.id),
        )
        await db.commit()
        return result
    except Exception as e:
        import traceback

        with open("/tmp/devbridge_error.log", "a") as f:
            f.write(f"Error in submit_feedback: {e}\n")
            traceback.print_exc(file=f)
        await db.rollback()
        logger.exception("Failed to submit feedback")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}",
        ) from e


@router.get(
    "/conversation/{conversation_id}",
    response_model=FeedbackForConversationResponse,
    summary="Get feedback for conversation",
    description="Get the current user's explicit feedback for a conversation (for UI hydration).",
)
async def get_feedback_for_conversation(
    conversation_id: UUID,
    org_id: CurrentOrgId,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
) -> FeedbackForConversationResponse:
    service = FeedbackService(db)

    items = await service.get_feedback_for_conversation(
        organization_id=UUID(org_id),
        conversation_id=conversation_id,
        user_id=UUID(current_user.id),
    )

    logger.info(
        "Feedback hydration loaded",
        extra={
            "conversation_id": str(conversation_id),
            "organization_id": str(org_id),
            "user_id": str(current_user.id),
            "items_count": len(items),
            "message_ids": [str(i.message_id) for i in items][:25],
        },
    )

    return FeedbackForConversationResponse(conversation_id=conversation_id, items=items)


@router.get(
    "/stats",
    response_model=FeedbackStats,
    summary="Get feedback statistics",
    description="Get aggregated feedback statistics for the organization.",
)
async def get_feedback_stats(
    org_id: CurrentOrgId,
    period_days: int = Query(7, ge=1, le=90, description="Period in days"),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> FeedbackStats:
    """Get feedback statistics for the current organization."""
    service = FeedbackService(db)

    return await service.get_feedback_stats(
        organization_id=UUID(org_id),
        period_days=period_days,
    )


@router.get(
    "/quality-score",
    response_model=QualityScore,
    summary="Get quality score",
    description="""
    Calculate the quality score v1.1 for the organization.

    The score is weighted:
    - Explicit feedback (thumbs up/down): weight 1.0
    - Implicit feedback (regeneration, copy, etc.): weight 0.3

    Confidence levels:
    - **low**: Less than 10 feedbacks (score not calculated)
    - **medium**: 10-50 feedbacks
    - **high**: 50+ feedbacks

    **Important**: Alerts should only trigger when confidence is HIGH.
    """,
)
async def get_quality_score(
    org_id: CurrentOrgId,
    period_days: int = Query(7, ge=1, le=90, description="Period in days"),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> QualityScore:
    """Calculate quality score with confidence level."""
    service = FeedbackService(db)

    return await service.calculate_quality_score(
        organization_id=UUID(org_id),
        period_days=period_days,
    )


@router.get(
    "/funnel",
    response_model=FeedbackFunnel,
    summary="Get feedback funnel",
    description="""
    Get feedback funnel metrics for observability.

    Stages:
    1. **generated**: Chat responses created by LLM
    2. **displayed**: Responses shown to user (>2s view time)
    3. **received**: Feedback events sent from UI
    4. **persisted**: Feedback successfully saved to database

    Use this to diagnose drop-offs:
    - Drop in generated→displayed = Latency/error issues
    - Drop in displayed→received = UX issues with feedback buttons
    - Drop in received→persisted = Backend validation/error issues
    """,
)
async def get_feedback_funnel(
    org_id: CurrentOrgId,
    period_days: int = Query(7, ge=1, le=90, description="Period in days"),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> FeedbackFunnel:
    """Get feedback funnel metrics."""
    service = FeedbackService(db)

    return await service.get_feedback_funnel(
        organization_id=UUID(org_id),
        period_days=period_days,
    )


@router.post(
    "/events/displayed",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Log response displayed",
    description="Log that a chat response was displayed to the user (funnel tracking).",
)
async def log_response_displayed(
    org_id: CurrentOrgId,
    generation_id: str = Query(..., description="Generation ID"),
    message_id: str = Query(..., description="Message ID"),
    trace_id: str | None = Query(None, description="Trace ID"),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> None:
    """Log response displayed event for funnel tracking."""
    service = FeedbackService(db)

    try:
        await service.log_response_displayed(
            generation_id=generation_id,
            message_id=message_id,
            organization_id=org_id,
            trace_id=trace_id,
        )
        await db.commit()
    except Exception as e:
        import traceback

        with open("/tmp/devbridge_error.log", "a") as f:
            f.write(f"Error in log_response_displayed: {e}\n")
            traceback.print_exc(file=f)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error logging displayed: {str(e)}",
        ) from e
