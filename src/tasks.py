import uuid
import json
from datetime import datetime, timezone
from sqlalchemy import select
from src.celery_app import celery_app
from src.db.database import SessionLocal
from src.db.models import ProcessedUserProfile
from src.nlp.synthesize_user_profile import get_llm_profile_synthesis

@celery_app.task(name="tasks.update_profile_background")
def update_profile_background(
    user_id_str: str,
    prompt: str,
    existing_metadata_json_str: str,
    existing_summary_text: str,
) -> None:
    """
    Celery task to synthesize and store the updated user profile asynchronously.
    """
    user_id = uuid.UUID(user_id_str)
    db = SessionLocal()
    try:
        user_messages_str = f"Timestamp: {datetime.now(timezone.utc).isoformat()}\\nUser: {prompt}"

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
            json.loads(raw_metadata_str)
            new_metadata_json_str = raw_metadata_str
        except json.JSONDecodeError:
            print(f"Error decoding metadata JSON from LLM response: {raw_metadata_str}")
            new_metadata_json_str = "{}"
        except AttributeError as e:
            print(f"Error accessing LLMAnalysisResult attributes: {e}")

        if new_summary is not None and new_metadata_json_str is not None:
            stmt = select(ProcessedUserProfile).where(ProcessedUserProfile.user_id == user_id)
            profile = db.execute(stmt).scalars().first()
            if profile:
                profile.summary_text = new_summary
                profile.metadata_json = new_metadata_json_str
                db.add(profile)
            else:
                profile = ProcessedUserProfile(
                    user_id=user_id,
                    summary_text=new_summary,
                    metadata_json=new_metadata_json_str,
                )
                db.add(profile)
            try:
                db.commit()
            except Exception as e:
                db.rollback()
                print(f"Failed to update user profile asynchronously: {e}")
        else:
            print(f"Could not extract summary or metadata from LLM response. Response: {llm_response}")
    finally:
        db.close() 