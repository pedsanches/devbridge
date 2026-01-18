"""
Feedback Service.

Business logic for feedback collection, deduplication, and quality scoring.
Implements v1.2 with append-only history, lineage validation, and weighted scoring.

Key behaviors:
- Append-only: Feedback is never updated; vote changes create new records
- Idempotency: Same feedback_type for same user+message is deduplicated
- Supersedes chain: New feedback references previous via supersedes_id

Reference: docs/architecture/continuous-learning-execution-plan.md
"""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feedback import (
    FEEDBACK_SCORE_MAP,
    FEEDBACK_SOURCE_MAP,
    EventLog,
    Feedback,
    FeedbackSource,
    FeedbackType,
    generate_idempotency_key,
)
from app.schemas.feedback import (
    FeedbackCreate,
    FeedbackForConversationItem,
    FeedbackFunnel,
    FeedbackFunnelStage,
    FeedbackStats,
    IdempotencyResult,
    QualityScore,
    QualityScoreConfidence,
)

logger = logging.getLogger(__name__)

# Configuration constants
MIN_SAMPLE_SIZE_MEDIUM = 10
MIN_SAMPLE_SIZE_HIGH = 50
MAX_VARIANCE_HIGH = 0.2
WEIGHT_EXPLICIT = 1.0
WEIGHT_IMPLICIT = 0.3


class FeedbackService:
    """
    Service for managing feedback collection and analysis.

    Key Responsibilities:
    - Idempotent feedback submission (deduplication)
    - Lineage validation (generation_id, prompt_version_id required)
    - Quality score calculation with confidence levels
    - Event logging for funnel analysis
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def submit_feedback(
        self,
        feedback_data: FeedbackCreate,
        organization_id: UUID,
        user_id: UUID | None = None,
    ) -> IdempotencyResult:
        """
        Submit feedback with append-only semantics.

        Behavior:
        - If identical feedback exists (same user+message+type): return existing (idempotent)
        - If different feedback exists (same user+message, different type): create new with supersedes_id
        - Otherwise: create new feedback

        Args:
            feedback_data: Feedback creation data
            organization_id: Organization ID (multi-tenant isolation)
            user_id: Optional user ID

        Returns:
            IdempotencyResult with created flag and feedback ID
        """
        # Determine score and source from type
        feedback_type = FeedbackType(feedback_data.feedback_type.value)
        score_raw = FEEDBACK_SCORE_MAP[feedback_type]
        source = FEEDBACK_SOURCE_MAP[feedback_type]

        user_id_str = str(user_id) if user_id else None
        message_id_str = str(feedback_data.message_id)

        # Generate idempotency key (includes feedback_type for deduplication)
        idempotency_key = generate_idempotency_key(
            user_id=user_id_str,
            message_id=message_id_str,
            feedback_type=feedback_type.value,
        )

        # Check for existing identical feedback (same type = duplicate submission)
        existing_identical = await self._get_by_idempotency_key(idempotency_key)
        if existing_identical:
            logger.info(
                "Feedback deduplicated (identical)",
                extra={
                    "feedback_id": existing_identical.id,
                    "type": feedback_type.value,
                },
            )
            return IdempotencyResult(
                created=False,
                feedback_id=UUID(existing_identical.id),
                message="Feedback already exists",
            )

        # Check for previous feedback on same message (vote change scenario)
        previous_feedback = await self._get_latest_feedback_for_message(
            user_id=user_id_str,
            message_id=message_id_str,
        )

        supersedes_id = previous_feedback.id if previous_feedback else None

        # Create new feedback (append-only)
        feedback = Feedback(
            idempotency_key=idempotency_key,
            supersedes_id=supersedes_id,
            organization_id=str(organization_id),
            user_id=user_id_str,
            message_id=message_id_str,
            conversation_id=str(feedback_data.conversation_id),
            generation_id=feedback_data.generation_id,
            prompt_version_id=feedback_data.prompt_version_id,
            trace_id=feedback_data.trace_id,
            feedback_type=feedback_type.value,
            source=source.value,
            score_raw=score_raw,
            weight=1.0,  # Default trust weight
            score_effective=score_raw * 1.0,  # Will be recalculated by event listener
            persona=feedback_data.persona,
            extra_metadata=feedback_data.metadata,
        )

        self.db.add(feedback)
        await self.db.flush()

        # Log event for funnel
        await self._log_event(
            event_type="feedback.persisted",
            trace_id=feedback_data.trace_id,
            generation_id=feedback_data.generation_id,
            message_id=message_id_str,
            user_id=user_id_str,
            organization_id=str(organization_id),
            payload={
                "feedback_id": feedback.id,
                "type": feedback_type.value,
                "supersedes_id": supersedes_id,
            },
        )

        log_message = "Feedback created (vote change)" if supersedes_id else "Feedback created"
        logger.info(
            log_message,
            extra={
                "feedback_id": feedback.id,
                "type": feedback_type.value,
                "score_effective": feedback.score_effective,
                "supersedes_id": supersedes_id,
            },
        )

        return IdempotencyResult(
            created=True,
            feedback_id=UUID(feedback.id),
            message=log_message,
        )

    async def _get_by_idempotency_key(self, key: str) -> Feedback | None:
        """Get feedback by idempotency key."""
        result = await self.db.execute(select(Feedback).where(Feedback.idempotency_key == key))
        return result.scalar_one_or_none()

    async def _get_latest_feedback_for_message(
        self,
        user_id: str | None,
        message_id: str,
    ) -> Feedback | None:
        """Get the most recent feedback for a user+message combination."""
        query = (
            select(Feedback)
            .where(
                Feedback.message_id == message_id,
                Feedback.user_id == user_id if user_id else Feedback.user_id.is_(None),
            )
            .order_by(Feedback.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def log_feedback_received(
        self,
        feedback_data: FeedbackCreate,
        organization_id: str,
        user_id: str | None = None,
        trace_id: str | None = None,
    ) -> None:
        """Log that a feedback request was received (for funnel tracking)."""
        await self._log_event(
            event_type="feedback.received",
            trace_id=trace_id,
            generation_id=feedback_data.generation_id,
            message_id=str(feedback_data.message_id),
            user_id=user_id,
            organization_id=organization_id,
            payload={"feedback_type": feedback_data.feedback_type.value},
        )

    async def get_feedback_for_conversation(
        self,
        organization_id: UUID,
        conversation_id: UUID,
        user_id: UUID,
    ) -> list[FeedbackForConversationItem]:
        """
        Get the latest explicit feedback for each message in a conversation.

        Uses a subquery to find the most recent feedback per message_id,
        supporting the append-only model where vote changes create new records.
        """
        # Subquery to get max created_at per message_id for this user
        latest_subquery = (
            select(
                Feedback.message_id,
                func.max(Feedback.created_at).label("max_created_at"),
            )
            .where(
                Feedback.organization_id == str(organization_id),
                Feedback.conversation_id == str(conversation_id),
                Feedback.user_id == str(user_id),
                Feedback.source == FeedbackSource.EXPLICIT.value,
            )
            .group_by(Feedback.message_id)
            .subquery()
        )

        # Join to get full feedback records
        result = await self.db.execute(
            select(Feedback)
            .join(
                latest_subquery,
                (Feedback.message_id == latest_subquery.c.message_id)
                & (Feedback.created_at == latest_subquery.c.max_created_at),
            )
            .where(
                Feedback.organization_id == str(organization_id),
                Feedback.conversation_id == str(conversation_id),
                Feedback.user_id == str(user_id),
                Feedback.source == FeedbackSource.EXPLICIT.value,
            )
            .order_by(Feedback.created_at.asc())
        )
        feedbacks = list(result.scalars().all())
        return [
            FeedbackForConversationItem(
                message_id=f.message_id,  # Already a string, no UUID conversion needed
                feedback_type=f.feedback_type,
                created_at=f.created_at,
            )
            for f in feedbacks
        ]

    async def get_feedback_stats(
        self,
        organization_id: UUID,
        period_days: int = 7,
    ) -> FeedbackStats:
        """
        Get feedback statistics for an organization.

        Args:
            organization_id: Organization ID
            period_days: Number of days to analyze

        Returns:
            FeedbackStats with counts and average score
        """
        since = datetime.now(UTC) - timedelta(days=period_days)

        # Base query
        base_query = select(Feedback).where(
            Feedback.organization_id == str(organization_id),
            Feedback.created_at >= since,
        )

        result = await self.db.execute(base_query)
        feedbacks = result.scalars().all()

        if not feedbacks:
            return FeedbackStats(
                total_count=0,
                explicit_count=0,
                implicit_count=0,
                positive_count=0,
                negative_count=0,
                average_score=None,
                period_days=period_days,
            )

        explicit_count = sum(1 for f in feedbacks if f.source == FeedbackSource.EXPLICIT.value)
        implicit_count = sum(1 for f in feedbacks if f.source == FeedbackSource.IMPLICIT.value)
        positive_count = sum(1 for f in feedbacks if f.score_raw > 0)
        negative_count = sum(1 for f in feedbacks if f.score_raw < 0)
        avg_score = sum(f.score_effective for f in feedbacks) / len(feedbacks)

        return FeedbackStats(
            total_count=len(feedbacks),
            explicit_count=explicit_count,
            implicit_count=implicit_count,
            positive_count=positive_count,
            negative_count=negative_count,
            average_score=avg_score,
            period_days=period_days,
        )

    async def calculate_quality_score(
        self,
        organization_id: UUID,
        period_days: int = 7,
    ) -> QualityScore:
        """
        Calculate quality score v1.1 with weighted explicit/implicit feedback.

        Formula:
            overall = (explicit_score * W_EXPLICIT + implicit_score * W_IMPLICIT)
                      / (W_EXPLICIT + W_IMPLICIT)

        Confidence based on sample size and variance.

        Args:
            organization_id: Organization ID
            period_days: Number of days to analyze

        Returns:
            QualityScore with value, confidence, and breakdown
        """
        since = datetime.now(UTC) - timedelta(days=period_days)

        result = await self.db.execute(
            select(Feedback).where(
                Feedback.organization_id == str(organization_id),
                Feedback.created_at >= since,
            )
        )
        feedbacks = list(result.scalars().all())
        total = len(feedbacks)

        # Insufficient data
        if total < MIN_SAMPLE_SIZE_MEDIUM:
            return QualityScore(
                value=None,
                confidence=QualityScoreConfidence.LOW,
                sample_size=total,
                explicit_score=None,
                implicit_score=None,
                period_days=period_days,
                reason="Insufficient data (need at least 10 feedbacks)",
            )

        # Separate explicit and implicit
        explicit = [f for f in feedbacks if f.source == FeedbackSource.EXPLICIT.value]
        implicit = [f for f in feedbacks if f.source == FeedbackSource.IMPLICIT.value]

        # Calculate scores (normalize to 0-1 range: (score + 1) / 2)
        def to_positive_rate(items: list[Feedback]) -> float | None:
            if not items:
                return None
            positive = sum(1 for f in items if f.score_raw > 0)
            return positive / len(items)

        explicit_score = to_positive_rate(explicit)
        implicit_score = to_positive_rate(implicit)

        # Weighted average
        if explicit_score is not None and implicit_score is not None:
            overall = (explicit_score * WEIGHT_EXPLICIT + implicit_score * WEIGHT_IMPLICIT) / (
                WEIGHT_EXPLICIT + WEIGHT_IMPLICIT
            )
        elif explicit_score is not None:
            overall = explicit_score
        elif implicit_score is not None:
            overall = implicit_score
        else:
            overall = None

        # Determine confidence
        if total >= MIN_SAMPLE_SIZE_HIGH:
            confidence = QualityScoreConfidence.HIGH
        else:
            confidence = QualityScoreConfidence.MEDIUM

        return QualityScore(
            value=overall,
            confidence=confidence,
            sample_size=total,
            explicit_score=explicit_score,
            implicit_score=implicit_score,
            period_days=period_days,
            reason=None,
        )

    async def get_feedback_funnel(
        self,
        organization_id: UUID,
        period_days: int = 7,
    ) -> FeedbackFunnel:
        """
        Get feedback funnel metrics for observability.

        Stages:
        1. chat.response.generated
        2. chat.response.displayed
        3. feedback.received
        4. feedback.persisted

        Args:
            organization_id: Organization ID
            period_days: Number of days to analyze

        Returns:
            FeedbackFunnel with stage-by-stage metrics
        """
        since = datetime.now(UTC) - timedelta(days=period_days)
        now = datetime.now(UTC)

        # Query event counts by type
        result = await self.db.execute(
            select(EventLog.event_type, func.count(EventLog.id))
            .where(
                EventLog.organization_id == str(organization_id),
                EventLog.timestamp >= since,
            )
            .group_by(EventLog.event_type)
        )
        counts = {row[0]: row[1] for row in result.all()}

        # Build funnel stages
        generated = counts.get("chat.response.generated", 0)
        displayed = counts.get("chat.response.displayed", 0)
        received = counts.get("feedback.received", 0)
        persisted = counts.get("feedback.persisted", 0)

        stages = [
            FeedbackFunnelStage(
                stage="generated",
                count=generated,
                percentage=100.0,
            ),
            FeedbackFunnelStage(
                stage="displayed",
                count=displayed,
                percentage=(displayed / generated * 100) if generated > 0 else 0.0,
            ),
            FeedbackFunnelStage(
                stage="received",
                count=received,
                percentage=(received / displayed * 100) if displayed > 0 else 0.0,
            ),
            FeedbackFunnelStage(
                stage="persisted",
                count=persisted,
                percentage=(persisted / received * 100) if received > 0 else 0.0,
            ),
        ]

        conversion_rate = (persisted / generated * 100) if generated > 0 else 0.0

        return FeedbackFunnel(
            period_start=since,
            period_end=now,
            stages=stages,
            total_generated=generated,
            total_persisted=persisted,
            conversion_rate=conversion_rate,
        )

    async def _log_event(
        self,
        event_type: str,
        trace_id: str | None = None,
        generation_id: str | None = None,
        message_id: str | None = None,
        user_id: str | None = None,
        organization_id: str | None = None,
        payload: dict | None = None,
    ) -> None:
        """Log an event for funnel tracking."""
        event = EventLog(
            event_type=event_type,
            trace_id=trace_id,
            generation_id=generation_id,
            message_id=message_id,
            user_id=user_id,
            organization_id=organization_id,
            payload=payload,
        )
        self.db.add(event)

    async def log_response_generated(
        self,
        generation_id: str,
        message_id: str,
        organization_id: str,
        trace_id: str | None = None,
        user_id: str | None = None,
        payload: dict | None = None,
    ) -> None:
        """Log that a chat response was generated."""
        await self._log_event(
            event_type="chat.response.generated",
            generation_id=generation_id,
            message_id=message_id,
            organization_id=organization_id,
            trace_id=trace_id,
            user_id=user_id,
            payload=payload,
        )

    async def log_response_displayed(
        self,
        generation_id: str,
        message_id: str,
        organization_id: str,
        trace_id: str | None = None,
    ) -> None:
        """Log that a chat response was displayed to user."""
        await self._log_event(
            event_type="chat.response.displayed",
            generation_id=generation_id,
            message_id=message_id,
            organization_id=organization_id,
            trace_id=trace_id,
        )
