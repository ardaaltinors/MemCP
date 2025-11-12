import logging
import os
from typing import Callable, Awaitable

from starlette.requests import Request
from starlette.responses import JSONResponse

from src.db.database import get_async_sessionmaker
from src.crud.crud_user import get_user_by_api_key, get_user_by_username
from src.core import security
from starlette.authentication import AuthCredentials
from mcp.server.auth.provider import AccessToken as SDKAccessToken
from mcp.server.auth.middleware.bearer_auth import AuthenticatedUser
from src.exceptions import InvalidAPIKeyError, InactiveUserError
from src.exceptions.handlers import ExceptionHandler
from src.utils.auth_cache import AuthCache
from src.db.models.user import User


logger = logging.getLogger(__name__)


class MCPPathAuthMiddleware:
    """
    Supports header-based auth via Authorization: Bearer <api_key> and path-based auth via /mcp/{api_key}[/*]
    Also supports legacy path-based auth: POST /mcp/{api_key}[/*] Rewrites the path to /mcp[/*]

    On success, sets `scope['state']['user']` for downstream handlers and tools.

    Performance: Uses Redis caching to reduce database queries by ~90%.
    """

    def __init__(self, app: Callable[[dict, Callable, Callable], Awaitable[None]]):
        self.app = app
        self.debug = os.getenv("DEBUG", "false").lower() == "true"

    async def _get_user_by_api_key_cached(self, api_key: str) -> User | None:
        """
        Get user by API key with Redis caching.

        Args:
            api_key: The API key to lookup

        Returns:
            User object if found and valid, None otherwise
        """
        # Try cache first
        cached_data = AuthCache.get_user_by_api_key(api_key)
        if cached_data:
            # Reconstruct User object from cached data
            user = User(
                id=cached_data["id"],
                username=cached_data["username"],
                email=cached_data["email"],
                is_active=cached_data["is_active"],
                is_superuser=cached_data["is_superuser"],
                hashed_password="",  # Not needed for auth
                api_key=api_key
            )
            if self.debug:
                logger.debug(f"[CACHE HIT] User found in cache for API key: {api_key[:10]}...")
            return user

        # Cache miss - query database
        if self.debug:
            logger.debug(f"[CACHE MISS] Querying database for API key: {api_key[:10]}...")

        session_maker = get_async_sessionmaker()
        async with session_maker() as db:
            user = await get_user_by_api_key(db, api_key)

            if user:
                # Cache the result
                AuthCache.set_user_by_api_key(api_key, user)
                if self.debug:
                    logger.debug(f"[CACHE WRITE] Cached user for API key: {api_key[:10]}...")

            return user

    async def _get_user_by_username_cached(self, username: str) -> User | None:
        """
        Get user by username with Redis caching (for JWT tokens).

        Args:
            username: The username to lookup

        Returns:
            User object if found and valid, None otherwise
        """
        # Try cache first
        cached_data = AuthCache.get_user_by_username(username)
        if cached_data:
            # Reconstruct User object from cached data
            user = User(
                id=cached_data["id"],
                username=cached_data["username"],
                email=cached_data["email"],
                is_active=cached_data["is_active"],
                is_superuser=cached_data["is_superuser"],
                hashed_password="",  # Not needed for auth
            )
            if self.debug:
                logger.debug(f"[CACHE HIT] User found in cache for username: {username}")
            return user

        # Cache miss - query database
        if self.debug:
            logger.debug(f"[CACHE MISS] Querying database for username: {username}")

        session_maker = get_async_sessionmaker()
        async with session_maker() as db:
            user = await get_user_by_username(db, username=username)

            if user:
                # Cache the result
                AuthCache.set_user_by_username(username, user)
                if self.debug:
                    logger.debug(f"[CACHE WRITE] Cached user for username: {username}")

            return user

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            return await self.app(scope, receive, send)

        path: str = scope.get("path", "")
        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}

        # Extract credentials from Authorization header
        api_key = None
        jwt_token = None
        auth_header = headers.get("authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            bearer = auth_header.split(" ", 1)[1].strip()
            # First, try to decode as our own JWT
            token_data = security.decode_token(bearer)
            if token_data and token_data.sub:
                jwt_token = bearer
                logger.debug(f"[AUTH] Identified as internal JWT for user: {token_data.sub}")
            else:
                # If it looks like a JWT (contains at least 2 dots), assume FastMCP OAuth token
                # and do NOT treat it as an API key. Let FastMCP auth handle it downstream.
                if bearer.count('.') >= 2:
                    logger.debug(f"[AUTH] Token has {bearer.count('.')} dots - passing to FastMCP OAuth validation")
                    pass  # leave both jwt_token and api_key as None
                else:
                    # Legacy behavior: allow API key in Bearer header
                    api_key = bearer
                    logger.debug(f"[AUTH] Token identified as API key: {api_key[:10]}...")
        # Also support X-API-Key header
        if not api_key and not jwt_token and headers.get("x-api-key"):
            api_key = headers.get("x-api-key")
            logger.debug(f"[AUTH] Using X-API-Key header: {api_key[:10]}...")

        # Legacy path-based auth: /mcp/{api_key}/...
        if path.startswith("/mcp/"):
            remainder = path[len("/mcp/"):]
            if remainder:
                first, _, tail = remainder.partition("/")
                # Only treat as API key if it looks like our keys (e.g., starts with sk_)
                if first.startswith("sk_") and not api_key:
                    api_key = first
                    new_path = "/mcp" + ("/" + tail if tail else "")
                    if new_path != path:
                        if self.debug:
                            logger.debug(f"Rewriting MCP path from {path} -> {new_path}")
                        scope = dict(scope)
                        scope["path"] = new_path
                        scope["raw_path"] = new_path.encode()

        if jwt_token:
            token_data = security.decode_token(jwt_token)
            if token_data and token_data.sub:
                # Use cached lookup
                user = await self._get_user_by_username_cached(token_data.sub)
                if user:
                    if user.is_active:
                        scope.setdefault("state", {})
                        scope["state"]["user"] = user
                    else:
                        exception = InactiveUserError(user_id=str(user.id), username=user.username)
                        response = ExceptionHandler.to_json_response(exception)
                        return await response(scope, receive, send)
            # if token invalid, fall through to next checks
        elif api_key:
            # Use cached lookup
            user = await self._get_user_by_api_key_cached(api_key)
            if user:
                if user.is_active:
                    if self.debug:
                        logger.debug(
                            f"✅ Authorized user via MCP auth: {user.username} (ID: {user.id})"
                        )
                    scope.setdefault("state", {})
                    scope["state"]["user"] = user
                    # bypass FastMCP's RequireAuthMiddleware by providing a synthetic authenticated user
                    access = SDKAccessToken(
                        token=api_key,
                        client_id=str(user.id),
                        scopes=["user"],
                        expires_at=None,
                    )
                    scope["user"] = AuthenticatedUser(access)
                    scope["auth"] = AuthCredentials(["user"])
                else:
                    if self.debug:
                        logger.warning(
                            f"❌ Inactive user attempted MCP access: {user.username} ({user.email})"
                        )
                    exception = InactiveUserError(user_id=str(user.id), username=user.username)
                    response = ExceptionHandler.to_json_response(exception)
                    return await response(scope, receive, send)
            else:
                if self.debug:
                    logger.warning("❌ Invalid API key attempted for MCP access")
                exception = InvalidAPIKeyError(
                    api_key_prefix=api_key[:10] + "..." if len(api_key) > 10 else api_key
                )
                response = ExceptionHandler.to_json_response(exception)
                return await response(scope, receive, send)

        return await self.app(scope, receive, send)
