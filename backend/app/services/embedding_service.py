"""
Embedding Service.

Generates embeddings using OpenAI for semantic search.
"""

import logging
from typing import cast

from openai import OpenAI

from app.core.config import settings
from app.services.privacy_service import PrivacyServiceError, privacy_service

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings."""

    def __init__(self, api_key: str | None = None):
        """Initialize with OpenAI API key."""
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        self.model = "text-embedding-3-small"

    def generate(self, text: str) -> list[float] | None:
        """
        Generate embedding for a text string.

        Args:
            text: Text to embed (max ~8000 tokens).

        Returns:
            List of floats representing the embedding vector, or None if failed.
        """
        if not self.client:
            return None

        # Truncate text if too long
        text = text[:8000] if len(text) > 8000 else text

        try:
            sanitized_text = privacy_service.sanitize(text)
        except PrivacyServiceError as exc:
            logger.error("PII sanitization failed: %s", exc)
            return None

        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=sanitized_text,
            )
            return cast(list[float], response.data[0].embedding)
        except Exception:
            return None

    def generate_batch(self, texts: list[str]) -> list[list[float] | None]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors (or None for failed items).
        """
        if not self.client:
            return [None] * len(texts)

        # Truncate each text
        texts = [t[:8000] if len(t) > 8000 else t for t in texts]

        try:
            sanitized_texts = [privacy_service.sanitize(text) for text in texts]
        except PrivacyServiceError as exc:
            logger.error("PII sanitization failed: %s", exc)
            return [None] * len(texts)

        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=sanitized_texts,
            )
            return [cast(list[float], item.embedding) for item in response.data]
        except Exception:
            return [None] * len(texts)


# Singleton instance
embedding_service = EmbeddingService()
