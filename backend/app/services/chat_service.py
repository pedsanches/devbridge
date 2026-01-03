"""
Chat Service.

Business logic for chat functionality.
Retrieves activities via semantic search (RAG) and generates AI responses.
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

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
        """Get activities from database as context for chat."""
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

    async def get_activities_by_ids(
        self,
        db: AsyncSession,
        activity_ids: list[UUID],
    ) -> list[dict[str, Any]]:
        """Get activities by their IDs."""
        query = (
            select(Activity, Repository.name.label("repo_name"))
            .join(Repository, Activity.repository_id == Repository.id)
            .where(Activity.id.in_(activity_ids))
        )

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

    async def search_activities_semantic(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Search activities using semantic vector search.

        Args:
            query: Search query text.
            limit: Maximum results.

        Returns:
            List of search results with activity IDs and scores.
        """
        try:
            from app.services.vector_service import vector_service

            return vector_service.search(query, limit=limit)
        except Exception:
            return []

    async def process_query(
        self,
        db: AsyncSession,
        query: str,
        repository: str | None = None,
        author: str | None = None,
        use_semantic_search: bool = True,
    ) -> dict[str, Any]:
        """
        Process a chat query and generate a response.

        Uses semantic search (RAG) when available, falls back to SQL.

        Args:
            db: Database session.
            query: User's question.
            repository: Optional repository filter.
            author: Optional author filter.
            use_semantic_search: Whether to try semantic search first.

        Returns:
            Response dictionary with answer and metadata.
        """
        activities: list[dict[str, Any]] = []
        search_method = "sql"

        # Try semantic search first
        if use_semantic_search:
            search_results = await self.search_activities_semantic(query, limit=15)
            if search_results:
                # Get full activity data for the top results
                activity_ids = [
                    UUID(r["activity_id"]) for r in search_results if r.get("activity_id")
                ]
                if activity_ids:
                    activities = await self.get_activities_by_ids(db, activity_ids)
                    search_method = "semantic"

        # Fall back to SQL-based search
        if not activities:
            query_lower = query.lower()
            if "esta semana" in query_lower or "essa semana" in query_lower:
                days = 7
            elif "hoje" in query_lower:
                days = 1
            elif "este mês" in query_lower or "esse mês" in query_lower:
                days = 30
            else:
                days = 7

            activities = await self.get_context_activities(
                db,
                repository_name=repository,
                author=author,
                days=days,
            )

        # Generate AI response
        response_text = await ai_service.summarize_activities(activities, query)

        return {
            "answer": response_text,
            "activities_count": len(activities),
            "search_method": search_method,
            "filters": {
                "repository": repository,
                "author": author,
            },
        }


# Singleton instance
chat_service = ChatService()
