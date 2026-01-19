"""
Tests for Chat Service.

Tests query processing with persona support and metadata generation.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.schemas.chat import Persona
from app.services.chat_service import ChatService


class TestChatService:
    """Tests for ChatService class."""

    @pytest.fixture
    def chat_service(self):
        """Create a ChatService instance."""
        return ChatService()

    @pytest.mark.asyncio
    async def test_process_query_returns_metadata(self, chat_service):
        """process_query should return structured metadata."""
        # Mock get_context_activities to return empty list
        with (
            patch.object(
                chat_service, "get_context_activities", new_callable=AsyncMock, return_value=[]
            ),
            patch.object(
                chat_service, "search_activities_semantic", new_callable=AsyncMock, return_value=[]
            ),
            patch(
                "app.services.chat_service.ai_service.summarize_activities",
                new_callable=AsyncMock,
                return_value="No activities found",
            ),
            patch("app.services.conversation_service.ConversationService") as MockConvService,
        ):
            # Mock ConversationService loaded inside the method
            mock_conv_instance = MockConvService.return_value
            mock_conv_instance.create_conversation = AsyncMock(
                return_value=MagicMock(id="123", organization_id="org")
            )
            mock_conv_instance.generate_title = AsyncMock(return_value="AI Generated Title")
            mock_conv_instance.update_conversation = AsyncMock()
            mock_conv_instance.add_message = AsyncMock()
            mock_conv_instance.get_conversation_messages = AsyncMock(return_value=[])

            result = await chat_service.process_query(
                MagicMock(),  # mock db
                query="What happened?",
                user_id=uuid4(),
                org_id=str(uuid4()),
                persona=Persona.EXECUTIVE,
            )

            assert "metadata" in result
            assert result["metadata"] is not None
            assert result["metadata"].persona_used == Persona.EXECUTIVE

    @pytest.mark.asyncio
    async def test_process_query_passes_persona_to_ai_service(self, chat_service):
        """process_query should pass persona to ai_service when activities exist."""
        # Must have activities for AI service to be called (anti-hallucination gate)
        mock_activities = [{"id": "test", "title": "Test Activity", "type": "commit"}]
        with (
            patch.object(
                chat_service,
                "get_context_activities",
                new_callable=AsyncMock,
                return_value=mock_activities,
            ),
            patch.object(
                chat_service, "search_activities_semantic", new_callable=AsyncMock, return_value=[]
            ),
            patch(
                "app.services.chat_service.ai_service.summarize_activities",
                new_callable=AsyncMock,
                return_value="Response",
            ) as mock_summarize,
            patch("app.services.conversation_service.ConversationService") as MockConvService,
        ):
            mock_conv_instance = MockConvService.return_value
            mock_conv_instance.create_conversation = AsyncMock(
                return_value=MagicMock(id="123", organization_id="org")
            )
            mock_conv_instance.generate_title = AsyncMock(return_value="AI Generated Title")
            mock_conv_instance.update_conversation = AsyncMock()
            mock_conv_instance.add_message = AsyncMock()
            mock_conv_instance.get_conversation_messages = AsyncMock(return_value=[])

            await chat_service.process_query(
                MagicMock(),
                query="What happened?",
                user_id=uuid4(),
                org_id=str(uuid4()),
                persona=Persona.TECHNICAL,
            )

            # Verify persona was passed
            mock_summarize.assert_called_once()
            call_args = mock_summarize.call_args
            # Args are: activities, query, persona
            assert call_args[0][2] == Persona.TECHNICAL

    @pytest.mark.asyncio
    async def test_process_query_default_persona(self, chat_service):
        """process_query should default to PRODUCT persona."""
        with (
            patch.object(
                chat_service, "get_context_activities", new_callable=AsyncMock, return_value=[]
            ),
            patch.object(
                chat_service, "search_activities_semantic", new_callable=AsyncMock, return_value=[]
            ),
            patch(
                "app.services.chat_service.ai_service.summarize_activities",
                new_callable=AsyncMock,
                return_value="Response",
            ),
            patch("app.services.conversation_service.ConversationService") as MockConvService,
        ):
            mock_conv_instance = MockConvService.return_value
            mock_conv_instance.create_conversation = AsyncMock(
                return_value=MagicMock(id="123", organization_id="org")
            )
            mock_conv_instance.generate_title = AsyncMock(return_value="AI Generated Title")
            mock_conv_instance.update_conversation = AsyncMock()
            mock_conv_instance.add_message = AsyncMock()
            mock_conv_instance.get_conversation_messages = AsyncMock(return_value=[])

            result = await chat_service.process_query(
                MagicMock(),
                query="What happened?",
                user_id=uuid4(),
                org_id=str(uuid4()),
            )

            assert result["metadata"].persona_used == Persona.PRODUCT

    @pytest.mark.asyncio
    async def test_process_query_sql_fallback_confidence(self, chat_service):
        """SQL fallback should have lower confidence than semantic search."""
        with (
            patch.object(
                chat_service, "get_context_activities", new_callable=AsyncMock, return_value=[]
            ),
            patch.object(
                chat_service, "search_activities_semantic", new_callable=AsyncMock, return_value=[]
            ),
            patch(
                "app.services.chat_service.ai_service.summarize_activities",
                new_callable=AsyncMock,
                return_value="Response",
            ),
            patch("app.services.conversation_service.ConversationService") as MockConvService,
        ):
            mock_conv_instance = MockConvService.return_value
            mock_conv_instance.create_conversation = AsyncMock(
                return_value=MagicMock(id="123", organization_id="org")
            )
            mock_conv_instance.generate_title = AsyncMock(return_value="AI Generated Title")
            mock_conv_instance.update_conversation = AsyncMock()
            mock_conv_instance.add_message = AsyncMock()
            mock_conv_instance.get_conversation_messages = AsyncMock(return_value=[])

            result = await chat_service.process_query(
                MagicMock(),
                query="What happened?",
                user_id=uuid4(),
                org_id=str(uuid4()),
            )

            # SQL with 0 activities should have base confidence (0.3)
            assert result["metadata"].confidence_score == 0.3
            assert result["metadata"].search_method == "sql"

    @pytest.mark.asyncio
    async def test_process_query_semantic_search_higher_confidence(self, chat_service):
        """Semantic search should have higher confidence."""
        mock_search_results = [
            {"activity_id": "12345678-1234-5678-1234-567812345678", "score": 0.9}
        ]

        with (
            patch.object(
                chat_service,
                "search_activities_semantic",
                new_callable=AsyncMock,
                return_value=mock_search_results,
            ),
            patch.object(
                chat_service,
                "get_activities_by_ids",
                new_callable=AsyncMock,
                return_value=[{"id": "test", "title": "Test"}],
            ),
            patch(
                "app.services.chat_service.ai_service.summarize_activities",
                new_callable=AsyncMock,
                return_value="Response",
            ),
            patch("app.services.conversation_service.ConversationService") as MockConvService,
        ):
            mock_conv_instance = MockConvService.return_value
            mock_conv_instance.create_conversation = AsyncMock(
                return_value=MagicMock(id="123", organization_id="org")
            )
            mock_conv_instance.generate_title = AsyncMock(return_value="AI Generated Title")
            mock_conv_instance.update_conversation = AsyncMock()
            mock_conv_instance.add_message = AsyncMock()
            mock_conv_instance.get_conversation_messages = AsyncMock(return_value=[])

            result = await chat_service.process_query(
                MagicMock(),
                query="What happened?",
                user_id=uuid4(),
                org_id=str(uuid4()),
            )

            # Semantic score 0.9 + coverage bonus (1 activity / 5 * 0.15 = 0.03) = 0.93
            assert result["metadata"].confidence_score == 0.93
            assert result["metadata"].search_method == "semantic"

    @pytest.mark.asyncio
    async def test_no_activities_skips_llm_call(self, chat_service):
        """When no activities found, should NOT call LLM (anti-hallucination gate)."""
        with (
            patch.object(
                chat_service, "get_context_activities", new_callable=AsyncMock, return_value=[]
            ),
            patch.object(
                chat_service, "search_activities_semantic", new_callable=AsyncMock, return_value=[]
            ),
            patch(
                "app.services.chat_service.ai_service.summarize_activities",
                new_callable=AsyncMock,
                return_value="Should not be called",
            ) as mock_summarize,
            patch("app.services.conversation_service.ConversationService") as MockConvService,
        ):
            mock_conv_instance = MockConvService.return_value
            mock_conv_instance.create_conversation = AsyncMock(
                return_value=MagicMock(id="123", organization_id="org")
            )
            mock_conv_instance.generate_title = AsyncMock(return_value="AI Generated Title")
            mock_conv_instance.update_conversation = AsyncMock()
            mock_conv_instance.add_message = AsyncMock()
            mock_conv_instance.get_conversation_messages = AsyncMock(return_value=[])

            result = await chat_service.process_query(
                MagicMock(),
                query="What happened?",
                user_id=uuid4(),
                org_id=str(uuid4()),
            )

            # LLM should NOT have been called
            mock_summarize.assert_not_called()

            # Response should be deterministic no-context message
            assert "Não encontrei atividades" in result["answer"]
            assert "ajuste os filtros" in result["answer"]

            # Metadata should reflect no activities
            assert result["activities_count"] == 0
            assert result["metadata"].activities_count == 0
            assert result["metadata"].confidence_score == 0.3  # Base confidence
