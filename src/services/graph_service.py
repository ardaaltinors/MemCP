import uuid
import asyncio
from typing import List, Dict, Set, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from src.crud import crud_memory
from src.utils.vector_store import VectorStore
from src.schemas.graph import GraphNode, GraphEdge, MemoryGraphResponse
from src.exceptions import MemorySearchError, QdrantServiceError
import logging

logger = logging.getLogger(__name__)


class GraphService:
    """Service for generating memory graphs with semantic relationships."""
    
    def __init__(self, similarity_threshold: float = 0.7):
        self.similarity_threshold = similarity_threshold
        self.vector_store = VectorStore()
    
    async def generate_memory_graph(
        self, 
        user_id: uuid.UUID, 
        db: AsyncSession,
        similarity_threshold: float = None
    ) -> MemoryGraphResponse:
        """
        Generate a graph of user's memories with semantic connections.
        
        Args:
            user_id: The user's UUID
            db: Database session
            similarity_threshold: Minimum similarity score for creating edges
        
        Returns:
            MemoryGraphResponse with nodes (memories) and edges (relationships)
        """
        threshold = similarity_threshold or self.similarity_threshold
        
        try:
            # Step 1: Fetch all user memories from PostgreSQL
            memories = await crud_memory.get_user_memories(db=db, user_id=user_id)
            
            if not memories:
                return MemoryGraphResponse(
                    nodes=[],
                    edges=[],
                    total_nodes=0,
                    total_edges=0
                )
            
            # Step 2: Convert memories to graph nodes
            nodes = self._create_nodes_from_memories(memories)
            
            # Step 3: Calculate semantic relationships using Qdrant
            edges = await self._calculate_semantic_edges(memories, user_id, threshold)
            
            return MemoryGraphResponse(
                nodes=nodes,
                edges=edges,
                total_nodes=len(nodes),
                total_edges=len(edges)
            )
            
        except Exception as e:
            logger.error(f"Error generating memory graph for user {user_id}: {str(e)}")
            raise MemorySearchError(
                message="Failed to generate memory graph",
                user_id=str(user_id),
                search_type="graph_generation",
                original_exception=e
            )
    
    def _create_nodes_from_memories(self, memories: List) -> List[GraphNode]:
        """Convert database memory records to graph nodes."""
        nodes = []
        
        for memory in memories:
            # Create a brief label from the content (first 50 chars)
            label = memory.content[:50] + "..." if len(memory.content) > 50 else memory.content
            
            node = GraphNode(
                id=str(memory.id),
                label=label,
                content=memory.content,
                created_at=memory.created_at,
                type="memory",
                tags=memory.tags or []
            )
            nodes.append(node)
        
        return nodes
    
    async def _calculate_semantic_edges(
        self, 
        memories: List, 
        user_id: uuid.UUID, 
        threshold: float
    ) -> List[GraphEdge]:
        """
        Calculates semantic relationships using a highly efficient, vectorized approach.
        """
        if len(memories) < 2:
            return []

        edges = []
        memory_ids = [str(m.id) for m in memories]

        try:
            # Step 1: Fetch all vectors in one batch
            vectors_dict = await self.vector_store.retrieve_vectors(memory_ids, user_id)
            
            # Align vectors with memory_ids, handling cases where a vector might be missing
            ordered_vectors = [vectors_dict.get(mid) for mid in memory_ids]
            
            # Filter out memories that didn't have a vector
            valid_indices = [i for i, v in enumerate(ordered_vectors) if v is not None]
            if len(valid_indices) < 2:
                return []
                
            valid_memory_ids = [memory_ids[i] for i in valid_indices]
            vector_matrix = np.array([ordered_vectors[i] for i in valid_indices])

            # Step 2: Calculate all-pairs cosine similarity in a single operation
            similarity_matrix = cosine_similarity(vector_matrix)

            # Step 3: Create edges from the upper triangle of the similarity matrix
            for i in range(len(valid_memory_ids)):
                for j in range(i + 1, len(valid_memory_ids)):
                    similarity_score = similarity_matrix[i, j]

                    if similarity_score >= threshold:
                        edge = GraphEdge(
                            source=valid_memory_ids[i],
                            target=valid_memory_ids[j],
                            type="semantic_similarity",
                            weight=round(float(similarity_score), 3)
                        )
                        edges.append(edge)
                        
        except Exception as e:
            logger.error(f"Error calculating semantic edges for user {user_id}: {str(e)}")
            # Re-raise as a service-specific exception
            raise QdrantServiceError(
                message="Failed to calculate semantic relationships",
                operation="calculate_edges_vectorized",
                collection_name=self.vector_store.collection_name,
                original_exception=e,
            )
        
        return edges
    
    async def close(self):
        """Clean up resources."""
        await self.vector_store.close() 