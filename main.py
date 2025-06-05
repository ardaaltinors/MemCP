from dotenv import load_dotenv
import logging

load_dotenv()

import uvicorn
from fastapi import FastAPI, HTTPException
import threading
from contextlib import asynccontextmanager
from src.mcp import mcp_app
from src.db.database import engine
from src.routers import auth
from src.core.config import MCP_SERVER_HOST, MCP_SERVER_PORT
from qdrant_client import QdrantClient
from sqlalchemy import text
import os
from src.exceptions import MemoryMCPException, ServiceUnavailableError
from src.exceptions.handlers import handle_memory_mcp_exception

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

# Include the authentication router
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])

@app.get("/")
async def health_check():
    """
    Health check endpoint that verifies the status of PostgreSQL and Qdrant services.
    """
    status = {
        "status": "healthy",
        "services": {
            "postgres": {"status": "unknown", "details": ""},
            "qdrant": {"status": "unknown", "details": ""}
        },
        "timestamp": None
    }
    
    from datetime import datetime, timezone
    status["timestamp"] = datetime.now(timezone.utc).isoformat()
    
    # Check PostgreSQL
    try:
        with engine.connect() as connection:
            # Simple query to test connection
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
            status["services"]["postgres"]["status"] = "healthy"
            status["services"]["postgres"]["details"] = "Connection successful"
    except Exception as e:
        status["services"]["postgres"]["status"] = "unhealthy"
        status["services"]["postgres"]["details"] = f"Connection failed: {str(e)}"
        status["status"] = "degraded"
    
    # Check Qdrant
    try:
        qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
        
        client = QdrantClient(host=qdrant_host, port=qdrant_port)
        client.get_collections() # This will raise an error if not connected
        status["services"]["qdrant"]["status"] = "healthy"
        status["services"]["qdrant"]["details"] = "Connection successful, able to list collections."
    except Exception as e:
        status["services"]["qdrant"]["status"] = "unhealthy"
        status["services"]["qdrant"]["details"] = f"Connection failed: {str(e)}"
        if status["status"] == "healthy":
            status["status"] = "degraded"
        elif status["status"] == "degraded":
            status["status"] = "unhealthy"
    
    # Determine overall status
    if (status["services"]["postgres"]["status"] == "unhealthy" and 
        status["services"]["qdrant"]["status"] == "unhealthy"):
        status["status"] = "unhealthy"
        # If both are unhealthy, raise 503 immediately
        raise ServiceUnavailableError(
            message="All critical services are unavailable",
            service_name="postgres,qdrant"
        ) 
    elif (status["services"]["postgres"]["status"] == "unhealthy" or 
          status["services"]["qdrant"]["status"] == "unhealthy"):
        status["status"] = "degraded"
        # If one is unhealthy, still return 200 but with degraded status
    
    return status

if __name__ == "__main__":
    uvicorn.run(app, host=MCP_SERVER_HOST, port=8000)
