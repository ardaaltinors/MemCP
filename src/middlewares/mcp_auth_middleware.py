import os
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from src.db.database import SessionLocal
from src.crud.crud_user import get_user_by_api_key
from src.core.context import set_current_user_id


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
                
                # Validate API key against database
                db = SessionLocal()
                try:
                    user = get_user_by_api_key(db, api_key)
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
                            return JSONResponse(
                                status_code=403,
                                content={"error": "User account is inactive"}
                            )
                    else:
                        if self.debug:
                            print(f"❌ INVALID API KEY: {api_key}")
                        return JSONResponse(
                            status_code=401,
                            content={"error": "Invalid API key"}
                        )
                finally:
                    db.close()
        
        response = await call_next(request)
        return response 