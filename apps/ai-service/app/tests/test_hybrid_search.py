
import asyncio

from app.services.embedding_service import EmbeddingService
from app.repositories.knowledge_repository import KnowledgeRepository


async def main():

    question = "GST Certificate PAN Business Registration Documents"

    project_id = "AzureDevOpsAI"

    # Generate query embedding
    embedding_service = EmbeddingService()

    embeddings = await embedding_service.generate_embeddings(
        [question]
    )

    query_embedding = embeddings[0]

    # Execute hybrid search
    repository = KnowledgeRepository()

    results = repository.search_hybrid_chunks(
        query=question,
        query_embedding=query_embedding,
        project_id=project_id,
        limit=5,
        candidate_limit=20,
    )

    print("Question:", question)
    print("Retrieved chunks:", len(results))

    for index, result in enumerate(results, start=1):

        print(f"\n--- Result {index} ---")
        print("Page:", result["page_number"])
        print("Chunk:", result["chunk_index"])
        print("Semantic rank:", result["semantic_rank"])
        print("Keyword rank:", result["keyword_rank"])
        print("RRF score:", round(result["rrf_score"], 6))
        print("Content:")
        print(result["content"][:500])


if __name__ == "__main__":
    asyncio.run(main())
