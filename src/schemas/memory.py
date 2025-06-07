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


class MemoryListResponse(BaseModel):
    """Response schema for listing memories."""
    memories: List[Memory] = Field(..., description="List of memories")
    total: int = Field(..., description="Total number of memories")
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, description="Number of items per page")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages") 