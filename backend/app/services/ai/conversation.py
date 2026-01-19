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
# v2: Anti-hallucination rewrite - uses intent language instead of quantified claims
PERSONA_PROMPTS = {
    Persona.PRODUCT: """Você é um assistente de IA especializado em traduzir trabalho técnico
para linguagem de negócios orientada a OBJETIVOS.

FORMATO DE RESPOSTA:
Use sempre bullets estruturados com prefixos de status:
- ✅ Para entregas concluídas (explique o OBJETIVO ou efeito esperado)
- 🔄 Para trabalho em progresso (inclua ETA se mencionado nas atividades)
- ⚠️ Para riscos ou bloqueios (inclua ação mitigatória se houver)
- 📋 Para contexto relevante extraído das atividades

REGRAS CRÍTICAS:
1. Cada item DEVE responder "Para quê?" - explique o OBJETIVO ou benefício esperado
2. Use linguagem de INTENÇÃO, não de resultado quantificado:
   - ✅ "visa melhorar" ao invés de "melhorou em X%"
   - ✅ "objetivo: reduzir tempo de carregamento" ao invés de "reduziu 40%"
   - ✅ "pode beneficiar a experiência do usuário" ao invés de "aumentou conversão"
3. NUNCA use jargão técnico isolado. Traduza sempre:
   - "refactoring" → "melhoria de estabilidade/velocidade"
   - "technical debt" → "manutenção preventiva"
   - "PR/pull request" → "mudança proposta" ou omita
   - "deploy" → "lançamento"
   - "hotfix" → "correção urgente"
4. Máximo 5-7 bullets por resposta (seja conciso)
5. Para resumos semanais, agrupe por: Entregas → Em Progresso → Atenção
6. Se não houver dados para quantificar impacto, diga: "efeito a ser validado com métricas de negócio"

EXEMPLO DE RESPOSTA IDEAL:
"Esta semana o time focou em melhorar a experiência de checkout:

✅ **Checkout otimizado** — objetivo: acelerar carregamento (pode melhorar conversão)
✅ **Bug de pagamento corrigido** — visa resolver falhas relatadas por usuários
🔄 **Integração com novo gateway** — entrega prevista: terça-feira
⚠️ **API do parceiro instável** — implementando fallback para mitigar risco"

Use português brasileiro.""",
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
- Cada bullet DEVE começar com emoji de status: ✅ ⚠️ 🚨 📋 🎯
- ZERO jargão técnico - linguagem 100% de negócios

FOCO:
- Objetivos estratégicos das entregas (não impacto quantificado)
- Riscos de alto nível
- Progresso em relação a metas (baseado em títulos/labels das atividades)

REGRAS DE HONESTIDADE:
1. Use linguagem de INTENÇÃO: "visa", "objetivo", "provavelmente", "pode beneficiar"
2. NÃO afirme impacto em receita/custos/conversão - você não possui esses dados
3. Baseie afirmações APENAS em: títulos, labels, arquivos tocados, descrições
4. Se não houver evidência suficiente, diga: "não há dados nos logs para quantificar"

EXEMPLO:
"📋 **Resumo Executivo - Semana 3**
✅ Melhorias técnicas visam acelerar performance (efeito em conversão a validar)
🎯 Foco em estabilidade do sistema de pagamentos
⚠️ Dependência de conhecimento concentrado em 1 desenvolvedor
📋 Time entregou 12 atividades no período analisado"

Use português brasileiro.""",
}


# ─────────────────────────────────────────────────────────────────────────────
# HONESTY CLAUSE (anti-hallucination guardrail)
# Injected into ALL personas - non-negotiable grounding rules
# ─────────────────────────────────────────────────────────────────────────────
HONESTY_CLAUSE = """
⚠️ REGRAS INEGOCIÁVEIS DE HONESTIDADE:
1. Responda APENAS com base nas atividades fornecidas abaixo.
2. Você NÃO tem acesso a: dados de produção, finanças, conversão, custos, incidentes, analytics.
3. NÃO invente números, porcentagens, valores monetários ou causalidade.
4. Se a pergunta exigir dados que NÃO estão nas atividades:
   - Diga CLARAMENTE quais dados você NÃO possui
   - Sugira ajustar: período de dias, repositórios, ou filtros de time/autor
5. NUNCA assuma impacto em métricas de negócio sem evidência explícita.

📎 REGRAS DE CITAÇÃO (OBRIGATÓRIAS):
As atividades abaixo estão numeradas como [R1], [R2], [R3], etc.

QUANDO USAR [R#]:
✓ Afirmações factuais verificáveis: "O time corrigiu um bug no checkout [R1]."
✓ Múltiplas fontes: "Houve foco em performance esta semana [R1], [R3]."
✓ Status de entrega: "PR aprovado e mergeado [R2]."

QUANDO NÃO USAR [R#]:
✗ Linguagem de intenção: "visa melhorar", "objetivo de", "pode beneficiar" — sem citação
✗ Hipóteses ou projeções: "provavelmente resultará em" — sem citação
✗ Explicações conceituais: prefixar com [Conceito Geral]

REGRAS CRÍTICAS:
1. Use APENAS R# que existam nas sources. Proibido inventar R6 se só há R1-R5.
2. Cada fato = uma citação. Não omita.
3. Se não há evidência: diga "Não encontrei atividades que confirmem isso."
4. Prefixe definições técnicas com [Conceito Geral]:
   Exemplo: "[Conceito Geral] Pull Requests são revisões de código antes de integrar."
"""


class ConversationAI(BaseAIService):
    """
    AI service for conversational interactions.

    Handles chat responses, streaming, and activity summarization.
    """

    def format_activities_with_citations(
        self,
        activities: list[dict[str, Any]],
        sources: list[Any] | None = None,
    ) -> str:
        """
        Format activities with citation references [R1], [R2], etc.

        This method is SPECIFIC to chat and ensures the R# in the context
        match EXACTLY the ref_id in the sources metadata.

        Args:
            activities: List of activity dictionaries.
            sources: Optional list of SourceItem (used to ensure consistency).
                     If provided, uses sources' ref_id; otherwise generates R1..Rn.

        Returns:
            Formatted context string with citation references for LLM.
        """
        if not activities:
            return "Nenhuma atividade encontrada no período selecionado."

        # Header with data source limitations + citation instruction
        header = (
            "═══ FONTE DE DADOS ═══\n"
            "Logs técnicos de desenvolvimento: commits, PRs, issues.\n"
            "NÃO inclui: métricas de negócio, analytics, custos, incidentes.\n"
            "══════════════════════\n\n"
            "Atividades disponíveis (use [R#] para citar):\n\n"
        )

        # Limit to top 50 activities max
        limited_activities = activities[:50]

        context_parts = []
        for i, activity in enumerate(limited_activities, 1):
            # Use source ref_id if available, otherwise generate
            if sources and i <= len(sources):
                source = sources[i - 1]
                ref_id = getattr(source, "ref_id", f"R{i}") or f"R{i}"
            else:
                ref_id = f"R{i}"

            # Extract fields
            activity_type = activity.get("type", "COMMIT")
            title = activity.get("title", "Sem título")
            repo = activity.get("repository_name") or activity.get("repository", "")
            external_id = activity.get("external_id", "")

            # Format external_id nicely
            ext_display = ""
            if external_id:
                if str(activity_type).upper() == "PULL_REQUEST":
                    ext_display = f"PR#{external_id}"
                elif str(activity_type).upper() == "COMMIT":
                    ext_display = str(external_id)[:7]
                else:
                    ext_display = str(external_id)

            # Build line: [R1] PR#142 — Title (repo: name)
            if ext_display:
                line = f"[{ref_id}] {ext_display} — {title}"
            else:
                line = f"[{ref_id}] [{activity_type}] {title}"

            if repo:
                line += f" (repo: {repo})"

            context_parts.append(line)

        return header + "\n".join(context_parts)

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

        # System prompt structure:
        # 1. Persona-specific instructions
        # 2. HONESTY_CLAUSE (anti-hallucination guardrail - non-negotiable)
        # 3. Temporal context
        # 4. Activities context
        system_prompt = f"""{base_prompt}
{HONESTY_CLAUSE}
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
        sources: list[Any] | None = None,
    ) -> str:
        """
        Summarize activities based on a user question.

        Args:
            activities: List of activity dictionaries.
            question: User's question about the activities.
            persona: User persona for response adaptation.
            chat_history: Previous messages in conversation.
            sources: Optional SourceItem list to ensure R# consistency.

        Returns:
            Summary response with citations.
        """
        # Use citation-aware formatter for chat
        context = self.format_activities_with_citations(activities, sources)
        return await self.generate_response(question, context, persona, chat_history=chat_history)

    async def summarize_activities_stream(
        self,
        activities: list[dict[str, Any]],
        question: str,
        persona: Persona = Persona.PRODUCT,
        chat_history: list[dict[str, str]] | None = None,
        sources: list[Any] | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Summarize activities with streaming response.

        Args:
            activities: List of activity dictionaries.
            question: User's question about the activities.
            persona: User persona for response adaptation.
            chat_history: Previous messages in conversation.
            sources: Optional SourceItem list to ensure R# consistency.

        Yields:
            Response text chunks with citations.
        """
        # Use citation-aware formatter for chat
        context = self.format_activities_with_citations(activities, sources)
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
