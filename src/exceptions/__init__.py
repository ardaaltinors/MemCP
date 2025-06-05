"""
Custom exceptions for the application.

This module provides a hierarchical exception structure for better error handling
and more precise error reporting throughout the application.
"""

from .base import (
    MemoryMCPException,
    ConfigurationError,
    ValidationError as MCPValidationError,
)

from .auth import (
    AuthenticationError,
    AuthorizationError,
    InvalidCredentialsError,
    InactiveUserError,
    InvalidAPIKeyError,
    TokenError,
    ExpiredTokenError,
    InvalidTokenError,
)

from .database import (
    DatabaseError,
    DatabaseConnectionError,
    RecordNotFoundError,
    DuplicateRecordError,
    DatabaseOperationError,
)

from .memory import (
    MemoryError,
    MemoryStoreError,
    MemorySearchError,
    EmbeddingError,
    UserContextError,
)

from .external_service import (
    ExternalServiceError,
    OpenAIServiceError,
    QdrantServiceError,
    ServiceUnavailableError,
    ServiceTimeoutError,
)

__all__ = [
    # Base exceptions
    "MemoryMCPException",
    "ConfigurationError",
    "MCPValidationError",
    
    # Auth exceptions
    "AuthenticationError",
    "AuthorizationError", 
    "InvalidCredentialsError",
    "InactiveUserError",
    "InvalidAPIKeyError",
    "TokenError",
    "ExpiredTokenError",
    "InvalidTokenError",
    
    # Database exceptions
    "DatabaseError",
    "DatabaseConnectionError",
    "RecordNotFoundError",
    "DuplicateRecordError",
    "DatabaseOperationError",
    
    # Memory exceptions
    "MemoryError",
    "MemoryStoreError",
    "MemorySearchError",
    "EmbeddingError",
    "UserContextError",
    
    # External service exceptions
    "ExternalServiceError",
    "OpenAIServiceError",
    "QdrantServiceError",
    "ServiceUnavailableError",
    "ServiceTimeoutError",
] 