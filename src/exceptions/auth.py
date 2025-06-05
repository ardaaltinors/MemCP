"""
Authentication and authorization exception classes.

This module defines exceptions related to user authentication, authorization,
API keys, tokens, and user account status.
"""

from typing import Optional, Dict, Any
from .base import MemoryMCPException


class AuthenticationError(MemoryMCPException):
    """
    Base class for authentication-related errors.
    
    This is the parent class for all authentication failures including
    invalid credentials, expired tokens, etc.
    """
    
    def __init__(
        self,
        message: str = "Authentication failed",
        error_code: str = "AUTHENTICATION_ERROR",
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, error_code=error_code, context=context)


class AuthorizationError(MemoryMCPException):
    """
    Raised when a user lacks permission to access a resource.
    
    This is used for authorization failures where the user is authenticated
    but doesn't have the required permissions.
    """
    
    def __init__(
        self,
        message: str = "Access denied",
        resource: Optional[str] = None,
        required_permission: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        context = {}
        if resource:
            context["resource"] = resource
        if required_permission:
            context["required_permission"] = required_permission
        if user_id:
            context["user_id"] = user_id
        
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            context=context
        )


class InvalidCredentialsError(AuthenticationError):
    """
    Raised when login credentials are invalid.
    
    This includes wrong username/password combinations or malformed credentials.
    """
    
    def __init__(
        self,
        message: str = "Invalid username or password",
        username: Optional[str] = None
    ):
        context = {}
        if username:
            context["username"] = username
        
        super().__init__(
            message=message,
            error_code="INVALID_CREDENTIALS",
            context=context
        )


class InactiveUserError(AuthenticationError):
    """
    Raised when a user account is inactive or disabled.
    """
    
    def __init__(
        self,
        message: str = "User account is inactive",
        user_id: Optional[str] = None,
        username: Optional[str] = None
    ):
        context = {}
        if user_id:
            context["user_id"] = user_id
        if username:
            context["username"] = username
        
        super().__init__(
            message=message,
            error_code="INACTIVE_USER",
            context=context
        )


class InvalidAPIKeyError(AuthenticationError):
    """
    Raised when an API key is invalid, expired, or malformed.
    """
    
    def __init__(
        self,
        message: str = "Invalid API key",
        api_key_prefix: Optional[str] = None
    ):
        context = {}
        if api_key_prefix:
            # Only store the prefix for security
            context["api_key_prefix"] = api_key_prefix
        
        super().__init__(
            message=message,
            error_code="INVALID_API_KEY",
            context=context
        )


class TokenError(AuthenticationError):
    """
    Base class for token-related errors.
    
    This is the parent class for JWT token validation failures.
    """
    
    def __init__(
        self,
        message: str = "Token error",
        error_code: str = "TOKEN_ERROR",
        token_type: Optional[str] = None
    ):
        context = {}
        if token_type:
            context["token_type"] = token_type
        
        super().__init__(
            message=message,
            error_code=error_code,
            context=context
        )


class ExpiredTokenError(TokenError):
    """
    Raised when a token has expired.
    """
    
    def __init__(
        self,
        message: str = "Token has expired",
        token_type: Optional[str] = None,
        expiry_time: Optional[str] = None
    ):
        context = {}
        if token_type:
            context["token_type"] = token_type
        if expiry_time:
            context["expiry_time"] = expiry_time
        
        super().__init__(
            message=message,
            error_code="EXPIRED_TOKEN",
            context=context
        )


class InvalidTokenError(TokenError):
    """
    Raised when a token is malformed or invalid.
    """
    
    def __init__(
        self,
        message: str = "Invalid token format",
        token_type: Optional[str] = None,
        validation_error: Optional[str] = None
    ):
        context = {}
        if token_type:
            context["token_type"] = token_type
        if validation_error:
            context["validation_error"] = validation_error
        
        super().__init__(
            message=message,
            error_code="INVALID_TOKEN",
            context=context
        ) 