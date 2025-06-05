"""
Memory management exception classes.

This module defines exceptions related to memory operations, embeddings,
and user context management in the Memory MCP application.
"""

from typing import Optional, Dict, Any
from .base import MemoryMCPException


class MemoryError(MemoryMCPException):
    """
    Base class for memory-related errors.
    
    This is the parent class for all memory operation failures.
    """
    
    def __init__(
        self,
        message: str = "Memory operation error",
        error_code: str = "MEMORY_ERROR",
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            context=context,
            original_exception=original_exception
        )


class MemoryStoreError(MemoryError):
    """
    Raised when storing a memory fails.
    
    This includes failures in both Qdrant vector storage and PostgreSQL storage.
    """
    
    def __init__(
        self,
        message: str = "Failed to store memory",
        memory_id: Optional[str] = None,
        user_id: Optional[str] = None,
        storage_type: Optional[str] = None,  # "qdrant" or "postgresql"
        original_exception: Optional[Exception] = None
    ):
        context = {}
        if memory_id:
            context["memory_id"] = memory_id
        if user_id:
            context["user_id"] = user_id
        if storage_type:
            context["storage_type"] = storage_type
        
        super().__init__(
            message=message,
            error_code="MEMORY_STORE_ERROR",
            context=context,
            original_exception=original_exception
        )


class MemorySearchError(MemoryError):
    """
    Raised when memory search operations fail.
    
    This includes failures in vector similarity search and query processing.
    """
    
    def __init__(
        self,
        message: str = "Memory search failed",
        query_text: Optional[str] = None,
        user_id: Optional[str] = None,
        search_type: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        context = {}
        if query_text:
            context["query_text"] = query_text[:100]  # Truncate for logging
        if user_id:
            context["user_id"] = user_id
        if search_type:
            context["search_type"] = search_type
        
        super().__init__(
            message=message,
            error_code="MEMORY_SEARCH_ERROR",
            context=context,
            original_exception=original_exception
        )


class EmbeddingError(MemoryError):
    """
    Raised when text embedding generation fails.
    
    This includes failures in OpenAI embedding API calls and processing.
    """
    
    def __init__(
        self,
        message: str = "Failed to generate embeddings",
        text_content: Optional[str] = None,
        embedding_model: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        context = {}
        if text_content:
            context["text_length"] = len(text_content)
            context["text_preview"] = text_content[:50]  # First 50 chars for context
        if embedding_model:
            context["embedding_model"] = embedding_model
        
        super().__init__(
            message=message,
            error_code="EMBEDDING_ERROR",
            context=context,
            original_exception=original_exception
        )


class UserContextError(MemoryError):
    """
    Raised when user context is missing or invalid.
    
    This includes cases where user_id cannot be retrieved from the current context.
    """
    
    def __init__(
        self,
        message: str = "User context not found or invalid",
        operation: Optional[str] = None,
        expected_context: Optional[str] = None
    ):
        context = {}
        if operation:
            context["operation"] = operation
        if expected_context:
            context["expected_context"] = expected_context
        
        super().__init__(
            message=message,
            error_code="USER_CONTEXT_ERROR",
            context=context
        ) 