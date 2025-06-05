"""
Base exception classes for the Memory MCP application.

This module defines the root exception hierarchy and common exception types
used throughout the application.
"""

from typing import Optional, Dict, Any


class MemoryMCPException(Exception):
    """
    Base exception class for all Memory MCP application exceptions.
    
    This class provides a common interface for all custom exceptions in the application,
    including error codes, context information, and structured error details.
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.context = context or {}
        self.original_exception = original_exception
    
    def __str__(self) -> str:
        if self.context:
            return f"{self.message} (Error: {self.error_code}, Context: {self.context})"
        return f"{self.message} (Error: {self.error_code})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON serialization."""
        result = {
            "error_code": self.error_code,
            "message": self.message,
            "type": self.__class__.__name__,
        }
        if self.context:
            result["context"] = self.context
        if self.original_exception:
            result["original_error"] = str(self.original_exception)
        return result


class ConfigurationError(MemoryMCPException):
    """
    Raised when there are configuration-related errors.
    
    This includes missing environment variables, invalid configuration values,
    or any other setup-related issues.
    """
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        expected_type: Optional[str] = None,
        actual_value: Optional[Any] = None
    ):
        context = {}
        if config_key:
            context["config_key"] = config_key
        if expected_type:
            context["expected_type"] = expected_type
        if actual_value is not None:
            context["actual_value"] = str(actual_value)
        
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            context=context
        )


class ValidationError(MemoryMCPException):
    """
    Raised when input validation fails.
    
    This exception is used for data validation errors that are specific to
    the Memory MCP application, distinct from Pydantic's ValidationError.
    """
    
    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        field_value: Optional[Any] = None,
        validation_rule: Optional[str] = None
    ):
        context = {}
        if field_name:
            context["field_name"] = field_name
        if field_value is not None:
            context["field_value"] = str(field_value)
        if validation_rule:
            context["validation_rule"] = validation_rule
        
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR", 
            context=context
        ) 