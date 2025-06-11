from dotenv import load_dotenv
import logging
import signal
import sys

load_dotenv()

import uvicorn
from fastapi import FastAPI
import threading
from contextlib import asynccontextmanager
from src.mcp import mcp_app
from src.routers import auth
from src.core.config import MCP_SERVER_HOST, MCP_SERVER_PORT
from src.exceptions import MemoryMCPException
from src.exceptions.handlers import handle_memory_mcp_exception
from src.utils.health import perform_full_health_check
from src.db.database import dispose_all_engines
import os

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper(), 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global reference to the MCP server thread and shutdown event
mcp_thread = None
mcp_shutdown_event = threading.Event()
mcp_server = None

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

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Import and include memory router
from src.routers import memory
app.include_router(memory.router, prefix="/memories", tags=["Memories"])

@app.get("/health")
async def health_check():
    """
    Main health check endpoint.
    Returns comprehensive system status.
    """
    try:
        return perform_full_health_check()
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "error": str(e),
            "services": {}
        }

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
