import os
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from src.db.database import get_async_sessionmaker
from src.crud.crud_user import get_user_by_api_key
from src.core.context import set_current_user_id
from src.exceptions import InvalidAPIKeyError, InactiveUserError
from src.exceptions.handlers import ExceptionHandler


class UserCredentialMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
    
    async def dispatch(self, request: Request, call_next):
        # Extract user credential (API key) from path
        path = request.url.path
        if path.startswith("/mcp/") and len(path) > 5:  # "/mcp/"
            api_key = path[5:]  # Remove "/mcp/" prefix
            if api_key and api_key != "health":
                if self.debug:
                    print(f"API KEY from path: {api_key}")
                
                # Validate API key against database using event-loop-specific session
                session_maker = get_async_sessionmaker()
                async with session_maker() as db:
                    user = await get_user_by_api_key(db, api_key)
                    if user:
                        if user.is_active:
                            if self.debug:
                                print(f"✅ AUTHORIZED USER: {user.username} ({user.email})")
                                print(f"   - User ID: {user.id}")
                                print(f"   - Is Superuser: {user.is_superuser}")
                                print(f"   - API Key Created: {user.api_key_created_at}")
                                print(f"   - Account Created: {user.created_at}")
                            
                            # Store user info in request state for later use
                            request.state.user = user
                            # Set the user_id in thread-local context for memory_manager
                            set_current_user_id(user.id)
                        else:
                            if self.debug:
                                print(f"❌ INACTIVE USER: {user.username} ({user.email})")
                            exception = InactiveUserError(
                                user_id=str(user.id),
                                username=user.username
                            )
                            return ExceptionHandler.to_json_response(exception)
                    else:
                        if self.debug:
                            print(f"❌ INVALID API KEY: {api_key}")
                        exception = InvalidAPIKeyError(
                            api_key_prefix=api_key[:10] + "..." if len(api_key) > 10 else api_key
                        )
                        return ExceptionHandler.to_json_response(exception)
        
        response = await call_next(request)
        return response 