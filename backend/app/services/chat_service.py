"""
Chat Service.

Business logic for chat functionality.
Retrieves activities via semantic search (RAG) and generates AI responses.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.version import get_prompt_version_id
from app.models import Activity, Repository
from app.models.membership import MemberRole
from app.schemas.chat import ChatMetadata, Persona, SourceItem
from app.services.ai_service import ai_service
from app.services.feedback_service import FeedbackService

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# NO-CONTEXT RESPONSE HELPER (anti-hallucination gate)
# ─────────────────────────────────────────────────────────────────────────────
NO_CONTEXT_RESPONSE = (
    "Não encontrei atividades de desenvolvimento para responder sua pergunta. "
    "Isso pode acontecer por alguns motivos:\n\n"
    "• **Período de tempo**: tente aumentar o filtro de dias\n"
    "• **Repositórios selecionados**: verifique se os repos corretos estão selecionados\n"
    "• **Time/Autor**: ajuste os filtros de equipe ou autor\n\n"
    "Por favor, ajuste os filtros e tente novamente."
)


def build_no_context_response(
    days: int | None = None,
    repository: str | list[str] | None = None,
) -> str:
    """
    Build a deterministic response when no activities are found.

    This avoids calling the LLM (anti-hallucination measure).

    Args:
        days: Current days filter value.
        repository: Current repository filter value.

    Returns:
        Helpful, deterministic message for the user.
    """
    hints: list[str] = []

    if days and days < 30:
        hints.append(f"aumentar o período (atualmente {days} dias)")
    if repository:
        repo_str = ", ".join(repository) if isinstance(repository, list) else repository
        hints.append(f"verificar se o repositório '{repo_str}' possui atividades recentes")

    base = (
        "Não encontrei atividades de desenvolvimento para responder sua pergunta. "
        "Isso pode acontecer por alguns motivos:\n\n"
    )

    bullets = [
        "• **Período de tempo**: tente aumentar o filtro de dias",
        "• **Repositórios selecionados**: verifique se os repos corretos estão selecionados",
        "• **Time/Autor**: ajuste os filtros de equipe ou autor",
    ]

    if hints:
        bullets.append(f"• **Sugestão específica**: {'; '.join(hints)}")

    return base + "\n".join(bullets) + "\n\nPor favor, ajuste os filtros e tente novamente."


def build_confidence_explanation(score: float, activities_count: int) -> str:
    """
    Build a human-readable explanation of the confidence score.

    Args:
        score: The confidence score (0.0 to 1.0).
        activities_count: Number of activities used as evidence.

    Returns:
        Short explanation string for UI display.
    """
    if activities_count == 0:
        return "Sem evidências digitais encontradas"

    if score >= 0.8:
        return f"Alta relevância • {activities_count} evidências encontradas"
    elif score >= 0.6:
        return f"Boa relevância • {activities_count} evidências encontradas"
    elif score >= 0.4:
        return f"Relevância moderada • {activities_count} evidências"
    else:
        return f"Poucas evidências • {activities_count} registros"


def build_sources_with_citations(
    activities: list[dict[str, Any]],
    limit: int = 5,
    ref_map: dict[UUID, str] | None = None,
) -> list[SourceItem]:
    """
    Build SourceItem list with citations (Smart References).

    Args:
        activities: List of activity dicts.
        limit: Maximum sources.
        ref_map: Optional mapping of activity_id -> persistent code (e.g. R-TEAM-123).

    Returns:
        List of SourceItem.
    """
    sources: list[SourceItem] = []

    for i, act in enumerate(activities[:limit], start=1):
        activity_id = act.get("id")
        # Use persistent code if available, else fallback to ephemeral R{i}
        if ref_map and activity_id and UUID(str(activity_id)) in ref_map:
            ref_id = ref_map[UUID(str(activity_id))]
        else:
            ref_id = f"R{i}"

        # Map external_id based on activity type
        activity_type = (act.get("type") or "").upper()
        raw_external_id = act.get("external_id")

        if raw_external_id:
            if activity_type == "PULL_REQUEST":
                # For PRs, external_id is the PR number
                external_id = f"PR#{raw_external_id}"
            elif activity_type == "COMMIT":
                # For commits, external_id is the SHA (show first 7 chars)
                external_id = str(raw_external_id)[:7]
            else:
                # Generic fallback
                external_id = str(raw_external_id)
        else:
            external_id = None

        sources.append(
            SourceItem(
                title=act.get("title", "Untitled"),
                repository=act.get("repository", "unknown"),
                type=act.get("type", "unknown"),
                author=act.get("author"),
                url=act.get("url"),
                ref_id=ref_id,
                external_id=external_id,
            )
        )

    return sources


class ChatService:
    """Service for handling chat queries about development activities."""

    async def get_context_activities(
        self,
        db: AsyncSession,
        *,
        org_id: str | None = None,
        team_id: str | None = None,
        user_role: "MemberRole | None" = None,
        repository_name: str | list[str] | None = None,
        author: str | None = None,
        days: int = 7,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Get activities from database as context for chat."""
        from app.models.membership import MemberRole
        from app.models.team import team_repositories

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

        # Team Scope (Security Boundary)
        if team_id:
            from sqlalchemy import or_

            query = query.outerjoin(
                team_repositories, Repository.id == team_repositories.c.repository_id
            ).where(
                or_(Repository.team_id == str(team_id), team_repositories.c.team_id == str(team_id))
            )

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
        is_viewer = user_role == MemberRole.VIEWER

        for row in rows:
            activity = row[0]
            repo_name = row[1]

            # Sanitization for VIEWER role (ADR-013)
            # Viewers see sanitized summaries, no raw diffs/content
            # Ideally we would fetch BusinessUpdate summary here
            # For now, we strictly hide raw technically dense content
            # Keep title as it's usually safe-ish, but hide full commit body
            content = activity.title if is_viewer else activity.content

            activities.append(
                {
                    "id": activity.id,
                    "type": activity.type.value
                    if hasattr(activity.type, "value")
                    else str(activity.type),
                    "title": activity.title,
                    "content": content,  # Role-based content
                    "author": activity.author
                    if not is_viewer
                    else activity.author.split("<")[
                        0
                    ].strip(),  # Simple obfuscation for viewers? Optional.
                    "repository": repo_name,
                    "external_id": activity.external_id
                    if not is_viewer
                    else None,  # Hide SHAs for viewers
                    "date": (activity.occurred_at or activity.created_at).isoformat()
                    if (activity.occurred_at or activity.created_at)
                    else None,
                    "created_at": activity.created_at.isoformat() if activity.created_at else None,
                    "files_touched": activity.files_touched if not is_viewer else [],
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
                    "external_id": activity.external_id,  # PR number or commit SHA
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

    def _calculate_confidence(
        self,
        search_results: list[dict[str, Any]],
        activities_count: int,
    ) -> float:
        """
        Calculate dynamic confidence score based on retrieval quality.

        Layered confidence calculation:
        - Base: 0.3 (no activities found)
        - Retrieval: Average of top-3 vector search scores
        - Coverage bonus: min(activities_count / 5, 1.0) * 0.2

        Args:
            search_results: Results from vector search with scores.
            activities_count: Number of activities found.

        Returns:
            Confidence score between 0.0 and 1.0.
        """
        if activities_count == 0:
            return 0.3

        if not search_results:
            # SQL fallback - moderate confidence
            return 0.5 + min(activities_count / 10, 0.2)

        # Get top-3 scores from semantic search
        top_scores: list[float] = [
            float(r.get("score", 0) or 0) for r in search_results[:3] if r.get("score") is not None
        ]

        if not top_scores:
            return 0.5

        avg_score = sum(top_scores) / len(top_scores)

        # Coverage bonus based on number of activities
        coverage_bonus = min(activities_count / 5, 1.0) * 0.15

        return min(avg_score + coverage_bonus, 1.0)

    async def search_activities_semantic(
        self,
        query: str,
        org_id: str | None = None,
        repository: str | list[str] | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Search activities using semantic vector search.

        Args:
            query: Search query text.
            org_id: Organization ID for multi-tenant filtering.
            repository: Repository name(s) to filter by.
            limit: Maximum results.

        Returns:
            List of search results with activity IDs and scores.
        """
        try:
            from app.services.vector_service import vector_service

            return cast(
                list[dict[str, Any]],
                vector_service.search(
                    query,
                    limit=limit,
                    org_id=org_id,
                    repository_name=repository,
                ),
            )
        except Exception:
            return []

    async def process_query(
        self,
        db: AsyncSession,
        query: str,
        user_id: UUID,
        org_id: str | None = None,
        conversation_id: UUID | None = None,
        team_id: str | None = None,
        user_role: "MemberRole | None" = None,
        repository: str | list[str] | None = None,
        author: str | None = None,
        persona: Persona = Persona.PRODUCT,
        days: int = 30,
        use_semantic_search: bool = True,
        trace_id: str | None = None,
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
            team_id: Optional Team ID for context scoping (ADR-013).
            user_role: User's role in the team (ADR-013).
            repository: Optional repository filter.
            author: Optional author filter.
            use_semantic_search: Whether to try semantic search first.

        Returns:
            Response dictionary with answer and metadata.
        """
        from app.models.conversation import MessageRole
        from app.services.conversation_service import ConversationService

        # Initialize services
        conversation_service = ConversationService(db)
        feedback_service = FeedbackService(db)

        # 0. Generate Lineage IDs
        from uuid import uuid4

        generation_id = str(uuid4())

        prompt_version_id = get_prompt_version_id()

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
        if conversation_id is None:
            raise ValueError("Conversation ID cannot be None")
        await conversation_service.add_message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=query,
        )

        activities: list[dict[str, Any]] = []
        search_method = "sql"
        search_results: list[dict[str, Any]] = []

        # Try semantic search first
        if use_semantic_search:
            search_results = await self.search_activities_semantic(
                query, org_id=org_id, repository=repository, limit=15
            )
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
            activities = await self.get_context_activities(
                db,
                org_id=org_id,
                team_id=str(team_id) if team_id else None,
                user_role=user_role,
                repository_name=repository,
                author=author,
                days=days,
            )
            # Clear search_results since we're using SQL fallback
            search_results = []

        # ─────────────────────────────────────────────────────────────────────
        # ANTI-HALLUCINATION GATE: No activities → No LLM call
        # ─────────────────────────────────────────────────────────────────────
        if not activities:
            logger.info(
                "No activities found for query - returning deterministic response",
                extra={
                    "query": query[:100],
                    "days": days,
                    "repository": repository,
                    "org_id": org_id,
                },
            )
            response_text = build_no_context_response(days=days, repository=repository)
            # No citations when no activities
            sources: list[SourceItem] = []
        else:
            # Build sources BEFORE calling LLM to ensure R# consistency
            # 1. Fetch persistent references if team context is available (ADR-013)
            ref_map = {}
            if team_id:
                try:
                    from app.services.reference_service import reference_service
                    from app.services.team_service import team_service

                    team_obj = await team_service.get_team(
                        db, str(team_id), str(org_id) if org_id else ""
                    )
                    if team_obj:
                        ref_map = await reference_service.get_or_create_references(
                            db, UUID(str(team_id)), team_obj.slug, activities
                        )
                except Exception:
                    logger.exception("Failed to fetch smart references")

            # 2. Enrich activities and sources with Ref Codes
            sources = build_sources_with_citations(activities, limit=50, ref_map=ref_map)

            # Generate AI response with persona and sources for citation consistency
            response_text = await ai_service.summarize_activities(
                activities, query, persona, chat_history=chat_history, sources=sources
            )

        # Calculate dynamic confidence score based on retrieval quality
        confidence_score = self._calculate_confidence(search_results, len(activities))

        # Build structured metadata (BR-011)
        metadata = ChatMetadata(
            activities_count=len(activities),
            search_method=search_method,
            confidence_score=confidence_score,
            persona_used=persona,
            sources=sources,
            generation_id=generation_id,
            prompt_version_id=prompt_version_id,
            trace_id=trace_id,
        )

        # Persist Assistant Message
        if conversation_id:
            message_obj = await conversation_service.add_message(
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT,
                content=response_text,
                message_metadata=metadata.model_dump(),
            )

            # 5. Log Chat Response Generation Event
            # Best-effort logging - don't fail the request
            try:
                await feedback_service.log_response_generated(
                    generation_id=generation_id,
                    message_id=str(message_obj.id),
                    organization_id=str(org_id) if org_id else "",
                    trace_id=trace_id,
                    user_id=str(user_id),
                    payload={
                        "model": ai_service.model or "gpt-4o-mini",
                        "persona": persona.value,
                        "prompt_version_id": prompt_version_id,
                        "activities_count": len(activities),
                        "search_method": search_method,
                        "confidence_score": confidence_score,
                    },
                )
            except Exception:
                # Log error but proceed
                logger.exception("Failed to log chat response event")

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
