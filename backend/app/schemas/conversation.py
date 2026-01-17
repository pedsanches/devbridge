"""Conversation Schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.conversation import ConversationStatus, MessageRole


# --- Message Schemas ---
class MessageBase(BaseModel):
    """Base schema for chat messages."""

    role: MessageRole
    content: str


class MessageCreate(MessageBase):
    """Schema for creating a new message."""

    pass


class MessageResponse(MessageBase):
    """Schema for message response."""

    id: UUID
    conversation_id: UUID
    tokens_used: int | None = None
    message_metadata: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Conversation Schemas ---
class ConversationBase(BaseModel):
    """Base schema for conversations."""

    title: str | None = None


class ConversationCreate(ConversationBase):
    """Schema for creating a new conversation."""

    # First message to start the conversation
    message: str | None = None


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation."""

    title: str | None = None
    status: ConversationStatus | None = None
    # Context fields can also be updated
    team_id: UUID | None = None
    persona: str | None = None
    days: int | None = None
    repositories: list[str] | None = None


class ConversationSummary(BaseModel):
    """Schema for conversation list (without messages)."""

    id: UUID
    title: str | None = None
    status: ConversationStatus
    message_count: int
    preview: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationDetail(ConversationSummary):
    """Schema for conversation detail (with messages)."""

    summary: str | None = None
    messages: list[MessageResponse] = Field(default_factory=list)
    # Context fields
    team_id: UUID | None = None
    persona: str | None = None
    days: int | None = None
    repositories: list[str] | None = None


class ConversationsListResponse(BaseModel):
    """Schema for paginated conversation list."""

    conversations: list[ConversationSummary]
    total: int
    has_more: bool


# --- Chat Input Schema (for sending messages) ---
class SendMessageRequest(BaseModel):
    """Schema for sending a message in a conversation."""

    message: str
    persona: str | None = "technical"  # executive, product, technical
