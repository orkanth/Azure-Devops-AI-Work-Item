
import asyncio

from app.rag.retrieval import RAGRetrievalService


async def main():
    service = RAGRetrievalService()

    result = await service.retrieve(
        query="What are the responsibilities of the Senior AI Developer?",
        project_id="AzureDevOpsAI",
        limit=5,
    )

    print("\nTotal results:", result["total_results"])
    print("\nRetrieved context:\n")
    print(result["context"])

    assert result["total_results"] > 0, "No relevant chunks retrieved."


if __name__ == "__main__":
    asyncio.run(main())
