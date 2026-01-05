"""Conversations API."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentOrgId, CurrentUserRequired, DbSession
from app.models.conversation import MessageRole
from app.schemas.conversation import (
    ConversationCreate,
    ConversationDetail,
    ConversationsListResponse,
    ConversationSummary,
    ConversationUpdate,
)
from app.services.conversation_service import ConversationService

router = APIRouter()


@router.post("", response_model=ConversationDetail)
async def create_conversation(
    conversation_in: ConversationCreate,
    db: DbSession,
    current_user: CurrentUserRequired,
    org_id: CurrentOrgId,
):
    """Create a new conversation."""
    service = ConversationService(db)

    # Create conversation
    conversation = await service.create_conversation(
        user_id=current_user.id,
        organization_id=UUID(org_id),
        title=None,
    )

    # If initial message provided, add it
    messages = []
    if conversation_in.message:
        message = await service.add_message(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=conversation_in.message,
        )
        messages.append(message)

        # TODO: Trigger AI response in background? For now, just save user message.
        # Auto-title generation should happen here or be queued.
        if not conversation.title:
            title = await service.generate_title(conversation_in.message)
            await service.update_conversation(
                conversation.id, UUID(org_id), ConversationUpdate(title=title)
            )
            conversation.title = title

    # Refresh conversation with messages to ensure Pydantic can serialize relationships
    # This avoids "MissingGreenlet" error with async SQLAlchemy
    return await service.get_conversation(conversation.id, UUID(org_id), include_messages=True)


@router.get("", response_model=ConversationsListResponse)
async def list_conversations(
    db: DbSession,
    current_user: CurrentUserRequired,
    org_id: CurrentOrgId,
    limit: int = 20,
    offset: int = 0,
):
    """List conversations."""
    service = ConversationService(db)
    return await service.list_conversations(
        user_id=current_user.id,
        organization_id=UUID(org_id),
        limit=limit,
        offset=offset,
    )


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: UUID,
    db: DbSession,
    current_user: CurrentUserRequired,
    org_id: CurrentOrgId,
):
    """Get conversation details with messages."""
    service = ConversationService(db)
    conversation = await service.get_conversation(
        conversation_id=conversation_id,
        organization_id=UUID(org_id),
        include_messages=True,
    )

    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    return conversation


@router.patch("/{conversation_id}", response_model=ConversationSummary)
async def update_conversation(
    conversation_id: UUID,
    conversation_in: ConversationUpdate,
    db: DbSession,
    current_user: CurrentUserRequired,
    org_id: CurrentOrgId,
):
    """Update conversation (title, status)."""
    service = ConversationService(db)

    # Check ownership
    conversation = await service.get_conversation(conversation_id, UUID(org_id))
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    updated = await service.update_conversation(
        conversation_id=conversation_id,
        organization_id=UUID(org_id),
        update_data=conversation_in,
    )
    return updated


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    db: DbSession,
    current_user: CurrentUserRequired,
    org_id: CurrentOrgId,
):
    """Delete conversation (soft delete)."""
    service = ConversationService(db)

    # Check ownership
    conversation = await service.get_conversation(conversation_id, UUID(org_id))
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    await service.delete_conversation(conversation_id, UUID(org_id))
    return None
