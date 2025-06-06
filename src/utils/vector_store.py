import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct, Filter, FieldCondition, MatchValue

from src.exceptions import QdrantServiceError, MemorySearchError
from src.utils.embedding import EmbeddingService


class VectorStore:
    """Service for managing vector storage and retrieval in Qdrant."""
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        collection_name: str = None,
        score_threshold: float = None,
        upper_score_threshold: float = None
    ):
        # Read configuration from environment variables with fallbacks
        self.host = host or os.getenv("QDRANT_HOST", "localhost")
        self.port = port or int(os.getenv("QDRANT_PORT", "6333"))
        self.collection_name = collection_name or os.getenv("QDRANT_COLLECTION_NAME", "memories")
        
        # Convert string environment variables to floats with fallbacks
        self.score_threshold = score_threshold if score_threshold is not None else float(os.getenv("MEMORY_SCORE_THRESHOLD", "0.40"))
        self.upper_score_threshold = upper_score_threshold if upper_score_threshold is not None else float(os.getenv("MEMORY_UPPER_SCORE_THRESHOLD", "0.98"))
        
        # Initialize services
        self.embedding_service = EmbeddingService()
        
        # Initialize Qdrant client
        try:
            self.client = QdrantClient(host=self.host, port=self.port)
        except Exception as e:
            raise QdrantServiceError(
                message="Failed to connect to Qdrant database",
                operation="initialize_client",
                collection_name=self.collection_name,
                original_exception=e
            )
        
        # Ensure the collection exists in Qdrant
        self._ensure_collection_exists()

    def _ensure_collection_exists(self):
        """Create the collection if it doesn't exist."""
        existing = [c.name for c in self.client.get_collections().collections]
        if self.collection_name not in existing:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_service.get_embedding_dimension(),
                    distance=Distance.COSINE
                )
            )

    def store_memory(
        self, 
        memory_id: str, 
        content: str, 
        user_id: uuid.UUID, 
        tags: Optional[list[str]] = None
    ) -> None:
        """Store a memory in the vector database."""
        try:
            vector = self.embedding_service.generate_embedding(content)
            payload = {
                "content": content,
                "tags": tags or [],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user_id": str(user_id)
            }
            point = PointStruct(
                id=memory_id,
                vector=vector,
                payload=payload
            )
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
        except Exception as e:
            raise QdrantServiceError(
                message="Failed to store memory in vector database",
                operation="upsert",
                collection_name=self.collection_name,
                original_exception=e
            )

    def search_memories(self, query_text: str, user_id: uuid.UUID) -> list[dict]:
        """Search for memories related to the query text, filtered by user."""
        query_embedding = self.embedding_service.generate_embedding(query_text)

        # Create filter to only search memories for the current user
        user_filter = Filter(
            must=[
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=str(user_id))
                )
            ]
        )

        try:
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=user_filter,
                score_threshold=self.score_threshold,
                limit=25,
                with_payload=True
            )
        except Exception as e:
            raise MemorySearchError(
                message="Failed to search memories in vector database",
                query_text=query_text,
                user_id=str(user_id),
                search_type="semantic_search",
                original_exception=e
            )

        results = []
        for hit in search_result:
            # Apply upper score threshold if provided
            if self.upper_score_threshold is not None and hit.score > self.upper_score_threshold:
                continue

            payload = hit.payload or {}
            results.append({
                "id": hit.id,
                "content": payload.get("content"),
                "tags": payload.get("tags"),
                "score": hit.score,
                "timestamp": payload.get("timestamp"),
                "user_id": payload.get("user_id")
            })
        return results 