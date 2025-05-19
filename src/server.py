import json
import os
from datetime import datetime
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from src.memory_manager import MemoryManager
from src.db import init_db


# Initialize the database
init_db()

mcp = FastMCP("Memory MCP Server")
memory_manager = MemoryManager()

@mcp.tool()
def retrieve_memories() -> list[dict]:
    """Retrieves all stored memories."""
    return memory_manager.retrieve_all()


@mcp.tool()
def add_memory(content: str, tags: list[str] | None = None) -> str:
    """Adds a new memory entry. This tool should be called when the user provides new information that should be stored in the memory. 
    Definitely call this tool when the user says "remember that", "remember this", "save to memory", "store in memory", "add to memory", "make a note", "remember for later", "keep track of". You can also call this tool if you think you will need to remember something for later.
    
    Args:
        content: The content of the memory.
        tags: The tags of the memory.
    """
    return memory_manager.store(content, tags)


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=4200,
        path="/mcp",
        log_level="debug",
    )