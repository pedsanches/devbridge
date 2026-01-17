"""
Chat Schemas.

Pydantic schemas for chat request/response.
Implements BR-011 (structured output) and BR-030 (persona-based responses).
"""

from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class Persona(str, Enum):
    """User persona for adapting AI responses (BR-030)."""

    EXECUTIVE = "executive"  # CEO/C-Level: Focus on outcomes, ROI, strategic impact
    TECHNICAL = "technical"  # CTO/Tech Lead: Technical details, architecture, code quality
    PRODUCT = "product"  # PM: Features delivered, roadmap progress, blockers


class ChatRequest(BaseModel):
    """Schema for chat request."""

    message: str = Field(..., description="User's question or message")
    repository: str | list[str] | None = Field(None, description="Filter by repository name(s)")
    author: str | None = Field(None, description="Filter by author")
    persona: Persona = Field(
        default=Persona.PRODUCT, description="User persona for response adaptation"
    )
    days: int | None = Field(30, description="Filter activities by last N days (default 30)")
    team_id: UUID | None = Field(None, alias="teamId", description="Team ID for context")
    conversation_id: UUID | None = Field(
        None,
        alias="conversationId",
        description="ID of the active conversation (optional)",
    )

    model_config = {"populate_by_name": True}


class SourceItem(BaseModel):
    """A source activity used to generate the response."""

    title: str = Field(..., description="Activity title")
    repository: str = Field(..., description="Repository name")
    type: str = Field(..., description="Activity type (commit, pr, issue)")
    author: str | None = Field(None, description="Activity author")
    url: str | None = Field(None, description="Link to the activity")


class ChatMetadata(BaseModel):
    """Structured metadata about the chat response (BR-011)."""

    activities_count: int = Field(..., description="Number of activities used as context")
    search_method: str = Field("sql", description="Method used: 'semantic' or 'sql'")
    confidence_score: float = Field(
        ge=0.0, le=1.0, default=0.8, description="AI confidence in response"
    )
    persona_used: Persona = Field(default=Persona.PRODUCT, description="Persona used for response")
    sources: list[SourceItem] = Field(
        default_factory=list, description="Top sources used to generate response"
    )


class ChatResponse(BaseModel):
    """Schema for chat response."""

    answer: str = Field(..., description="AI-generated answer")
    activities_count: int = Field(..., description="Number of activities used as context")
    filters: dict[str, str | int | None] = Field(
        default_factory=dict, description="Applied filters"
    )
    metadata: ChatMetadata | None = Field(None, description="Structured response metadata")
    conversation_id: UUID | None = Field(
        None, description="Conversation ID associated with this interaction"
    )


class StreamingChatResponse(BaseModel):
    """Schema for streaming chat response chunk."""

    chunk: str = Field(..., description="Response text chunk")
    done: bool = Field(False, description="Whether this is the final chunk")
