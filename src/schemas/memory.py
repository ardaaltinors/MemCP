import uuid
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class MemoryBase(BaseModel):
    """Base memory schema with common fields."""
    content: str = Field(..., min_length=1, max_length=10000, description="Memory content")
    tags: Optional[List[str]] = Field(default=None, description="Optional tags for categorization")


class MemoryCreate(MemoryBase):
    """Schema for creating a new memory."""
    pass


class MemoryUpdate(BaseModel):
    """Schema for updating a memory."""
    content: Optional[str] = Field(None, min_length=1, max_length=10000, description="Updated memory content")
    tags: Optional[List[str]] = Field(None, description="Updated tags")


class Memory(MemoryBase):
    """Complete memory schema for responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID = Field(..., description="Unique memory identifier")
    user_id: uuid.UUID = Field(..., description="Owner's user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class MemoryBulkCreate(BaseModel):
    """Schema for bulk creating memories."""
    memories: List[MemoryCreate] = Field(..., min_items=1, max_items=100, description="List of memories to create")


class BulkMemoryResult(BaseModel):
    """Result for individual memory in bulk operation."""
    success: bool = Field(..., description="Whether the memory was created successfully")
    memory: Optional[Memory] = Field(None, description="Created memory if successful")
    error: Optional[str] = Field(None, description="Error message if failed")
    index: int = Field(..., description="Index in the original request list")


class MemoryBulkResponse(BaseModel):
    """Response schema for bulk memory creation."""
    results: List[BulkMemoryResult] = Field(..., description="Results for each memory creation")
    total_requested: int = Field(..., description="Total number of memories requested to create")
    total_created: int = Field(..., description="Total number of memories successfully created")
    total_failed: int = Field(..., description="Total number of memories that failed to create")


class MemoryListResponse(BaseModel):
    """Response schema for listing memories."""
    memories: List[Memory] = Field(..., description="List of memories")
    total: int = Field(..., description="Total number of memories")
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, description="Number of items per page")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages") 