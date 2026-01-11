"""
Activity Analyzer Module.

Analyzes activities for tagging and classification.
"""

import json
import logging
from typing import Any

from app.services.ai.base import BaseAIService

logger = logging.getLogger(__name__)

# Business value tags
VALUE_TAGS = [
    "RISK_MITIGATION",  # Security, bug fixes, stability
    "VELOCITY_ENABLER",  # Refactoring, tooling, CI/CD
    "FEATURE_DELIVERY",  # New features, user value
    "TECH_DEBT_REDUCTION",  # Code quality, architecture
]


class ActivityAnalyzer(BaseAIService):
    """
    AI service for analyzing and classifying activities.

    Handles tagging activities with business value classifications.
    """

    async def classify_activity_tags(self, activity: dict[str, Any]) -> list[str]:
        """
        Classify an activity with business-value tags using LLM.

        Tags:
        - RISK_MITIGATION: Security fixes, bug fixes, stability improvements
        - VELOCITY_ENABLER: Refactoring, tooling, CI/CD improvements
        - FEATURE_DELIVERY: New features, user-facing improvements
        - TECH_DEBT_REDUCTION: Code quality, architecture improvements

        Args:
            activity: Activity dictionary with title, content, labels, etc.

        Returns:
            List of applicable tags (can be multiple).
        """
        title = activity.get("title", "")
        content = activity.get("content", "")[:1000]
        labels = activity.get("labels", []) or []
        files = activity.get("files_touched", []) or []

        system_prompt = """Você é um classificador de atividades de desenvolvimento.
Analise a atividade e classifique com uma ou mais tags de valor:

- RISK_MITIGATION: correções de segurança, bugs, melhorias de estabilidade
- VELOCITY_ENABLER: refatoração, ferramentas, melhorias de CI/CD
- FEATURE_DELIVERY: novas funcionalidades, melhorias visíveis ao usuário
- TECH_DEBT_REDUCTION: qualidade de código, melhorias de arquitetura

Responda APENAS com um array JSON de tags aplicáveis.
Exemplo: ["FEATURE_DELIVERY", "TECH_DEBT_REDUCTION"]"""

        user_message = f"""Título: {title}
Conteúdo: {content}
Labels: {', '.join(labels) if labels else 'Nenhum'}
Arquivos: {', '.join(files[:10]) if files else 'Não informado'}"""

        try:
            response = await self._call_llm(
                system_prompt, user_message, max_tokens=100, temperature=0.3
            )

            # Parse JSON response
            response = response.strip()
            if response.startswith("["):
                tags = json.loads(response)
                # Validate tags
                return [t for t in tags if t in VALUE_TAGS]
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse tags JSON: {response}")
        except Exception as e:
            logger.error(f"Failed to classify activity: {e}")

        # Default fallback based on simple heuristics
        return self._fallback_classification(title, labels, files)

    def _fallback_classification(
        self, title: str, labels: list[str], _files: list[str]
    ) -> list[str]:
        """
        Simple heuristic classification as fallback.

        Args:
            title: Activity title.
            labels: Activity labels.
            files: Files touched.

        Returns:
            List of inferred tags.
        """
        tags = []
        title_lower = title.lower()
        labels_lower = [label.lower() for label in labels] if labels else []

        # Security/bug patterns
        if any(kw in title_lower for kw in ["fix", "bug", "security", "patch", "hotfix"]):
            tags.append("RISK_MITIGATION")

        # Feature patterns
        if any(kw in title_lower for kw in ["feat", "add", "new", "implement"]):
            tags.append("FEATURE_DELIVERY")

        # Refactor patterns
        if any(kw in title_lower for kw in ["refactor", "chore", "ci", "cd", "tool"]):
            tags.append("VELOCITY_ENABLER")

        # Tech debt patterns
        if any(kw in title_lower for kw in ["clean", "improve", "optim", "debt"]):
            tags.append("TECH_DEBT_REDUCTION")

        # Check labels
        if ("bug" in labels_lower or "security" in labels_lower) and "RISK_MITIGATION" not in tags:
            tags.append("RISK_MITIGATION")

        if (
            "enhancement" in labels_lower or "feature" in labels_lower
        ) and "FEATURE_DELIVERY" not in tags:
            tags.append("FEATURE_DELIVERY")

        # Default to feature if nothing matched
        return tags if tags else ["FEATURE_DELIVERY"]
