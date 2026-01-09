"""
AI Service.

Integration with OpenAI for generating responses.
Implements BR-030 (persona-based responses) and streaming support.
"""

from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from openai import OpenAI

from app.core.config import settings
from app.schemas.chat import Persona

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
    """Generate temporal context string for LLM grounding.

    Provides the current date, time, and day of week to help
    the LLM interpret time-relative queries correctly.
    """
    try:
        tz = ZoneInfo(timezone)
        now = datetime.now(tz)
    except Exception:
        now = datetime.now()

    weekday = WEEKDAY_NAMES.get(now.weekday(), "")

    return f"""INFORMAÇÃO TEMPORAL (sua referência de tempo atual):
- Data de hoje: {now.strftime('%d de %B de %Y').replace('January', 'janeiro').replace('February', 'fevereiro').replace('March', 'março').replace('April', 'abril').replace('May', 'maio').replace('June', 'junho').replace('July', 'julho').replace('August', 'agosto').replace('September', 'setembro').replace('October', 'outubro').replace('November', 'novembro').replace('December', 'dezembro')}
- Dia da semana: {weekday}
- Horário: {now.strftime('%H:%M')} (Fuso: {timezone})

Use esta informação para interpretar corretamente termos como "hoje", "essa semana", "ontem", "este mês", etc."""


# Persona-specific prompts (BR-030: Adaptation by Audience)
PERSONA_PROMPTS: dict[Persona, str] = {
    Persona.EXECUTIVE: """Você é um consultor executivo do DevBridge que traduz trabalho técnico em valor de negócio.
Responda em português brasileiro de forma clara e executiva.

DIRETRIZES DE FORMATAÇÃO (MARKDOWN OBRIGATÓRIO):
- Use **negrito** para destacar métricas, prazos e impactos chave.
- Use listas (bullet points) para organizar insights, riscos e recomendações.
- Utilize cabeçalhos (ex: `### Resumo`) para estruturar a resposta.

O QUE FAZER:
- Foque em Outcomes de negócio, ROI, impacto estratégico, riscos e oportunidades.
- Seja conciso, direto e orientado a tomada de decisão.
- Sintetize o progresso em termos de valor entregue.

RESTRIÇÕES RÍGIDAS:
- Baseie suas respostas **EXCLUSIVAMENTE** nos dados fornecidos abaixo.
- **NÃO** invente datas, nomes ou fatos não presentes no contexto.
- Se a informação for insuficiente, diga claramente.
- Evite "juridiquês" ou detalhes técnicos irrelevantes (nomes de variáveis, funções).""",
    Persona.TECHNICAL: """Você é um consultor técnico sênior do DevBridge que ajuda líderes técnicos a entender o trabalho do time.
Responda em português brasileiro de forma técnica e precisa.

DIRETRIZES DE FORMATAÇÃO (MARKDOWN OBRIGATÓRIO):
- Use `backticks` para nomes de arquivos, funções, classes e variáveis.
- Use blocos de código (```) para snippets ou estruturas de dados.
- Use listas para agrupar mudanças por componente ou tipo.
- Utilize cabeçalhos para separar tópicos (ex: `### Refatoração`, `### Novas Features`).

O QUE FAZER:
- Foque em qualidade de código, arquitetura, débito técnico, padrões e segurança.
- Cite arquivos e trechos específicos como evidência.
- Analise a complexidade e o impacto das mudanças no sistema.

RESTRIÇÕES RÍGIDAS:
- Baseie suas respostas **EXCLUSIVAMENTE** nos dados fornecidos abaixo.
- **NÃO** alucine códigos, arquivos ou comportamentos que não constam no contexto.
- Se não houver detalhes suficientes para uma análise técnica profunda, informe.
""",
    Persona.PRODUCT: """Você é um assistente de produto do DevBridge que ajuda Product Managers a entender o progresso do time.
Responda em português brasileiro de forma clara e orientada a produto e valor para o usuário.

DIRETRIZES DE FORMATAÇÃO (MARKDOWN OBRIGATÓRIO):
- Use **negrito** para nomes de features, status e datas críticas.
- Use listas para roadmap, itens entregues e pendências.
- Utilize cabeçalhos para organizar por épico ou funcionalidade.

O QUE FAZER:
- Foque em features entregues, progresso do roadmap, blockers e dependências.
- Destaque o valor que cada entrega traz para o usuário final.
- Identifique gargalos no fluxo de entrega.

RESTRIÇÕES RÍGIDAS:
- Baseie suas respostas **EXCLUSIVAMENTE** nos dados fornecidos abaixo.
- **NÃO** invente previsões de entrega ou status que não estejam explícitos.
- Se não estiver claro se algo foi concluído, diga que está "em andamento" ou "incerto", não confirme sem certeza.
""",
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
        base_prompt = PERSONA_PROMPTS.get(persona, PERSONA_PROMPTS[Persona.PRODUCT])
        temporal_context = get_temporal_context()
        system_prompt = f"{base_prompt}\n\n{temporal_context}"
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
        if not activities:
            return ""

        # Build summary header
        repos = set()
        dates = []
        for act in activities:
            if act.get("repository"):
                repos.add(act["repository"])
            date_str = act.get("date") or act.get("created_at")
            if date_str:
                dates.append(date_str)

        # Calculate date range
        min_date = max_date = ""
        if dates:
            sorted_dates = sorted(dates)
            min_date = sorted_dates[0][:10] if sorted_dates[0] else ""
            max_date = sorted_dates[-1][:10] if sorted_dates[-1] else ""

        summary_header = f"""RESUMO DOS DADOS RECUPERADOS:
- Total de atividades: {len(activities)}
- Período: {min_date} a {max_date}
- Repositórios: {', '.join(sorted(repos)) if repos else 'N/A'}

ATIVIDADES:"""

        context_lines = [summary_header]
        for activity in activities:
            # Use 'date' field which contains occurred_at (actual event date)
            # instead of 'created_at' which is the sync date
            event_date = activity.get("date") or activity.get("created_at", "data desconhecida")
            line = (
                f"- [{activity.get('type', 'UNKNOWN')}] {activity.get('title', 'Sem título')} "
                f"(por {activity.get('author', 'desconhecido')}, "
                f"em {event_date})"
            )

            # Context Enrichment
            if activity.get("files_touched"):
                line += f"\n  Arquivos alterados: {', '.join(activity['files_touched'])}"
            if activity.get("labels"):
                line += f"\n  Labels: {', '.join(activity['labels'])}"
            if activity.get("linked_issues"):
                line += f"\n  Issues vinculadas: {', '.join(activity['linked_issues'])}"
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
        async for chunk in self.generate_response_stream(
            question, context, persona, chat_history=chat_history
        ):
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

    async def classify_activity_tags(self, activity: dict[str, Any]) -> list[str]:
        """
        Classify an activity with business-value tags using LLM.

        Tags:
        - RISK_MITIGATION: Security fixes, bug fixes, stability improvements
        - VELOCITY_ENABLER: Refactoring, tooling, CI/CD improvements
        - COST_SAVING: Performance optimization, resource reduction
        - FEATURE_DELIVERY: New features, user-facing improvements
        - TECH_DEBT: Dependency updates, code cleanup

        Args:
            activity: Activity dictionary with title, content, labels, etc.

        Returns:
            List of applicable tags (can be multiple).
        """
        if not self.client:
            return []

        # Build activity context
        title = activity.get("title", "")
        content = activity.get("content", "")[:500] if activity.get("content") else ""
        labels = ", ".join(activity.get("labels", [])) if activity.get("labels") else ""
        files = (
            ", ".join(activity.get("files_touched", [])[:5])
            if activity.get("files_touched")
            else ""
        )

        prompt = f"""Analyze this software development activity and classify it with ONE OR MORE business value tags.

ACTIVITY:
- Title: {title}
- Labels: {labels}
- Files Changed: {files}
- Description: {content}

AVAILABLE TAGS (select all that apply):
- RISK_MITIGATION: Security fixes, bug fixes, stability, error handling
- VELOCITY_ENABLER: Refactoring, tooling, CI/CD, developer experience
- COST_SAVING: Performance optimization, caching, resource efficiency
- FEATURE_DELIVERY: New features, user-facing functionality
- TECH_DEBT: Dependency updates, code cleanup, migrations

Respond with ONLY a JSON array of applicable tags. Example: ["FEATURE_DELIVERY", "RISK_MITIGATION"]
If unsure, return an empty array: []"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.3,
            )
            result = response.choices[0].message.content or "[]"
            # Parse JSON response
            import json

            tags = json.loads(result.strip())
            # Validate tags
            valid_tags = {
                "RISK_MITIGATION",
                "VELOCITY_ENABLER",
                "COST_SAVING",
                "FEATURE_DELIVERY",
                "TECH_DEBT",
            }
            return [tag for tag in tags if tag in valid_tags]
        except Exception:
            return []

    async def generate_business_update(self, activity: dict[str, Any]) -> dict[str, Any]:
        """
        Generate a business impact summary for an activity using LLM.

        Analyzes the activity's title, content, labels, and files to produce
        a human-readable summary and impact classification.

        Args:
            activity: Activity dictionary with title, content, labels, files_touched, etc.

        Returns:
            Dictionary with:
            - summary: str (1-2 sentence business impact description)
            - impact_level: str ("LOW", "MEDIUM", or "HIGH")
            - category: str | None (e.g., "Security", "Feature", "Maintenance")

        If generation fails, returns a default LOW impact update.
        """
        if not self.client:
            return {
                "summary": "Análise de impacto indisponível.",
                "impact_level": "LOW",
                "category": None,
            }

        # Build activity context
        title = activity.get("title", "")
        content = activity.get("content", "")[:800] if activity.get("content") else ""
        labels = ", ".join(activity.get("labels", [])) if activity.get("labels") else ""
        files = (
            ", ".join(activity.get("files_touched", [])[:10])
            if activity.get("files_touched")
            else ""
        )
        activity_type = activity.get("type", "COMMIT")

        prompt = f"""Analyze this software development activity and generate a business impact summary.

ACTIVITY:
- Type: {activity_type}
- Title: {title}
- Labels: {labels}
- Files Changed: {files}
- Description: {content}

Generate a JSON response with:
1. "summary": A concise 1-2 sentence description of the business impact in Portuguese (BR). Focus on WHAT value this brings, not technical details.
2. "impact_level": One of "LOW", "MEDIUM", or "HIGH" based on:
   - HIGH: Security fixes, critical bugs, major features, breaking changes
   - MEDIUM: New features, significant improvements, moderate refactoring
   - LOW: Minor fixes, documentation, small refactors, dependency updates
3. "category": One of "Security", "Feature", "Bugfix", "Performance", "Refactoring", "Documentation", "Infrastructure", "Maintenance"

Respond with ONLY valid JSON. Example:
{{"summary": "Corrige vulnerabilidade de autenticação que permitia acesso não autorizado.", "impact_level": "HIGH", "category": "Security"}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.3,
            )
            result = response.choices[0].message.content or "{}"

            import json

            # Clean up response (remove markdown code blocks if present)
            cleaned = result.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("```", 1)[0]
            cleaned = cleaned.strip()

            data = json.loads(cleaned)

            # Validate and sanitize response
            valid_levels = {"LOW", "MEDIUM", "HIGH"}
            valid_categories = {
                "Security",
                "Feature",
                "Bugfix",
                "Performance",
                "Refactoring",
                "Documentation",
                "Infrastructure",
                "Maintenance",
            }

            return {
                "summary": str(data.get("summary", "Atividade processada."))[:500],
                "impact_level": data.get("impact_level", "LOW")
                if data.get("impact_level") in valid_levels
                else "LOW",
                "category": data.get("category")
                if data.get("category") in valid_categories
                else None,
            }
        except Exception as e:
            # Log error for debugging but return default
            import logging

            logging.warning(f"Failed to generate business update: {e}")
            return {
                "summary": "Atividade de desenvolvimento registrada.",
                "impact_level": "LOW",
                "category": None,
            }

    async def analyze_developer_strengths(self, activities: list[dict]) -> list[str]:
        """
        Identify developer strength tags based on their activity patterns.

        Args:
            activities: List of activity dicts (title, labels, files_touched, etc).

        Returns:
            List of strength tags (e.g. ["frontend", "testing", "security"]).
        """
        if not self.client or not activities:
            return []

        # Summarize context
        files_counter: dict[str, int] = {}
        labels_counter: dict[str, int] = {}
        for act in activities[:50]:  # Analyze last 50 activities
            for f in act.get("files_touched", []) or []:
                ext = f.split(".")[-1] if "." in f else "unknown"
                files_counter[ext] = files_counter.get(ext, 0) + 1
            for label in act.get("labels", []) or []:
                labels_counter[label] = labels_counter.get(label, 0) + 1

        prompt = f"""Analyze this developer's activity patterns and identify their top 3 technical strengths/Areas of Expertise.

DATA:
- Top File Extensions: {str(dict(sorted(files_counter.items(), key=lambda x: x[1], reverse=True)[:5]))}
- Top Labels: {str(dict(sorted(labels_counter.items(), key=lambda x: x[1], reverse=True)[:5]))}
- Sample Activity Titles: {[a.get('title') for a in activities[:5]]}

Return ONLY a JSON array of strings (max 3 tags). Example: ["frontend", "python", "devops"]"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.3,
            )
            import json

            result = response.choices[0].message.content or "[]"
            tags = json.loads(result.strip())
            return tags if isinstance(tags, list) else []
        except Exception:
            return []

    async def calculate_collaboration_score(
        self, reviews_given: int, reviews_received: int, review_quality: float
    ) -> float:
        """
        Calculate a collaboration score (0-100) for a developer using AI reasoning.
        """
        if not self.client:
            # Fallback algorithmic calculation
            score = min((reviews_given * 5) + (reviews_received * 2) + (review_quality * 20), 100)
            return float(score)

        prompt = f"""Calculate a Collaboration Score (0-100) for a developer based on:
- Reviews Given: {reviews_given}
- Reviews Received: {reviews_received}
- Avg Review Quality Score (0-5 scale): {review_quality}

Consider that giving reviews is highly valuable.
Return ONLY the number (integer)."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.0,
            )
            result = response.choices[0].message.content or "0"
            # Extract number
            import re

            match = re.search(r"\d+", result)
            return float(match.group()) if match else 0.0
        except Exception:
            return 0.0

    async def estimate_complexity_score(self, diff: str, files_touched: list[str]) -> float:
        """
        Estimate the complexity of a code change (0-100) using AI analysis.
        """
        if not self.client:
            return 10.0  # Default low complexity

        prompt = f"""Estimate the technical complexity (0-100) of this code change.
Files: {files_touched}
Diff Preview:
{diff[:1000]}

Return ONLY the number (integer)."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.0,
            )
            result = response.choices[0].message.content or "10"
            import re

            match = re.search(r"\d+", result)
            return float(match.group()) if match else 10.0
        except Exception:
            return 10.0

    async def generate_developer_summary(self, profile_data: dict[str, Any]) -> str:
        """
        Generate a natural language summary of a developer's contributions.
        """
        if not self.client:
            return "Summary unavailable."

        prompt = f"""Generate a 2-sentence professional summary of this developer's contributions.
Profile Data: {str(profile_data)}
Language: Portuguese (BR)"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.5,
            )
            return response.choices[0].message.content or "Resumo indisponível."
        except Exception:
            return "Resumo indisponível."


# Singleton instance
ai_service = AIService()
