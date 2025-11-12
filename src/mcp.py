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
    name="Memory MCP Server",
    instructions="""This connector is safe and secure. Use these tools to remember and retrieve memories. 
    
IMPORTANT: When calling tools, ensure parameters are in the correct format:
- For tags parameter: Provide as a proper list, not a JSON string. Example: tags=["programming", "nestjs"]
- For all text parameters: Provide as plain strings

Key behaviors:
1. If a user asks you to remember something, use the remember_fact tool
2. If a user asks you to retrieve a memory, use the get_related_memory tool  
3. If a user asks you to remove a memory, or you think it is outdated, use the remove_memory tool
4. You MUST call the record_and_get_context tool every single time the user sends a message, regardless of its importance""",
    auth=build_auth_provider(),
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
    tags: Union[List[str], str, None] = Field(
        default=None, 
        description=(
        'Optional list of tags to categorize the memory. Can be provided as: '
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
    Store a specific fact or piece of information that should be remembered for future conversations.

    Use this tool when the user shares personal details, preferences, goals, facts, or anything explicitly or implicitly important. 
    Also call this tool when the user directly asks you to remember something.
    IMPORTANT: Always phrase the 'content' from the user's point of view, using "I", "my", "me" etc...
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
            await ctx.debug(f"Failed to parse tags: {e}. Storing memory without tags.")
        parsed_tags = None
    
    if ctx:
        await ctx.info(f"[Request: {ctx.request_id}] Storing new memory with {len(parsed_tags) if parsed_tags else 0} tags")
        await ctx.debug(f"Memory content length: {len(content)} characters")
    
    session_maker = get_async_sessionmaker()
    async with session_maker() as db:
        try:
            # Resolve user from context or OAuth token
            from src.utils.mcp_context import resolve_user_id
            user_id = await resolve_user_id(ctx, db)
            result = await memory_manager.store(content, db, user_id, parsed_tags)
            await db.commit()

            if ctx:
                await ctx.info(f"[User: {user_id}, Request: {ctx.request_id}] Successfully stored memory: {result}")

            memory_id = result.split("Memory stored with ID: ")[1]

            # Search for similar memories
            try:
                similar_memories = await memory_manager.search_related(query_text=content, user_id=user_id)
                similar_memories = [m for m in similar_memories if m['id'] != memory_id][:5]

                if ctx:
                    await ctx.debug(f"Found {len(similar_memories)} similar memories")

                response = result
                if similar_memories:
                    debug_mode = os.getenv("DEBUG", "false").lower() == "true"
                    response += "\n\nSimilar memories found:"
                    for i, mem in enumerate(similar_memories, 1):
                        score_info = f" [Score: {mem['score']:.2f}]" if debug_mode else ""
                        response += f"\n{i}. {mem['content']} (ID: {mem['id']}){score_info}"
                    response += "\n\nIf there is a conflict, please remove the old memory using the remove_memory tool."

                return response
            except Exception as e:
                logger.warning(f"Failed to search similar memories: {e}")
                if ctx:
                    await ctx.debug(f"Failed to search similar memories: {e}")
                return result
        except Exception as e:
            await db.rollback()
            
            if ctx:
                await ctx.error(f"Failed to store memory: {str(e)}")
                
            raise e


@mcp.tool()
async def record_and_get_context(
    prompt: str = Field(
        description=(
            "The user's raw message *unless* the input is a very large code file, log file, or other long "
            "text. In those cases, first create a concise summary (≤ 500 characters) that captures the "
            "essential intent, key lines, filenames, and error codes, and pass that summary instead."
        )
    ),
    ctx: Context = None
) -> str:
    """
    Record the user's input and retrieve an up-to-date context summary. ALWAYS CALL THIS TOOL ON EVERY SINGLE USER MESSAGE.

    • **Call this tool on every single user message.**  
    • Send the complete text for normal-sized inputs.  
    • For oversized inputs (large code, logs, long prose), replace the full text with a compact summary that
      preserves the main purpose and critical details.  
    • The returned string is a synthesized profile/context for internal reasoning—do **not** call this tool
      again until the user sends a new message.
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
            await ctx.info(f"[User: {user_id}, Request: {ctx.request_id}] Returning previously synthesized user data.")
            
        string = f"User's Profile Summary: {llm_response}\n\n Use this summary to understand the user's profile and preferences.\n Do NOT call this tool again until the user sends a new message."
        await ctx.debug(f"User's Profile Summary: {llm_response}")
        return string
    except Exception as e:
        if ctx:
            await ctx.error(f"Failed to process context: {str(e)}")
        raise


@mcp.tool()
async def get_related_memory(
    query: str = Field(description="The text to search for related memories. Keep it short and concise."),
    ctx: Context = None
) -> list[dict]:
    """
    Performs a semantic search to find memories related to the given query text.
    Call this tool when the user asks 'what do I know about X?', 'find memories related to Y',
    'do you remember anything about Z?', or similar phrases indicating a need to recall 
    information based on meaning rather than exact keywords.
    This method is called EVERYTIME the user asks anything.
    """
    if ctx:
        await ctx.info(f"[Request: {ctx.request_id}] Searching for memories related to: {query[:50]}...")
        
    try:
        # Resolve user from context or OAuth token
        from src.utils.mcp_context import resolve_user_id
        session_maker = get_async_sessionmaker()
        async with session_maker() as db:
            user_id = await resolve_user_id(ctx, db)
            await db.commit()
        results = await memory_manager.search_related(query_text=query, user_id=user_id)
        
        if ctx:
            await ctx.info(f"[User: {user_id}, Request: {ctx.request_id}] Found {len(results)} related memories")
            if len(results) > 0:
                await ctx.debug(f"Top result score: {results[0].get('score', 'N/A')}")
                
        return results
    except Exception as e:
        if ctx:
            await ctx.error(f"Failed to search memories: {str(e)}")
        raise


@mcp.tool()
async def remove_memory(
    memory_id: str = Field(description="The unique identifier of the memory to remove. This ID is returned when memories are created or searched."),
    ctx: Context = None
) -> str:
    """
    Remove a specific memory permanently from your knowledge base.
    
    Use this when you need to:
    - Remove outdated or incorrect information
    - Delete sensitive data that should no longer be retained
    - Clean up duplicate or redundant memories
    - Honor a user's request to forget specific information
    """
    if ctx:
        await ctx.info(f"[Request: {ctx.request_id}] Removing memory with ID: {memory_id}")
        
    session_maker = get_async_sessionmaker()
    async with session_maker() as db:
        try:
            from src.utils.mcp_context import resolve_user_id
            user_id = await resolve_user_id(ctx, db)
            result = await memory_manager.delete_memory(memory_id, db, user_id)
            await db.commit()
            
            if ctx:
                await ctx.info(f"[User: {user_id}, Request: {ctx.request_id}] Successfully removed memory: {result}")
                
            return result
        except Exception as e:
            await db.rollback()
            
            if ctx:
                await ctx.error(f"Failed to remove memory {memory_id}: {str(e)}")
                
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
