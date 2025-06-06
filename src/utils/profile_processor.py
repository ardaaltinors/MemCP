import uuid
import json
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import AsyncSessionLocal
from src.db.models import UserMessage, ProcessedUserProfile
from src.nlp.synthesize_user_profile import get_llm_profile_synthesis
from src.exceptions import UserContextError
from src.tasks import update_profile_background


class ProfileProcessor:
    """Service for processing user profiles and messages."""
    
    @staticmethod
    async def record_message_and_get_profile(user_id: uuid.UUID, prompt: str) -> str:
        """Record the user's message and return the current synthesized profile."""
        async with AsyncSessionLocal() as db:
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

            user_synthesized_data = {
                "metadata_json": existing_metadata_json_str,
                "summary_text": existing_summary_text,
                "last_updated_timestamp": last_updated_timestamp_iso,
            }
            
            # Dispatch background task to update profile
            update_profile_background.delay(
                user_id_str=str(user_id),
                prompt=prompt,
                existing_metadata_json_str=existing_metadata_json_str,
                existing_summary_text=existing_summary_text,
            )

            return (
                f"User's Metadata: \\n {user_synthesized_data['metadata_json']}\\n "
                f"User's Profile Summary: \\n\\n {user_synthesized_data['summary_text']}\\n"
            )