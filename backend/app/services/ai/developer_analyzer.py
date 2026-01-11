"""
Developer Analyzer Module.

Analyzes developer activity patterns for insights.
"""

import json
import logging

from app.services.ai.base import BaseAIService

logger = logging.getLogger(__name__)


class DeveloperAnalyzer(BaseAIService):
    """
    AI service for analyzing developer patterns and metrics.

    Provides insights on developer strengths and collaboration.
    """

    async def analyze_developer_strengths(self, activities: list[dict]) -> list[str]:
        """
        Identify developer strength tags based on activity patterns.

        Args:
            activities: List of activity dicts (title, labels, files_touched, etc).

        Returns:
            List of strength tags (e.g. ["frontend", "testing", "security"]).
        """
        if not activities:
            return []

        # Summarize activity patterns
        file_extensions: dict[str, int] = {}
        keywords: list[str] = []
        labels_seen: list[str] = []

        for activity in activities[:50]:
            # Extract file patterns
            files = activity.get("files_touched", []) or []
            for f in files:
                if "." in f:
                    ext = f.rsplit(".", 1)[-1].lower()
                    file_extensions[ext] = file_extensions.get(ext, 0) + 1

            # Extract keywords from titles
            title = activity.get("title", "").lower()
            keywords.append(title)

            # Collect labels
            labels = activity.get("labels", []) or []
            labels_seen.extend([label.lower() for label in labels])

        # Build context
        top_extensions = sorted(file_extensions.items(), key=lambda x: -x[1])[:10]
        ext_summary = ", ".join([f"{ext}({count})" for ext, count in top_extensions])

        system_prompt = """Analise o padrão de atividades de um desenvolvedor.
Identifique as áreas de força baseado em extensões de arquivos, títulos e labels.

Responda APENAS com um array JSON de tags de força (máximo 5):
Exemplos de tags: "frontend", "backend", "testing", "devops", "security",
"database", "api", "mobile", "performance", "documentation"

Exemplo: ["frontend", "testing", "api"]"""

        user_message = f"""Extensões de arquivo trabalhadas: {ext_summary}
Títulos recentes: {'; '.join(keywords[:10])}
Labels usados: {', '.join(set(labels_seen[:20]))}"""

        try:
            response = await self._call_llm(
                system_prompt, user_message, max_tokens=100, temperature=0.3
            )

            response = response.strip()
            if response.startswith("["):
                return json.loads(response)[:5]
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse strengths JSON: {response}")
        except Exception as e:
            logger.error(f"Failed to analyze developer strengths: {e}")

        # Fallback based on file extensions
        return self._infer_strengths_from_extensions(file_extensions)

    def _infer_strengths_from_extensions(self, extensions: dict[str, int]) -> list[str]:
        """
        Infer developer strengths from file extensions.

        Args:
            extensions: Dict mapping extensions to counts.

        Returns:
            List of inferred strength tags.
        """
        strengths = []
        total = sum(extensions.values())
        if total == 0:
            return []

        # Map extensions to categories
        frontend_exts = {"tsx", "jsx", "vue", "css", "scss", "html"}
        backend_exts = {"py", "go", "java", "rb", "rs", "cs"}
        devops_exts = {"yaml", "yml", "dockerfile", "sh"}

        frontend_count = sum(extensions.get(e, 0) for e in frontend_exts)
        backend_count = sum(extensions.get(e, 0) for e in backend_exts)

        if frontend_count > total * 0.3:
            strengths.append("frontend")
        if backend_count > total * 0.3:
            strengths.append("backend")

        # Check for testing in file names (handled by keywords usually)
        for ext in extensions:
            if ("test" in ext or "spec" in ext) and "testing" not in strengths:
                strengths.append("testing")

        if sum(extensions.get(e, 0) for e in devops_exts) > total * 0.1:
            strengths.append("devops")

        if extensions.get("sql", 0) > 0:
            strengths.append("database")

        return strengths[:5] if strengths else ["general"]

    async def calculate_collaboration_score(
        self, reviews_given: int, reviews_received: int, review_quality: float
    ) -> int:
        """
        Calculate a collaboration score (0-100) for a developer.

        Args:
            reviews_given: Number of code reviews given.
            reviews_received: Number of code reviews received.
            review_quality: Average quality score of reviews (0-1).

        Returns:
            Collaboration score from 0 to 100.
        """
        system_prompt = """Calcule um score de colaboração (0-100) para um desenvolvedor.
Considere:
- Balance entre reviews dados e recebidos (ideal ~1:1)
- Qualidade dos reviews
- Participação ativa na revisão de código

Responda APENAS com um número inteiro de 0 a 100."""

        user_message = f"""Reviews dados: {reviews_given}
Reviews recebidos: {reviews_received}
Qualidade média dos reviews: {review_quality:.2f}"""

        try:
            response = await self._call_llm(
                system_prompt, user_message, max_tokens=10, temperature=0.3
            )

            score = int(response.strip())
            return max(0, min(100, score))
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse collaboration score: {e}")
        except Exception as e:
            logger.error(f"Failed to calculate collaboration score: {e}")

        # Fallback calculation
        return self._calculate_score_heuristic(reviews_given, reviews_received, review_quality)

    def _calculate_score_heuristic(self, given: int, received: int, quality: float) -> int:
        """
        Calculate collaboration score using simple heuristics.

        Args:
            given: Reviews given.
            received: Reviews received.
            quality: Review quality (0-1).

        Returns:
            Score from 0 to 100.
        """
        if given == 0 and received == 0:
            return 50

        # Balance score (ideal is 1:1)
        total = given + received
        if total > 0:
            balance_ratio = (
                min(given, received) / max(given, received) if max(given, received) > 0 else 0
            )
        else:
            balance_ratio = 0

        # Activity score
        activity_score = min(100, total * 5)

        # Combine scores
        score = int(
            balance_ratio * 30  # Balance contributes 30 points
            + (quality * 40)  # Quality contributes 40 points
            + (activity_score * 0.3)  # Activity contributes 30 points
        )

        return max(0, min(100, score))
