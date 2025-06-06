import uuid
from typing import Optional

from src.core.context import get_current_user_id
from src.db.database import get_db
from src.db.models import Memory
from src.exceptions import UserContextError, DatabaseOperationError
from src.utils.vector_store import VectorStore
from src.utils.profile_processor import ProfileProcessor

class MemoryManager:
    """Main interface for memory operations."""
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        collection_name: str = None,
        embedding_model: str = None,
        score_threshold: float = None,
        upper_score_threshold: float = None
    ):
        # Initialize vector store with all configuration
        self.vector_store = VectorStore(
            host=host,
            port=port,
            collection_name=collection_name,
            score_threshold=score_threshold,
            upper_score_threshold=upper_score_threshold
        )

    def store(self, content: str, tags: Optional[list[str]] = None) -> str:
        """Stores a new memory entry in both vector and relational databases."""
        # Get current user context
        user_id = get_current_user_id()
        if user_id is None:
            raise UserContextError(
                message="User context is required for memory storage",
                operation="store_memory"
            )
        
        # Generate a UUID for this memory
        memory_id = str(uuid.uuid4())
        
        # Store in vector database
        self.vector_store.store_memory(memory_id, content, user_id, tags)
        
        # Store in relational database
        try:
            db = get_db()
            db_memory = Memory(
                id=uuid.UUID(memory_id),
                content=content,
                tags=tags or [],
                user_id=user_id
            )
            db.add(db_memory)
            db.commit()
        except Exception as e:
            raise DatabaseOperationError(
                message="Failed to store memory in relational database",
                operation="insert",
                table_name="memories",
                original_exception=e
            )
        
        return f"Memory stored with ID: {memory_id} for user: {user_id}"

    def search_related(self, query_text: str) -> list[dict]:
        """Performs a semantic search for memories related to the query text."""
        # Get current user context
        user_id = get_current_user_id()
        if user_id is None:
            raise UserContextError(
                message="User context is required for memory search",
                operation="search_memories"
            )
        
        return self.vector_store.search_memories(query_text, user_id)

    def process_context(self, prompt: str, tags: Optional[list[str]] = None) -> str:
        """Record the user's message and return the synthesized profile."""
        user_id = get_current_user_id()
        if user_id is None:
            raise UserContextError(
                message="User context is required for profile processing",
                operation="process_context"
            )

        return ProfileProcessor.record_message_and_get_profile(user_id, prompt)