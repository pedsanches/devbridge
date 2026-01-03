"""
Embedding Service.

Generates embeddings using OpenAI for semantic search.
"""

from openai import OpenAI

from app.core.config import settings


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
            response = self.client.embeddings.create(
                model=self.model,
                input=text,
            )
            return response.data[0].embedding
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
            response = self.client.embeddings.create(
                model=self.model,
                input=texts,
            )
            return [item.embedding for item in response.data]
        except Exception:
            return [None] * len(texts)


# Singleton instance
embedding_service = EmbeddingService()
