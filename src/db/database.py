import asyncio
from typing import AsyncGenerator, Generator, Dict
import weakref

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine,
)

from src.core.config import ASYNC_DATABASE_URL, DATABASE_URL

# --- Synchronous Setup (for Alembic, etc.) ---
sync_engine = create_engine(DATABASE_URL, echo=True)
SyncSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=sync_engine
)

# --- Asynchronous Setup (per event loop) ---
# Store engines per event loop to prevent cross-loop contamination
_async_engines: Dict[asyncio.AbstractEventLoop, AsyncEngine] = weakref.WeakKeyDictionary()
_async_sessionmakers: Dict[asyncio.AbstractEventLoop, async_sessionmaker] = weakref.WeakKeyDictionary()

def get_async_engine() -> AsyncEngine:
    """
    Get or create an async engine for the current event loop.
    This prevents cross-loop contamination between different threads/servers.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No event loop running, create a basic engine (shouldn't happen in async context)
        return create_async_engine(ASYNC_DATABASE_URL, echo=True)
    
    if loop not in _async_engines:
        # Create a new engine for this event loop
        engine = create_async_engine(
            ASYNC_DATABASE_URL, 
            echo=True,
            # Connection pool settings optimized for per-loop usage
            pool_size=5,  # Smaller pool per loop
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,  # Recycle connections every 30 minutes
            pool_pre_ping=True,  # Verify connections before use
            # Asyncpg-specific settings
            connect_args={
                "server_settings": {
                    "application_name": f"memory_mcp_loop_{id(loop)}",
                },
                "command_timeout": 60,
            }
        )
        _async_engines[loop] = engine
        
        # Create sessionmaker for this loop
        session_maker = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        _async_sessionmakers[loop] = session_maker
    
    return _async_engines[loop]

def get_async_sessionmaker() -> async_sessionmaker:
    """Get the async sessionmaker for the current event loop."""
    # Ensure engine exists first
    get_async_engine()
    loop = asyncio.get_running_loop()
    return _async_sessionmakers[loop]

# Legacy compatibility - these will use the current event loop's engine
def get_legacy_async_engine() -> AsyncEngine:
    """Legacy function for backward compatibility."""
    return get_async_engine()

def get_legacy_sessionmaker() -> async_sessionmaker:
    """Legacy function for backward compatibility."""
    return get_async_sessionmaker()

# For backward compatibility, create module-level references
async_engine = get_legacy_async_engine
AsyncSessionLocal = get_legacy_sessionmaker

Base = declarative_base()


# --- Engine Management ---
async def dispose_async_engine():
    """Properly dispose of the async engine for the current event loop."""
    try:
        loop = asyncio.get_running_loop()
        if loop in _async_engines:
            engine = _async_engines[loop]
            await engine.dispose()
            # Remove from cache
            del _async_engines[loop]
            if loop in _async_sessionmakers:
                del _async_sessionmakers[loop]
    except RuntimeError:
        # No event loop running
        pass

async def dispose_all_engines():
    """Dispose of all engines across all event loops."""
    engines_to_dispose = list(_async_engines.values())
    for engine in engines_to_dispose:
        try:
            await engine.dispose()
        except Exception as e:
            print(f"Error disposing engine: {e}")
    
    _async_engines.clear()
    _async_sessionmakers.clear()


# --- Dependencies ---
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a synchronous database session.
    Primarily for use with Alembic or synchronous scripts.
    """
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides an async database session with proper cleanup.
    Uses the event-loop-specific sessionmaker to prevent cross-loop issues.
    """
    session_maker = get_async_sessionmaker()
    session = None
    try:
        session = session_maker()
        yield session
        await session.commit()
    except asyncio.CancelledError:
        if session:
            await session.rollback()
        raise
    except Exception:
        if session:
            await session.rollback()
        raise
    finally:
        if session:
            await session.close() 