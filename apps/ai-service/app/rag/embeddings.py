
from langchain_openai import OpenAIEmbeddings

from app.core.config import settings


class EmbeddingService:
    """Generate vector embeddings for document chunks and search queries."""

    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            dimensions=settings.embedding_dimensions,
            api_key=settings.openai_api_key,
        )

    async def embed_text(self, text: str) -> list[float]:
        """Generate an embedding for a single text."""
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Text cannot be empty.")

        return await self.embeddings.aembed_query(text)

    async def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """Generate embeddings for multiple document chunks."""
        if not texts:
            return []

        if any(not isinstance(text, str) or not text.strip() for text in texts):
            raise ValueError("All document texts must be non-empty strings.")

        return await self.embeddings.aembed_documents(texts)
