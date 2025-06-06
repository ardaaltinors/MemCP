import asyncio
from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)

from src.core.config import ASYNC_DATABASE_URL, DATABASE_URL

# --- Synchronous Setup (for Alembic, etc.) ---
sync_engine = create_engine(DATABASE_URL, echo=True)
SyncSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=sync_engine
)

# --- Asynchronous Setup (for FastAPI) ---
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


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
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except asyncio.CancelledError:
            await session.rollback()
            raise
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close() 