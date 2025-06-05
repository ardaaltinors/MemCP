"""
Exception handler utilities for consistent error handling.

This module provides utilities for converting custom exceptions to HTTP responses,
logging errors, and handling exception propagation throughout the application.
"""

import logging
from typing import Dict, Any, Union, Optional
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

from .base import MemoryMCPException
from .auth import (
    AuthenticationError, AuthorizationError, InvalidCredentialsError,
    InactiveUserError, InvalidAPIKeyError, TokenError
)
from .database import DatabaseError, RecordNotFoundError, DuplicateRecordError
from .memory import MemoryError, UserContextError
from .external_service import ExternalServiceError, ServiceUnavailableError, ServiceTimeoutError

logger = logging.getLogger(__name__)


class ExceptionHandler:
    """
    Centralized exception handling for the Memory MCP application.
    
    This class provides methods to convert custom exceptions to appropriate
    HTTP responses and log errors consistently.
    """
    
    # Mapping of custom exception types to HTTP status codes
    EXCEPTION_STATUS_MAP = {
        # Authentication/Authorization errors
        InvalidCredentialsError: status.HTTP_401_UNAUTHORIZED,
        AuthenticationError: status.HTTP_401_UNAUTHORIZED,
        InvalidAPIKeyError: status.HTTP_401_UNAUTHORIZED,
        TokenError: status.HTTP_401_UNAUTHORIZED,
        InactiveUserError: status.HTTP_403_FORBIDDEN,
        AuthorizationError: status.HTTP_403_FORBIDDEN,
        
        # Database errors
        RecordNotFoundError: status.HTTP_404_NOT_FOUND,
        DuplicateRecordError: status.HTTP_409_CONFLICT,
        
        # Memory/User context errors
        UserContextError: status.HTTP_400_BAD_REQUEST,
        
        # External service errors
        ServiceUnavailableError: status.HTTP_503_SERVICE_UNAVAILABLE,
        ServiceTimeoutError: status.HTTP_504_GATEWAY_TIMEOUT,
    }
    
    @classmethod
    def to_http_exception(cls, exception: MemoryMCPException) -> HTTPException:
        """
        Convert a custom exception to an HTTPException.
        
        Args:
            exception: The custom exception to convert
            
        Returns:
            HTTPException with appropriate status code and details
        """
        status_code = cls.EXCEPTION_STATUS_MAP.get(
            type(exception),
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
        detail = {
            "error_code": exception.error_code,
            "message": exception.message,
            "type": exception.__class__.__name__
        }
        
        # Add context if available (but sanitize sensitive information)
        if exception.context:
            detail["context"] = cls._sanitize_context(exception.context)
        
        return HTTPException(status_code=status_code, detail=detail)
    
    @classmethod
    def to_json_response(cls, exception: MemoryMCPException) -> JSONResponse:
        """
        Convert a custom exception to a JSONResponse.
        
        Args:
            exception: The custom exception to convert
            
        Returns:
            JSONResponse with appropriate status code and details
        """
        status_code = cls.EXCEPTION_STATUS_MAP.get(
            type(exception),
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
        content = exception.to_dict()
        # Sanitize context for response
        if "context" in content:
            content["context"] = cls._sanitize_context(content["context"])
        
        return JSONResponse(status_code=status_code, content=content)
    
    @classmethod
    def log_exception(
        cls,
        exception: Union[MemoryMCPException, Exception],
        operation: Optional[str] = None,
        user_id: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log an exception with consistent formatting.
        
        Args:
            exception: The exception to log
            operation: The operation that failed
            user_id: The user ID associated with the operation
            additional_context: Additional context for logging
        """
        log_data = {
            "exception_type": exception.__class__.__name__,
            "message": str(exception),
        }
        
        if operation:
            log_data["operation"] = operation
        if user_id:
            log_data["user_id"] = user_id
        if additional_context:
            log_data.update(additional_context)
        
        if isinstance(exception, MemoryMCPException):
            log_data["error_code"] = exception.error_code
            if exception.context:
                log_data["context"] = cls._sanitize_context(exception.context)
            if exception.original_exception:
                log_data["original_exception"] = str(exception.original_exception)
            
            # Log at appropriate level based on exception type
            if isinstance(exception, (AuthenticationError, AuthorizationError)):
                logger.warning("Authentication/Authorization error: %s", log_data)
            elif isinstance(exception, ExternalServiceError):
                logger.error("External service error: %s", log_data)
            elif isinstance(exception, DatabaseError):
                logger.error("Database error: %s", log_data)
            else:
                logger.error("Application error: %s", log_data)
        else:
            logger.error("Unhandled exception: %s", log_data, exc_info=True)
    
    @staticmethod
    def _sanitize_context(context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize context data to remove sensitive information.
        
        Args:
            context: The context dictionary to sanitize
            
        Returns:
            Sanitized context dictionary
        """
        sanitized = {}
        sensitive_keys = {
            "password", "token", "api_key", "secret", "private_key",
            "access_token", "refresh_token", "hashed_password"
        }
        
        for key, value in context.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, str) and len(value) > 100:
                # Truncate long strings
                sanitized[key] = value[:100] + "..."
            else:
                sanitized[key] = value
        
        return sanitized


def handle_memory_mcp_exception(request, exception: MemoryMCPException) -> JSONResponse:
    """
    FastAPI exception handler for MemoryMCPException.
    
    This function can be registered as a FastAPI exception handler to
    automatically handle all custom exceptions consistently.
    
    Args:
        request: The FastAPI request object
        exception: The MemoryMCPException to handle
        
    Returns:
        JSONResponse with appropriate error details
    """
    ExceptionHandler.log_exception(exception)
    return ExceptionHandler.to_json_response(exception)


def wrap_database_exceptions(func):
    """
    Decorator to wrap database operations and convert SQLAlchemy exceptions
    to custom database exceptions.
    
    Args:
        func: The function to wrap
        
    Returns:
        Wrapped function that converts database exceptions
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            from sqlalchemy.exc import IntegrityError, OperationalError
            from .database import DatabaseOperationError, DuplicateRecordError, DatabaseConnectionError
            
            if isinstance(e, IntegrityError):
                raise DuplicateRecordError(
                    message="Database integrity constraint violation",
                    original_exception=e
                )
            elif isinstance(e, OperationalError):
                raise DatabaseConnectionError(
                    message="Database connection or operation failed",
                    original_exception=e
                )
            else:
                raise DatabaseOperationError(
                    message="Database operation failed",
                    original_exception=e
                )
    
    return wrapper 