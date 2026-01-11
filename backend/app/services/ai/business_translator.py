"""
Business Translator Module.

Translates technical activities into business impact summaries.
"""

import json
import logging
from typing import Any

from app.services.ai.base import BaseAIService

logger = logging.getLogger(__name__)


class BusinessTranslator(BaseAIService):
    """
    AI service for translating technical work to business impact.

    Generates business-friendly summaries and impact classifications.
    """

    async def generate_business_update(self, activity: dict[str, Any]) -> dict[str, Any]:
        """
        Generate a business impact summary for an activity.

        Args:
            activity: Activity dictionary with title, content, labels, files.

        Returns:
            Dict with:
                - summary: str (1-2 sentence business impact description)
                - impact_level: str ("LOW", "MEDIUM", or "HIGH")
                - category: str | None (e.g., "Security", "Feature", "Maintenance")

        If generation fails, returns a default LOW impact update.
        """
        title = activity.get("title", "")
        content = activity.get("content", "")[:2000]
        labels = activity.get("labels", []) or []
        files = activity.get("files_touched", []) or []
        activity_type = activity.get("type", "COMMIT")

        system_prompt = """Você é um tradutor de impacto de negócios.
Analise a atividade técnica e gere um resumo orientado a negócios.

Responda APENAS com um objeto JSON válido:
{
    "summary": "1-2 frases descrevendo o impacto de negócios",
    "impact_level": "LOW" | "MEDIUM" | "HIGH",
    "category": "Security" | "Feature" | "Performance" | "Maintenance" | "Documentation" | "Infrastructure"
}

Critérios de impacto:
- HIGH: Afeta usuários finais diretamente, segurança, ou funcionalidade crítica
- MEDIUM: Melhora eficiência, qualidade de código, ou prepara entregas
- LOW: Manutenção rotineira, pequenos ajustes, documentação"""

        user_message = f"""Tipo: {activity_type}
Título: {title}
Conteúdo: {content}
Labels: {', '.join(labels) if labels else 'Nenhum'}
Arquivos modificados: {', '.join(files[:10]) if files else 'Não informado'}"""

        try:
            response = await self._call_llm(
                system_prompt, user_message, max_tokens=300, temperature=0.3
            )

            # Parse JSON response
            response = response.strip()
            if response.startswith("{"):
                data = json.loads(response)
                return {
                    "summary": data.get("summary", title),
                    "impact_level": data.get("impact_level", "MEDIUM"),
                    "category": data.get("category"),
                }
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse business update JSON: {response}")
        except Exception as e:
            logger.error(f"Failed to generate business update: {e}")

        # Fallback
        return self._fallback_business_update(title, labels)

    def _fallback_business_update(self, title: str, labels: list[str]) -> dict[str, Any]:
        """
        Generate fallback business update based on heuristics.

        Args:
            title: Activity title.
            labels: Activity labels.

        Returns:
            Default business update dict.
        """
        title_lower = title.lower()
        labels_lower = [label.lower() for label in labels] if labels else []

        # Determine impact and category
        impact = "MEDIUM"
        category = "Maintenance"

        if any(kw in title_lower for kw in ["security", "vuln", "cve"]):
            impact = "HIGH"
            category = "Security"
        elif any(kw in title_lower for kw in ["feat", "add", "new"]):
            impact = "MEDIUM"
            category = "Feature"
        elif any(kw in title_lower for kw in ["fix", "bug"]):
            impact = "MEDIUM"
            category = "Maintenance"
        elif any(kw in title_lower for kw in ["doc", "readme"]):
            impact = "LOW"
            category = "Documentation"
        elif any(kw in title_lower for kw in ["perf", "optim", "speed"]):
            impact = "MEDIUM"
            category = "Performance"
        elif any(kw in title_lower for kw in ["deploy", "ci", "cd", "infra"]):
            impact = "MEDIUM"
            category = "Infrastructure"

        # Check labels
        if "bug" in labels_lower or "security" in labels_lower:
            impact = "HIGH" if "security" in labels_lower else "MEDIUM"

        return {
            "summary": f"Atividade de {category.lower()}: {title[:100]}",
            "impact_level": impact,
            "category": category,
        }
