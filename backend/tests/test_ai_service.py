from unittest.mock import patch

import pytest

from app.schemas.chat import Persona
from app.services.ai.business_translator import BusinessTranslator
from app.services.ai.conversation import PERSONA_PROMPTS, ConversationAI


class TestConversationAI:
    """Tests for ConversationAI class."""

    def test_persona_prompts_exist(self):
        """All persona types should have corresponding prompts."""
        for persona in Persona:
            assert persona in PERSONA_PROMPTS
            assert len(PERSONA_PROMPTS[persona]) > 100  # Non-trivial prompt

    def test_executive_prompt_focuses_on_business(self):
        """Executive prompt should focus on business outcomes and brevity."""
        prompt = PERSONA_PROMPTS[Persona.EXECUTIVE]
        assert "negócio" in prompt.lower() or "roi" in prompt.lower()
        # Check for brevity constraint (changed from "conciso" to "máximo" in improved prompts)
        assert "máximo" in prompt.lower() or "conciso" in prompt.lower()

    def test_technical_prompt_focuses_on_code(self):
        """Technical prompt should include code/architecture focus."""
        prompt = PERSONA_PROMPTS[Persona.TECHNICAL]
        assert "arquitetura" in prompt.lower() or "código" in prompt.lower()

    def test_product_prompt_focuses_on_features(self):
        """Product prompt should focus on product impact."""
        prompt = PERSONA_PROMPTS[Persona.PRODUCT]
        assert "produto" in prompt.lower() or "progresso" in prompt.lower()

    def test_build_messages_with_persona(self):
        """_build_messages should use correct persona prompt."""
        service = ConversationAI(api_key="test-key")

        messages = service._build_messages(
            user_message="What happened?",
            context="Some context",
            persona=Persona.EXECUTIVE,
        )

        # System message is returned separately in new implementation
        system_prompt, msgs_list = messages

        assert "negócio" in system_prompt.lower() or "roi" in system_prompt.lower()

        # Check messages list
        # format: (system_prompt, messages_list)
        # messages_list should contain: [{"role": "user", "content": "What happened?"}]
        assert len(msgs_list) == 1
        assert msgs_list[0]["content"] == "What happened?"

    def test_build_messages_with_chat_history(self):
        """_build_messages should align chat_history correctly."""
        service = ConversationAI(api_key="test-key")

        history = [
            {"role": "user", "content": "Prev q"},
            {"role": "assistant", "content": "Prev a"},
        ]

        _, messages = service._build_messages(
            user_message="New q",
            context="Ctx",
            persona=Persona.PRODUCT,
            chat_history=history,
        )

        assert len(messages) == 3  # history (2) + new user message (1)
        assert messages[0] == history[0]
        assert messages[1] == history[1]
        assert messages[2]["content"] == "New q"

    def test_format_activities_context(self):
        """_format_activities_context should format activities correctly."""
        service = ConversationAI(api_key="test-key")

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
        """generate_response without API key should raise error when client is None."""
        service = ConversationAI(api_key="")
        service.client = None  # Force no client

        # It should raise AttributeError or Exception when trying to use None client
        with pytest.raises((AttributeError, Exception)):
            await service.generate_response("Hello")

    @pytest.mark.asyncio
    async def test_summarize_activities_empty_list(self):
        """summarize_activities with empty list should return appropriate message."""
        service = ConversationAI(api_key="test-key")

        # Mock generate_response to avoid API call
        with patch.object(service, "generate_response", return_value="Summary") as mock_gen:
            await service.summarize_activities([], "What happened?")

            # The logic inside summarize_activities:
            # context = self._format_activities_context(activities)
            # return await self.generate_response(question, context, ...)

            # If activities is empty, _format_activities_context returns "Nenhuma atividade..."
            # It then calls generate_response with that context.
            # Wait, the previous test assertion was: assert "Não encontrei atividades" in response
            # My reading of _format_activities_context: returns "Nenhuma atividade encontrada..." if empty.
            # Then generate_response is called.

            # So the response comes from generate_response (the LLM).
            # Unless summarize_activities short-circuits?
            # Code: return await self.generate_response(...)
            # So we rely on LLM to say "Não encontrei".
            # BUT the test was asserting a string response WITHOUT mocking LLM before (which caused Auth error).
            # If I mock generate_response, I control the return.

            # Let's check logic: _format_activities_context returns "Nenhuma atividade encontrada..."

            mock_gen.assert_called_once()
            call_args = mock_gen.call_args
            assert "Nenhuma atividade encontrada" in call_args[0][1]  # context

    @pytest.mark.asyncio
    async def test_generate_response_with_mock_client(self):
        """generate_response should call LLM correctly."""
        service = ConversationAI(api_key="test-key")

        # Mock the _call_llm_with_history method to avoid complex client mocking
        with patch.object(
            service, "_call_llm_with_history", return_value="Mocked response"
        ) as mock_call:
            response = await service.generate_response(
                "Test question",
                context="Test context",
                persona=Persona.TECHNICAL,
            )

            assert response == "Mocked response"
            mock_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_title(self):
        """generate_title should return a trimmed title."""
        service = ConversationAI(api_key="test-key")

        with patch.object(service, "_call_llm", return_value='"Mocked Title"'):
            title = await service.generate_title("Long message content...")
            # The service does .strip()[:50] but mock returned quotes
            # If the mock returns "Mocked Title", strip() preserves quotes.
            # We should assert it returns exactly what _call_llm returns (trimmed)
            assert title == '"Mocked Title"'


class TestBusinessTranslator:
    """Tests for BusinessTranslator class."""

    @pytest.mark.asyncio
    async def test_generate_business_update_returns_structured_data(self):
        """generate_business_update should return structured dict."""
        service = BusinessTranslator(api_key="test-key")

        mock_content = """{
            "summary": "Corrige bug de login.",
            "impact_level": "MEDIUM",
            "category": "Bugfix"
        }"""

        with patch.object(service, "_call_llm", return_value=mock_content):
            result = await service.generate_business_update(
                {
                    "type": "COMMIT",
                    "title": "Fix login bug",
                    "content": "Fixed authentication flow",
                    "labels": [],
                    "files_touched": ["auth.py"],
                }
            )

            assert "summary" in result
            assert result["summary"] == "Corrige bug de login."
            assert result["impact_level"] == "MEDIUM"
            assert result["category"] == "Bugfix"

    @pytest.mark.asyncio
    async def test_generate_business_update_without_client(self):
        """generate_business_update without API key should return default update."""
        service = BusinessTranslator(api_key="")
        service.client = None

        result = await service.generate_business_update(
            {
                "type": "COMMIT",
                "title": "Test",
            }
        )

        assert result["impact_level"] == "MEDIUM"
        assert "Maintenance" in result["category"]
