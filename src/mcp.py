from fastmcp import FastMCP, Context
from pydantic import Field
from typing import Optional, List, Union
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.middleware import Middleware
from src.memory_manager import MemoryManager
from src.db import init_db
from src.db.database import get_async_sessionmaker
from src.middlewares import MCPPathAuthMiddleware, MCPOAuthHintMiddleware, MCPOAuthRedirectMiddleware
from src.core.mcp_auth_provider import build_auth_provider
from src.utils.tag_parser import parse_tags_input
import logging
import os

logger = logging.getLogger(__name__)


# Initialize the database
init_db()

mcp = FastMCP(
    name="Data Storage Connector",
    instructions="""Use these tools to store and retrieve information.

IMPORTANT: When calling tools, ensure parameters are in the correct format:
- For tags parameter: Provide as a proper list, not a JSON string. Example: tags=["programming", "nestjs"]
- For all text parameters: Provide as plain strings

Key behaviors:
1. To store information, use the store_item tool
2. To retrieve stored information, use the search_items tool
3. To remove stored information, use the delete_item tool
4. Call the get_context tool on every user message to retrieve relevant context""",
    auth=build_auth_provider(),
)
memory_manager = MemoryManager()

@mcp.tool()
async def store_item(
    content: str = Field(
        description=(
            "The text content to store for later retrieval. "
            "Use first-person phrasing when appropriate. "
            "Example: 'I prefer using TypeScript' instead of 'The user prefers TypeScript'."
        )
    ),
    tags: Union[List[str], str, None] = Field(
        default=None,
        description=(
        'Optional list of tags for categorization. Can be provided as: '
        '1) A list: ["work", "project", "deadline"] '
        '2) A JSON string: \'["work", "project", "deadline"]\' '
        '3) Comma-separated: "work, project, deadline" '
        '4) Single tag: "work" '
        'Maximum 3 tags.'
        )
    ),
    ctx: Context = None
) -> str:
    """
    Store a piece of information for later retrieval.

    Use this tool to store information that may be useful in future interactions.
    """
    # Parse and validate tags using the helper function with error handling
    try:
        parsed_tags = parse_tags_input(tags)
        
        if ctx:
            await ctx.debug(f"Original tags input: {tags} (type: {type(tags).__name__})")
            await ctx.debug(f"Parsed tags: {parsed_tags}")
        
        # Enforce maximum 3 tags limit
        if parsed_tags and len(parsed_tags) > 3:
            parsed_tags = parsed_tags[:3]
            if ctx:
                await ctx.debug(f"Truncated tags to first 3: {parsed_tags}")
                
    except Exception as e:
        logger.warning(f"Failed to parse tags, continuing without tags. Error: {e}")
        if ctx:
            await ctx.debug(f"Failed to parse tags: {e}. Storing item without tags.")
        parsed_tags = None
    
    if ctx:
        await ctx.info(f"[Request: {ctx.request_id}] Storing new item with {len(parsed_tags) if parsed_tags else 0} tags")
        await ctx.debug(f"Content length: {len(content)} characters")
    
    session_maker = get_async_sessionmaker()
    async with session_maker() as db:
        try:
            # Resolve user from context or OAuth token
            from src.utils.mcp_context import resolve_user_id
            user_id = await resolve_user_id(ctx, db)
            result = await memory_manager.store(content, db, user_id, parsed_tags)
            await db.commit()

            if ctx:
                await ctx.info(f"[User: {user_id}, Request: {ctx.request_id}] Successfully stored item: {result}")

            memory_id = result.split("Memory stored with ID: ")[1]

            # Search for similar items
            try:
                similar_memories = await memory_manager.search_related(query_text=content, user_id=user_id)
                similar_memories = [m for m in similar_memories if m['id'] != memory_id][:5]

                if ctx:
                    await ctx.debug(f"Found {len(similar_memories)} similar items")

                response = result
                if similar_memories:
                    debug_mode = os.getenv("DEBUG", "false").lower() == "true"
                    response += "\n\nSimilar items found:"
                    for i, mem in enumerate(similar_memories, 1):
                        score_info = f" [Score: {mem['score']:.2f}]" if debug_mode else ""
                        response += f"\n{i}. {mem['content']} (ID: {mem['id']}){score_info}"
                    response += "\n\nIf there is a conflict, consider removing the old item using the delete_item tool."

                return response
            except Exception as e:
                logger.warning(f"Failed to search similar items: {e}")
                if ctx:
                    await ctx.debug(f"Failed to search similar items: {e}")
                return result
        except Exception as e:
            await db.rollback()

            if ctx:
                await ctx.error(f"Failed to store item: {str(e)}")

            raise e


@mcp.tool()
async def get_context(
    prompt: str = Field(
        description=(
            "The user's message text. For very large inputs (code files, logs), "
            "provide a concise summary (≤ 500 characters) capturing the essential intent, "
            "key details, filenames, and error codes."
        )
    ),
    ctx: Context = None
) -> str:
    """
    Retrieve contextual information based on the user's message. Call this tool on every user message.

    • Call this tool on every single user message.
    • Send the complete text for normal-sized inputs.
    • For oversized inputs (large code, logs), provide a compact summary that preserves the main purpose and critical details.
    • The returned string provides context for the current interaction. Do not call this tool again until the user sends a new message.
    """
    if ctx:
        await ctx.info(f"[Request: {ctx.request_id}] Processing user context from message")
    
    try:
        # Resolve user from context or OAuth token
        from src.utils.mcp_context import resolve_user_id
        session_maker = get_async_sessionmaker()
        async with session_maker() as db:
            user_id = await resolve_user_id(ctx, db)
            await db.commit()
        llm_response = await memory_manager.process_context(prompt, user_id)

        if ctx:
            await ctx.info(f"[User: {user_id}, Request: {ctx.request_id}] Returning synthesized context data.")

        string = f"Context Summary: {llm_response}\n\nUse this summary to inform your responses.\nDo NOT call this tool again until the user sends a new message."
        await ctx.debug(f"Context Summary: {llm_response}")
        return string
    except Exception as e:
        if ctx:
            await ctx.error(f"Failed to process context: {str(e)}")
        raise


@mcp.tool()
async def search_items(
    query: str = Field(description="The search query text. Keep it short and concise."),
    ctx: Context = None
) -> list[dict]:
    """
    Perform a semantic search to find stored items related to the given query text.
    Call this tool when the user asks 'what do I know about X?', 'find information about Y',
    or similar phrases indicating a need to search for stored information.
    """
    if ctx:
        await ctx.info(f"[Request: {ctx.request_id}] Searching for items related to: {query[:50]}...")

    try:
        # Resolve user from context or OAuth token
        from src.utils.mcp_context import resolve_user_id
        session_maker = get_async_sessionmaker()
        async with session_maker() as db:
            user_id = await resolve_user_id(ctx, db)
            await db.commit()
        results = await memory_manager.search_related(query_text=query, user_id=user_id)

        if ctx:
            await ctx.info(f"[User: {user_id}, Request: {ctx.request_id}] Found {len(results)} related items")
            if len(results) > 0:
                await ctx.debug(f"Top result score: {results[0].get('score', 'N/A')}")

        return results
    except Exception as e:
        if ctx:
            await ctx.error(f"Failed to search items: {str(e)}")
        raise


@mcp.tool()
async def delete_item(
    item_id: str = Field(description="The unique identifier of the item to delete. This ID is returned when items are created or searched."),
    ctx: Context = None
) -> str:
    """
    Delete a specific stored item by its unique identifier.

    Use this when you need to:
    - Remove outdated or incorrect information
    - Clean up duplicate or redundant items
    - Honor a user's request to delete specific information
    """
    if ctx:
        await ctx.info(f"[Request: {ctx.request_id}] Deleting item with ID: {item_id}")

    session_maker = get_async_sessionmaker()
    async with session_maker() as db:
        try:
            from src.utils.mcp_context import resolve_user_id
            user_id = await resolve_user_id(ctx, db)
            result = await memory_manager.delete_memory(item_id, db, user_id)
            await db.commit()

            if ctx:
                await ctx.info(f"[User: {user_id}, Request: {ctx.request_id}] Successfully deleted item: {result}")

            return result
        except Exception as e:
            await db.rollback()

            if ctx:
                await ctx.error(f"Failed to delete item {item_id}: {str(e)}")

            raise e


@mcp.custom_route("/health", methods=["GET"])
async def health_check(_: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")


# Create the ASGI app with middleware
mcp_app = mcp.http_app(
    path="/mcp",
    middleware=[
        Middleware(MCPOAuthRedirectMiddleware),
        Middleware(MCPOAuthHintMiddleware),
        Middleware(MCPPathAuthMiddleware)
    ]
)
