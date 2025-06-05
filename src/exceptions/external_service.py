"""
External service exception classes.

This module defines exceptions related to external service integrations
like OpenAI, Qdrant, and other third-party services.
"""

from typing import Optional, Dict, Any
from .base import MemoryMCPException


class ExternalServiceError(MemoryMCPException):
    """
    Base class for external service-related errors.
    
    This is the parent class for all external service failures.
    """
    
    def __init__(
        self,
        message: str = "External service error",
        error_code: str = "EXTERNAL_SERVICE_ERROR",
        service_name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        if context is None:
            context = {}
        if service_name:
            context["service_name"] = service_name
        
        super().__init__(
            message=message,
            error_code=error_code,
            context=context,
            original_exception=original_exception
        )


class OpenAIServiceError(ExternalServiceError):
    """
    Raised when OpenAI API operations fail.
    
    This includes embedding generation failures, API key issues,
    rate limiting, and other OpenAI-specific errors.
    """
    
    def __init__(
        self,
        message: str = "OpenAI service error",
        api_operation: Optional[str] = None,
        model_name: Optional[str] = None,
        status_code: Optional[int] = None,
        rate_limit_type: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        context = {}
        if api_operation:
            context["api_operation"] = api_operation
        if model_name:
            context["model_name"] = model_name
        if status_code:
            context["status_code"] = status_code
        if rate_limit_type:
            context["rate_limit_type"] = rate_limit_type
        
        super().__init__(
            message=message,
            error_code="OPENAI_SERVICE_ERROR",
            service_name="OpenAI",
            context=context,
            original_exception=original_exception
        )


class QdrantServiceError(ExternalServiceError):
    """
    Raised when Qdrant operations fail.
    
    This includes collection operations, vector search failures,
    connection issues, and other Qdrant-specific errors.
    """
    
    def __init__(
        self,
        message: str = "Qdrant service error",
        operation: Optional[str] = None,
        collection_name: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        original_exception: Optional[Exception] = None
    ):
        context = {}
        if operation:
            context["operation"] = operation
        if collection_name:
            context["collection_name"] = collection_name
        if host:
            context["host"] = host
        if port:
            context["port"] = port
        
        super().__init__(
            message=message,
            error_code="QDRANT_SERVICE_ERROR",
            service_name="Qdrant",
            context=context,
            original_exception=original_exception
        )


class ServiceUnavailableError(ExternalServiceError):
    """
    Raised when an external service is temporarily unavailable.
    
    This includes service outages, maintenance windows,
    and temporary connectivity issues.
    """
    
    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        service_name: Optional[str] = None,
        expected_recovery_time: Optional[str] = None,
        retry_after: Optional[int] = None,
        original_exception: Optional[Exception] = None
    ):
        context = {}
        if expected_recovery_time:
            context["expected_recovery_time"] = expected_recovery_time
        if retry_after:
            context["retry_after"] = retry_after
        
        super().__init__(
            message=message,
            error_code="SERVICE_UNAVAILABLE",
            service_name=service_name,
            context=context,
            original_exception=original_exception
        )


class ServiceTimeoutError(ExternalServiceError):
    """
    Raised when an external service call times out.
    
    This includes read timeouts, connection timeouts,
    and other time-related service failures.
    """
    
    def __init__(
        self,
        message: str = "Service call timed out",
        service_name: Optional[str] = None,
        timeout_duration: Optional[float] = None,
        operation: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        context = {}
        if timeout_duration:
            context["timeout_duration"] = timeout_duration
        if operation:
            context["operation"] = operation
        
        super().__init__(
            message=message,
            error_code="SERVICE_TIMEOUT",
            service_name=service_name,
            context=context,
            original_exception=original_exception
        ) 