import os
from typing import Callable, Awaitable


class MCPOAuthHintMiddleware:
    """
    Ensures OAuth-capable MCP clients (Cursor/VS Code) see a 401 with
    WWW-Authenticate + resource metadata when no credentials are supplied.

    This does NOT change behavior for API-key auth or OAuth Bearer tokens.
    It only hints unauthenticated requests to start the OAuth flow.
    """

    def __init__(self, app: Callable[[dict, Callable, Callable], Awaitable[None]]):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            return await self.app(scope, receive, send)

        path: str = scope.get("path", "")
        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}

        # Already presenting credentials? Let downstream handle it
        has_auth_header = any(h.lower() == "authorization" for h in headers.keys())
        has_x_api_key = "x-api-key" in headers

        # Hint only on the MCP endpoint root (with or without trailing slash), without any credentials
        if path in ("/mcp", "/mcp/") and not has_auth_header and not has_x_api_key:
            # Compute absolute metadata URL - always without trailing slash
            # FastMCP serves .well-known endpoints without trailing slash
            scheme = (headers.get("x-forwarded-proto") or "http").split(",")[0].strip()
            host = headers.get("host", "localhost:4200")
            # Always use /mcp (no trailing slash) for metadata URL
            metadata_url = f"{scheme}://{host}/.well-known/oauth-protected-resource/mcp"

            # 401 with WWW-Authenticate per RFC specs used by FastMCP clients
            www_authenticate = (
                f"Bearer error=\"invalid_token\", error_description=\"Authentication required\", "
                f"resource_metadata=\"{metadata_url}\""
            )

            await send(
                {
                    "type": "http.response.start",
                    "status": 401,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"content-length", b"0"),
                        (b"www-authenticate", www_authenticate.encode()),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": b""})
            return

        return await self.app(scope, receive, send)

