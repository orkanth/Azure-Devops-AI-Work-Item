
import asyncio

from app.agents.rag.agent import RAGAgent


async def main():
    agent = RAGAgent()

    result = await agent.answer_question(
        question=(
            "What are the key responsibilities of the Senior AI Developer? "
            "Include AI development, MLOps, and cloud AI platform delivery."
        ),
        project_id="AzureDevOpsAI",
        limit=5,
    )

    print("\n========== RAG ANSWER ==========\n")
    print(result["answer"])

    print("\n========== SOURCES ==========\n")
    for source in result["sources"]:
        print(source)

    print("\nTotal retrieved chunks:", result["total_results"])


if __name__ == "__main__":
    asyncio.run(main())
