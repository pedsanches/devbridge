"""
Chat Endpoints.

API for conversational queries about development activities.
Implements persona-based responses (BR-030) and streaming.
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

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

    The response is adapted based on the persona:
    - **executive**: Focus on business outcomes, ROI, strategic impact
    - **technical**: Technical details, architecture, code quality
    - **product**: Features delivered, roadmap progress, blockers

    Example questions:
    - "O que o time fez essa semana?"
    - "Quais PRs foram abertos?"
    - "O que o Pedro commitou?"

    Args:
        db: Database session.
        request: Chat request with message, optional filters, and persona.
        _current_user: Authenticated user (required).
        org_id: Current organization context.

    Returns:
        AI-generated response with activity context and metadata.
    """
    result = await chat_service.process_query(
        db,
        query=request.message,
        user_id=_current_user.id,
        conversation_id=request.conversation_id,
        repository=request.repository,
        author=request.author,
        persona=request.persona,
        org_id=org_id,
    )

    return ChatResponse(
        answer=result["answer"],
        activities_count=result["activities_count"],
        filters=result["filters"],
        metadata=result.get("metadata"),
        conversation_id=result.get("conversation_id"),
    )


@router.post("/stream")
async def chat_stream(
    db: DbSession,
    request: ChatRequest,
    _current_user: CurrentUserRequired,
    org_id: CurrentOrgId,
) -> StreamingResponse:
    """
    Send a message and get a streaming AI-generated response.

    Uses Server-Sent Events (SSE) to stream the response in real-time.

    Args:
        db: Database session.
        request: Chat request with message, optional filters, and persona.
        _current_user: Authenticated user (required).
        org_id: Current organization context.

    Returns:
        Streaming response with AI-generated text chunks.
    """
    from app.services.ai_service import ai_service

    # Get activities for context
    activities = await chat_service.get_context_activities(
        db,
        org_id=org_id,
        repository_name=request.repository,
        author=request.author,
    )

    async def generate():
        async for chunk in ai_service.summarize_activities_stream(
            activities, request.message, request.persona
        ):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
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
