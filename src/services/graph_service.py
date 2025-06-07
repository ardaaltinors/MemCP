import uuid
import asyncio
from typing import List, Dict, Set, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

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
        Calculate semantic relationships between memories using Qdrant.
        
        For each memory, we find its most similar memories and create edges
        if the similarity is above the threshold.
        """
        edges = []
        processed_pairs: Set[Tuple[str, str]] = set()
        
        try:
            # Create a mapping of memory IDs to content for quick lookup
            memory_map = {str(memory.id): memory.content for memory in memories}
            memory_ids = list(memory_map.keys())
            
            # For each memory, find its semantic neighbors
            for memory in memories:
                memory_id = str(memory.id)
                
                # Search for similar memories using the memory's content
                similar_memories = await self.vector_store.search_memories(
                    query_text=memory.content,
                    user_id=user_id
                )
                
                # Create edges for memories above the similarity threshold
                for similar_memory in similar_memories:
                    similar_id = similar_memory["id"]
                    similarity_score = similar_memory["score"]
                    
                    # Skip self-connections
                    if similar_id == memory_id:
                        continue
                    
                    # Skip if similarity is below threshold
                    if similarity_score < threshold:
                        continue
                    
                    # Skip if we already processed this pair (avoid duplicates)
                    pair = tuple(sorted([memory_id, similar_id]))
                    if pair in processed_pairs:
                        continue
                    
                    # Verify the similar memory belongs to this user's memory set
                    if similar_id in memory_ids:
                        edge = GraphEdge(
                            source=memory_id,
                            target=similar_id,
                            type="semantic_similarity",
                            weight=round(similarity_score, 3)
                        )
                        edges.append(edge)
                        processed_pairs.add(pair)
                        
                        logger.debug(f"Created edge between {memory_id} and {similar_id} with weight {similarity_score}")
                
                # Add a small delay to prevent overwhelming Qdrant
                await asyncio.sleep(0.01)
                
        except Exception as e:
            logger.error(f"Error calculating semantic edges: {str(e)}")
            raise QdrantServiceError(
                message="Failed to calculate semantic relationships",
                operation="calculate_edges",
                collection_name=self.vector_store.collection_name,
                original_exception=e
            )
        
        return edges
    
    async def close(self):
        """Clean up resources."""
        await self.vector_store.close() 