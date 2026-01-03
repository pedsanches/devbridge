"""
AI Service.

Integration with OpenAI for generating responses.
Designed to be extended for RAG pipeline in the future.
"""

from typing import Any

from openai import OpenAI

from app.core.config import settings


class AIService:
    """Service for AI-powered text generation using OpenAI."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """
        Initialize AI service.

        Args:
            api_key: OpenAI API key (uses settings if not provided).
            model: Model to use (uses settings if not provided).
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    async def generate_response(
        self,
        user_message: str,
        context: str = "",
        system_prompt: str | None = None,
        max_tokens: int = 1024,
    ) -> str:
        """
        Generate a response using OpenAI.

        Args:
            user_message: The user's question/message.
            context: Additional context to provide (e.g., activities data).
            system_prompt: Custom system prompt (uses default if not provided).
            max_tokens: Maximum tokens in response.

        Returns:
            Generated response text.
        """
        if not self.client:
            return "❌ AI service not configured. Please set OPENAI_API_KEY."

        default_system = """Você é um assistente técnico do DevBridge que ajuda stakeholders a entender
o trabalho do time de desenvolvimento. Responda em português brasileiro de forma clara e objetiva.

Baseie suas respostas APENAS nos dados fornecidos no contexto. Se não houver informação suficiente,
diga isso claramente ao invés de inventar."""

        messages = [{"role": "system", "content": system_prompt or default_system}]

        # Add context as user message if provided
        if context:
            messages.append(
                {
                    "role": "user",
                    "content": f"Aqui estão os dados de atividades do time:\n\n{context}",
                }
            )
            messages.append(
                {
                    "role": "assistant",
                    "content": "Entendi. Vou usar esses dados para responder suas perguntas.",
                }
            )

        # Add user message
        messages.append({"role": "user", "content": user_message})

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=messages,
        )

        return response.choices[0].message.content or ""

    async def summarize_activities(
        self,
        activities: list[dict[str, Any]],
        question: str,
    ) -> str:
        """
        Summarize activities based on a question.

        This is the main entry point for the chat service.
        Designed to be extended with RAG context in the future.

        Args:
            activities: List of activity dictionaries.
            question: User's question about the activities.

        Returns:
            Summary response.
        """
        if not activities:
            return "Não encontrei atividades para a sua consulta."

        # Format activities as context
        context_lines = []
        for activity in activities:
            line = (
                f"- [{activity.get('type', 'UNKNOWN')}] {activity.get('title', 'Sem título')} "
                f"(por {activity.get('author', 'desconhecido')}, "
                f"em {activity.get('created_at', 'data desconhecida')})"
            )
            if activity.get("content"):
                content_preview = activity["content"][:200]
                if len(activity["content"]) > 200:
                    content_preview += "..."
                line += f"\n  Conteúdo: {content_preview}"
            context_lines.append(line)

        context = "\n".join(context_lines)

        return await self.generate_response(question, context)


# Singleton instance
ai_service = AIService()
