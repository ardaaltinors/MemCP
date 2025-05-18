import os
from datetime import datetime, timezone
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
import uuid

class MemoryManager:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "memories",
        embedding_model: str = "text-embedding-3-small"
    ):
        # Initialize Qdrant client
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = collection_name
        self.embedding_model = embedding_model

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
        """Stores a new memory entry in Qdrant."""
        vector = self._embed(content)
        payload = {
            "content": content,
            "tags": tags or [],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        # Use a UUID as a unique ID
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload=payload
        )
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
        return "Memory stored in Qdrant."

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
