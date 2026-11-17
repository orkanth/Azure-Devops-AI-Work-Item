
import asyncio

from app.services.document_extractor import extract_document
from app.services.document_processor import DocumentProcessor
from app.repositories.knowledge_repository import KnowledgeRepository


class DocumentIngestionService:
    """Orchestrate document extraction, processing and persistence."""

    def __init__(
        self,
        processor: DocumentProcessor | None = None,
        repository: KnowledgeRepository | None = None,
    ):
        self.processor = processor or DocumentProcessor()
        self.repository = repository or KnowledgeRepository()

    async def ingest_document(
        self,
        document_id: str,
        project_id: str,
        file_name: str,
        file_content: bytes,
    ) -> dict:
        """Extract, chunk, embed and persist a document."""

        self._validate_input(
            document_id,
            project_id,
            file_name,
            file_content,
        )

        # Step 1: Extract document content.
        extracted_data = extract_document(
            file_name=file_name,
            file_content=file_content,
        )

        # Step 2: Generate chunks and embeddings.
        chunks = await self.processor.process_document(
            document_id=document_id,
            project_id=project_id,
            file_name=file_name,
            extracted_data=extracted_data,
        )

        if not chunks:
            raise ValueError(
                "The document contains no extractable text."
            )

        # Step 3: Persist chunks without blocking the async event loop.
        saved_count = await asyncio.to_thread(
            self.repository.save_chunks,
            chunks,
        )

        return {
            "document_id": document_id,
            "project_id": project_id,
            "file_name": file_name,
            "chunk_count": saved_count,
            "status": "completed",
        }

    @staticmethod
    def _validate_input(
        document_id: str,
        project_id: str,
        file_name: str,
        file_content: bytes,
    ) -> None:
        if not isinstance(document_id, str) or not document_id.strip():
            raise ValueError("Document ID is required.")

        if not isinstance(project_id, str) or not project_id.strip():
            raise ValueError("Project ID is required.")

        if not isinstance(file_name, str) or not file_name.strip():
            raise ValueError("File name is required.")

        if not isinstance(file_content, bytes) or not file_content:
            raise ValueError("Document content must be non-empty bytes.")
