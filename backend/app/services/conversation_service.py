"""Conversation Service.

Handles CRUD operations for conversations and messages.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import ChatMessage, Conversation, ConversationStatus, MessageRole
from app.schemas.conversation import (
    ConversationsListResponse,
    ConversationSummary,
    ConversationUpdate,
)


class ConversationService:
    """Service for managing conversations and messages."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_conversation(
        self,
        user_id: UUID,
        organization_id: UUID,
        title: str | None = None,
        # Context fields
        team_id: UUID | None = None,
        persona: str | None = None,
        days: int | None = None,
        repositories: list[str] | None = None,
    ) -> Conversation:
        """Create a new conversation with optional context settings."""
        conversation = Conversation(
            user_id=user_id,
            organization_id=organization_id,
            title=title,
            status=ConversationStatus.ACTIVE,
            message_count=0,
            # Context fields
            team_id=team_id,
            persona=persona,
            days=days,
            repositories=repositories,
        )
        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)
        return conversation

    async def get_conversation(
        self,
        conversation_id: UUID,
        organization_id: UUID,
        include_messages: bool = False,
    ) -> Conversation | None:
        """Get a conversation by ID."""
        query = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.organization_id == organization_id,
        )

        if include_messages:
            query = query.options(selectinload(Conversation.messages))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_conversations(
        self,
        user_id: UUID,
        organization_id: UUID,
        limit: int = 20,
        offset: int = 0,
        status: ConversationStatus | None = None,
    ) -> ConversationsListResponse:
        """List conversations for a user."""
        query = select(Conversation).where(
            Conversation.user_id == user_id,
            Conversation.organization_id == organization_id,
        )

        if status:
            query = query.where(Conversation.status == status)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = query.order_by(Conversation.updated_at.desc()).offset(offset).limit(limit + 1)
        result = await self.db.execute(query)
        conversations = list(result.scalars().all())

        has_more = len(conversations) > limit
        if has_more:
            conversations = conversations[:limit]

        summaries = []
        for c in conversations:
            summary = ConversationSummary.model_validate(c)

            # Fetch last message for preview
            last_msg_query = (
                select(ChatMessage)
                .where(ChatMessage.conversation_id == c.id)
                .order_by(ChatMessage.created_at.desc())
                .limit(1)
            )
            last_msg_result = await self.db.execute(last_msg_query)
            last_msg = last_msg_result.scalar_one_or_none()

            if last_msg:
                # Truncate content for preview (limit to 60 chars)
                content = last_msg.content.replace("\n", " ")
                preview_text = content[:60] + "..." if len(content) > 60 else content
                summary.preview = preview_text

            summaries.append(summary)

        return ConversationsListResponse(
            conversations=summaries,
            total=total,
            has_more=has_more,
        )

    async def update_conversation(
        self,
        conversation_id: UUID,
        organization_id: UUID,
        update_data: ConversationUpdate,
    ) -> Conversation | None:
        """Update a conversation."""
        conversation = await self.get_conversation(conversation_id, organization_id)
        if not conversation:
            return None

        if update_data.title is not None:
            conversation.title = update_data.title
        if update_data.status is not None:
            conversation.status = update_data.status
        # Context fields
        if update_data.team_id is not None:
            conversation.team_id = update_data.team_id
        if update_data.persona is not None:
            conversation.persona = update_data.persona
        if update_data.days is not None:
            conversation.days = update_data.days
        if update_data.repositories is not None:
            conversation.repositories = update_data.repositories

        conversation.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(conversation)
        return conversation

    async def delete_conversation(
        self,
        conversation_id: UUID,
        organization_id: UUID,
    ) -> bool:
        """Delete a conversation (soft delete by archiving)."""
        conversation = await self.get_conversation(conversation_id, organization_id)
        if not conversation:
            return False

        conversation.status = ConversationStatus.ARCHIVED
        conversation.updated_at = datetime.utcnow()
        await self.db.commit()
        return True

    async def add_message(
        self,
        conversation_id: UUID,
        role: MessageRole,
        content: str,
        tokens_used: int | None = None,
        message_metadata: dict | None = None,
    ) -> ChatMessage:
        """Add a message to a conversation."""
        message = ChatMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            tokens_used=tokens_used,
            message_metadata=message_metadata,
        )
        self.db.add(message)

        # Update conversation message count and timestamp
        query = select(Conversation).where(Conversation.id == conversation_id)
        result = await self.db.execute(query)
        conversation = result.scalar_one_or_none()
        if conversation:
            conversation.message_count += 1
            conversation.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def get_conversation_messages(
        self,
        conversation_id: UUID,
        limit: int = 50,
        before_id: UUID | None = None,
    ) -> list[ChatMessage]:
        """Get messages for a conversation."""
        query = select(ChatMessage).where(ChatMessage.conversation_id == conversation_id)

        if before_id:
            query = query.where(ChatMessage.id < before_id)

        query = query.order_by(ChatMessage.created_at.desc()).limit(limit)
        result = await self.db.execute(query)
        messages = list(result.scalars().all())

        # Return in chronological order
        return list(reversed(messages))

    async def generate_title(self, first_message: str) -> str:
        """Generate a title from the first message using AI."""
        # Avoid circular import
        from app.services.ai_service import ai_service

        return await ai_service.generate_title(first_message)
