"""
Chat Service.

Business logic for chat functionality.
Retrieves activities via semantic search (RAG) and generates AI responses.
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Activity, Repository
from app.schemas.chat import ChatMetadata, Persona
from app.services.ai_service import ai_service


class ChatService:
    """Service for handling chat queries about development activities."""

    async def get_context_activities(
        self,
        db: AsyncSession,
        *,
        org_id: str | None = None,
        repository_name: str | list[str] | None = None,
        author: str | None = None,
        days: int = 7,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Get activities from database as context for chat."""
        since = datetime.now(UTC) - timedelta(days=days)

        query = (
            select(Activity, Repository.name.label("repo_name"))
            .join(Repository, Activity.repository_id == Repository.id)
            .where(func.coalesce(Activity.occurred_at, Activity.created_at) >= since)
            .order_by(func.coalesce(Activity.occurred_at, Activity.created_at).desc())
            .limit(limit)
        )

        # Multi-tenant filter
        if org_id:
            query = query.where(Repository.organization_id == org_id)

        if repository_name:
            if isinstance(repository_name, list):
                # Filter by any of the repo names
                from sqlalchemy import or_

                conditions = [Repository.name.ilike(f"%{name}%") for name in repository_name]
                query = query.where(or_(*conditions))
            else:
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
                    "date": (activity.occurred_at or activity.created_at).isoformat()
                    if (activity.occurred_at or activity.created_at)
                    else None,
                    "created_at": activity.created_at.isoformat() if activity.created_at else None,
                    "files_touched": activity.files_touched,
                    "labels": activity.labels,
                    "linked_issues": activity.linked_issues,
                    "value_tags": activity.value_tags,
                }
            )

        return activities

    async def get_activities_by_ids(
        self,
        db: AsyncSession,
        activity_ids: list[UUID],
        org_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get activities by their IDs."""
        query = (
            select(Activity, Repository.name.label("repo_name"))
            .join(Repository, Activity.repository_id == Repository.id)
            .where(Activity.id.in_(activity_ids))
        )

        # Multi-tenant filter
        if org_id:
            query = query.where(Repository.organization_id == org_id)

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
                    "date": (activity.occurred_at or activity.created_at).isoformat()
                    if (activity.occurred_at or activity.created_at)
                    else None,
                    "created_at": activity.created_at.isoformat() if activity.created_at else None,
                    "files_touched": activity.files_touched,
                    "labels": activity.labels,
                    "linked_issues": activity.linked_issues,
                    "value_tags": activity.value_tags,
                }
            )

        return activities

    async def search_activities_semantic(
        self,
        query: str,
        org_id: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Search activities using semantic vector search.

        Args:
            query: Search query text.
            org_id: Organization ID for multi-tenant filtering.
            limit: Maximum results.

        Returns:
            List of search results with activity IDs and scores.
        """
        try:
            from app.services.vector_service import vector_service

            return vector_service.search(query, limit=limit, org_id=org_id)
        except Exception:
            return []

    async def process_query(
        self,
        db: AsyncSession,
        query: str,
        user_id: UUID,
        org_id: str | None = None,
        conversation_id: UUID | None = None,
        repository: str | list[str] | None = None,
        author: str | None = None,
        persona: Persona = Persona.PRODUCT,
        use_semantic_search: bool = True,
    ) -> dict[str, Any]:
        """
        Process a chat query and generate a response.

        Uses semantic search (RAG) when available, falls back to SQL.
        Persists the interaction in a conversation.

        Args:
            db: Database session.
            query: User's question.
            user_id: ID of the user sending the query.
            org_id: Organization ID for multi-tenant filtering.
            conversation_id: Optional ID of existing conversation.
            repository: Optional repository filter.
            author: Optional author filter.
            use_semantic_search: Whether to try semantic search first.

        Returns:
            Response dictionary with answer and metadata.
        """
        from app.models.conversation import MessageRole
        from app.services.conversation_service import ConversationService

        conversation_service = ConversationService(db)

        # 1. Handle Conversation Persistence
        chat_history = []

        if conversation_id:
            # Fetch existing history for context (limit to last 6 messages)
            # Fetch BEFORE adding current message to avoid duplication in context
            existing_msgs = await conversation_service.get_conversation_messages(
                conversation_id, limit=6
            )
            chat_history = [{"role": m.role.value, "content": m.content} for m in existing_msgs]
        else:
            # Create new conversation if not provided
            conversation = await conversation_service.create_conversation(
                user_id=user_id,
                organization_id=UUID(org_id)
                if org_id
                else UUID(int=0),  # Should always have org_id in prod
            )
            conversation_id = conversation.id

            # Auto-title generation (simple heuristic for now)
            # Future: Use LLM to generate title based on first query
            title = await conversation_service.generate_title(query)
            # Update title
            from app.schemas.conversation import ConversationUpdate

            await conversation_service.update_conversation(
                conversation.id, conversation.organization_id, ConversationUpdate(title=title)
            )

        # Persist User Message
        assert conversation_id is not None
        await conversation_service.add_message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=query,
        )

        activities: list[dict[str, Any]] = []
        search_method = "sql"

        # Try semantic search first
        if use_semantic_search:
            search_results = await self.search_activities_semantic(query, org_id=org_id, limit=15)
            if search_results:
                # Get full activity data for the top results
                activity_ids = [
                    UUID(r["activity_id"]) for r in search_results if r.get("activity_id")
                ]
                if activity_ids:
                    activities = await self.get_activities_by_ids(db, activity_ids, org_id=org_id)
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
                org_id=org_id,
                repository_name=repository,
                author=author,
                days=days,
            )

        # Generate AI response with persona
        response_text = await ai_service.summarize_activities(
            activities, query, persona, chat_history=chat_history
        )

        # Build structured metadata (BR-011)
        metadata = ChatMetadata(
            activities_count=len(activities),
            search_method=search_method,
            confidence_score=0.9 if search_method == "semantic" else 0.7,
            persona_used=persona,
        )

        # Persist Assistant Message
        if conversation_id:
            await conversation_service.add_message(
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT,
                content=response_text,
                message_metadata=metadata.model_dump(),
            )

        return {
            "answer": response_text,
            "activities_count": len(activities),
            "search_method": search_method,
            "conversation_id": conversation_id,
            "filters": {
                "repository": repository,
                "author": author,
            },
            "metadata": metadata,
        }


# Singleton instance
chat_service = ChatService()
