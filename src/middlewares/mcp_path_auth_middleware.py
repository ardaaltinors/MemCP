import logging
import os
from typing import Callable, Awaitable

from starlette.requests import Request
from starlette.responses import JSONResponse

from src.db.database import get_async_sessionmaker
from src.crud.crud_user import get_user_by_api_key
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

        # Extract API key from Authorization header
        api_key = None
        auth_header = headers.get("authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            api_key = auth_header.split(" ", 1)[1].strip()

        # Legacy path-based auth: /mcp/{api_key}/...
        if path.startswith("/mcp/"):
            remainder = path[len("/mcp/"):]
            if remainder and not remainder.startswith("health"):
                first, _, tail = remainder.partition("/")
                if not api_key:
                    api_key = first
                new_path = "/mcp" + ("/" + tail if tail else "")
                if new_path != path:
                    if self.debug:
                        logger.debug(f"Rewriting MCP path from {path} -> {new_path}")
                    scope = dict(scope)
                    scope["path"] = new_path
                    scope["raw_path"] = new_path.encode()

        if api_key:
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

