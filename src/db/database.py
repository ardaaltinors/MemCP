import asyncio
from typing import AsyncGenerator, Generator, Dict
import weakref
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine,
)

from src.core.config import ASYNC_DATABASE_URL, DATABASE_URL

# Configure logger for database operations
logger = logging.getLogger(__name__)

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
        # No event loop running, create a simple engine for sync usage
        logger.warning("No event loop running, creating simple engine")
        return create_async_engine(ASYNC_DATABASE_URL, echo=True)
    
    if loop not in _async_engines:
        # Create a new engine for this event loop
        logger.info(f"Creating new async engine for event loop {id(loop)}")
        engine = create_async_engine(
            ASYNC_DATABASE_URL, 
            echo=True,
            # Optimized pool settings per event loop
            pool_size=5,        # Smaller pool per loop
            max_overflow=10,    # Additional connections when needed
            pool_timeout=30,    # Wait time for connection
            pool_recycle=1800,  # Recycle connections every 30 minutes
            pool_pre_ping=True, # Verify connections before use
            connect_args={
                "server_settings": {
                    "application_name": f"memory_mcp_loop_{id(loop)}",
                },
                "command_timeout": 60,  # Prevent hanging connections
            }
        )
        _async_engines[loop] = engine
        
        # Create sessionmaker for this loop with configurable options
        session_maker = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            # These settings can be overridden for specific use cases like migrations
            autocommit=False,  # Explicit transaction control
            autoflush=False,   # Manual flush control for better performance
        )
        _async_sessionmakers[loop] = session_maker
        logger.info(f"Created sessionmaker for event loop {id(loop)}")
    
    return _async_engines[loop]

def get_async_sessionmaker() -> async_sessionmaker:
    """Get the async sessionmaker for the current event loop."""
    get_async_engine()  # Ensure engine exists first
    try:
        loop = asyncio.get_running_loop()
        return _async_sessionmakers[loop]
    except RuntimeError:
        logger.error("No event loop running when trying to get sessionmaker")
        raise

# --- Session Dependencies ---

# Sync session dependency (for Alembic, etc.)
def get_sync_db() -> Generator[Session, None, None]:
    """Synchronous database session dependency."""
    db = SyncSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# Async session dependency
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for async database sessions.
    Uses per-event-loop sessionmaker to prevent cross-loop contamination.
    """
    session_maker = get_async_sessionmaker()
    session = None
    try:
        session = session_maker()
        yield session
        await session.commit()
    except asyncio.CancelledError:
        logger.warning("Database session cancelled, rolling back")
        if session:
            await session.rollback()
        raise
    except Exception as e:
        logger.error(f"Database session error: {e}", exc_info=True)
        if session:
            await session.rollback()
        raise
    finally:
        if session:
            await session.close()

# --- Cleanup Functions ---

async def dispose_async_engine():
    """Dispose of the async engine for the current event loop."""
    try:
        loop = asyncio.get_running_loop()
        if loop in _async_engines:
            engine = _async_engines[loop]
            logger.info(f"Disposing async engine for event loop {id(loop)}")
            await engine.dispose()
            del _async_engines[loop]
            if loop in _async_sessionmakers:
                del _async_sessionmakers[loop]
            logger.info(f"Successfully disposed engine for event loop {id(loop)}")
    except RuntimeError:
        logger.warning("No event loop running during engine disposal")

async def dispose_all_engines():
    """
    Dispose of all engines across all event loops.
    Used during application shutdown.
    """
    if not _async_engines:
        logger.info("No engines to dispose")
        return
        
    logger.info(f"Disposing {len(_async_engines)} async engines")
    engines_to_dispose = list(_async_engines.values())
    
    disposed_count = 0
    error_count = 0
    
    for engine in engines_to_dispose:
        try:
            await engine.dispose()
            disposed_count += 1
            logger.debug(f"Disposed engine {id(engine)}")
        except Exception as e:
            error_count += 1
            logger.error(f"Error disposing engine {id(engine)}: {e}", exc_info=True)
    
    # Clear the dictionaries
    _async_engines.clear()
    _async_sessionmakers.clear()
    
    logger.info(f"Engine disposal complete: {disposed_count} successful, {error_count} errors")

# --- Configuration Functions for Special Cases ---

def create_migration_sessionmaker() -> async_sessionmaker:
    """
    Create a sessionmaker with migration-specific settings.
    Uses autocommit=True and autoflush=True for migration scripts.
    """
    engine = get_async_engine()
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=True,   # Auto-commit for migration operations
        autoflush=True,    # Auto-flush for immediate changes
    )

# --- Database Models Base ---
Base = declarative_base() 