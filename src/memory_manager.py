import os
from datetime import datetime, timezone
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
import uuid
from src.db.database import get_db
from src.db.models import Memory
from sqlalchemy import select

class MemoryManager:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "memories",
        embedding_model: str = "text-embedding-3-small",
        score_threshold: float = 0.25
    ):
        # Initialize Qdrant client
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.score_threshold = score_threshold
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not found.")
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
        resp = self.openai_client.embeddings.create(
            input=[content],
            model=self.embedding_model
        )
        return resp.data[0].embedding

    def store(self, content: str, tags: list[str] | None = None) -> str:
        """Stores a new memory entry in Qdrant and PostgreSQL."""
        # Generate a UUID to use in both databases
        memory_id = str(uuid.uuid4())
        
        # Store in Qdrant for vector similarity search
        vector = self._embed(content)
        payload = {
            "content": content,
            "tags": tags or [],
            "timestamp": datetime.now(timezone.utc).isoformat()
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
        
        # Store in PostgreSQL for relational queries
        db = get_db()
        db_memory = Memory(
            id=uuid.UUID(memory_id),
            content=content,
            tags=tags or [],
            timestamp=datetime.now(timezone.utc)
        )
        db.add(db_memory)
        db.commit()
        
        return f"Memory stored with ID: {memory_id}"

    def retrieve_all(self) -> list[dict]:
        """Retrieves all stored memories from Qdrant."""
        all_points = []
        offset = None
        limit = 1000

        while True:
            records, next_page_offset = self.client.scroll(
                collection_name=self.collection_name,
                limit=limit,
                offset=offset
            )
            all_points.extend(records)
            if next_page_offset is None:
                break
            offset = next_page_offset

        memories = []
        for point in all_points:
            payload = point.payload or {}
            memories.append({
                "id": point.id,
                "content": payload.get("content"),
                "tags": payload.get("tags"),
                "timestamp": payload.get("timestamp")
            })
        return memories

    def search_related(self, query_text: str) -> list[dict]:
        """Performs a semantic search in Qdrant for memories related to the query text, filtered by score threshold."""
        query_embedding = self._embed(query_text)

        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            score_threshold=self.score_threshold,
            limit=25,
            with_payload=True
        )

        results = []
        for hit in search_result:
            payload = hit.payload or {}
            results.append({
                "id": hit.id,
                "content": payload.get("content"),
                "tags": payload.get("tags"),
                "score": hit.score,
                "timestamp": payload.get("timestamp")
            })
        return results
