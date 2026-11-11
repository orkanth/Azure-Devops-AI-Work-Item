
from app.services.embedding_service import EmbeddingService
from app.repositories.knowledge_repository import KnowledgeRepository


class RAGRetrievalService:

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.knowledge_repository = KnowledgeRepository()

    async def retrieve(
        self,
        question: str,
        project_id: str,
        limit: int = 5,
    ) -> list[dict]:

        
        if not question.strip():
            raise ValueError("Question cannot be empty.")

        if not project_id.strip():
            raise ValueError("Project ID is required.")

        if limit < 1 or limit > 50:
            raise ValueError("Limit must be between 1 and 50.")


        # Step 1: Generate embedding for the question
        embeddings = await self.embedding_service.generate_embeddings(
            [question]
        )

        query_embedding = embeddings[0]

        # Step 2: Perform hybrid search
        results = self.knowledge_repository.search_hybrid_chunks(
            query=question,
            query_embedding=query_embedding,
            project_id=project_id,
            limit=limit,
        )

        return results
