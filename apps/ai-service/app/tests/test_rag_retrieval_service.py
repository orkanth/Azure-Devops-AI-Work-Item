
import asyncio
from unittest import result

from app.services.rag_retrieval_service import RAGRetrievalService


async def main():
    service = RAGRetrievalService()

    question = "What documents are required during company registration?"
    project_id = "AzureDevOpsAI"

    results = await service.retrieve(
        question=question,
        project_id=project_id,
        limit=5,
    )

    print("Question:", question)
    print("Retrieved chunks:", len(results))
    for index, result in enumerate(results, start=1):
        print(f"\n--- Result {index} ---")
        print("Page:", result["page_number"])
        print("Chunk:", result["chunk_index"])
        print("RRF Score:", round(result["rrf_score"], 6))
        print("Content:")
        print(result["content"][:500])
        
        print("Semantic rank:", result["semantic_rank"])
        print("Keyword rank:", result["keyword_rank"]) 
        print("RRF score:", round(result["rrf_score"], 6))

if __name__ == "__main__":
    asyncio.run(main())
