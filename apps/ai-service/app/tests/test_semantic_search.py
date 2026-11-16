
import asyncio

from app.services.embedding_service import EmbeddingService
from app.repositories.knowledge_repository import KnowledgeRepository


async def main():

    question = "What documents are required during company registration?"

    project_id = "AzureDevOpsAI"

    # Step 1: Generate embedding for the user's question
    embedding_service = EmbeddingService()

    embeddings = await embedding_service.generate_embeddings(
        [question]
    )

    query_embedding = embeddings[0]
    print("Embedding dimensions:", len(query_embedding))
    print("First 5 values:", query_embedding[:5])
    print("Question:", question)
    print("Query embedding dimensions:", len(query_embedding))

    # Step 2: Search PostgreSQL
    repository = KnowledgeRepository()

    results = repository.search_similar_chunks(
        query_embedding=query_embedding,
        project_id=project_id,
        limit=5,
    )

    # Step 3: Display retrieved chunks
    print("\nRetrieved chunks:", len(results))

    for index, result in enumerate(results, start=1):

        print(f"\n--- Result {index} ---")
        print("Document:", result["document_id"])
        print("Page:", result["page_number"])
        print("Chunk:", result["chunk_index"])
        print("Similarity:", round(result["similarity"], 4))
        print("Content:")
        print(result["content"][:500])


if __name__ == "__main__":
    asyncio.run(main())
