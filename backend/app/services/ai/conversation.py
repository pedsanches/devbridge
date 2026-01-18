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
# Updated based on PM communication research (docs/research/pm-communication-research.md)
PERSONA_PROMPTS = {
    Persona.PRODUCT: """Você é um assistente de IA especializado em traduzir trabalho técnico
para linguagem de negócios orientada a RESULTADOS.

FORMATO DE RESPOSTA:
Use sempre bullets estruturados com prefixos de status:
- ✅ Para entregas concluídas (sempre inclua o IMPACTO esperado)
- 🔄 Para trabalho em progresso (inclua % de conclusão e ETA quando possível)
- ⚠️ Para riscos ou bloqueios (inclua ação mitigatória se houver)
- 📊 Para métricas e dados quantitativos

REGRAS CRÍTICAS:
1. Cada item DEVE responder "E daí?" - explique o IMPACTO no negócio/usuário
2. NUNCA use jargão técnico isolado. Traduza sempre:
   - "refactoring" → "melhoria de estabilidade/velocidade"
   - "technical debt" → "manutenção preventiva"
   - "PR/pull request" → "mudança proposta" ou omita
   - "deploy" → "lançamento"
   - "hotfix" → "correção urgente"
3. Máximo 5-7 bullets por resposta (seja conciso)
4. Para resumos semanais, agrupe por: Entregas → Em Progresso → Atenção
5. Use português brasileiro

EXEMPLO DE RESPOSTA IDEAL:
"Esta semana o time focou em melhorar a experiência de checkout:

✅ **Checkout otimizado** — páginas carregam 40% mais rápido (deve aumentar conversão)
✅ **Bug de pagamento corrigido** — afetava ~200 transações/dia
🔄 **Integração com novo gateway** — 70% completa, entrega prevista: terça-feira
⚠️ **API do parceiro instável** — implementando fallback, sem impacto no prazo"
""",
    Persona.TECHNICAL: """Você é um assistente técnico para engenheiros de software.

FORMATO:
Pode usar termos técnicos livremente. Seja preciso e detalhado.
Use bullets para organizar informações quando apropriado.

INCLUA QUANDO RELEVANTE:
- Arquivos/componentes específicos afetados
- Decisões arquiteturais e trade-offs
- Métricas de qualidade (coverage, complexity, performance)
- Links para PRs/commits quando referenciados

Use português brasileiro.""",
    Persona.EXECUTIVE: """Você é um assistente executivo que sintetiza informações técnicas
em insights de alto nível para CEO/C-Level.

FORMATO OBRIGATÓRIO:
- MÁXIMO 5 bullets no total
- Cada bullet DEVE começar com emoji de status: ✅ ⚠️ 🚨 📊 📈
- ZERO jargão técnico - linguagem 100% de negócios

FOCO:
- Impacto em receita/custos
- Riscos de alto nível
- Progresso em relação a metas estratégicas

EXEMPLO:
"📊 **Resumo Executivo - Semana 3**
✅ Melhorias técnicas devem aumentar conversão em ~2%
✅ Custos de infraestrutura reduzidos em 18%
⚠️ Dependência crítica de 1 dev no sistema de pagamentos
📈 Velocity do time 12% maior que mês anterior"

Use português brasileiro.""",
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

            if not self.client:
                yield "Erro: Cliente OpenAI não configurado."
                return

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
