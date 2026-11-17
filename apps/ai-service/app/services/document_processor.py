
from app.rag.chunker import chunk_extracted_document
from app.rag.embeddings import EmbeddingService


class DocumentProcessor:
    """Convert extracted documents into embedded knowledge chunks."""

    def __init__(self, embedding_service: EmbeddingService | None = None):
        self.embedding_service = embedding_service or EmbeddingService()

    async def process_document(
        self,
        document_id: str,
        project_id: str,
        file_name: str,
        extracted_data: dict,
    ) -> list[dict]:
        if not document_id:
            raise ValueError("Document ID is required.")

        if not isinstance(project_id, str) or not project_id.strip():
            raise ValueError("Project ID is required.")

        if not file_name:
            raise ValueError("File name is required.")

        chunks = chunk_extracted_document(
            document_id=document_id,
            file_name=file_name,
            extracted_data=extracted_data,
        )

        if not chunks:
            return []

        texts = [chunk["content"] for chunk in chunks]

        embeddings = await self.embedding_service.embed_documents(texts)

        if len(embeddings) != len(chunks):
            raise ValueError(
                "Embedding count does not match chunk count."
            )

        for chunk, embedding in zip(chunks, embeddings):
            chunk["project_id"] = project_id
            chunk["embedding"] = embedding

        return chunks

