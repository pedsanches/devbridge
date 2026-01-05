"""
AI Service.

Integration with OpenAI for generating responses.
Implements BR-030 (persona-based responses) and streaming support.
"""

from collections.abc import AsyncGenerator
from typing import Any

from openai import OpenAI

from app.core.config import settings
from app.schemas.chat import Persona

# Persona-specific prompts (BR-030: Adaptation by Audience)
PERSONA_PROMPTS: dict[Persona, str] = {
    Persona.EXECUTIVE: """Você é um consultor executivo do DevBridge que traduz trabalho técnico em valor de negócio.
Responda em português brasileiro de forma clara e executiva.

FOCO: Outcomes de negócio, ROI, impacto estratégico, riscos e oportunidades.
EVITE: Detalhes técnicos de implementação, nomes de funções, código.
TOM: Conciso, orientado a decisões, bullets quando apropriado.

Baseie suas respostas APENAS nos dados fornecidos. Se não houver informação suficiente,
diga isso claramente ao invés de inventar.""",
    Persona.TECHNICAL: """Você é um consultor técnico sênior do DevBridge que ajuda líderes técnicos a entender o trabalho do time.
Responda em português brasileiro de forma técnica e precisa.

FOCO: Qualidade de código, arquitetura, débito técnico, padrões seguidos.
INCLUA: Nomes de arquivos, funções, decisões arquiteturais quando relevante.
TOM: Técnico mas acessível, cite evidências do código.

Baseie suas respostas APENAS nos dados fornecidos. Se não houver informação suficiente,
diga isso claramente ao invés de inventar.""",
    Persona.PRODUCT: """Você é um assistente de produto do DevBridge que ajuda Product Managers a entender o progresso do time.
Responda em português brasileiro de forma clara e orientada a produto.

FOCO: Features entregues, progresso em roadmap, blockers, dependências entre times.
EVITE: Detalhes muito técnicos de implementação.
TOM: Colaborativo, orientado a entregas, mencione status quando relevante.

Baseie suas respostas APENAS nos dados fornecidos. Se não houver informação suficiente,
diga isso claramente ao invés de inventar.""",
}


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

    def _build_messages(
        self,
        user_message: str,
        context: str = "",
        persona: Persona = Persona.PRODUCT,
        chat_history: list[dict[str, str]] | None = None,
    ) -> list[dict[str, str]]:
        """Build the messages array for OpenAI chat completion."""
        system_prompt = PERSONA_PROMPTS.get(persona, PERSONA_PROMPTS[Persona.PRODUCT])
        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

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

        if chat_history:
            messages.extend(chat_history)

        messages.append({"role": "user", "content": user_message})
        return messages

    async def generate_response(
        self,
        user_message: str,
        context: str = "",
        persona: Persona = Persona.PRODUCT,
        max_tokens: int = 1024,
        chat_history: list[dict[str, str]] | None = None,
    ) -> str:
        """
        Generate a response using OpenAI.

        Args:
            user_message: The user's question/message.
            context: Additional context to provide (e.g., activities data).
            persona: User persona for response adaptation (BR-030).
            max_tokens: Maximum tokens in response.
            chat_history: Optional list of previous messages.

        Returns:
            Generated response text.
        """
        if not self.client:
            return "❌ AI service not configured. Please set OPENAI_API_KEY."

        messages = self._build_messages(user_message, context, persona, chat_history)

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=messages,
        )

        return response.choices[0].message.content or ""

    async def generate_response_stream(
        self,
        user_message: str,
        context: str = "",
        persona: Persona = Persona.PRODUCT,
        max_tokens: int = 1024,
        chat_history: list[dict[str, str]] | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response using OpenAI.

        Args:
            user_message: The user's question/message.
            context: Additional context to provide.
            persona: User persona for response adaptation (BR-030).
            max_tokens: Maximum tokens in response.
            chat_history: Optional list of previous messages.

        Yields:
            Response text chunks.
        """
        if not self.client:
            yield "❌ AI service not configured. Please set OPENAI_API_KEY."
            return

        messages = self._build_messages(user_message, context, persona, chat_history)

        stream = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=messages,
            stream=True,
        )

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def _format_activities_context(self, activities: list[dict[str, Any]]) -> str:
        """Format activities list into a context string for the LLM."""
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
        return "\n".join(context_lines)

    async def summarize_activities(
        self,
        activities: list[dict[str, Any]],
        question: str,
        persona: Persona = Persona.PRODUCT,
        chat_history: list[dict[str, str]] | None = None,
    ) -> str:
        """
        Summarize activities based on a question.

        This is the main entry point for the chat service.

        Args:
            activities: List of activity dictionaries.
            question: User's question about the activities.
            persona: User persona for response adaptation (BR-030).
            chat_history: Optional list of previous messages.

        Returns:
            Summary response.
        """
        if not activities:
            return "Não encontrei atividades para a sua consulta."

        context = self._format_activities_context(activities)
        return await self.generate_response(question, context, persona, chat_history=chat_history)

    async def summarize_activities_stream(
        self,
        activities: list[dict[str, Any]],
        question: str,
        persona: Persona = Persona.PRODUCT,
        chat_history: list[dict[str, str]] | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Summarize activities with streaming response.

        Args:
            activities: List of activity dictionaries.
            question: User's question about the activities.
            persona: User persona for response adaptation (BR-030).
            chat_history: Optional list of previous messages.

        Yields:
            Response text chunks.
        """
        if not activities:
            yield "Não encontrei atividades para a sua consulta."
            return

        context = self._format_activities_context(activities)
        async for chunk in self.generate_response_stream(question, context, persona, chat_history=chat_history):
            yield chunk


    async def generate_title(self, message: str) -> str:
        """
        Generate a concise title for the conversation based on the first message.
        """
        if not self.client:
            return "Nova Conversa"
            
        prompt = (
            "Gere um título curto (máximo 5 palavras) e direto para esta mensagem de chat. "
            "Use português brasileiro. Não use aspas ou pontuação final.\n\n"
            f"Mensagem: {message}"
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=20,
                temperature=0.5,
            )
            title = response.choices[0].message.content or "Nova Conversa"
            return title.strip().strip('"')
        except Exception:
            # Fallback in case of error
            return message[:50] + "..." if len(message) > 50 else message

# Singleton instance
ai_service = AIService()

