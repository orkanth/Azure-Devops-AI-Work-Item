import asyncio

from app.services.rag_retrieval_service import RAGRetrievalService
from app.rag.context_builder import RAGContextBuilder


async def main():
    question = "What documents are required during company registration?"
    project_id = "AzureDevOpsAI"

    # Step 1: Retrieve relevant chunks
    retrieval_service = RAGRetrievalService()

    chunks = await retrieval_service.retrieve(
        question=question,
        project_id=project_id,
        limit=5,
    )

    print("Retrieved chunks:", len(chunks))

    # Step 2: Build LLM context
    context_builder = RAGContextBuilder()

    context = context_builder.build_context(chunks)

    print("\n--- GENERATED RAG CONTEXT ---")
    print(context)


if __name__ == "__main__":
    asyncio.run(main())