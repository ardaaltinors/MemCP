from dotenv import load_dotenv
import logging

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
import os

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper(), 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Function to run the MCP server
def run_mcp_server():
    try:
        uvicorn.run(
            mcp_app,
            host=MCP_SERVER_HOST,
            port=MCP_SERVER_PORT,
            log_level="debug",
        )
    except Exception as e:
        logger.error(f"MCP server encountered an error: {e}", exc_info=True)
    finally:
        logger.info("MCP server has shut down.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for FastAPI application.
    Starts the MCP server in a separate daemon thread on startup.
    """
    mcp_thread = threading.Thread(target=run_mcp_server, daemon=True)
    mcp_thread.start()
    logger.info("MCP server has been initiated in a background thread.")
    yield
    logger.info("FastAPI application shutting down...")

app = FastAPI(lifespan=lifespan)

# Add exception handlers
app.add_exception_handler(MemoryMCPException, handle_memory_mcp_exception)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Import and include memory router
from src.routers import memory
app.include_router(memory.router, prefix="/memories", tags=["Memories"])

@app.get("/")
async def health_check():
    """
    Health check endpoint that verifies the status of all services:
    PostgreSQL, Qdrant, RabbitMQ, Redis, and Celery workers.
    """
    return perform_full_health_check()

if __name__ == "__main__":
    uvicorn.run(app, host=MCP_SERVER_HOST, port=8000)
