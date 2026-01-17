"""
Conversation Models.

Stores chat conversations and messages for persistent chat history.
"""

import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ConversationStatus(str, enum.Enum):
    """Status of a conversation."""

    ACTIVE = "active"
    ARCHIVED = "archived"


class MessageRole(str, enum.Enum):
    """Role of a message sender."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Conversation(Base, UUIDMixin, TimestampMixin):
    """Conversation (chat thread) model.

    Represents a single chat session that can contain multiple messages.
    Multi-tenant: isolated by organization_id.
    """

    __tablename__ = "conversations"

    # Multi-tenancy
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Content
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)  # Compressed context

    # Status and metadata
    status: Mapped[ConversationStatus] = mapped_column(
        Enum(ConversationStatus), default=ConversationStatus.ACTIVE, nullable=False
    )
    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Context settings (persisted from conversation)
    team_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, index=True
    )
    persona: Mapped[str | None] = mapped_column(String(50), nullable=True)
    days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    repositories: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="conversations")
    user = relationship("User", back_populates="conversations")
    team = relationship("Team", foreign_keys=[team_id])
    messages = relationship(
        "ChatMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )


class ChatMessage(Base, UUIDMixin):
    """Chat message model.

    A single message in a conversation thread.
    """

    __tablename__ = "chat_messages"

    # Relationships
    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Content
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Analytics and metadata
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    message_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # message_metadata can contain: activity_ids, confidence_score, persona, search_method, etc.

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
