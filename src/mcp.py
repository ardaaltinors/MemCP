from fastmcp import FastMCP
from pydantic import Field
from typing import Optional, List
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.middleware import Middleware
from src.memory_manager import MemoryManager
from src.db import init_db
from src.db.database import get_async_sessionmaker
from src.middlewares import UserCredentialMiddleware


# Initialize the database
init_db()

mcp = FastMCP(
    name="Memory MCP Server",
    instructions="Use these tools to remember and retrieve memories.If a user asks you to remember something, use the remember_fact tool. If a user asks you to retrieve a memory, use the get_related_memory tool. If a user asks you to remove a memory, or you think it is outdated, use the remove_memory tool. You MUST call the record_and_get_context tool every single time the user sends a message, regardless of its importance.",
    tags={"memory", "memcp", "memorize", "remember"}
)
memory_manager = MemoryManager()

@mcp.tool()
async def remember_fact(
    content: str = Field(
        description=(
            "The specific fact or piece of information to be remembered, written from the user's "
            "first-person perspective. It should sound as if the user said it themselves. "
            "For example, use 'I don't like OpenAI' instead of 'The user does not like OpenAI'."
        )
    ),
    tags: Optional[List[str]] = Field(
        default=None, 
        description="Optional tags to help categorize the memory. Max 3 tags.", 
        max_length=3
    )
) -> str:
    """
    Store a specific fact or piece of information that should be remembered for future conversations.

    Use this tool when the user shares personal details, preferences, goals, facts, or anything explicitly or implicitly important. 
    Also call this tool when the user directly asks you to remember something.
    IMPORTANT: Always phrase the 'content' from the user's point of view, using "I", "my", "me" etc...
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
async def record_and_get_context(
    prompt: str = Field(description="The user's raw input message.")
) -> str:
    """
    You MUST call this tool every single time the user sends a message, regardless of its importance.
    This ensures that all interactions are recorded as context for future reasoning.
    """
    llm_response = await memory_manager.process_context(prompt)
    string = f"User's Profile Summary: {llm_response}\n\n Use this summary to understand the user's profile and preferences.\n Do NOT call this tool again until the user sends a new message."
    return string


@mcp.tool()
async def get_related_memory(
    query: str = Field(description="The text to search for related memories. Keep it short and concise.")
) -> list[dict]:
    """
    Performs a semantic search to find memories related to the given query text.
    Call this tool when the user asks 'what do I know about X?', 'find memories related to Y',
    'do you remember anything about Z?', or similar phrases indicating a need to recall 
    information based on meaning rather than exact keywords.
    This method is called EVERYTIME the user asks anything.
    """
    return await memory_manager.search_related(query_text=query)


@mcp.tool()
async def remove_memory(
    memory_id: str = Field(description="The unique identifier of the memory to remove. This ID is returned when memories are created or searched.")
) -> str:
    """
    Remove a specific memory permanently from your knowledge base.
    
    Use this when you need to:
    - Remove outdated or incorrect information
    - Delete sensitive data that should no longer be retained
    - Clean up duplicate or redundant memories
    - Honor a user's request to forget specific information
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