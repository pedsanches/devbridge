"""
Conversation AI Module.

Handles chat interactions, streaming responses, and summarization.
"""

import logging
from collections.abc import AsyncGenerator
from typing import Any

from app.schemas.chat import Persona
from app.services.ai.base import BaseAIService, get_temporal_context

logger = logging.getLogger(__name__)

# Persona-specific system prompts
PERSONA_PROMPTS = {
    Persona.PRODUCT: """Você é um assistente de IA especializado em traduzir trabalho técnico
para linguagem de negócios. Responda de forma clara e orientada a resultados,
focando em impacto de produto, entregas e progresso do time.
Evite jargões técnicos. Use português brasileiro.""",
    Persona.TECHNICAL: """Você é um assistente técnico para engenheiros de software.
Pode usar termos técnicos, discutir arquitetura, código e métricas de engenharia.
Seja preciso e detalhado quando necessário. Use português brasileiro.""",
    Persona.EXECUTIVE: """Você é um assistente executivo que sintetiza informações técnicas
em insights de alto nível. Foque em métricas de negócio, ROI, riscos e oportunidades.
Seja extremamente conciso - máximo 5 bullets por resposta. Use português brasileiro.""",
}


class ConversationAI(BaseAIService):
    """
    AI service for conversational interactions.

    Handles chat responses, streaming, and activity summarization.
    """

    def _build_messages(
        self,
        user_message: str,
        context: str = "",
        persona: Persona = Persona.PRODUCT,
        chat_history: list[dict[str, str]] | None = None,
    ) -> tuple[str, list[dict[str, str]]]:
        """
        Build the system prompt and messages for chat completion.

        Args:
            user_message: The user's question/message.
            context: Additional context (e.g., activities data).
            persona: User persona for response adaptation.
            chat_history: Previous messages in the conversation.

        Returns:
            Tuple of (system_prompt, messages_list).
        """
        base_prompt = PERSONA_PROMPTS.get(persona, PERSONA_PROMPTS[Persona.PRODUCT])
        temporal = get_temporal_context()

        system_prompt = f"""{base_prompt}

{temporal}

Contexto das atividades recentes:
{context if context else "Nenhum contexto adicional fornecido."}"""

        messages = []
        if chat_history:
            messages.extend(chat_history)
        messages.append({"role": "user", "content": user_message})

        return system_prompt, messages

    async def generate_response(
        self,
        user_message: str,
        context: str = "",
        persona: Persona = Persona.PRODUCT,
        max_tokens: int = 1024,
        chat_history: list[dict[str, str]] | None = None,
    ) -> str:
        """
        Generate a non-streaming response.

        Args:
            user_message: The user's question/message.
            context: Additional context to provide.
            persona: User persona for response adaptation.
            max_tokens: Maximum tokens in response.
            chat_history: Previous messages in conversation.

        Returns:
            Generated response text.
        """
        system_prompt, messages = self._build_messages(user_message, context, persona, chat_history)
        return await self._call_llm_with_history(system_prompt, messages, max_tokens=max_tokens)

    async def generate_response_stream(
        self,
        user_message: str,
        context: str = "",
        persona: Persona = Persona.PRODUCT,
        max_tokens: int = 1024,
        chat_history: list[dict[str, str]] | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response.

        Args:
            user_message: The user's question/message.
            context: Additional context to provide.
            persona: User persona for response adaptation.
            max_tokens: Maximum tokens in response.
            chat_history: Previous messages in conversation.

        Yields:
            Response text chunks.
        """
        system_prompt, messages = self._build_messages(user_message, context, persona, chat_history)

        try:
            sanitized_system_prompt = await self._sanitize_text(system_prompt)
            sanitized_messages = await self._sanitize_messages(messages)
            model = self.model or "gpt-4o-mini"
            full_messages = [
                {"role": "system", "content": sanitized_system_prompt},
                *sanitized_messages,
            ]

            stream = self.client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                messages=full_messages,
                stream=True,
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Streaming response failed: {e}")
            yield f"Erro ao gerar resposta: {e}"

    async def summarize_activities(
        self,
        activities: list[dict[str, Any]],
        question: str,
        persona: Persona = Persona.PRODUCT,
        chat_history: list[dict[str, str]] | None = None,
    ) -> str:
        """
        Summarize activities based on a user question.

        Args:
            activities: List of activity dictionaries.
            question: User's question about the activities.
            persona: User persona for response adaptation.
            chat_history: Previous messages in conversation.

        Returns:
            Summary response.
        """
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
            persona: User persona for response adaptation.
            chat_history: Previous messages in conversation.

        Yields:
            Response text chunks.
        """
        context = self._format_activities_context(activities)
        async for chunk in self.generate_response_stream(
            question, context, persona, chat_history=chat_history
        ):
            yield chunk

    async def generate_title(self, message: str) -> str:
        """
        Generate a concise title for a conversation.

        Args:
            message: The first message in the conversation.

        Returns:
            A short title (max 50 chars).
        """
        system_prompt = """Gere um título curto (máximo 50 caracteres) para esta conversa.
Responda APENAS com o título, sem aspas ou pontuação extra."""

        try:
            title = await self._call_llm(system_prompt, message, max_tokens=50, temperature=0.3)
            return title.strip()[:50]
        except Exception as e:
            logger.error(f"Failed to generate title: {e}")
            return message[:50] + "..." if len(message) > 50 else message
