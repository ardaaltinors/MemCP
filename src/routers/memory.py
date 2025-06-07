import uuid
from typing import List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_async_db
from src.routers.auth import get_current_active_user
from src.db.models.user import User as DBUser
from src.schemas import memory as memory_schema
from src.crud import crud_memory
from src.memory_manager import MemoryManager
from src.core.context import set_current_user_id

router = APIRouter()

# Initialize memory manager
memory_manager = MemoryManager()


@router.get("/", response_model=memory_schema.MemoryListResponse, tags=["Memories"])
async def get_user_memories(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get paginated list of user's memories from PostgreSQL.
    """
    skip = (page - 1) * per_page
    
    memories = await crud_memory.get_user_memories(
        db=db, 
        user_id=current_user.id, 
        skip=skip, 
        limit=per_page
    )
    
    # Get total count for pagination
    all_memories = await crud_memory.get_user_memories(db=db, user_id=current_user.id)
    total = len(all_memories)
    
    return {
        "memories": memories,
        "total": total,
        "page": page,
        "per_page": per_page,
        "has_next": skip + per_page < total,
        "has_prev": page > 1
    }


@router.get("/{memory_id}", response_model=memory_schema.Memory, tags=["Memories"])
async def get_memory(
    memory_id: uuid.UUID,
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get a specific memory by ID from PostgreSQL.
    """
    memory = await crud_memory.get_memory_by_id(db=db, memory_id=memory_id)
    
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )
    
    if memory.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You can only view your own memories."
        )
    
    return memory


@router.post("/", response_model=memory_schema.Memory, status_code=status.HTTP_201_CREATED, tags=["Memories"])
async def create_memory(
    memory_in: memory_schema.MemoryCreate,
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new memory.
    
    This stores the memory in both PostgreSQL and Qdrant for optimal 
    retrieval and semantic search capabilities.
    """
    # Set user context for memory manager
    set_current_user_id(current_user.id)
    
    # Use memory manager to store in both databases
    result_message = await memory_manager.store(
        content=memory_in.content,
        db=db,
        tags=memory_in.tags
    )
    
    # Get the most recently created memory for response
    memories = await crud_memory.get_user_memories(db=db, user_id=current_user.id, limit=1)
    
    if not memories:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Memory was created but could not be retrieved"
        )
    
    return memories[0]


@router.put("/{memory_id}", response_model=memory_schema.Memory, tags=["Memories"])
async def update_memory(
    memory_id: uuid.UUID,
    memory_update: memory_schema.MemoryUpdate,
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update an existing memory.
    
    This updates the memory in both PostgreSQL and Qdrant.
    """
    # Set user context for memory manager
    set_current_user_id(current_user.id)
    
    # Use memory manager to update in both databases
    result_message = await memory_manager.update_memory(
        memory_id=str(memory_id),
        content=memory_update.content,
        db=db,
        tags=memory_update.tags
    )
    
    # Get the updated memory for response
    memory = await crud_memory.get_memory_by_id(db=db, memory_id=memory_id)
    
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found after update"
        )
    
    return memory


@router.delete("/{memory_id}", tags=["Memories"])
async def delete_memory(
    memory_id: uuid.UUID,
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete a memory.
    
    This deletes the memory from both PostgreSQL and Qdrant.
    """
    # Set user context for memory manager
    set_current_user_id(current_user.id)
    
    # Use memory manager to delete from both databases
    result_message = await memory_manager.delete_memory(
        memory_id=str(memory_id),
        db=db
    )
    
    return {"message": result_message}


@router.get("/search/semantic", tags=["Memories"])
async def search_memories(
    query: str = Query(..., min_length=1, description="Search query"),
    current_user: DBUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Perform semantic search across user's memories using Qdrant.
    """
    # Set user context for memory manager
    set_current_user_id(current_user.id)
    
    # Perform semantic search using Qdrant
    qdrant_results = await memory_manager.search_related(query)
    
    # Enhance results with full memory details from PostgreSQL
    enhanced_results = []
    for qdrant_result in qdrant_results:
        memory_id = uuid.UUID(qdrant_result["id"])
        memory = await crud_memory.get_memory_by_id(db=db, memory_id=memory_id)
        
        if memory:
            enhanced_results.append({
                "memory": memory,
                "similarity_score": qdrant_result["score"],
                "qdrant_data": qdrant_result
            })
    
    return {
        "query": query,
        "results": enhanced_results,
        "total_results": len(enhanced_results)
    } 