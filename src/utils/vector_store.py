import os
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, TYPE_CHECKING

from qdrant_client import AsyncQdrantClient
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

if TYPE_CHECKING:
    from fastmcp import Context


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

    async def delete_memory(self, memory_id: str, user_id: uuid.UUID) -> None:
        """Delete a memory from the vector database."""
        try:
            # First verify the memory belongs to the user before deletion
            points = await self.client.retrieve(
                collection_name=self.collection_name,
                ids=[memory_id],
                with_payload=True
            )
            
            if not points:
                raise QdrantServiceError(
                    message="Memory not found in vector database",
                    operation="delete",
                    collection_name=self.collection_name
                )
            
            # Check if the memory belongs to the user
            if points[0].payload.get("user_id") == str(user_id):
                await self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=[memory_id],
                    wait=True  # Ensure the operation completes
                )
            else:
                raise QdrantServiceError(
                    message="User can only delete their own memories",
                    operation="delete",
                    collection_name=self.collection_name
                )
        except Exception as e:
            if isinstance(e, QdrantServiceError):
                raise
            raise QdrantServiceError(
                message="Failed to delete memory from vector database",
                operation="delete",
                collection_name=self.collection_name,
                original_exception=e
            )

    async def delete_all_user_memories(self, user_id: uuid.UUID) -> int:
        """Delete all memories for a user from the vector database. Returns count of deleted memories."""
        try:
            # Use filter to delete all points for the user
            user_filter = Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=str(user_id))
                    )
                ]
            )
            
            # Get count before deletion for return value
            search_result = await self.client.search(
                collection_name=self.collection_name,
                query_vector=[0.0] * self.embedding_service.get_embedding_dimension(),  # Dummy vector
                query_filter=user_filter,
                limit=10000,  # Large limit to get all memories
                with_payload=False,
                with_vectors=False
            )
            
            count = len(search_result)
            
            if count > 0:
                # Delete all points for the user
                await self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=user_filter,
                    wait=True  # Ensure the operation completes
                )
            
            return count
        except Exception as e:
            raise QdrantServiceError(
                message="Failed to delete all user memories from vector database",
                operation="bulk_delete",
                collection_name=self.collection_name,
                original_exception=e
            )

    async def store_memories_batch(
        self,
        memories: List[Dict[str, any]],
        user_id: uuid.UUID,
        ctx: Optional['Context'] = None
    ) -> int:
        """
        Store multiple memories in batch with progress reporting.
        
        Args:
            memories: List of dicts with 'id', 'content', and optional 'tags'
            user_id: User UUID
            ctx: Optional FastMCP context for progress reporting
            
        Returns:
            Number of successfully stored memories
        """
        total = len(memories)
        if ctx:
            await ctx.info(f"Starting batch vector storage for {total} memories")
        
        # Process embeddings in batches
        batch_size = 10
        points = []
        
        for i in range(0, total, batch_size):
            if ctx:
                await ctx.report_progress(progress=i, total=total)
            
            batch = memories[i:i + batch_size]
            
            # Generate embeddings for batch
            try:
                contents = [m['content'] for m in batch]
                embeddings = await self.embedding_service.generate_embeddings(contents)
                
                # Create points for batch
                for j, (memory, embedding) in enumerate(zip(batch, embeddings)):
                    point = PointStruct(
                        id=memory['id'],
                        vector=embedding,
                        payload={
                            "content": memory['content'],
                            "user_id": str(user_id),
                            "tags": memory.get('tags', []),
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                    )
                    points.append(point)
                    
            except Exception as e:
                if ctx:
                    await ctx.warning(f"Failed to process batch {i//batch_size + 1}: {str(e)}")
        
        # Upload all points
        if points:
            try:
                await self.client.upsert(
                    collection_name=self.collection_name,
                    points=points,
                    wait=True
                )
                if ctx:
                    await ctx.report_progress(progress=total, total=total)
                    await ctx.info(f"Successfully stored {len(points)} vectors")
            except Exception as e:
                raise QdrantServiceError(
                    message="Failed to upload vectors to Qdrant",
                    operation="batch_upsert",
                    collection_name=self.collection_name,
                    original_exception=e
                )
        
        return len(points)

    async def close(self):
        """Close the async client connection."""
        try:
            await self.client.close()
        except Exception as e:
            # Log the error but don't raise as this is cleanup
            pass 