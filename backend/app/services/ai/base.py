"""
Base AI Service.

Core functionality shared by all AI service modules.
"""

import logging
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import openai

from app.core.config import settings

logger = logging.getLogger(__name__)

# Day of week names in Portuguese
WEEKDAY_NAMES = {
    0: "Segunda-feira",
    1: "Terça-feira",
    2: "Quarta-feira",
    3: "Quinta-feira",
    4: "Sexta-feira",
    5: "Sábado",
    6: "Domingo",
}


def get_temporal_context(timezone: str = "America/Sao_Paulo") -> str:
    """
    Generate temporal context string for LLM grounding.

    Provides the current date, time, and day of week to help
    the LLM interpret time-relative queries correctly.
    """
    try:
        tz = ZoneInfo(timezone)
        now = datetime.now(tz)
        weekday = WEEKDAY_NAMES.get(now.weekday(), now.strftime("%A"))
        date_str = now.strftime("%d/%m/%Y")
        time_str = now.strftime("%H:%M")
        return f"Data atual: {weekday}, {date_str} às {time_str} (horário de Brasília)"
    except Exception:
        return f"Data atual: {datetime.now().strftime('%d/%m/%Y')}"


class BaseAIService:
    """
    Base class for AI-powered services.

    Provides common functionality for API calls, message building,
    and response handling.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """
        Initialize AI service.

        Args:
            api_key: OpenAI API key (uses settings if not provided).
            model: Model to use (uses settings if not provided).
        """
        self.api_key = api_key or getattr(settings, "OPENAI_API_KEY", None) or None
        self.model = model or getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
        self.client: openai.OpenAI | None = None
        if self.api_key:
            self.client = openai.OpenAI(api_key=self.api_key)

    async def _sanitize_text(self, text: str) -> str:
        """Sanitize text using Presidio before LLM processing.

        NOTE: Presidio is temporarily disabled. Returning original text.
        """
        # TODO: Re-enable Presidio when service is properly configured
        return text
        # try:
        #     return await privacy_service.sanitize_async(text)
        # except PrivacyServiceError as exc:
        #     logger.error("PII sanitization failed: %s", exc)
        #     raise

    async def _sanitize_messages(self, messages: list[dict[str, str]]) -> list[dict[str, str]]:
        """Sanitize a list of chat messages.

        NOTE: Presidio is temporarily disabled. Returning original messages.
        """
        # TODO: Re-enable Presidio when service is properly configured
        return messages

    async def _call_llm(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """
        Make a call to the LLM with the given prompts.

        Args:
            system_prompt: System message to set context.
            user_message: User message/query.
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature.

        Returns:
            The LLM response text.
        """
        try:
            client = self.client
            if client is None:
                raise RuntimeError("OpenAI client not configured")

            sanitized_system_prompt = await self._sanitize_text(system_prompt)
            sanitized_user_message = await self._sanitize_text(user_message)
            model = self.model or "gpt-4o-mini"
            messages = [
                {"role": "system", "content": sanitized_system_prompt},
                {"role": "user", "content": sanitized_user_message},
            ]
            response = client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                messages=messages,
                temperature=temperature,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    async def _call_llm_with_history(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """
        Make a call to the LLM with conversation history.

        Args:
            system_prompt: System message to set context.
            messages: List of message dicts with 'role' and 'content'.
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature.

        Returns:
            The LLM response text.
        """
        try:
            client = self.client
            if client is None:
                raise RuntimeError("OpenAI client not configured")

            sanitized_system_prompt = await self._sanitize_text(system_prompt)
            sanitized_messages = await self._sanitize_messages(messages)
            model = self.model or "gpt-4o-mini"
            full_messages = [
                {"role": "system", "content": sanitized_system_prompt},
                *sanitized_messages,
            ]

            response = client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                messages=full_messages,
                temperature=temperature,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"LLM call with history failed: {e}")
            raise

    def _format_activities_context(self, activities: list[dict[str, Any]]) -> str:
        """
        Format activities list into a context string for the LLM.

        This is a GENERIC formatter that does NOT include citation logic.
        Citation-aware formatting should be done in domain-specific services
        like ConversationAI.

        Args:
            activities: List of activity dictionaries.

        Returns:
            Formatted context string (neutral, no citations).
        """
        if not activities:
            return "Nenhuma atividade encontrada no período selecionado."

        # Header clarifying data source limitations (anti-hallucination)
        header = (
            "═══ FONTE DE DADOS ═══\n"
            "Logs técnicos de desenvolvimento: commits, PRs, issues.\n"
            "NÃO inclui: métricas de negócio, analytics, custos, incidentes de produção.\n"
            "══════════════════════\n\n"
        )

        context_parts = []
        for i, activity in enumerate(activities[:50], 1):
            # Get the proper date field
            date = activity.get("occurred_at") or activity.get("created_at", "")
            if hasattr(date, "strftime"):
                date = date.strftime("%d/%m/%Y %H:%M")
            elif isinstance(date, str) and "T" in date:
                date = date.split("T")[0]

            activity_type = activity.get("type", "COMMIT")
            title = activity.get("title", "Sem título")
            author = activity.get("author", "desconhecido")
            repo = activity.get("repository_name") or activity.get("repository", "")

            # Build activity info (neutral format, no citations)
            parts = [f"{i}. [{activity_type}] {title}"]
            parts.append(f"   Autor: {author} | Data: {date}")
            if repo:
                parts.append(f"   Repositório: {repo}")

            # Add metrics if available
            lines_added = activity.get("lines_added")
            lines_deleted = activity.get("lines_deleted")
            if lines_added is not None or lines_deleted is not None:
                parts.append(f"   +{lines_added or 0}/-{lines_deleted or 0} linhas")

            # Add labels if available
            labels = activity.get("labels")
            if labels:
                parts.append(f"   Labels: {', '.join(labels)}")

            # Add business update if available
            business_update = activity.get("business_update")
            if business_update:
                summary = business_update.get("summary", "")
                impact = business_update.get("impact_level", "")
                if summary:
                    parts.append(f"   Impacto: [{impact}] {summary}")

            context_parts.append("\n".join(parts))

        return header + "\n\n".join(context_parts)


