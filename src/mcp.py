import json
import os
from datetime import datetime
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.middleware import Middleware
from src.memory_manager import MemoryManager
from src.db import init_db
from src.db.database import get_async_sessionmaker
from src.middlewares import UserCredentialMiddleware


# Initialize the database
init_db()

mcp = FastMCP("Memory MCP Server")
memory_manager = MemoryManager()

@mcp.tool()
async def remember_fact(content: str, tags: list[str] | None = None) -> str:
    """
    Store a specific fact or piece of information that should be remembered for future conversations.
    
    Use this tool when the user shares personal details, preferences, goals, facts, or anything explicitly or implicitly important. 
    Also call this tool when the user directly asks you to remember something.

    Args:
        content: The content or fact to be remembered.
        tags: Optional tags to help categorize the memory.
    """
    session_maker = get_async_sessionmaker()
    async with session_maker() as db:
        try:
            result = await memory_manager.store(content, db, tags)
            await db.commit()  # Explicitly commit the transaction
            return result
        except Exception as e:
            await db.rollback()  # Rollback on error
            raise e


@mcp.tool()
async def record_and_get_context(prompt: str) -> str:
    """
    You MUST call this tool every single time the user sends a message, regardless of its importance.
    This ensures that all interactions are recorded as context for future reasoning.

    Args:
        prompt: The user's raw input message.
    """
    llm_response = await memory_manager.process_context(prompt)
    string = f"User's Profile Summary: {llm_response}\n\n Use this summary to understand the user's profile and preferences.\n Do NOT call this tool again until the user sends a new message."
    return string


@mcp.tool()
async def get_related_memory(query: str) -> list[dict]:
    """
    Performs a semantic search to find memories related to the given query text.
    Call this tool when the user asks 'what do I know about X?', 'find memories related to Y',
    'do you remember anything about Z?', or similar phrases indicating a need to recall 
    information based on meaning rather than exact keywords.
    This method is called EVERYTIME the user asks anything.

    Args:
        query: The text to search for related memories.
    """
    return await memory_manager.search_related(query_text=query)


@mcp.tool()
async def remove_memory(memory_id: str) -> str:
    """
    Remove a specific memory permanently from your knowledge base.
    
    This tool deletes a memory from both the vector database (Qdrant) and 
    the relational database (PostgreSQL), ensuring complete removal.
    
    Use this when you need to:
    - Remove outdated or incorrect information
    - Delete sensitive data that should no longer be retained
    - Clean up duplicate or redundant memories
    - Honor a user's request to forget specific information
    
    Args:
        memory_id: The unique identifier of the memory to remove.
                   This ID is returned when memories are created or searched.
    
    Returns:
        A confirmation message indicating successful deletion.
    
    Note: This action is permanent and cannot be undone. The memory will be 
    completely removed from all storage systems.
    """
    session_maker = get_async_sessionmaker()
    async with session_maker() as db:
        try:
            result = await memory_manager.delete_memory(memory_id, db)
            await db.commit()
            return result
        except Exception as e:
            await db.rollback()
            raise e


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")


# Create the ASGI app with middleware
mcp_app = mcp.http_app(
    path="/mcp",
    middleware=[
        Middleware(UserCredentialMiddleware)
    ]
)