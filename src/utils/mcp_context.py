"""
Utilities for handling user context in MCP tools.
"""
import uuid
from typing import Optional
from fastmcp import Context
from fastmcp.server.dependencies import get_http_request
from src.exceptions import AuthenticationError


def get_user_id_from_context(ctx: Optional[Context]) -> uuid.UUID:
    """
    Extract user_id from the FastMCP context.
    
    Args:
        ctx: The FastMCP context object
        
    Returns:
        The authenticated user's ID
        
    Raises:
        AuthenticationError: If no user is found in the request context
    """
    if not ctx:
        raise AuthenticationError(
            message="No context provided to extract user information"
        )
    
    # Get the HTTP request from the FastMCP dependency (stable in 2.13)
    try:
        request = get_http_request()
    except Exception:
        request = None
    if not request:
        raise AuthenticationError(
            message="No HTTP request found in context"
        )
    
    # Get the user from request state (set by middleware)
    if not hasattr(request.state, 'user') or not request.state.user:
        raise AuthenticationError(
            message="No authenticated user found in request"
        )
    
    return request.state.user.id
