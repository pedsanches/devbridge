"""
AI Service Facade.

Provides backward compatibility with the original AIService interface
by delegating to specialized modules.
"""

from collections.abc import AsyncGenerator
from typing import Any

from app.schemas.chat import Persona
from app.services.ai.activity_analyzer import ActivityAnalyzer
from app.services.ai.business_translator import BusinessTranslator
from app.services.ai.conversation import ConversationAI
from app.services.ai.developer_analyzer import DeveloperAnalyzer


class AIService:
    """
    Unified AI Service facade.

    Maintains backward compatibility with the original AIService interface
    while internally delegating to specialized modules.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """
        Initialize all AI service modules.

        Args:
            api_key: OpenAI API key (uses settings if not provided).
            model: Model to use (uses settings if not provided).
        """
        self._conversation = ConversationAI(api_key, model)
        self._activity_analyzer = ActivityAnalyzer(api_key, model)
        self._business_translator = BusinessTranslator(api_key, model)
        self._developer_analyzer = DeveloperAnalyzer(api_key, model)

    @property
    def api_key(self) -> str | None:
        """Get API key from conversation service."""
        return self._conversation.api_key

    @property
    def model(self) -> str:
        """Get model from conversation service."""
        return str(self._conversation.model)

    # =========================================================================
    # Conversation methods (delegated to ConversationAI)
    # =========================================================================

    async def generate_response(
        self,
        user_message: str,
        context: str = "",
        persona: Persona = Persona.PRODUCT,
        max_tokens: int = 1024,
        chat_history: list[dict[str, str]] | None = None,
    ) -> str:
        """Generate a non-streaming response."""
        return await self._conversation.generate_response(
            user_message, context, persona, max_tokens, chat_history
        )

    async def generate_response_stream(
        self,
        user_message: str,
        context: str = "",
        persona: Persona = Persona.PRODUCT,
        max_tokens: int = 1024,
        chat_history: list[dict[str, str]] | None = None,
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response."""
        async for chunk in self._conversation.generate_response_stream(
            user_message, context, persona, max_tokens, chat_history
        ):
            yield chunk

    async def summarize_activities(
        self,
        activities: list[dict[str, Any]],
        question: str,
        persona: Persona = Persona.PRODUCT,
        chat_history: list[dict[str, str]] | None = None,
        sources: list[Any] | None = None,
    ) -> str:
        """Summarize activities based on a question."""
        return await self._conversation.summarize_activities(
            activities, question, persona, chat_history, sources
        )

    async def summarize_activities_stream(
        self,
        activities: list[dict[str, Any]],
        question: str,
        persona: Persona = Persona.PRODUCT,
        chat_history: list[dict[str, str]] | None = None,
        sources: list[Any] | None = None,
    ) -> AsyncGenerator[str, None]:
        """Summarize activities with streaming response."""
        async for chunk in self._conversation.summarize_activities_stream(
            activities, question, persona, chat_history, sources
        ):
            yield chunk

    async def generate_title(self, message: str) -> str:
        """Generate a concise title for a conversation."""
        return await self._conversation.generate_title(message)

    # =========================================================================
    # Activity analysis methods (delegated to ActivityAnalyzer)
    # =========================================================================

    async def classify_activity_tags(self, activity: dict[str, Any]) -> list[str]:
        """Classify an activity with business-value tags."""
        return await self._activity_analyzer.classify_activity_tags(activity)

    # =========================================================================
    # Business translation methods (delegated to BusinessTranslator)
    # =========================================================================

    async def generate_business_update(self, activity: dict[str, Any]) -> dict[str, Any]:
        """Generate a business impact summary for an activity."""
        return await self._business_translator.generate_business_update(activity)

    # =========================================================================
    # Developer analysis methods (delegated to DeveloperAnalyzer)
    # =========================================================================

    async def analyze_developer_strengths(self, activities: list[dict]) -> list[str]:
        """Identify developer strength tags based on activity patterns."""
        return await self._developer_analyzer.analyze_developer_strengths(activities)

    async def calculate_collaboration_score(
        self, reviews_given: int, reviews_received: int, review_quality: float
    ) -> int:
        """Calculate a collaboration score (0-100) for a developer."""
        return await self._developer_analyzer.calculate_collaboration_score(
            reviews_given, reviews_received, review_quality
        )


# Singleton instance for backward compatibility
ai_service = AIService()
