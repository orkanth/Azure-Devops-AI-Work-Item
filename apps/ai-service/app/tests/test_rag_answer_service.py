
import asyncio

from app.services.rag_answer_service import RAGAnswerService


async def main():
    service = RAGAnswerService()

    question = (
        "What documents are required during company registration?"
    )

    result = await service.answer_question(
        question=question,
        project_id="AzureDevOpsAI",
        limit=5,
    )

    print("\n--- USER QUESTION ---")
    print(result["question"])

    print("\n--- AI GENERATED ANSWER ---")
    print(result["answer"])

    print("\n--- SOURCE REFERENCES ---")

    for source in result["sources"]:
        print(
            f"Source {source['source']} | "
            f"Page: {source['page_number']} | "
            f"Chunk: {source['chunk_index']} | "
            f"RRF: {source['rrf_score']}"
        )


if __name__ == "__main__":
    asyncio.run(main())
