"""
Chat Endpoints.

API for conversational queries about development activities.
"""

from fastapi import APIRouter

from app.api.deps import CurrentOrgId, CurrentUserRequired, DbSession
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import chat_service

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(
    db: DbSession,
    request: ChatRequest,
    _current_user: CurrentUserRequired,
    org_id: CurrentOrgId,
) -> ChatResponse:
    """
    Send a message and get an AI-generated response about activities.

    The AI will analyze recent development activities and answer
    questions about what the team has been working on.

    Example questions:
    - "O que o time fez essa semana?"
    - "Quais PRs foram abertos?"
    - "O que o Pedro commitou?"

    Args:
        db: Database session.
        request: Chat request with message and optional filters.
        _current_user: Authenticated user (required).
        org_id: Current organization context.

    Returns:
        AI-generated response with activity context.
    """
    result = await chat_service.process_query(
        db,
        query=request.message,
        repository=request.repository,
        author=request.author,
        org_id=org_id,
    )

    return ChatResponse(
        answer=result["answer"],
        activities_count=result["activities_count"],
        filters=result["filters"],
    )


@router.get("/health")
async def chat_health() -> dict[str, str]:
    """
    Check chat service health.

    Returns:
        Health status.
    """
    from app.services.ai_service import ai_service

    has_api_key = bool(ai_service.api_key)
    return {
        "status": "healthy" if has_api_key else "degraded",
        "ai_configured": "yes" if has_api_key else "no",
        "model": ai_service.model,
    }
