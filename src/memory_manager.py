import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.context import get_current_user_id
from src.db.models import Memory
from src.exceptions import UserContextError, DatabaseOperationError
from src.utils.vector_store import VectorStore
from src.utils.profile_processor import ProfileProcessor

if TYPE_CHECKING:
    from fastmcp import Context

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
        
        return f"Memory stored with ID: {memory_id}"

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

    async def update_memory(self, memory_id: str, content: str, db: AsyncSession, tags: Optional[list[str]] = None) -> str:
        """
        Updates a memory in both vector and relational databases.
        """
        from src.crud.crud_memory import update_memory
        
        user_id = get_current_user_id()
        if user_id is None:
            raise UserContextError(
                message="User context is required for memory update",
                operation="update_memory"
            )
        
        # Update in PostgreSQL first
        try:
            updated_memory = await update_memory(
                db=db,
                memory_id=uuid.UUID(memory_id),
                user_id=user_id,
                content=content,
                tags=tags
            )
            
            if not updated_memory:
                raise DatabaseOperationError(
                    message="Memory not found or access denied",
                    operation="update",
                    table_name="memories"
                )
            
        except Exception as e:
            raise DatabaseOperationError(
                message="Failed to update memory in relational database",
                operation="update",
                table_name="memories",
                original_exception=e
            )
        
        # Update in Qdrant
        try:
            await self.vector_store.store_memory(memory_id, content, user_id, tags)
        except Exception as e:
            # Log error but don't fail the operation since PostgreSQL was updated
            # This is part of the data consistency issue mentioned in IMPLEMENTATION_ISSUES.md
            pass
        
        return f"Memory {memory_id} updated successfully"

    async def delete_memory(self, memory_id: str, db: AsyncSession) -> str:
        """
        Deletes a memory from both vector and relational databases.
        """
        from src.crud.crud_memory import delete_memory
        
        user_id = get_current_user_id()
        if user_id is None:
            raise UserContextError(
                message="User context is required for memory deletion",
                operation="delete_memory"
            )
        
        # Delete from PostgreSQL first
        try:
            success = await delete_memory(
                db=db,
                memory_id=uuid.UUID(memory_id),
                user_id=user_id
            )
            
            if not success:
                raise DatabaseOperationError(
                    message="Memory not found or access denied",
                    operation="delete",
                    table_name="memories"
                )
            
        except Exception as e:
            raise DatabaseOperationError(
                message="Failed to delete memory from relational database",
                operation="delete",
                table_name="memories",
                original_exception=e
            )
        
        # Delete from Qdrant
        try:
            await self.vector_store.delete_memory(memory_id, user_id)
        except Exception as e:
            # Log error but don't fail since PostgreSQL deletion succeeded
            # This maintains partial consistency - the memory is removed from PostgreSQL
            # even if Qdrant deletion fails
            pass
        
        return f"Memory {memory_id} deleted successfully"

    async def delete_all_user_memories(self, db: AsyncSession) -> str:
        """
        Delete all memories for a user from both PostgreSQL and Qdrant, plus processed profile.
        """
        from src.crud.crud_memory import delete_all_user_memories
        from src.crud.crud_processed_user_profile import delete_processed_user_profile
        
        user_id = get_current_user_id()
        if user_id is None:
            raise UserContextError(
                message="User context is required for bulk memory deletion",
                operation="delete_all_memories"
            )
        
        # Delete from PostgreSQL first
        try:
            postgres_count = await delete_all_user_memories(db=db, user_id=user_id)
        except Exception as e:
            raise DatabaseOperationError(
                message="Failed to delete all memories from relational database",
                operation="bulk_delete",
                table_name="memories",
                original_exception=e
            )
        
        # Delete from Qdrant
        qdrant_count = 0
        try:
            qdrant_count = await self.vector_store.delete_all_user_memories(user_id)
        except Exception as e:
            # Log error but don't fail since PostgreSQL deletion succeeded
            # This maintains partial consistency - memories are removed from PostgreSQL
            pass
        
        # Delete processed user profile
        profile_deleted = False
        try:
            profile_deleted = await delete_processed_user_profile(db=db, user_id=user_id)
        except Exception as e:
            # Log error but don't fail the operation
            pass
        
        profile_msg = " and processed profile" if profile_deleted else ""
        return f"Deleted {postgres_count} memories from PostgreSQL, {qdrant_count} from Qdrant{profile_msg}"

    async def process_context(self, prompt: str, tags: Optional[list[str]] = None) -> str:
        """Record the user's message and return the synthesized profile."""
        user_id = get_current_user_id()
        if user_id is None:
            raise UserContextError(
                message="User context is required for profile processing",
                operation="process_context"
            )

        return await ProfileProcessor.record_message_and_get_profile(user_id, prompt)
    
    async def store_batch(
        self, 
        memories: list[dict],
        db: AsyncSession,
        ctx: Optional['Context'] = None
    ) -> str:
        """
        Store multiple memories with progress reporting.
        
        Args:
            memories: List of dicts with 'content' and optional 'tags' keys
            db: Database session
            ctx: Optional FastMCP context for progress reporting
        """
        user_id = get_current_user_id()
        if user_id is None:
            raise UserContextError(
                message="User context is required for batch memory storage",
                operation="store_batch"
            )
        
        total = len(memories)
        successful = 0
        failed = 0
        
        if ctx:
            await ctx.info(f"Starting batch storage of {total} memories")
        
        for i, memory_data in enumerate(memories):
            if ctx:
                await ctx.report_progress(progress=i, total=total)
            
            try:
                content = memory_data.get('content', '')
                tags = memory_data.get('tags', [])
                
                # Generate a UUID for this memory
                memory_id = str(uuid.uuid4())
                
                # Store in vector database
                await self.vector_store.store_memory(memory_id, content, user_id, tags)
                
                # Store in relational database
                db_memory = Memory(
                    id=uuid.UUID(memory_id),
                    content=content,
                    tags=tags or [],
                    user_id=user_id
                )
                db.add(db_memory)
                successful += 1
                
            except Exception as e:
                failed += 1
                if ctx:
                    await ctx.warning(f"Failed to store memory {i+1}: {str(e)}")
        
        await db.flush()
        
        if ctx:
            await ctx.report_progress(progress=total, total=total)
            await ctx.info(f"Batch storage complete: {successful} successful, {failed} failed")
        
        return f"Stored {successful} memories, {failed} failed"