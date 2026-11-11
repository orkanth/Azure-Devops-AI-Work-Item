
from openai import AsyncOpenAI

from app.core.config import settings


class EmbeddingService:

    def __init__(self):
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")

        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key
        )

        self.model = settings.embedding_model


    async def generate_embeddings(
        self,
        texts: list[str],
    ) -> list[list[float]]:

        if not texts:
            return []

        if any(not text.strip() for text in texts):
            raise ValueError(
                "Input texts cannot contain empty values."
            )

        response = await self.client.embeddings.create(
            model=self.model,
            input=texts,
        )

        # Preserve the original input order.
        results = sorted(
            response.data,
            key=lambda item: item.index,
        )

        embeddings = [
            item.embedding
            for item in results
        ]

        if any(len(item) != 1536 for item in embeddings):
            raise ValueError(
                "Unexpected embedding dimensions."
            )

        return embeddings
