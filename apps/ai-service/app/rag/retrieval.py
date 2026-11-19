import asyncio

from app.rag.embeddings import EmbeddingService
from app.rag.context_builder import RAGContextBuilder
from app.repositories.knowledge_repository import KnowledgeRepository


class RAGRetrievalService:
    """Retrieve relevant project knowledge using hybrid search."""

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        knowledge_repository: KnowledgeRepository | None = None,
        context_builder: RAGContextBuilder | None = None,
    ):
        self.embedding_service = embedding_service or EmbeddingService()
        self.knowledge_repository = knowledge_repository or KnowledgeRepository()
        self.context_builder = context_builder or RAGContextBuilder()

    async def retrieve(
        self,
        query: str,
        project_id: str,
        limit: int = 5,
        document_reference: str | None = None,
    ) -> dict:
        """Retrieve relevant chunks from project or a specific document."""

        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query cannot be empty.")

        if not isinstance(project_id, str) or not project_id.strip():
            raise ValueError("Project ID cannot be empty.")

        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
            raise ValueError("Limit must be a positive integer.")

        query = query.strip()
        project_id = project_id.strip()

        # 1. Resolve an explicitly selected document.
        document_id = None

        if document_reference is not None:
            if (
                not isinstance(document_reference, str)
                or not document_reference.strip()
            ):
                raise ValueError("Document reference cannot be empty.")

            document_id = await asyncio.to_thread(
                self.knowledge_repository.resolve_document_id,
                project_id,
                document_reference.strip(),
            )

        # 2. Generate the question embedding.
        query_embedding = await self.embedding_service.embed_text(query)

        # 3. Execute hybrid search without blocking the event loop.
        chunks = await asyncio.to_thread(
            self.knowledge_repository.search_hybrid_chunks,
            query,
            query_embedding,
            project_id,
            limit,
            document_id=document_id,
        )

        # 4. Build context for the LLM.
        context = self.context_builder.build_context(chunks)

        return {
            "query": query,
            "project_id": project_id,
            "document_id": document_id,
            "total_results": len(chunks),
            "chunks": chunks,
            "context": context,
        }
