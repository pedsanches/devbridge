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
    Creates or updates conversations and persists messages.

    Args:
        db: Database session.
        request: Chat request with message, optional filters, and persona.
        _current_user: Authenticated user (required).
        org_id: Current organization context.

    Returns:
        Streaming response with AI-generated text chunks and metadata.
    """
    import json
    from uuid import UUID

    from app.models.conversation import MessageRole
    from app.services.ai_service import ai_service
    from app.services.conversation_service import ConversationService

    conversation_service = ConversationService(db)

    # Get or create conversation
    if request.conversation_id:
        conversation = await conversation_service.get_conversation(
            request.conversation_id, UUID(org_id)
        )
        if not conversation or conversation.user_id != _current_user.id:
            # Invalid conversation_id, create new one
            conversation = await conversation_service.create_conversation(
                user_id=_current_user.id,
                organization_id=UUID(org_id),
            )
    else:
        # Create new conversation
        conversation = await conversation_service.create_conversation(
            user_id=_current_user.id,
            organization_id=UUID(org_id),
        )

    # Save user message
    await conversation_service.add_message(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=request.message,
    )

    # Try semantic search first, then fallback to SQL
    search_results = await chat_service.search_activities_semantic(
        request.message, org_id=org_id, repository=request.repository, limit=15
    )

    if search_results:
        from uuid import UUID as UUIDType

        activity_ids = [UUIDType(r["activity_id"]) for r in search_results if r.get("activity_id")]
        if activity_ids:
            activities = await chat_service.get_activities_by_ids(db, activity_ids, org_id=org_id)
        else:
            activities = await chat_service.get_context_activities(
                db,
                org_id=org_id,
                repository_name=request.repository,
                author=request.author,
            )
    else:
        activities = await chat_service.get_context_activities(
            db,
            org_id=org_id,
            repository_name=request.repository,
            author=request.author,
        )

    # Build sources list for transparency (top 5)
    sources = [
        {
            "title": act.get("title", "Untitled"),
            "repository": act.get("repository", "unknown"),
            "type": act.get("type", "unknown"),
            "author": act.get("author"),
            "url": act.get("url"),
        }
        for act in activities[:5]
    ]

    # Calculate confidence score
    confidence_score = chat_service._calculate_confidence(search_results, len(activities))

    async def generate():
        # Send metadata first with conversation_id and sources
        metadata = {
            "type": "metadata",
            "conversation_id": str(conversation.id),
            "activities_count": len(activities),
            "sources": sources,
            "confidence_score": confidence_score,
        }
        yield f"data: {json.dumps(metadata)}\n\n"

        # Accumulate response for saving
        full_response = ""

        # Stream AI response
        async for chunk in ai_service.summarize_activities_stream(
            activities, request.message, request.persona
        ):
            full_response += chunk
            yield f"data: {chunk}\n\n"

        # Save assistant message BEFORE sending [DONE]
        # This ensures the message is persisted before the client closes the connection
        await conversation_service.add_message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=full_response,
            message_metadata=metadata,  # Persist metadata with sources
        )

        # Generate title if this is the first exchange (2 messages total)
        # Need to refresh conversation to get updated message_count
        updated_conv = await conversation_service.get_conversation(conversation.id, UUID(org_id))
        if updated_conv and updated_conv.message_count == 2 and not updated_conv.title:
            from app.schemas.conversation import ConversationUpdate

            title = await conversation_service.generate_title(request.message)
            await conversation_service.update_conversation(
                conversation.id, UUID(org_id), ConversationUpdate(title=title)
            )

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
