
from app.repositories.knowledge_repository import KnowledgeRepository


def main():

    question = "What documents are required during company registration?"

    repository = KnowledgeRepository()

    results = repository.search_keyword_chunks(
        query=question,
        project_id="AzureDevOpsAI",
        limit=5,
    )

    print("Question:", question)
    print("Retrieved chunks:", len(results))

    for index, result in enumerate(results, start=1):

        print(f"\n--- Result {index} ---")
        print("Page:", result["page_number"])
        print("Chunk:", result["chunk_index"])
        print("Keyword score:", round(result["keyword_score"], 4))
        print("Content:")
        print(result["content"][:500])


if __name__ == "__main__":
    main()
