import os
import logging
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from src.db.database import get_async_sessionmaker
from src.crud.crud_user import get_user_by_api_key
# Removed set_current_user_id import - no longer using global context
from src.exceptions import InvalidAPIKeyError, InactiveUserError
from src.exceptions.handlers import ExceptionHandler

# Configure logger for middleware
logger = logging.getLogger(__name__)

class UserCredentialMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
    
    async def dispatch(self, request: Request, call_next):
        # Extract user credential (API key) from path
        path = request.url.path
        if path.startswith("/mcp/"):
            api_key = path.split("/mcp/")[1].split("/")[0] if len(path.split("/mcp/")[1].split("/")) > 0 else None
            
            # Remove "/mcp/" prefix and handle health checks
            if api_key and api_key != "health":
                if self.debug:
                    logger.debug(f"Processing API key from path: {api_key[:10]}...")
                
                # Validate API key against database using event-loop-specific session
                session_maker = get_async_sessionmaker()
                async with session_maker() as db:
                    user = await get_user_by_api_key(db, api_key)
                    if user:
                        if user.is_active:
                            if self.debug:
                                logger.debug(
                                    f"✅ Authorized user: {user.username} (ID: {user.id}, "
                                    f"Superuser: {user.is_superuser}, "
                                    f"API Key Created: {user.api_key_created_at})"
                                )
                            
                            # Store user info in request state for later use
                            request.state.user = user
                            # No longer setting global context - user_id passed explicitly
                        else:
                            if self.debug:
                                logger.warning(f"❌ Inactive user attempted access: {user.username} ({user.email})")
                            
                            exception = InactiveUserError(
                                user_id=str(user.id),
                                username=user.username
                            )
                            
                            # Log the security event
                            ExceptionHandler.log_exception(
                                exception=exception,
                                operation="mcp_auth_middleware",
                                user_id=str(user.id),
                                additional_context={
                                    "path": path,
                                    "api_key_prefix": api_key[:10] + "..." if len(api_key) > 10 else api_key
                                }
                            )
                            
                            return ExceptionHandler.to_json_response(exception)
                    else:
                        if self.debug:
                            logger.warning(f"❌ Invalid API key attempted: {api_key[:10]}...")
                        
                        exception = InvalidAPIKeyError(
                            api_key_prefix=api_key[:10] + "..." if len(api_key) > 10 else api_key
                        )
                        
                        # Log the security event
                        ExceptionHandler.log_exception(
                            exception=exception,
                            operation="mcp_auth_middleware",
                            additional_context={
                                "path": path,
                                "api_key_prefix": api_key[:10] + "..." if len(api_key) > 10 else api_key
                            }
                        )
                        
                        return ExceptionHandler.to_json_response(exception)
            else:
                if self.debug:
                    logger.debug(f"Health check or no API key required for path: {path}")
        
        # Continue to the next middleware/route
        response = await call_next(request)
        return response 