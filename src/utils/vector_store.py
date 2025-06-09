import os
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from qdrant_client import AsyncQdrantClient, QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from src.exceptions import QdrantServiceError, MemorySearchError
from src.utils.embedding import EmbeddingService


class VectorStore:
    """Service for managing vector storage and retrieval in Qdrant (Async version)."""
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        collection_name: str = None,
        score_threshold: float = None,
        upper_score_threshold: float = None
    ):
        self.host = host or os.getenv("QDRANT_HOST", "localhost")
        self.port = port or int(os.getenv("QDRANT_PORT", "6333"))
        self.collection_name = collection_name or os.getenv("QDRANT_COLLECTION_NAME", "memories")
        
        self.score_threshold = score_threshold if score_threshold is not None else float(os.getenv("MEMORY_SCORE_THRESHOLD", "0.40"))
        self.upper_score_threshold = upper_score_threshold if upper_score_threshold is not None else float(os.getenv("MEMORY_UPPER_SCORE_THRESHOLD", "0.98"))
        
        self.timeout = float(os.getenv("QDRANT_TIMEOUT", "60"))
        self.prefer_grpc = os.getenv("QDRANT_PREFER_GRPC", "false").lower() == "true"
        
        # Initialize services
        self.embedding_service = EmbeddingService()
        
        # Initialize Qdrant client
        try:
            self.client = AsyncQdrantClient(
                host=self.host, 
                port=self.port,
                timeout=self.timeout,
                prefer_grpc=self.prefer_grpc
            )
        except Exception as e:
            raise QdrantServiceError(
                message="Failed to connect to Qdrant database",
                operation="initialize_client",
                collection_name=self.collection_name,
                original_exception=e
            )

    async def _ensure_collection_exists(self):
        """Create the collection if it doesn't exist."""
        try:
            collection_exists = await self.client.collection_exists(self.collection_name)
            if not collection_exists:
                await self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_service.get_embedding_dimension(),
                        distance=Distance.COSINE
                    )
                )
        except Exception as e:
            raise QdrantServiceError(
                message="Failed to create collection in Qdrant database",
                operation="create_collection",
                collection_name=self.collection_name,
                original_exception=e
            )

    async def store_memory(
        self, 
        memory_id: str, 
        content: str, 
        user_id: uuid.UUID, 
        tags: Optional[list[str]] = None
    ) -> None:
        """Store a memory in the vector database."""
        try:
            # Ensure collection exists
            await self._ensure_collection_exists()
            
            vector = await self.embedding_service.generate_embedding(content)
            
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
            
            await self.client.upsert(
                collection_name=self.collection_name,
                points=[point],
                wait=True  # Ensure the operation completes
            )
        except Exception as e:
            raise QdrantServiceError(
                message="Failed to store memory in vector database",
                operation="upsert",
                collection_name=self.collection_name,
                original_exception=e
            )

    async def search_memories(self, query_text: str, user_id: uuid.UUID) -> list[dict]:
        """Search for memories related to the query text, filtered by user."""
        try:
            await self._ensure_collection_exists()
            
            # Use async embedding generation for better concurrency
            query_embedding = await self.embedding_service.generate_embedding(query_text)

            # Create filter to only search memories for the current user
            user_filter = Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=str(user_id))
                    )
                ]
            )

            # Use async Qdrant search for better concurrency
            search_result = await self.client.search(
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

    async def retrieve_vectors(
        self, memory_ids: List[str], user_id: uuid.UUID
    ) -> Dict[str, List[float]]:
        """Retrieve vectors for a list of memory IDs, ensuring they belong to the user."""
        if not memory_ids:
            return {}

        try:
            points = await self.client.retrieve(
                collection_name=self.collection_name,
                ids=memory_ids,
                with_vectors=True,
            )

            # Filter points to ensure they belong to the correct user and return a dict
            user_id_str = str(user_id)
            return {
                str(point.id): point.vector
                for point in points
                if point.payload and point.payload.get("user_id") == user_id_str
            }
        except Exception as e:
            raise QdrantServiceError(
                message="Failed to retrieve vectors from vector database",
                operation="retrieve_vectors",
                collection_name=self.collection_name,
                original_exception=e,
            )

    async def close(self):
        """Close the async client connection."""
        try:
            await self.client.close()
        except Exception as e:
            # Log the error but don't raise as this is cleanup
            pass


class SyncVectorStore:
    """Synchronous service for managing vector storage and retrieval in Qdrant.
    
    This is optimized for use in Celery tasks and other synchronous contexts
    where creating async event loops would be inefficient.
    """
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        collection_name: str = None,
        score_threshold: float = None,
        upper_score_threshold: float = None
    ):
        self.host = host or os.getenv("QDRANT_HOST", "localhost")
        self.port = port or int(os.getenv("QDRANT_PORT", "6333"))
        self.collection_name = collection_name or os.getenv("QDRANT_COLLECTION_NAME", "memories")
        
        self.score_threshold = score_threshold if score_threshold is not None else float(os.getenv("MEMORY_SCORE_THRESHOLD", "0.40"))
        self.upper_score_threshold = upper_score_threshold if upper_score_threshold is not None else float(os.getenv("MEMORY_UPPER_SCORE_THRESHOLD", "0.98"))
        
        self.timeout = float(os.getenv("QDRANT_TIMEOUT", "60"))
        self.prefer_grpc = os.getenv("QDRANT_PREFER_GRPC", "false").lower() == "true"
        
        # Initialize services
        self.embedding_service = EmbeddingService()
        
        # Initialize synchronous Qdrant client
        try:
            self.client = QdrantClient(
                host=self.host, 
                port=self.port,
                timeout=self.timeout,
                prefer_grpc=self.prefer_grpc
            )
        except Exception as e:
            raise QdrantServiceError(
                message="Failed to connect to Qdrant database",
                operation="initialize_sync_client",
                collection_name=self.collection_name,
                original_exception=e
            )

    def _ensure_collection_exists(self):
        """Create the collection if it doesn't exist (sync version)."""
        try:
            collection_exists = self.client.collection_exists(self.collection_name)
            if not collection_exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_service.get_embedding_dimension(),
                        distance=Distance.COSINE
                    )
                )
        except Exception as e:
            raise QdrantServiceError(
                message="Failed to create collection in Qdrant database",
                operation="create_collection_sync",
                collection_name=self.collection_name,
                original_exception=e
            )

    def store_memory(
        self, 
        memory_id: str, 
        content: str, 
        user_id: uuid.UUID, 
        tags: Optional[list[str]] = None
    ) -> None:
        """Store a memory in the vector database (sync version)."""
        try:
            # Ensure collection exists
            self._ensure_collection_exists()
            
            # Generate embedding synchronously
            vector = self.embedding_service.generate_embedding_sync(content)
            
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
                points=[point],
                wait=True  # Ensure the operation completes
            )
        except Exception as e:
            raise QdrantServiceError(
                message="Failed to store memory in vector database",
                operation="upsert_sync",
                collection_name=self.collection_name,
                original_exception=e
            )

    def store_memories_batch(
        self,
        memory_data: List[Dict[str, Any]],
        user_id: uuid.UUID
    ) -> None:
        """Store multiple memories in a single batch operation for better performance.
        
        Args:
            memory_data: List of dicts with keys: memory_id, content, tags
            user_id: User ID
        """
        if not memory_data:
            return
            
        try:
            # Ensure collection exists
            self._ensure_collection_exists()
            
            points = []
            for data in memory_data:
                # Generate embedding synchronously
                vector = self.embedding_service.generate_embedding_sync(data["content"])
                
                payload = {
                    "content": data["content"],
                    "tags": data.get("tags", []),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "user_id": str(user_id)
                }
                
                point = PointStruct(
                    id=data["memory_id"],
                    vector=vector,
                    payload=payload
                )
                points.append(point)
            
            # Batch upsert for better performance
            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
                wait=True
            )
        except Exception as e:
            raise QdrantServiceError(
                message="Failed to store memories batch in vector database",
                operation="batch_upsert_sync",
                collection_name=self.collection_name,
                original_exception=e
            )

    def search_memories(self, query_text: str, user_id: uuid.UUID) -> list[dict]:
        """Search for memories related to the query text, filtered by user (sync version)."""
        try:
            self._ensure_collection_exists()
            
            # Generate embedding synchronously
            query_embedding = self.embedding_service.generate_embedding_sync(query_text)

            # Create filter to only search memories for the current user
            user_filter = Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=str(user_id))
                    )
                ]
            )

            # Use sync Qdrant search
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
                search_type="semantic_search_sync",
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

    def close(self):
        """Close the sync client connection."""
        try:
            self.client.close()
        except Exception as e:
            # Log the error but don't raise as this is cleanup
            pass 