import uuid
from typing import Optional, List
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.memory import Memory
from src.exceptions import RecordNotFoundError, DatabaseOperationError


async def get_memory_by_id(db: AsyncSession, memory_id: uuid.UUID) -> Optional[Memory]:
    """Get a single memory by its ID."""
    result = await db.execute(select(Memory).filter(Memory.id == memory_id))
    return result.scalars().first()


async def get_user_memories(
    db: AsyncSession, 
    user_id: uuid.UUID,
    skip: int = 0,
    limit: Optional[int] = None
) -> List[Memory]:
    """Get all memories for a user with pagination."""
    query = select(Memory).filter(Memory.user_id == user_id)
    query = query.order_by(desc(Memory.created_at))
    
    if skip > 0:
        query = query.offset(skip)
    
    if limit:
        query = query.limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


async def create_memory(
    db: AsyncSession,
    content: str,
    user_id: uuid.UUID,
    tags: Optional[List[str]] = None,
    memory_id: Optional[uuid.UUID] = None
) -> Memory:
    """Create a new memory record."""
    try:
        memory = Memory(
            id=memory_id or uuid.uuid4(),
            content=content,
            tags=tags or [],
            user_id=user_id
        )
        db.add(memory)
        await db.flush()
        await db.refresh(memory)
        return memory
    except Exception as e:
        raise DatabaseOperationError(
            message="Failed to create memory",
            operation="insert",
            table_name="memories",
            original_exception=e
        )


async def update_memory(
    db: AsyncSession,
    memory_id: uuid.UUID,
    user_id: uuid.UUID,
    content: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> Optional[Memory]:
    """Update an existing memory. Only the memory owner can update it."""
    memory = await get_memory_by_id(db, memory_id)
    
    if not memory:
        raise RecordNotFoundError(
            table_name="memories",
            record_id=str(memory_id)
        )
    
    if memory.user_id != user_id:
        raise DatabaseOperationError(
            message="User can only update their own memories",
            operation="update",
            table_name="memories"
        )
    
    try:
        if content is not None:
            memory.content = content
        if tags is not None:
            memory.tags = tags
        
        await db.flush()
        await db.refresh(memory)
        return memory
    except Exception as e:
        raise DatabaseOperationError(
            message="Failed to update memory",
            operation="update",
            table_name="memories",
            original_exception=e
        )


async def delete_memory(
    db: AsyncSession,
    memory_id: uuid.UUID,
    user_id: uuid.UUID
) -> bool:
    """Delete a memory. Only the memory owner can delete it."""
    memory = await get_memory_by_id(db, memory_id)
    
    if not memory:
        raise RecordNotFoundError(
            table_name="memories",
            record_id=str(memory_id)
        )
    
    if memory.user_id != user_id:
        raise DatabaseOperationError(
            message="User can only delete their own memories",
            operation="delete",
            table_name="memories"
        )
    
    try:
        await db.delete(memory)
        await db.flush()
        return True
    except Exception as e:
        raise DatabaseOperationError(
            message="Failed to delete memory",
            operation="delete",
            table_name="memories",
            original_exception=e
        ) 