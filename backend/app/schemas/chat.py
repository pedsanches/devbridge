"""
Chat Schemas.

Pydantic schemas for chat request/response.
"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Schema for chat request."""

    message: str = Field(..., description="User's question or message")
    repository: str | None = Field(None, description="Filter by repository name")
    author: str | None = Field(None, description="Filter by author")


class ChatResponse(BaseModel):
    """Schema for chat response."""

    answer: str = Field(..., description="AI-generated answer")
    activities_count: int = Field(..., description="Number of activities used as context")
    filters: dict[str, str | int | None] = Field(
        default_factory=dict, description="Applied filters"
    )


class StreamingChatResponse(BaseModel):
    """Schema for streaming chat response chunk."""

    chunk: str = Field(..., description="Response text chunk")
    done: bool = Field(False, description="Whether this is the final chunk")
