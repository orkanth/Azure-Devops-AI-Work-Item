
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.rag.ingestion import DocumentIngestionService


@pytest.fixture
def service():
    processor = MagicMock()
    processor.process_document = AsyncMock()

    repository = MagicMock()
    repository.save_chunks.return_value = 2

    return DocumentIngestionService(
        processor=processor,
        repository=repository,
    ), processor, repository


@pytest.mark.asyncio
async def test_ingest_document_success(service):
    ingestion, processor, repository = service

    chunks = [
        {"content": "First chunk"},
        {"content": "Second chunk"},
    ]

    processor.process_document.return_value = chunks

    extracted_data = {
        "file_type": "docx",
        "full_text": "Sample document content",
    }

    with patch(
        "app.rag.ingestion.extract_document",
        return_value=extracted_data,
    ) as extractor:
        result = await ingestion.ingest_document(
            document_id="doc-123",
            project_id="project-123",
            file_name="sample.docx",
            file_content=b"document-content",
        )

    extractor.assert_called_once_with(
        file_name="sample.docx",
        file_content=b"document-content",
    )

    processor.process_document.assert_awaited_once_with(
        document_id="doc-123",
        project_id="project-123",
        file_name="sample.docx",
        extracted_data=extracted_data,
    )

    repository.save_chunks.assert_called_once_with(chunks)

    assert result["status"] == "completed"
    assert result["chunk_count"] == 2


@pytest.mark.asyncio
async def test_ingest_document_rejects_empty_content(service):
    ingestion, processor, repository = service

    with pytest.raises(ValueError, match="non-empty bytes"):
        await ingestion.ingest_document(
            document_id="doc-123",
            project_id="project-123",
            file_name="sample.docx",
            file_content=b"",
        )

    processor.process_document.assert_not_called()
    repository.save_chunks.assert_not_called()


@pytest.mark.asyncio
async def test_ingest_document_rejects_missing_project_id(service):
    ingestion, processor, repository = service

    with pytest.raises(ValueError, match="Project ID"):
        await ingestion.ingest_document(
            document_id="doc-123",
            project_id=" ",
            file_name="sample.docx",
            file_content=b"document-content",
        )

    processor.process_document.assert_not_called()
    repository.save_chunks.assert_not_called()


@pytest.mark.asyncio
async def test_ingest_document_rejects_empty_chunks(service):
    ingestion, processor, repository = service

    processor.process_document.return_value = []

    with patch(
        "app.rag.ingestion.extract_document",
        return_value={"file_type": "docx", "full_text": ""},
    ):
        with pytest.raises(
            ValueError,
            match="no extractable text",
        ):
            await ingestion.ingest_document(
                document_id="doc-123",
                project_id="project-123",
                file_name="empty.docx",
                file_content=b"document-content",
            )

    repository.save_chunks.assert_not_called()
