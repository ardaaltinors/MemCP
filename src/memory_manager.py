import os
from datetime import datetime, timezone
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
import uuid
import json
from src.db.database import get_db
from src.db.models import Memory, UserMessage, ProcessedUserProfile
from sqlalchemy import select
from src.nlp.synthesize_user_profile import get_llm_profile_synthesis
from src.core.context import get_current_user_id
from src.exceptions import (
    ConfigurationError, UserContextError, MemoryStoreError, 
    MemorySearchError, EmbeddingError, OpenAIServiceError,
    QdrantServiceError, DatabaseOperationError
)

class MemoryManager:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "memories",
        embedding_model: str = "text-embedding-3-small",
        score_threshold: float = 0.40,
        upper_score_threshold: float = 0.98
    ):
        # Initialize Qdrant client
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.score_threshold = score_threshold
        self.upper_score_threshold = upper_score_threshold
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ConfigurationError(
                message="OpenAI API key is required for memory operations",
                config_key="OPENAI_API_KEY",
                expected_type="string"
            )
        self.openai_client = OpenAI(api_key=api_key)

        # Ensure the collection exists in Qdrant
        existing = [c.name for c in self.client.get_collections().collections]
        if self.collection_name not in existing:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self._embedding_dim(),
                    distance=Distance.COSINE
                )
            )

    def _embedding_dim(self) -> int:
        # text-embedding-3-small produces 1536-dimensional vectors
        return 1536

    def _embed(self, content: str) -> list[float]:
        # Generate embedding for the content string
        try:
            resp = self.openai_client.embeddings.create(
                input=[content],
                model=self.embedding_model
            )
            return resp.data[0].embedding
        except Exception as e:
            raise EmbeddingError(
                message="Failed to generate embedding for content",
                text_content=content,
                embedding_model=self.embedding_model,
                original_exception=e
            )

    def store(self, content: str, tags: list[str] | None = None) -> str:
        """Stores a new memory entry in Qdrant and PostgreSQL."""
        from src.core.context import get_current_user_id
        
        # Get the current user_id from async context
        user_id = get_current_user_id()
        if user_id is None:
            raise UserContextError(
                message="User context is required for memory storage",
                operation="store_memory"
            )
        
        # Generate a UUID to use in both databases
        memory_id = str(uuid.uuid4())
        
        # Store in Qdrant for vector similarity search
        try:
            vector = self._embed(content)
            payload = {
                "content": content,
                "tags": tags or [],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user_id": str(user_id)  # Include user_id in Qdrant payload
            }
            point = PointStruct(
                id=memory_id,
                vector=vector,
                payload=payload
            )
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
        except Exception as e:
            raise QdrantServiceError(
                message="Failed to store memory in vector database",
                operation="upsert",
                collection_name=self.collection_name,
                original_exception=e
            )
        
        # Store in PostgreSQL for relational queries
        try:
            db = get_db()
            db_memory = Memory(
                id=uuid.UUID(memory_id),
                content=content,
                tags=tags or [],
                user_id=user_id  # Associate memory with user
            )
            db.add(db_memory)
            db.commit()
        except Exception as e:
            raise DatabaseOperationError(
                message="Failed to store memory in relational database",
                operation="insert",
                table_name="memories",
                original_exception=e
            )
        
        return f"Memory stored with ID: {memory_id} for user: {user_id}"


    def search_related(self, query_text: str) -> list[dict]:
        """Performs a semantic search in Qdrant for memories related to the query text, filtered by score threshold and user_id."""
        from src.core.context import get_current_user_id
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        # Get the current user_id from async context
        user_id = get_current_user_id()
        if user_id is None:
            raise UserContextError(
                message="User context is required for memory search",
                operation="search_memories"
            )
        
        query_embedding = self._embed(query_text)

        # Create filter to only search memories for the current user
        user_filter = Filter(
            must=[
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=str(user_id))
                )
            ]
        )

        try:
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=user_filter,  # Filter by user_id
                score_threshold=self.score_threshold,
                limit=25,
                with_payload=True
            )
        except Exception as e:
            raise MemorySearchError(
                message="Failed to search memories in vector database",
                query_text=query_text,
                user_id=str(user_id),
                search_type="semantic_search",
                original_exception=e
            )

        results = []
        for hit in search_result:
            # Apply upper score threshold if provided
            if self.upper_score_threshold is not None and hit.score > self.upper_score_threshold:
                continue

            payload = hit.payload or {}
            results.append({
                "id": hit.id,
                "content": payload.get("content"),
                "tags": payload.get("tags"),
                "score": hit.score,
                "timestamp": payload.get("timestamp"),
                "user_id": payload.get("user_id")
            })
        return results

    def process_context(self, prompt: str, tags: list[str] | None = None) -> str:
        """
        Saves the user message to the database, synthesizes a user profile based on the message,
        and returns the synthesized profile.
        """
        # Get the current user_id from async context
        user_id = get_current_user_id()
        if user_id is None:
            raise UserContextError(
                message="User context is required for profile processing",
                operation="process_context"
            )

        db = get_db()
        db_user_message = UserMessage(
            user_id=user_id,
            message_content=prompt
        )
        db.add(db_user_message)
        db.commit()

        # 1) Get user's metadata, summary text, and last_updated_timestamp
        user_synthesized_data = None
        stmt = select(ProcessedUserProfile).where(ProcessedUserProfile.user_id == user_id)
        existing_profile = db.execute(stmt).scalars().first()

        existing_metadata_json_str = ""
        existing_summary_text = ""
        last_updated_timestamp_iso = None

        if existing_profile:
            existing_metadata_json_str = existing_profile.metadata_json if existing_profile.metadata_json else ""
            existing_summary_text = existing_profile.summary_text if existing_profile.summary_text else ""
            last_updated_timestamp_iso = existing_profile.updated_at.isoformat()
            user_synthesized_data = {
                "metadata_json": existing_metadata_json_str,
                "summary_text": existing_summary_text,
                "last_updated_timestamp": last_updated_timestamp_iso
            }
        else:
             user_synthesized_data = { # Default if no profile exists
                "metadata_json": "",
                "summary_text": "",
                "last_updated_timestamp": None
            }
        
        # Format the current prompt as a user message string
        # This might need adjustment if the synthesis function expects a more complex history
        user_messages_str = f"Timestamp: {datetime.now(timezone.utc).isoformat()}\\nUser: {prompt}"

        # 2) Call the get_llm_profile_synthesis function
        llm_response = get_llm_profile_synthesis(
            user_messages_str=user_messages_str,
            existing_metadata_json_str=existing_metadata_json_str,
            existing_summary_text=existing_summary_text
        )
        
        # Extract summary and metadata from LLMAnalysisResult object
        new_summary = None
        new_metadata_json_str = None

        try:
            new_summary = llm_response.user_profile_summary.strip()
            raw_metadata_str = llm_response.user_profile_metadata.strip()
            
            # Validate the extracted string is valid JSON
            json.loads(raw_metadata_str)
            new_metadata_json_str = raw_metadata_str
        except json.JSONDecodeError:
            print(f"Error decoding metadata JSON from LLM response: {raw_metadata_str}")
            # Fallback to an empty JSON object string if parsing fails
            new_metadata_json_str = "{}"
        except AttributeError as e:
            print(f"Error accessing LLMAnalysisResult attributes: {e}")
            # Handle case where llm_response doesn't have expected attributes

        # Update or create ProcessedUserProfile in the DB
        if new_summary is not None and new_metadata_json_str is not None:
            if existing_profile:
                existing_profile.summary_text = new_summary
                existing_profile.metadata_json = new_metadata_json_str # SQLAlchemy's JSONB handles string
                # last_updated_timestamp should be auto-updated by onupdate=func.now()
                db.add(existing_profile) # Ensure SQLAlchemy tracks changes
            else:
                new_db_profile = ProcessedUserProfile(
                    user_id=user_id,
                    summary_text=new_summary,
                    metadata_json=new_metadata_json_str
                    # last_updated_timestamp will be set by server_default for new entries
                )
                db.add(new_db_profile)
            
            try:
                db.commit()
            except Exception as e:
                db.rollback()
                raise DatabaseOperationError(
                    message="Failed to update user profile in database",
                    operation="update",
                    table_name="processed_user_profiles",
                    original_exception=e
                )
        else:
            print(f"Could not extract summary or metadata from LLM response. Response: {llm_response}")
            # Optionally, log this error more formally

        # 3) Return the user_synthesized_data from step 1 (data before this update)
        responseString = f"User's Metadata: \n {user_synthesized_data['metadata_json']}\n User's Profile Summary: \n\n {user_synthesized_data['summary_text']}\n"
        return responseString
