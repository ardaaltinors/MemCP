import uuid
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy import select, update
from celery.exceptions import SoftTimeLimitExceeded
from celery_singleton import Singleton
from src.celery_app import celery_app
from src.db.database import SyncSessionLocal
from src.db.models import ProcessedUserProfile, UserMessage
from src.nlp.synthesize_user_profile import get_llm_profile_synthesis
from src.exceptions import UserContextError
from src.exceptions.handlers import ExceptionHandler

# Configure logger for celery tasks
logger = logging.getLogger(__name__)

@celery_app.task(
    name="tasks.update_profile_background", 
    bind=True,
    base=Singleton,
    max_retries=1,  # Only retry once
    default_retry_delay=60,  # Wait 60 seconds before retry
    soft_time_limit=300,  # 5 minutes soft limit
    time_limit=360,  # 6 minutes hard limit
    unique_on=['user_id_str'],  # Prevent duplicate tasks per user
    lock_expiry=600  # Lock expires after 10 minutes
)
def update_profile_background(
    self,
    user_id_str: str,
    unprocessed_messages: List[Dict[str, Any]],
    existing_metadata_json_str: str,
    existing_summary_text: str,
) -> None:
    """
    Celery task to synthesize and store the updated user profile asynchronously.
    
    This task uses celery-singleton to ensure only one instance runs per user at a time.
    If a duplicate task is submitted while one is already running, it will be discarded.
    The lock is automatically released when the task completes or fails.
    
    Args:
        user_id_str: UUID string of the user (used as unique key for singleton)
        unprocessed_messages: List of unprocessed messages to process
        existing_metadata_json_str: Current metadata as JSON string
        existing_summary_text: Current profile summary
        
    Raises:
        UserContextError: If profile update fails
    """
    try:
        user_id = uuid.UUID(user_id_str)
        logger.info(f"Starting profile update task for user {user_id} with {len(unprocessed_messages)} messages")
        
        # Log if this is a duplicate task that got through before lock was acquired
        if hasattr(self, 'is_duplicate') and self.is_duplicate:
            logger.warning(f"Duplicate task detected for user {user_id}, will be prevented by Singleton lock")
        
        # Early exit if no messages to process
        if not unprocessed_messages:
            logger.info(f"No unprocessed messages for user {user_id}, skipping task")
            return
        
        # Update task state to show progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': len(unprocessed_messages), 'status': 'Preparing messages'}
        )
        
        db = SyncSessionLocal()
        try:
            # First, check if these messages are already processed (deduplication)
            message_ids = [msg.get("id") for msg in unprocessed_messages if msg.get("id")]
            if message_ids:
                check_stmt = select(UserMessage.id).where(
                    UserMessage.id.in_(message_ids),
                    UserMessage.is_processed == True
                )
                already_processed = db.execute(check_stmt).scalars().all()
                if already_processed:
                    logger.warning(f"Found {len(already_processed)} already processed messages for user {user_id}, potential duplicate task")
                    # Filter out already processed messages
                    unprocessed_messages = [
                        msg for msg in unprocessed_messages 
                        if msg.get("id") not in already_processed
                    ]
                    if not unprocessed_messages:
                        logger.info(f"All messages already processed for user {user_id}, exiting task")
                        return
            # Build comprehensive user messages string from all unprocessed messages
            user_messages_parts = []
            message_ids_to_mark = []
            
            for idx, msg_data in enumerate(unprocessed_messages):
                timestamp = msg_data.get("created_at", datetime.now(timezone.utc).isoformat())
                content = msg_data.get("message_content", "")
                message_id = msg_data.get("id")
                
                user_messages_parts.append(f"Timestamp: {timestamp}\nUser: {content}")
                if message_id:
                    message_ids_to_mark.append(message_id)
                
                # Update progress every 5 messages
                if idx % 5 == 0:
                    self.update_state(
                        state='PROGRESS',
                        meta={'current': idx, 'total': len(unprocessed_messages), 'status': 'Processing messages'}
                    )
            
            user_messages_str = "\n\n".join(user_messages_parts)
            
            logger.debug(f"Processing {len(unprocessed_messages)} messages for user {user_id}")
            logger.debug(f"Combined messages length: {len(user_messages_str)} characters")
            
            # Update state before LLM call
            self.update_state(
                state='PROGRESS',
                meta={'current': len(unprocessed_messages), 'total': len(unprocessed_messages), 'status': 'Synthesizing profile with LLM'}
            )

            logger.debug(f"Calling LLM for profile synthesis for user {user_id}")
            try:
                llm_response = get_llm_profile_synthesis(
                    user_messages_str=user_messages_str,
                    existing_metadata_json_str=existing_metadata_json_str,
                    existing_summary_text=existing_summary_text,
                )
            except SoftTimeLimitExceeded:
                logger.error(f"Task soft time limit exceeded for user {user_id}")
                raise UserContextError(
                    message="Profile synthesis timed out",
                    operation="llm_synthesis",
                    user_id=str(user_id)
                )

            new_summary = None
            new_metadata_json_str = None

            try:
                new_summary = llm_response.user_profile_summary.strip()
                raw_metadata_str = llm_response.user_profile_metadata.strip()
                
                # Validate JSON format
                json.loads(raw_metadata_str)
                new_metadata_json_str = raw_metadata_str
                
                logger.debug(f"Successfully parsed LLM response for user {user_id}")
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON metadata from LLM for user {user_id}: {raw_metadata_str[:100]}...", exc_info=True)
                new_metadata_json_str = "{}"  # Fallback to empty JSON
                
            except AttributeError as e:
                logger.error(f"Missing attributes in LLM response for user {user_id}: {e}", exc_info=True)
                raise UserContextError(
                    message="LLM response format is invalid",
                    operation="parse_llm_response",
                    user_id=str(user_id),
                    original_exception=e
                )

            if new_summary is not None and new_metadata_json_str is not None:
                logger.debug(f"Updating database profile for user {user_id}")
                
                # Find existing profile or create new one
                stmt = select(ProcessedUserProfile).where(ProcessedUserProfile.user_id == user_id)
                profile = db.execute(stmt).scalars().first()
                
                if profile:
                    logger.debug(f"Updating existing profile for user {user_id}")
                    profile.summary_text = new_summary
                    profile.metadata_json = new_metadata_json_str
                    db.add(profile)
                else:
                    logger.debug(f"Creating new profile for user {user_id}")
                    profile = ProcessedUserProfile(
                        user_id=user_id,
                        summary_text=new_summary,
                        metadata_json=new_metadata_json_str,
                    )
                    db.add(profile)
                
                try:
                    db.commit()
                    logger.info(f"Successfully updated profile for user {user_id}")
                    
                    # Update state to completed
                    self.update_state(
                        state='SUCCESS',
                        meta={'current': len(unprocessed_messages), 'total': len(unprocessed_messages), 'status': 'Profile update completed'}
                    )
                    
                    # Mark specific processed messages as processed after successful profile update
                    if message_ids_to_mark:
                        logger.debug(f"Marking {len(message_ids_to_mark)} specific messages as processed for user {user_id}")
                        update_stmt = (
                            update(UserMessage)
                            .where(UserMessage.id.in_(message_ids_to_mark))
                            .values(is_processed=True)
                        )
                        result = db.execute(update_stmt)
                        processed_count = result.rowcount
                        db.commit()
                        logger.info(f"Marked {processed_count} messages as processed for user {user_id}")
                    
                except Exception as e:
                    db.rollback()
                    logger.error(f"Database commit failed for user {user_id}: {e}", exc_info=True)
                    raise UserContextError(
                        message="Failed to save user profile to database",
                        operation="commit_profile_update",
                        user_id=str(user_id),
                        original_exception=e
                    )
            else:
                logger.error(f"Could not extract valid summary or metadata from LLM response for user {user_id}")
                raise UserContextError(
                    message="LLM response extraction failed",
                    operation="extract_profile_data",
                    user_id=str(user_id)
                )
                
        finally:
            db.close()
            logger.debug(f"Database session closed for user {user_id}")
            
    except ValueError as e:
        logger.error(f"Invalid user ID format: {user_id_str}", exc_info=True)
        raise UserContextError(
            message="Invalid user ID format",
            operation="parse_user_id",
            original_exception=e
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in profile update task for user {user_id_str}: {e}", exc_info=True)
        # Log the exception through the centralized handler
        ExceptionHandler.log_exception(
            exception=e,
            operation="update_profile_background",
            user_id=user_id_str,
            additional_context={
                "message_count": len(unprocessed_messages) if unprocessed_messages else 0,
                "has_existing_metadata": bool(existing_metadata_json_str),
                "has_existing_summary": bool(existing_summary_text)
            }
        )
        raise 