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


logger = logging.getLogger(__name__)


class MCPPathAuthMiddleware:
    """
    Supports header-based auth via Authorization: Bearer <api_key> and path-based auth via /mcp/{api_key}[/*]
    Also supports legacy path-based auth: POST /mcp/{api_key}[/*] Rewrites the path to /mcp[/*]
      
    On success, sets `scope['state']['user']` for downstream handlers and tools.
    """

    def __init__(self, app: Callable[[dict, Callable, Callable], Awaitable[None]]):
        self.app = app
        self.debug = os.getenv("DEBUG", "false").lower() == "true"

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            return await self.app(scope, receive, send)

        path: str = scope.get("path", "")
        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}

        # Debug logging for troubleshooting
        if path.startswith("/mcp"):
            auth_header_preview = headers.get("authorization", "None")[:50] if headers.get("authorization") else "None"
            logger.info(f"[AUTH] MCP Request - Path: {path}, Auth Header: {auth_header_preview}...")

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
                if path.startswith("/mcp"):
                    logger.info(f"[AUTH] Identified as internal JWT for user: {token_data.sub}")
            else:
                # If it looks like a JWT (contains at least 2 dots), assume FastMCP OAuth token
                # and do NOT treat it as an API key. Let FastMCP auth handle it downstream.
                if bearer.count('.') >= 2:
                    if path.startswith("/mcp"):
                        logger.info(f"[AUTH] Token has {bearer.count('.')} dots - passing to FastMCP OAuth validation")
                    pass  # leave both jwt_token and api_key as None
                else:
                    # Legacy behavior: allow API key in Bearer header
                    api_key = bearer
                    if path.startswith("/mcp"):
                        logger.info(f"[AUTH] Token identified as API key: {api_key[:10]}...")
        # Also support X-API-Key header
        if not api_key and not jwt_token and headers.get("x-api-key"):
            api_key = headers.get("x-api-key")
            if path.startswith("/mcp"):
                logger.info(f"[AUTH] Using X-API-Key header: {api_key[:10]}...")

        # Log if no credentials found
        if path.startswith("/mcp") and not api_key and not jwt_token and not auth_header:
            logger.info(f"[AUTH] No credentials found - request will be handled by downstream auth")

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
                session_maker = get_async_sessionmaker()
                async with session_maker() as db:
                    user = await get_user_by_username(db, username=token_data.sub)
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
            session_maker = get_async_sessionmaker()
            async with session_maker() as db:
                user = await get_user_by_api_key(db, api_key)
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
