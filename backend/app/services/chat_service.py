"""
Chat Service.

Business logic for chat functionality.
Retrieves activities and generates AI responses.
Designed to be extended with RAG/vector search in the future.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Activity, Repository
from app.services.ai_service import ai_service


class ChatService:
    """Service for handling chat queries about development activities."""

    async def get_context_activities(
        self,
        db: AsyncSession,
        *,
        repository_name: str | None = None,
        author: str | None = None,
        days: int = 7,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Get activities as context for chat.

        Args:
            db: Database session.
            repository_name: Filter by repository name.
            author: Filter by author.
            days: Number of days to look back.
            limit: Maximum number of activities.

        Returns:
            List of activity dictionaries.
        """
        since = datetime.now(UTC) - timedelta(days=days)

        query = (
            select(Activity, Repository.name.label("repo_name"))
            .join(Repository, Activity.repository_id == Repository.id)
            .where(Activity.created_at >= since)
            .order_by(Activity.created_at.desc())
            .limit(limit)
        )

        if repository_name:
            query = query.where(Repository.name.ilike(f"%{repository_name}%"))

        if author:
            query = query.where(Activity.author.ilike(f"%{author}%"))

        result = await db.execute(query)
        rows = result.all()

        activities = []
        for row in rows:
            activity = row[0]
            repo_name = row[1]
            activities.append(
                {
                    "id": activity.id,
                    "type": activity.type.value
                    if hasattr(activity.type, "value")
                    else str(activity.type),
                    "title": activity.title,
                    "content": activity.content,
                    "author": activity.author,
                    "repository": repo_name,
                    "created_at": activity.created_at.isoformat() if activity.created_at else None,
                }
            )

        return activities

    async def process_query(
        self,
        db: AsyncSession,
        query: str,
        repository: str | None = None,
        author: str | None = None,
    ) -> dict[str, Any]:
        """
        Process a chat query and generate a response.

        This is the main entry point for chat functionality.
        Currently uses simple SQL queries, designed to be extended with RAG.

        Args:
            db: Database session.
            query: User's question.
            repository: Optional repository filter.
            author: Optional author filter.

        Returns:
            Response dictionary with answer and metadata.
        """
        # Extract filters from query (simple keyword detection)
        # This can be extended with NLP/LLM classification later
        effective_author = author
        effective_repo = repository

        # Simple keyword extraction
        query_lower = query.lower()
        if "esta semana" in query_lower or "essa semana" in query_lower:
            days = 7
        elif "hoje" in query_lower:
            days = 1
        elif "este mês" in query_lower or "esse mês" in query_lower:
            days = 30
        else:
            days = 7  # Default

        # Get activities as context
        activities = await self.get_context_activities(
            db,
            repository_name=effective_repo,
            author=effective_author,
            days=days,
        )

        # Generate AI response
        response_text = await ai_service.summarize_activities(activities, query)

        return {
            "answer": response_text,
            "activities_count": len(activities),
            "filters": {
                "repository": effective_repo,
                "author": effective_author,
                "days": days,
            },
        }


# Singleton instance
chat_service = ChatService()
