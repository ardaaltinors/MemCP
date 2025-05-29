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
def remember_fact(content: str, tags: list[str] | None = None) -> str:
    """
    Store a specific fact or piece of information that should be remembered for future conversations.
    
    Use this tool when the user shares personal details, preferences, goals, facts, or anything explicitly or implicitly important. 
    Also call this tool when the user directly asks you to remember something.

    Args:
        content: The content or fact to be remembered.
        tags: Optional tags to help categorize the memory.
    """
    return memory_manager.store(content, tags)


# TODO: Bu tool ayni zamanda kullanicinin summary sini de dondurecek sekilde yapilacak.
@mcp.tool()
def record_and_get_context(prompt: str) -> str:
    """ALWAYS CALL THIS TOOL. 
    
    You MUST call this tool every single time the user sends a message, regardless of its importance.
    This ensures that all interactions are recorded as context for future reasoning.

    Args:
        prompt: The user's raw input message.
    """
    
    return memory_manager.process_context(prompt)


@mcp.tool()
def get_related_memory(query: str) -> list[dict]:
    """
    Performs a semantic search to find memories related to the given query text.
    Call this tool when the user asks 'what do I know about X?', 'find memories related to Y',
    'do you remember anything about Z?', or similar phrases indicating a need to recall 
    information based on meaning rather than exact keywords.
    This method is called EVERYTIME the user asks anything.

    Args:
        query: The text to search for related memories.
    """
    return memory_manager.search_related(query_text=query)


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