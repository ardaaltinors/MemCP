import uuid
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.processed_user_profile import ProcessedUserProfile
from src.exceptions import DatabaseOperationError


async def get_processed_user_profile(
    db: AsyncSession, 
    user_id: uuid.UUID
) -> Optional[ProcessedUserProfile]:
    """Get processed user profile by user ID."""
    result = await db.execute(
        select(ProcessedUserProfile).filter(ProcessedUserProfile.user_id == user_id)
    )
    return result.scalars().first()


async def delete_processed_user_profile(
    db: AsyncSession,
    user_id: uuid.UUID
) -> bool:
    """Delete processed user profile for a user. Returns True if deleted, False if not found."""
    try:
        stmt = delete(ProcessedUserProfile).where(ProcessedUserProfile.user_id == user_id)
        result = await db.execute(stmt)
        await db.flush()
        
        # Return True if a row was deleted
        return result.rowcount > 0
    except Exception as e:
        raise DatabaseOperationError(
            message="Failed to delete processed user profile",
            operation="delete",
            table_name="processed_user_profiles",
            original_exception=e
        )