import uuid
import json
import logging
import os
from datetime import datetime, timezone
from typing import List, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_async_sessionmaker
from src.db.models import UserMessage, ProcessedUserProfile
from src.nlp.synthesize_user_profile import get_llm_profile_synthesis
from src.exceptions import UserContextError
from src.tasks import update_profile_background

logger = logging.getLogger(__name__)


LLM_PROCESS_BATCH_SIZE = int(os.getenv("LLM_PROCESS_BATCH_SIZE", "3"))

class ProfileProcessor:
    """Service for processing user profiles and messages."""
    
    @staticmethod
    async def _should_trigger_profile_update(
        db: AsyncSession,
        user_id: uuid.UUID,
        existing_profile: ProcessedUserProfile,
        existing_metadata_json_str: str,
        existing_summary_text: str,
    ) -> Tuple[bool, List[UserMessage]]:
        """
        Determines if the background profile update task should be triggered.
        
        Returns:
            Tuple of (should_trigger: bool, unprocessed_messages: List[UserMessage])
        """
        if not existing_profile:
            logger.debug(f"No existing profile found for user {user_id}. Triggering immediate update.")
            # For new users, we still need to get unprocessed messages
            unprocessed_stmt = select(UserMessage).where(
                UserMessage.user_id == user_id,
                UserMessage.is_processed == False
            ).order_by(UserMessage.created_at.asc())
            unprocessed_result = await db.execute(unprocessed_stmt)
            unprocessed_messages = list(unprocessed_result.scalars().all())
            return True, unprocessed_messages

        # Check if profile is effectively empty (both metadata and summary are null/empty)
        profile_is_empty = (
            not existing_metadata_json_str or existing_metadata_json_str.strip() == "" or existing_metadata_json_str.strip() == "{}"
        ) and (
            not existing_summary_text or existing_summary_text.strip() == ""
        )

        if profile_is_empty:
            logger.debug(f"Existing profile for user {user_id} is empty. Triggering immediate update.")
            # Get all unprocessed messages for empty profile case
            unprocessed_stmt = select(UserMessage).where(
                UserMessage.user_id == user_id,
                UserMessage.is_processed == False
            ).order_by(UserMessage.created_at.asc())
            unprocessed_result = await db.execute(unprocessed_stmt)
            unprocessed_messages = list(unprocessed_result.scalars().all())
            return True, unprocessed_messages
        else:
            # Profile has content - check unprocessed message count
            unprocessed_count_stmt = select(func.count(UserMessage.id)).where(
                UserMessage.user_id == user_id,
                UserMessage.is_processed == False
            )
            unprocessed_count_result = await db.execute(unprocessed_count_stmt)
            unprocessed_count = unprocessed_count_result.scalar()
            logger.debug(f"User {user_id} has {unprocessed_count} unprocessed messages.")

            # Trigger update if we have enough unprocessed messages
            if unprocessed_count >= LLM_PROCESS_BATCH_SIZE:
                logger.debug(f"Unprocessed message count for user {user_id} is >= {LLM_PROCESS_BATCH_SIZE}. Triggering update.")
                # Get ALL unprocessed messages when threshold is met
                unprocessed_stmt = select(UserMessage).where(
                    UserMessage.user_id == user_id,
                    UserMessage.is_processed == False
                ).order_by(UserMessage.created_at.asc())
                unprocessed_result = await db.execute(unprocessed_stmt)
                unprocessed_messages = list(unprocessed_result.scalars().all())
                return True, unprocessed_messages
        
        logger.debug(f"Profile update conditions not met for user {user_id}.")
        return False, []

    @staticmethod
    async def record_message_and_get_profile(user_id: uuid.UUID, prompt: str) -> str:
        """Record the user's message and return the current synthesized profile."""
        session_maker = get_async_sessionmaker()
        async with session_maker() as db:
            # Record the user message
            db_user_message = UserMessage(user_id=user_id, message_content=prompt)
            db.add(db_user_message)
            await db.flush()

            # Get existing profile
            stmt = select(ProcessedUserProfile).where(ProcessedUserProfile.user_id == user_id)
            result = await db.execute(stmt)
            existing_profile = result.scalars().first()

            existing_metadata_json_str = ""
            existing_summary_text = ""
            last_updated_timestamp_iso = None

            if existing_profile:
                existing_metadata_json_str = existing_profile.metadata_json or ""
                existing_summary_text = existing_profile.summary_text or ""
                last_updated_timestamp_iso = existing_profile.updated_at.isoformat()

            # check if we should trigger background profile update and get unprocessed messages
            should_trigger_update, unprocessed_messages = await ProfileProcessor._should_trigger_profile_update(
                db,
                user_id,
                existing_profile,
                existing_metadata_json_str,
                existing_summary_text,
            )

            user_synthesized_data = {
                "metadata_json": existing_metadata_json_str,
                "summary_text": existing_summary_text,
                "last_updated_timestamp": last_updated_timestamp_iso,
            }

            # Trigger background task if conditions are met
            if should_trigger_update:
                # Convert unprocessed messages to the format expected by the background task
                unprocessed_message_data = [
                    {
                        "id": msg.id,
                        "message_content": msg.message_content,
                        "created_at": msg.created_at.isoformat()
                    }
                    for msg in unprocessed_messages
                ]
                
                logger.info(f"Triggering background update for user {user_id} with {len(unprocessed_messages)} unprocessed messages")
                
                # Use a deterministic task ID based on user and message count to prevent duplicates
                task_id = f"profile_update_{user_id}_{len(unprocessed_messages)}"
                
                update_profile_background.apply_async(
                    args=[
                        str(user_id),
                        unprocessed_message_data,
                        existing_metadata_json_str,
                        existing_summary_text,
                    ],
                    task_id=task_id,
                    countdown=2  # Small delay to ensure DB commit completes
                )

            await db.commit()

            return json.dumps(user_synthesized_data, indent=2)