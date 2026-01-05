"""
Tests for AI Service.

Tests persona-based prompts and response generation.
Uses mocks to avoid calling OpenAI API.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.schemas.chat import Persona
from app.services.ai_service import PERSONA_PROMPTS, AIService


class TestAIService:
    """Tests for AIService class."""

    def test_persona_prompts_exist(self):
        """All persona types should have corresponding prompts."""
        for persona in Persona:
            assert persona in PERSONA_PROMPTS
            assert len(PERSONA_PROMPTS[persona]) > 100  # Non-trivial prompt

    def test_executive_prompt_focuses_on_business(self):
        """Executive prompt should focus on business outcomes."""
        prompt = PERSONA_PROMPTS[Persona.EXECUTIVE]
        assert "negócio" in prompt.lower() or "roi" in prompt.lower()
        assert "EVITE" in prompt  # Should avoid technical details

    def test_technical_prompt_includes_code_details(self):
        """Technical prompt should include code/architecture focus."""
        prompt = PERSONA_PROMPTS[Persona.TECHNICAL]
        assert "arquitetura" in prompt.lower() or "código" in prompt.lower()
        assert "INCLUA" in prompt  # Should include technical details

    def test_product_prompt_focuses_on_features(self):
        """Product prompt should focus on features and roadmap."""
        prompt = PERSONA_PROMPTS[Persona.PRODUCT]
        assert "features" in prompt.lower() or "roadmap" in prompt.lower()

    def test_build_messages_with_persona(self):
        """_build_messages should use correct persona prompt."""
        service = AIService(api_key="test-key")

        messages = service._build_messages(
            user_message="What happened?",
            context="Some context",
            persona=Persona.EXECUTIVE,
        )

        # System message should be executive prompt
        assert messages[0]["role"] == "system"
        assert (
            "negócio" in messages[0]["content"].lower() or "roi" in messages[0]["content"].lower()
        )

        # Should have context and user message
        assert len(messages) == 4  # system + context + ack + user

    def test_build_messages_with_chat_history(self):
        """_build_messages should align chat_history correctly."""
        service = AIService(api_key="test-key")

        history = [
            {"role": "user", "content": "Prev q"},
            {"role": "assistant", "content": "Prev a"},
        ]

        messages = service._build_messages(
            user_message="New q",
            context="Ctx",
            persona=Persona.PRODUCT,
            chat_history=history,
        )

        # System(0) -> ContextUser(1) -> ContextAssistant(2) -> HistoryUser(3) -> HistoryAssistant(4) -> NewUser(5)
        assert len(messages) == 6
        assert messages[3] == history[0]
        assert messages[4] == history[1]
        assert messages[5]["content"] == "New q"

    def test_format_activities_context(self):
        """_format_activities_context should format activities correctly."""
        service = AIService(api_key="test-key")

        activities = [
            {
                "type": "COMMIT",
                "title": "Fix login bug",
                "author": "pedro",
                "created_at": "2026-01-04",
                "content": "Fixed the authentication flow",
            },
            {
                "type": "PR",
                "title": "Add new feature",
                "author": "maria",
                "created_at": "2026-01-03",
            },
        ]

        context = service._format_activities_context(activities)

        assert "COMMIT" in context
        assert "Fix login bug" in context
        assert "pedro" in context
        assert "PR" in context
        assert "Add new feature" in context

    @pytest.mark.asyncio
    async def test_generate_response_without_client(self):
        """generate_response without API key should return error message."""
        service = AIService(api_key="")
        service.client = None  # Force no client

        response = await service.generate_response("Hello")

        assert "❌" in response
        assert "OPENAI_API_KEY" in response

    @pytest.mark.asyncio
    async def test_summarize_activities_empty_list(self):
        """summarize_activities with empty list should return appropriate message."""
        service = AIService(api_key="test-key")

        response = await service.summarize_activities([], "What happened?")

        assert "Não encontrei atividades" in response

    @pytest.mark.asyncio
    async def test_generate_response_with_mock_client(self):
        """generate_response should call OpenAI client correctly."""
        service = AIService(api_key="test-key")

        # Mock the OpenAI client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Mocked response"

        with patch.object(
            service.client.chat.completions, "create", return_value=mock_response
        ) as mock_create:
            response = await service.generate_response(
                "Test question",
                context="Test context",
                persona=Persona.TECHNICAL,
            )

            assert response == "Mocked response"
            mock_create.assert_called_once()

            # Verify the call included correct model
            call_args = mock_create.call_args
            assert call_args.kwargs["model"] == service.model

    @pytest.mark.asyncio
    async def test_generate_title(self):
        """generate_title should return a trimmed title."""
        service = AIService(api_key="test-key")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '"Mocked Title"'

        with patch.object(service.client.chat.completions, "create", return_value=mock_response):
            title = await service.generate_title("Long message content...")
            assert title == "Mocked Title"  # Should strip quotes
