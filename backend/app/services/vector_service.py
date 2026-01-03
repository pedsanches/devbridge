"""
Vector Service.

Manages vector storage and search using Qdrant.
"""

from typing import Any
from uuid import UUID

from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.core.config import settings
from app.services.embedding_service import embedding_service


class VectorService:
    """Service for vector storage and semantic search with Qdrant."""

    VECTOR_SIZE = 1536  # OpenAI text-embedding-3-small dimension

    def __init__(self, url: str | None = None, collection: str | None = None):
        """Initialize Qdrant client."""
        self.url = url or settings.QDRANT_URL
        self.collection = collection or settings.QDRANT_COLLECTION
        self.client = QdrantClient(url=self.url)
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Create collection if it doesn't exist."""
        try:
            self.client.get_collection(self.collection)
        except Exception:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=models.VectorParams(
                    size=self.VECTOR_SIZE,
                    distance=models.Distance.COSINE,
                ),
            )

    def index_activity(
        self,
        activity_id: UUID,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """
        Index an activity in the vector database.

        Args:
            activity_id: UUID of the activity.
            content: Text content to embed and index.
            metadata: Additional metadata to store.

        Returns:
            True if indexed successfully.
        """
        embedding = embedding_service.generate(content)
        if not embedding:
            return False

        point = models.PointStruct(
            id=str(activity_id),
            vector=embedding,
            payload={
                "activity_id": str(activity_id),
                "content_preview": content[:500],
                **(metadata or {}),
            },
        )

        self.client.upsert(
            collection_name=self.collection,
            points=[point],
        )
        return True

    def search(
        self,
        query: str,
        limit: int = 10,
        filter_conditions: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search for similar activities.

        Args:
            query: Search query text.
            limit: Maximum results to return.
            filter_conditions: Optional Qdrant filter conditions.

        Returns:
            List of matching activity data with scores.
        """
        embedding = embedding_service.generate(query)
        if not embedding:
            return []

        query_filter = None
        if filter_conditions:
            conditions = []
            for key, value in filter_conditions.items():
                conditions.append(
                    models.FieldCondition(
                        key=key,
                        match=models.MatchValue(value=value),
                    )
                )
            query_filter = models.Filter(must=conditions)

        results = self.client.search(
            collection_name=self.collection,
            query_vector=embedding,
            limit=limit,
            query_filter=query_filter,
        )

        return [
            {
                "activity_id": hit.payload.get("activity_id") if hit.payload else None,
                "content_preview": hit.payload.get("content_preview") if hit.payload else None,
                "score": hit.score,
                "metadata": hit.payload,
            }
            for hit in results
        ]

    def delete_activity(self, activity_id: UUID) -> bool:
        """Delete an activity from the vector database."""
        try:
            self.client.delete(
                collection_name=self.collection,
                points_selector=models.PointIdsList(
                    points=[str(activity_id)],
                ),
            )
            return True
        except Exception:
            return False


# Singleton instance
vector_service = VectorService()
