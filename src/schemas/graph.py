from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel


class GraphNode(BaseModel):
    """Represents a memory node in the graph."""
    id: str
    label: str
    content: str
    created_at: datetime
    type: str = "memory"
    tags: Optional[List[str]] = None


class GraphEdge(BaseModel):
    """Represents a relationship between two memories."""
    source: str
    target: str
    type: str = "semantic_similarity"
    weight: float


class MemoryGraphResponse(BaseModel):
    """Response schema for the memory graph endpoint."""
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    total_nodes: int
    total_edges: int 