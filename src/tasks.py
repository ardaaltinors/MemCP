import uuid
import json
import logging
from datetime import datetime, timezone
from sqlalchemy import select
from src.celery_app import celery_app
from src.db.database import SyncSessionLocal
from src.db.models import ProcessedUserProfile
from src.nlp.synthesize_user_profile import get_llm_profile_synthesis
from src.exceptions import UserContextError
from src.exceptions.handlers import ExceptionHandler

# Configure logger for celery tasks
logger = logging.getLogger(__name__)

@celery_app.task(name="tasks.update_profile_background")
def update_profile_background(
    user_id_str: str,
    prompt: str,
    existing_metadata_json_str: str,
    existing_summary_text: str,
) -> None:
    """
    Celery task to synthesize and store the updated user profile asynchronously.
    
    Args:
        user_id_str: UUID string of the user
        prompt: New user message to process
        existing_metadata_json_str: Current metadata as JSON string
        existing_summary_text: Current profile summary
        
    Raises:
        UserContextError: If profile update fails
    """
    try:
        user_id = uuid.UUID(user_id_str)
        logger.info(f"Starting profile update task for user {user_id}")
        
        db = SyncSessionLocal()
        try:
            user_messages_str = f"Timestamp: {datetime.now(timezone.utc).isoformat()}\\nUser: {prompt}"

            logger.debug(f"Calling LLM for profile synthesis for user {user_id}")
            llm_response = get_llm_profile_synthesis(
                user_messages_str=user_messages_str,
                existing_metadata_json_str=existing_metadata_json_str,
                existing_summary_text=existing_summary_text,
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
            
    except uuid.ValueError as e:
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
                "prompt_length": len(prompt) if prompt else 0,
                "has_existing_metadata": bool(existing_metadata_json_str),
                "has_existing_summary": bool(existing_summary_text)
            }
        )
        raise 