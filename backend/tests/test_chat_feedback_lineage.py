from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import ChatMessage
from app.models.feedback import EventLog
from app.services.chat_service import chat_service


@pytest.mark.asyncio
async def test_chat_lineage_and_logging(db_session: AsyncSession, test_user, test_org):
    """
    Test that chat response includes lineage and logs generation event.
    """
    query = "What's new?"

    with (
        patch(
            "app.services.chat_service.ai_service.summarize_activities", new_callable=AsyncMock
        ) as mock_ai,
        patch(
            "app.services.ai_service.ai_service.generate_title", new_callable=AsyncMock
        ) as mock_title,
        patch("app.services.chat_service.get_prompt_version_id") as mock_version,
    ):
        mock_ai.return_value = "Everything is awesome."
        mock_title.return_value = "Status Update"
        # Mock version to verify propagation
        mock_version.return_value = "v1.2.3-test"

        # Call service
        result = await chat_service.process_query(
            db_session,
            query=query,
            user_id=test_user.id,
            org_id=str(test_org.id),
            trace_id="trace-123",
            use_semantic_search=False,  # Skip vector search setup
        )

        # 1. Verify Metadata returned to client
        metadata = result["metadata"]
        assert metadata.generation_id is not None
        assert len(metadata.generation_id) > 10  # Should be UUID
        assert metadata.prompt_version_id == "v1.2.3-test"
        assert metadata.trace_id == "trace-123"

        # 2. Verify Persistence in ChatMessage
        conversation_id = result["conversation_id"]
        # Fetch last message (Assistant)
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.desc())
        )
        res = await db_session.execute(stmt)
        msg = res.scalars().first()

        assert msg is not None
        assert msg.message_metadata["generation_id"] == metadata.generation_id
        assert msg.message_metadata["prompt_version_id"] == "v1.2.3-test"

        # 3. Verify Event Log creation via FeedbackService
        # (This confirms log_response_generated was called and worked)
        stmt_log = select(EventLog).where(EventLog.generation_id == metadata.generation_id)
        res_log = await db_session.execute(stmt_log)
        event = res_log.scalar_one_or_none()

        assert event is not None
        assert event.event_type == "chat.response.generated"
        assert event.trace_id == "trace-123"
        assert event.organization_id == str(test_org.id)
        assert event.user_id == str(test_user.id)
        assert event.message_id == str(msg.id)

        # Verify payload metadata
        assert event.payload["model"] == "gpt-4o-mini"
        assert event.payload["prompt_version_id"] == "v1.2.3-test"


@pytest.mark.asyncio
async def test_chat_stream_lineage_in_metadata(test_user, test_org, async_client):
    """
    Test that streaming endpoint includes lineage fields in SSE metadata.
    """
    from unittest.mock import AsyncMock, MagicMock, patch
    from uuid import uuid4

    query = "What's new?"

    with (
        patch(
            "app.api.v1.chat.chat_service.search_activities_semantic", new_callable=AsyncMock
        ) as mock_search,
        patch(
            "app.api.v1.chat.chat_service.get_activities_by_ids", new_callable=AsyncMock
        ) as mock_get_activities,
        patch(
            "app.api.v1.chat.chat_service.get_context_activities", new_callable=AsyncMock
        ) as mock_get_context,
        patch("app.api.v1.chat.chat_service._calculate_confidence") as mock_confidence,
        patch(
            "app.services.ai_service.ai_service.summarize_activities_stream", new_callable=AsyncMock
        ) as mock_stream,
        patch("app.core.version.get_prompt_version_id") as mock_version,
        patch("app.api.v1.chat.ConversationService") as MockConvService,
    ):
        # Setup mocks
        mock_search.return_value = []
        mock_get_activities.return_value = []
        mock_get_context.return_value = []
        mock_confidence.return_value = 0.8

        # Mock ConversationService
        mock_conv_instance = MagicMock()
        mock_conv_instance.get_conversation = AsyncMock(return_value=None)
        mock_conv_instance.create_conversation = AsyncMock(
            return_value=MagicMock(
                id=uuid4(), organization_id=test_org.id, user_id=test_user.id, message_count=0
            )
        )
        mock_conv_instance.add_message = AsyncMock(return_value=MagicMock(id=uuid4()))
        mock_conv_instance.generate_title = AsyncMock(return_value="Test Title")
        mock_conv_instance.update_conversation = AsyncMock()
        MockConvService.return_value = mock_conv_instance

        # Mock streaming response
        async def mock_stream_generator():
            yield "Response chunk 1"
            yield "Response chunk 2"

        mock_stream.return_value = mock_stream_generator()
        mock_version.return_value = "v1.2.3-stream-test"

        # Make request to streaming endpoint
        response = await async_client.post(
            "/api/v1/chat/stream",
            json={
                "message": query,
                "persona": "product",
            },
            headers={"X-Trace-ID": "trace-stream-123"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

        # Parse SSE events - read the stream
        content = ""
        async for chunk in response.aiter_text():
            content += chunk

        events = []
        for line in content.split("\n"):
            if line.startswith("data: "):
                import json

                try:
                    event_data = json.loads(line[6:])  # Remove "data: " prefix
                    events.append(event_data)
                except json.JSONDecodeError:
                    pass

        # Find metadata event
        metadata_event = None
        for event in events:
            if event.get("type") == "metadata":
                metadata_event = event
                break

        assert metadata_event is not None, "Metadata event not found in SSE stream"

        # Verify lineage fields are present
        assert "generation_id" in metadata_event
        assert "prompt_version_id" in metadata_event
        assert "trace_id" in metadata_event

        assert metadata_event["generation_id"] is not None
        assert len(metadata_event["generation_id"]) > 10  # Should be UUID string
        assert metadata_event["prompt_version_id"] == "v1.2.3-stream-test"
        assert metadata_event["trace_id"] == "trace-stream-123"

        # Verify other expected fields
        assert "conversation_id" in metadata_event
        assert "activities_count" in metadata_event
        assert "sources" in metadata_event
        assert "confidence_score" in metadata_event
