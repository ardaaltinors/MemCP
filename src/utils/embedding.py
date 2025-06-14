import os
from openai import AsyncOpenAI
from src.exceptions import ConfigurationError, EmbeddingError


class EmbeddingService:
    """Service for generating text embeddings using OpenAI."""
    
    def __init__(self, embedding_model: str = None):
        self.embedding_model = embedding_model or os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ConfigurationError(
                message="OpenAI API key is required for embedding operations",
                config_key="OPENAI_API_KEY",
                expected_type="string"
            )
        
        self.openai_client = AsyncOpenAI(api_key=api_key)

    def get_embedding_dimension(self) -> int:
        """Get the dimension size for the current embedding model."""
        # text-embedding-3-small produces 1536-dimensional vectors
        return 1536

    async def generate_embedding(self, content: str) -> list[float]:
        """Generate embedding for the given text content (asynchronous)."""
        try:
            resp = await self.openai_client.embeddings.create(
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
    
    async def generate_embeddings(self, contents: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple text contents in batch."""
        if not contents:
            return []
        
        try:
            resp = await self.openai_client.embeddings.create(
                input=contents,
                model=self.embedding_model
            )
            return [item.embedding for item in resp.data]
        except Exception as e:
            raise EmbeddingError(
                message=f"Failed to generate embeddings for {len(contents)} contents",
                text_content=f"Batch of {len(contents)} texts",
                embedding_model=self.embedding_model,
                original_exception=e
            ) 