import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.context import get_current_user_id
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

    async def store(self, content: str, db: AsyncSession, tags: Optional[list[str]] = None) -> str:
        """
        Stores a new memory entry in both vector and relational databases.
        
        Args:
            content: The content to store
            db: Database session (injected via FastAPI dependency)
            tags: Optional tags for the memory
        """
        # Get current user context
        user_id = get_current_user_id()
        if user_id is None:
            raise UserContextError(
                message="User context is required for memory storage",
                operation="store_memory"
            )
        
        # Generate a UUID for this memory
        memory_id = str(uuid.uuid4())
        
        # Store in vector database first
        await self.vector_store.store_memory(memory_id, content, user_id, tags)
        
        # Store in relational database
        try:
            db_memory = Memory(
                id=uuid.UUID(memory_id),
                content=content,
                tags=tags or [],
                user_id=user_id
            )
            db.add(db_memory)
            await db.flush()  # Use flush instead of commit as get_async_db handles commit
        except Exception as e:
            # If relational DB fails, we should ideally remove from vector DB too
            # This is part of the data consistency issue mentioned in IMPLEMENTATION_ISSUES.md
            raise DatabaseOperationError(
                message="Failed to store memory in relational database",
                operation="insert",
                table_name="memories",
                original_exception=e
            )
        
        return f"Memory stored with ID: {memory_id} for user: {user_id}"

    async def search_related(self, query_text: str) -> list[dict]:
        """Performs a semantic search for memories related to the query text."""
        # Get current user context
        user_id = get_current_user_id()
        if user_id is None:
            raise UserContextError(
                message="User context is required for memory search",
                operation="search_memories"
            )
        
        return await self.vector_store.search_memories(query_text, user_id)

    async def process_context(self, prompt: str, tags: Optional[list[str]] = None) -> str:
        """Record the user's message and return the synthesized profile."""
        user_id = get_current_user_id()
        if user_id is None:
            raise UserContextError(
                message="User context is required for profile processing",
                operation="process_context"
            )

        return await ProfileProcessor.record_message_and_get_profile(user_id, prompt)