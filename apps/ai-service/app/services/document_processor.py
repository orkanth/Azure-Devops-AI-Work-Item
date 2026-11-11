
from app.rag.chunker import chunk_extracted_document
from app.services.embedding_service import EmbeddingService


class DocumentProcessor:

    def __init__(self):
        self.embedding_service = EmbeddingService()

    async def process_document(
        self,
        document_id: str,
        project_id: str,
        file_name: str,
        extracted_data: dict,
    ) -> list[dict]:

        # Step 1: Generate metadata-aware chunks
        chunks = chunk_extracted_document(
            document_id=document_id,
            file_name=file_name,
            extracted_data=extracted_data,
        )

        if not chunks:
            return []

        # Step 2: Extract text from every chunk
        texts = [
            chunk["content"]
            for chunk in chunks
        ]

        # Step 3: Generate embeddings in a batch
        embeddings = await self.embedding_service.generate_embeddings(
            texts
        )

        if len(embeddings) != len(chunks):
            raise ValueError(
                "Embedding count does not match chunk count."
            )

        # Step 4: Attach project ID and embeddings
        for chunk, embedding in zip(chunks, embeddings):
            chunk["project_id"] = project_id
            chunk["embedding"] = embedding

        return chunks
