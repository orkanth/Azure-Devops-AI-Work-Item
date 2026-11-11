import asyncio

from app.services.embedding_service import EmbeddingService


async def main():
    service = EmbeddingService()

    texts = [
        "Users authenticate using email and password.",
        "Access tokens expire after 15 minutes.",
        "User permissions are managed through RBAC.",
    ]

    embeddings = await service.generate_embeddings(texts)

    print("Batch embedding successful!")
    print("Total embeddings:", len(embeddings))

    for index, embedding in enumerate(embeddings):
        print(
            f"Chunk {index}: "
            f"Dimensions = {len(embedding)}"
        )


if __name__ == "__main__":
    asyncio.run(main())