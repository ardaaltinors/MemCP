"""
Utilities for handling user context in MCP tools.
"""
import uuid
from typing import Optional
from fastmcp import Context
from fastmcp.server.dependencies import get_http_request
from fastmcp.server.dependencies import get_access_token
from sqlalchemy.ext.asyncio import AsyncSession
from src.crud import crud_oauth, crud_user
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


async def resolve_user_id(ctx: Optional[Context], db: AsyncSession) -> uuid.UUID:
    """
    Resolve a user_id for the current request context.

    Order of resolution:
    1) If middleware already attached a DB user on request.state.user, use it.
    2) If an OAuth access token is present (via FastMCP auth), map or provision a user:
       - Prefer exact OAuth account match (provider + subject)
       - Fallback to email match
       - Optionally create a new user if not found
    """
    # Prefer middleware-attached user
    request = None
    try:
        request = get_http_request()
    except Exception:
        request = None

    if request and hasattr(request.state, 'user') and request.state.user:
        return request.state.user.id

    # Try FastMCP OAuth token
    token = None
    try:
        token = get_access_token()
    except Exception:
        token = None

    if token and getattr(token, 'claims', None):
        claims = token.claims
        # Infer provider + subject
        iss = str(claims.get('iss', ''))
        provider = 'oidc'
        if 'accounts.google.com' in iss or claims.get('email_verified') is True:
            provider = 'google'
        elif 'github' in iss or 'login' in claims or 'github' in str(claims.get('aud','')):
            provider = 'github'

        subject = str(claims.get('sub') or claims.get('id') or claims.get('login'))
        email = claims.get('email')

        # If we can link by provider+subject, do so; otherwise fallback to email
        account = await crud_oauth.get_oauth_account(db, provider=provider, subject=subject)
        if account:
            return account.user_id

        if email:
            existing = await crud_oauth.get_user_by_email(db, email=email)
            if existing:
                await crud_oauth.link_oauth_account(
                    db,
                    user=existing,
                    provider=provider,
                    subject=subject,
                    email=email,
                    access_token=token.access_token if hasattr(token, 'access_token') else None,
                    refresh_token=getattr(token, 'refresh_token', None),
                    expires_at=None,
                )
                return existing.id

        created = await crud_oauth.get_or_create_user_for_oauth(
            db,
            provider=provider,
            subject=subject,
            email=email,
            username_hint=claims.get('login') or (email.split('@')[0] if email else None),
        )
        await crud_oauth.link_oauth_account(
            db,
            user=created,
            provider=provider,
            subject=subject,
            email=email,
            access_token=token.access_token if hasattr(token, 'access_token') else None,
            refresh_token=getattr(token, 'refresh_token', None),
            expires_at=None,
        )
        return created.id

    raise AuthenticationError(
        message="No authenticated user found in request"
    )
