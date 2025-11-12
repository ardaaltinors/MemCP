from dotenv import load_dotenv
import logging
import signal
import sys
from datetime import datetime, timezone

load_dotenv()

import uvicorn
from fastapi import FastAPI
import threading
from contextlib import asynccontextmanager
from src.mcp import mcp_app
from src.routers import auth
from src.routers import oauth as oauth_router
from src.core.config import MCP_SERVER_HOST, MCP_SERVER_PORT
from src.exceptions import MemoryMCPException
from src.exceptions.handlers import handle_memory_mcp_exception
from src.utils.health import perform_full_health_check
from src.db.database import dispose_all_engines
import os
from starlette.middleware.sessions import SessionMiddleware
from src.core.security import SECRET_KEY as AUTH_SECRET_KEY

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper(), 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global reference to the MCP server thread and shutdown event
mcp_thread = None
mcp_shutdown_event = threading.Event()
mcp_server = None

# Track server start time
server_start_time = None

# Function to run the MCP server
def run_mcp_server():
    global mcp_server
    try:
        # Create server configuration
        config = uvicorn.Config(
            mcp_app,
            host=MCP_SERVER_HOST,
            port=MCP_SERVER_PORT,
            log_level="info"
        )
        mcp_server = uvicorn.Server(config)
        
        # Run the server
        mcp_server.run()
    except Exception as e:
        logger.error(f"MCP server failed to start: {e}", exc_info=True)
        raise
    finally:
        logger.info("MCP server thread exiting")

async def shutdown_mcp_server():
    """Gracefully shutdown the MCP server."""
    global mcp_server
    if mcp_server:
        logger.info("Signaling MCP server to shutdown...")
        mcp_server.should_exit = True
        mcp_shutdown_event.set()

async def graceful_shutdown():
    """Perform graceful shutdown operations."""
    logger.info("Starting graceful shutdown...")
    
    try:
        # Dispose of all database engines
        await dispose_all_engines()
        logger.info("Database engines disposed successfully.")
    except Exception as e:
        logger.error(f"Error disposing database engines: {e}", exc_info=True)
    
    # Additional cleanup can be added here
    logger.info("Graceful shutdown completed.")

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, initiating shutdown...")
    # Signal MCP server to shutdown
    if mcp_server:
        mcp_server.should_exit = True
    mcp_shutdown_event.set()
    # For sync signal handlers, we need to handle async cleanup differently
    # This will be handled by the lifespan context manager
    sys.exit(0)

# Register signal handlers for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Termination signal

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    Handles MCP server startup and graceful cleanup.
    """
    global mcp_thread
    
    # Startup
    logger.info("FastAPI application starting up...")

    # Log environment configuration
    logger.info(f"[CONFIG] ENVIRONMENT: {os.getenv('ENVIRONMENT') or 'NOT SET'}")
    logger.info(f"[CONFIG] LOG_LEVEL: {os.getenv('LOG_LEVEL') or 'NOT SET (using INFO)'}")
    logger.info(f"[CONFIG] DEBUG: {os.getenv('DEBUG') or 'NOT SET (using false)'}")

    # Record server start time
    global server_start_time
    server_start_time = datetime.now(timezone.utc)
    
    try:
        # Start MCP server thread
        mcp_thread = threading.Thread(target=run_mcp_server, daemon=False)
        mcp_thread.start()
        logger.info("MCP server has been initiated in a non-daemon background thread.")
        
        # Wait a bit to ensure server starts
        import time
        time.sleep(2)
        
        # Verify MCP server started successfully
        if mcp_thread.is_alive():
            logger.info("MCP server thread is running successfully.")
        else:
            logger.error("MCP server thread failed to start properly.")
            
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}", exc_info=True)
        raise
    
    # Application is ready
    logger.info("FastAPI application startup completed.")
    
    yield
    
    # Shutdown
    logger.info("FastAPI application shutting down...")
    try:
        # First shutdown MCP server
        await shutdown_mcp_server()
        
        # Wait for MCP thread to finish with timeout
        if mcp_thread and mcp_thread.is_alive():
            logger.info("Waiting for MCP server thread to finish...")
            mcp_thread.join(timeout=30)
            
            if mcp_thread.is_alive():
                logger.warning("MCP server thread did not finish within timeout")
            else:
                logger.info("MCP server thread finished successfully")
        
        # Then perform other shutdown operations
        await graceful_shutdown()
    except Exception as e:
        logger.error(f"Error during graceful shutdown: {e}", exc_info=True)
    
    logger.info("FastAPI application shutdown completed.")

# Create the FastAPI app with lifespan management
app = FastAPI(
    title="Memory MCP API",
    description="Long-term memory management system for AI assistants",
    version="1.0.0",
    lifespan=lifespan
)

# Add exception handlers
app.add_exception_handler(MemoryMCPException, handle_memory_mcp_exception)

# Add session middleware for OAuth state handling
app.add_middleware(SessionMiddleware, secret_key=AUTH_SECRET_KEY)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(oauth_router.router)

# Import and include memory router
from src.routers import memory
app.include_router(memory.router, prefix="/memories", tags=["Memories"])

@app.get("/health")
async def health_check():
    """
    Main health check endpoint.
    Returns comprehensive system status with uptime.
    """
    try:
        health_status = perform_full_health_check()
        
        # Calculate uptime if server has started
        if server_start_time:
            current_time = datetime.now(timezone.utc)
            uptime_seconds = (current_time - server_start_time).total_seconds()
            
            # Format uptime in a human-readable format
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            seconds = int(uptime_seconds % 60)
            
            uptime_formatted = ""
            if days > 0:
                uptime_formatted += f"{days}d "
            if hours > 0 or days > 0:
                uptime_formatted += f"{hours}h "
            if minutes > 0 or hours > 0 or days > 0:
                uptime_formatted += f"{minutes}m "
            uptime_formatted += f"{seconds}s"
            
            health_status["uptime"] = {
                "seconds": uptime_seconds,
                "formatted": uptime_formatted.strip(),
                "start_time": server_start_time.isoformat()
            }
        else:
            health_status["uptime"] = {
                "seconds": 0,
                "formatted": "0s",
                "start_time": None
            }
            
        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "error": str(e),
            "services": {},
            "uptime": {
                "seconds": 0,
                "formatted": "0s",
                "start_time": None
            }
        }

@app.get("/healthcheck")
async def health_check_alias():
    """
    Alias for /health endpoint for compatibility.
    Returns comprehensive system status with uptime.
    """
    return await health_check()

@app.get("/ping")
async def ping():
    """Simple ping endpoint for basic availability checks."""
    return {"status": "ok", "message": "pong"}

if __name__ == "__main__":
    # This will only run if the script is executed directly (not via uvicorn command)
    logger.info("Starting Memory MCP server directly...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Set to True for development
        log_level="info"
    )
