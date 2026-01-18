"""
Tests for FeedbackService.

Tests the append-only feedback model with supersedes chain,
idempotency, and funnel event logging.
"""

from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import ChatMessage, Conversation
from app.models.feedback import EventLog, Feedback, FeedbackSource
from app.schemas.feedback import FeedbackCreate
from app.schemas.feedback import FeedbackType as SchemaFeedbackType
from app.services.feedback_service import FeedbackService


@pytest.fixture
async def test_conversation(db_session: AsyncSession, test_org, test_user) -> Conversation:
    """Create a test conversation with a message."""
    conversation = Conversation(
        organization_id=str(test_org.id),
        user_id=str(test_user.id),
        title="Test Conversation",
    )
    db_session.add(conversation)
    await db_session.flush()
    return conversation


@pytest.fixture
async def test_message(db_session: AsyncSession, test_conversation) -> ChatMessage:
    """Create a test chat message."""
    message = ChatMessage(
        conversation_id=str(test_conversation.id),
        role="assistant",
        content="This is a test response.",
        message_metadata={
            "generation_id": "gen-123",
            "prompt_version_id": "v1.0.0",
        },
    )
    db_session.add(message)
    await db_session.flush()
    return message


@pytest.mark.asyncio
async def test_submit_feedback_creates_new_record(
    db_session: AsyncSession, test_org, test_user, test_conversation, test_message
):
    """Test that submitting feedback creates a new record."""
    service = FeedbackService(db_session)

    feedback_data = FeedbackCreate(
        message_id=UUID(test_message.id),
        conversation_id=UUID(test_conversation.id),
        feedback_type=SchemaFeedbackType.THUMBS_UP,
        generation_id="gen-123",
        prompt_version_id="v1.0.0",
    )

    result = await service.submit_feedback(
        feedback_data=feedback_data,
        organization_id=UUID(test_org.id),
        user_id=UUID(test_user.id),
    )
    await db_session.flush()

    assert result.created is True
    assert result.feedback_id is not None

    # Verify record in database
    stmt = select(Feedback).where(Feedback.id == str(result.feedback_id))
    res = await db_session.execute(stmt)
    feedback = res.scalar_one()

    assert feedback.feedback_type == "thumbs_up"
    assert feedback.source == FeedbackSource.EXPLICIT.value
    assert feedback.score_raw == 1.0
    assert feedback.supersedes_id is None


@pytest.mark.asyncio
async def test_submit_feedback_idempotent_same_type(
    db_session: AsyncSession, test_org, test_user, test_conversation, test_message
):
    """Test that submitting the same feedback type twice is idempotent."""
    service = FeedbackService(db_session)

    feedback_data = FeedbackCreate(
        message_id=UUID(test_message.id),
        conversation_id=UUID(test_conversation.id),
        feedback_type=SchemaFeedbackType.THUMBS_UP,
        generation_id="gen-123",
        prompt_version_id="v1.0.0",
    )

    # First submission
    result1 = await service.submit_feedback(
        feedback_data=feedback_data,
        organization_id=UUID(test_org.id),
        user_id=UUID(test_user.id),
    )
    await db_session.flush()

    # Second submission (same type)
    result2 = await service.submit_feedback(
        feedback_data=feedback_data,
        organization_id=UUID(test_org.id),
        user_id=UUID(test_user.id),
    )
    await db_session.flush()

    assert result1.created is True
    assert result2.created is False
    assert result1.feedback_id == result2.feedback_id


@pytest.mark.asyncio
async def test_vote_change_creates_supersedes_chain(
    db_session: AsyncSession, test_org, test_user, test_conversation, test_message
):
    """Test that changing vote creates a new record with supersedes_id."""
    service = FeedbackService(db_session)

    # First vote: thumbs up
    feedback_data_up = FeedbackCreate(
        message_id=UUID(test_message.id),
        conversation_id=UUID(test_conversation.id),
        feedback_type=SchemaFeedbackType.THUMBS_UP,
        generation_id="gen-123",
        prompt_version_id="v1.0.0",
    )

    result1 = await service.submit_feedback(
        feedback_data=feedback_data_up,
        organization_id=UUID(test_org.id),
        user_id=UUID(test_user.id),
    )
    await db_session.flush()

    # Second vote: thumbs down (vote change)
    feedback_data_down = FeedbackCreate(
        message_id=UUID(test_message.id),
        conversation_id=UUID(test_conversation.id),
        feedback_type=SchemaFeedbackType.THUMBS_DOWN,
        generation_id="gen-123",
        prompt_version_id="v1.0.0",
    )

    result2 = await service.submit_feedback(
        feedback_data=feedback_data_down,
        organization_id=UUID(test_org.id),
        user_id=UUID(test_user.id),
    )
    await db_session.flush()

    assert result1.created is True
    assert result2.created is True
    assert result1.feedback_id != result2.feedback_id

    # Verify supersedes chain
    stmt = select(Feedback).where(Feedback.id == str(result2.feedback_id))
    res = await db_session.execute(stmt)
    feedback2 = res.scalar_one()

    assert feedback2.supersedes_id == str(result1.feedback_id)
    assert feedback2.feedback_type == "thumbs_down"
    assert feedback2.score_raw == -1.0


@pytest.mark.asyncio
async def test_get_feedback_for_conversation_returns_latest(
    db_session: AsyncSession, test_org, test_user, test_conversation, test_message
):
    """Test that get_feedback_for_conversation returns only the latest feedback per message."""
    service = FeedbackService(db_session)

    # Submit multiple feedbacks (vote change)
    for feedback_type in [SchemaFeedbackType.THUMBS_UP, SchemaFeedbackType.THUMBS_DOWN]:
        feedback_data = FeedbackCreate(
            message_id=UUID(test_message.id),
            conversation_id=UUID(test_conversation.id),
            feedback_type=feedback_type,
            generation_id="gen-123",
            prompt_version_id="v1.0.0",
        )
        await service.submit_feedback(
            feedback_data=feedback_data,
            organization_id=UUID(test_org.id),
            user_id=UUID(test_user.id),
        )
        await db_session.flush()

    # Get feedbacks for conversation
    items = await service.get_feedback_for_conversation(
        organization_id=UUID(test_org.id),
        conversation_id=UUID(test_conversation.id),
        user_id=UUID(test_user.id),
    )

    # Should return only one item (the latest)
    assert len(items) == 1
    assert items[0].feedback_type == "thumbs_down"


@pytest.mark.asyncio
async def test_feedback_persisted_event_logged(
    db_session: AsyncSession, test_org, test_user, test_conversation, test_message
):
    """Test that feedback.persisted event is logged on submission."""
    service = FeedbackService(db_session)

    feedback_data = FeedbackCreate(
        message_id=UUID(test_message.id),
        conversation_id=UUID(test_conversation.id),
        feedback_type=SchemaFeedbackType.THUMBS_UP,
        generation_id="gen-123",
        prompt_version_id="v1.0.0",
        trace_id="trace-test-123",
    )

    result = await service.submit_feedback(
        feedback_data=feedback_data,
        organization_id=UUID(test_org.id),
        user_id=UUID(test_user.id),
    )
    await db_session.flush()

    # Verify event was logged
    stmt = select(EventLog).where(
        EventLog.event_type == "feedback.persisted",
        EventLog.generation_id == "gen-123",
    )
    res = await db_session.execute(stmt)
    event = res.scalar_one_or_none()

    assert event is not None
    assert event.trace_id == "trace-test-123"
    assert event.message_id == str(test_message.id)
    assert event.organization_id == str(test_org.id)
    assert event.payload["feedback_id"] == str(result.feedback_id)
    assert event.payload["type"] == "thumbs_up"


@pytest.mark.asyncio
async def test_log_feedback_received(
    db_session: AsyncSession, test_org, test_user, test_conversation, test_message
):
    """Test that feedback.received event can be logged."""
    service = FeedbackService(db_session)

    feedback_data = FeedbackCreate(
        message_id=UUID(test_message.id),
        conversation_id=UUID(test_conversation.id),
        feedback_type=SchemaFeedbackType.THUMBS_UP,
        generation_id="gen-456",
        prompt_version_id="v1.0.0",
    )

    await service.log_feedback_received(
        feedback_data=feedback_data,
        organization_id=str(test_org.id),
        user_id=str(test_user.id),
        trace_id="trace-received-123",
    )
    await db_session.flush()

    # Verify event was logged
    stmt = select(EventLog).where(
        EventLog.event_type == "feedback.received",
        EventLog.generation_id == "gen-456",
    )
    res = await db_session.execute(stmt)
    event = res.scalar_one_or_none()

    assert event is not None
    assert event.trace_id == "trace-received-123"
    assert event.payload["feedback_type"] == "thumbs_up"
