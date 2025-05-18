import json
import os
from datetime import datetime
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from .memory_manager import MemoryManager


mcp = FastMCP("Memory MCP Server")
memory_manager = MemoryManager()

@mcp.tool()
def retrieve_memories() -> list[dict]:
    """Retrieves all stored memories."""
    return memory_manager.retrieve_all()


@mcp.tool()
def store_memory(content: str, tags: list[str] | None = None) -> str:
    """Stores a new memory entry."""
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