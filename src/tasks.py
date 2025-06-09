import uuid
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from src.celery_app import celery_app
from src.db.database import SyncSessionLocal
from src.db.models import ProcessedUserProfile, UserMessage, Memory
from src.nlp.synthesize_user_profile import get_llm_profile_synthesis
from src.exceptions import UserContextError, MemoryStoreError
from src.exceptions.handlers import ExceptionHandler
from src.utils.vector_store import SyncVectorStore
from src.core.context import user_context

# Configure logger for celery tasks
logger = logging.getLogger(__name__)

def _store_memory_sync(
    user_id: uuid.UUID,
    content: str,
    db: Session,
    tags: Optional[List[str]] = None
) -> str:
    """
    Synchronous helper function to store a memory in PostgreSQL.
    Used within Celery tasks that use sync database sessions.
    
    Args:
        user_id: User ID
        content: Memory content
        db: Sync database session
        tags: Optional tags for the memory
        
    Returns:
        Memory ID string
        
    Raises:
        MemoryStoreError: If memory storage fails
    """
    try:
        memory_id = uuid.uuid4()
        
        # Store in PostgreSQL
        db_memory = Memory(
            id=memory_id,
            content=content,
            tags=tags or [],
            user_id=user_id
        )
        db.add(db_memory)
        db.flush()  # Don't commit yet, let the calling function handle it
        
        logger.debug(f"Stored memory {memory_id} in PostgreSQL for user {user_id}")
        return str(memory_id)
        
    except Exception as e:
        logger.error(f"Failed to store memory in PostgreSQL for user {user_id}: {e}", exc_info=True)
        raise MemoryStoreError(
            message="Failed to store memory in PostgreSQL",
            user_id=str(user_id),
            storage_type="postgresql",
            original_exception=e
        )

def _store_memories_batch(
    user_id: uuid.UUID,
    memories: List[str],
    db: Session
) -> List[str]:
    """
    Store multiple memories synchronously in both PostgreSQL and Qdrant using optimized batch operations.
    Checks for duplicates before storing to avoid redundant memories.
    
    Args:
        user_id: User ID
        memories: List of memory contents
        db: Sync database session
        
    Returns:
        List of memory IDs that were successfully stored
    """
    if not memories:
        return []
    
    # Initialize vector store for duplicate checking
    sync_vector_store = SyncVectorStore()
    
    # Prepare memory data for batch operations
    memory_data = []
    stored_memory_ids = []
    skipped_duplicates = 0
    
    # Check each memory for duplicates before storing
    for memory_content in memories:
        if not memory_content.strip():
            continue
        
        cleaned_content = memory_content.strip()
        
        # Check for similar memories in Qdrant
        try:
            similar_memories = sync_vector_store.search_similar_memories(
                content=cleaned_content,
                user_id=user_id
            )
            
            if similar_memories:
                # Found duplicate, skip this memory
                skipped_duplicates += 1
                logger.debug(
                    f"Skipping duplicate memory for user {user_id}. "
                    f"Found {len(similar_memories)} similar memories with top score: {similar_memories[0]['score']:.3f}"
                )
                continue
                
        except Exception as e:
            logger.warning(f"Failed to check for duplicate memories: {e}", exc_info=True)
            # Continue with storing the memory if duplicate check fails
            
        # No duplicates found, proceed with storing
        try:
            memory_id = _store_memory_sync(user_id, cleaned_content, db, tags=["ai_extracted"])
            stored_memory_ids.append(memory_id)
            
            # Prepare data for Qdrant batch operation
            memory_data.append({
                "memory_id": memory_id,
                "content": cleaned_content,
                "tags": ["ai_extracted"]
            })
            
        except MemoryStoreError as e:
            logger.error(f"Failed to store memory in PostgreSQL: {cleaned_content[:50]}...", exc_info=True)
            # Continue with other memories rather than failing completely
    
    if skipped_duplicates > 0:
        logger.info(f"Skipped {skipped_duplicates} duplicate memories for user {user_id}")
            
    # Commit all PostgreSQL changes at once
    try:
        db.commit()
        logger.info(f"Successfully stored {len(stored_memory_ids)} memories in PostgreSQL for user {user_id}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to commit memories to PostgreSQL for user {user_id}: {e}", exc_info=True)
        sync_vector_store.close()
        return []
    
    # Now store in Qdrant using the synchronous batch operation
    if memory_data:
        try:
            sync_vector_store.store_memories_batch(memory_data, user_id)
            logger.info(f"Successfully stored {len(memory_data)} memories in Qdrant for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to store memories in Qdrant for user {user_id}: {e}", exc_info=True)
            # Don't fail the task since PostgreSQL storage succeeded
    
    sync_vector_store.close()
    return stored_memory_ids

@celery_app.task(name="tasks.update_profile_background")
def update_profile_background(
    user_id_str: str,
    unprocessed_messages: List[Dict[str, Any]],
    existing_metadata_json_str: str,
    existing_summary_text: str,
) -> None:
    """
    Celery task to synthesize and store the updated user profile asynchronously.
    
    Args:
        user_id_str: UUID string of the user
        unprocessed_messages: List of unprocessed messages to process
        existing_metadata_json_str: Current metadata as JSON string
        existing_summary_text: Current profile summary
        
    Raises:
        UserContextError: If profile update fails
    """
    try:
        user_id = uuid.UUID(user_id_str)
        logger.info(f"Starting profile update task for user {user_id} with {len(unprocessed_messages)} messages")
        
        db = SyncSessionLocal()
        try:
            # Build comprehensive user messages string from all unprocessed messages
            user_messages_parts = []
            message_ids_to_mark = []
            
            for msg_data in unprocessed_messages:
                timestamp = msg_data.get("created_at", datetime.now(timezone.utc).isoformat())
                content = msg_data.get("message_content", "")
                message_id = msg_data.get("id")
                
                user_messages_parts.append(f"Timestamp: {timestamp}\nUser: {content}")
                if message_id:
                    message_ids_to_mark.append(message_id)
            
            user_messages_str = "\n\n".join(user_messages_parts)
            
            logger.debug(f"Processing {len(unprocessed_messages)} messages for user {user_id}")
            logger.debug(f"Combined messages length: {len(user_messages_str)} characters")

            logger.debug(f"Calling LLM for profile synthesis for user {user_id}")
            llm_response = get_llm_profile_synthesis(
                user_messages_str=user_messages_str,
                existing_metadata_json_str=existing_metadata_json_str,
                existing_summary_text=existing_summary_text,
            )

            new_summary = None
            new_metadata_json_str = None
            memories_to_store = []

            try:
                new_summary = llm_response.user_profile_summary.strip()
                raw_metadata_str = llm_response.user_profile_metadata.strip()
                memories_to_store = llm_response.user_profile_memories or []
                
                # Validate JSON format
                json.loads(raw_metadata_str)
                new_metadata_json_str = raw_metadata_str
                
                logger.debug(f"Successfully parsed LLM response for user {user_id}")
                logger.debug(f"Extracted {len(memories_to_store)} memories to store")
                
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
                    
                    # Store extracted memories in both PostgreSQL and Qdrant
                    if memories_to_store:
                        logger.info(f"Storing {len(memories_to_store)} extracted memories for user {user_id}")
                        with user_context(user_id):
                            stored_memory_ids = _store_memories_batch(user_id, memories_to_store, db)
                            logger.info(f"Successfully stored {len(stored_memory_ids)} memories for user {user_id}")
                    
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
                "message_count": len(unprocessed_messages) if unprocessed_messages else 0,
                "has_existing_metadata": bool(existing_metadata_json_str),
                "has_existing_summary": bool(existing_summary_text)
            }
        )
        raise 