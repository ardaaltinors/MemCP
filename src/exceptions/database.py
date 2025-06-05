"""
Database exception classes.

This module defines exceptions related to database operations, connections,
and data integrity issues.
"""

from typing import Optional, Dict, Any
from .base import MemoryMCPException


class DatabaseError(MemoryMCPException):
    """
    Base class for database-related errors.
    
    This is the parent class for all database operation failures.
    """
    
    def __init__(
        self,
        message: str = "Database error occurred",
        error_code: str = "DATABASE_ERROR",
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            context=context,
            original_exception=original_exception
        )


class DatabaseConnectionError(DatabaseError):
    """
    Raised when database connection fails.
    
    This includes connection timeouts, invalid connection strings,
    and database server unavailability.
    """
    
    def __init__(
        self,
        message: str = "Failed to connect to database",
        database_url: Optional[str] = None,
        connection_timeout: Optional[int] = None,
        original_exception: Optional[Exception] = None
    ):
        context = {}
        if database_url:
            # Sanitize the URL to remove credentials
            context["database_url"] = self._sanitize_db_url(database_url)
        if connection_timeout:
            context["connection_timeout"] = connection_timeout
        
        super().__init__(
            message=message,
            error_code="DATABASE_CONNECTION_ERROR",
            context=context,
            original_exception=original_exception
        )
    
    @staticmethod
    def _sanitize_db_url(url: str) -> str:
        """Remove credentials from database URL for logging."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            sanitized = f"{parsed.scheme}://***:***@{parsed.hostname}"
            if parsed.port:
                sanitized += f":{parsed.port}"
            if parsed.path:
                sanitized += parsed.path
            return sanitized
        except Exception:
            return "***sanitized***"


class RecordNotFoundError(DatabaseError):
    """
    Raised when a requested database record is not found.
    """
    
    def __init__(
        self,
        message: str = "Record not found",
        table_name: Optional[str] = None,
        record_id: Optional[str] = None,
        search_criteria: Optional[Dict[str, Any]] = None
    ):
        context = {}
        if table_name:
            context["table_name"] = table_name
        if record_id:
            context["record_id"] = record_id
        if search_criteria:
            context["search_criteria"] = search_criteria
        
        super().__init__(
            message=message,
            error_code="RECORD_NOT_FOUND",
            context=context
        )


class DuplicateRecordError(DatabaseError):
    """
    Raised when attempting to create a record that violates uniqueness constraints.
    """
    
    def __init__(
        self,
        message: str = "Record already exists",
        table_name: Optional[str] = None,
        conflicting_field: Optional[str] = None,
        conflicting_value: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        context = {}
        if table_name:
            context["table_name"] = table_name
        if conflicting_field:
            context["conflicting_field"] = conflicting_field
        if conflicting_value:
            context["conflicting_value"] = conflicting_value
        
        super().__init__(
            message=message,
            error_code="DUPLICATE_RECORD",
            context=context,
            original_exception=original_exception
        )


class DatabaseOperationError(DatabaseError):
    """
    Raised when a database operation fails.
    
    This includes transaction failures, constraint violations,
    and other SQL execution errors.
    """
    
    def __init__(
        self,
        message: str = "Database operation failed",
        operation: Optional[str] = None,
        table_name: Optional[str] = None,
        sql_error_code: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        context = {}
        if operation:
            context["operation"] = operation
        if table_name:
            context["table_name"] = table_name
        if sql_error_code:
            context["sql_error_code"] = sql_error_code
        
        super().__init__(
            message=message,
            error_code="DATABASE_OPERATION_ERROR",
            context=context,
            original_exception=original_exception
        ) 