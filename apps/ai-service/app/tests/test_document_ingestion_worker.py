
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.document_ingestion_worker import DocumentIngestionWorker


@pytest.fixture
def worker():
    client = MagicMock()
    client.claim_ingestion_job = AsyncMock()
    client.get_document_content = AsyncMock()
    client.complete_ingestion_job = AsyncMock()
    client.fail_ingestion_job = AsyncMock()

    ingestion_service = MagicMock()
    ingestion_service.ingest_document = AsyncMock()

    return DocumentIngestionWorker(
        ingestion_service=ingestion_service,
        client=client,
    ), client, ingestion_service


@pytest.mark.asyncio
async def test_process_next_job_success(worker):
    service, client, ingestion = worker

    client.claim_ingestion_job.return_value = {
        "id": "job-123",
        "document": {
            "id": "doc-123",
            "projectId": "project-123",
            "fileName": "requirements.docx",
        },
    }

    client.get_document_content.return_value = b"document bytes"

    ingestion.ingest_document.return_value = {
        "document_id": "doc-123",
        "chunk_count": 2,
        "status": "completed",
    }

    result = await service.process_next_job()

    ingestion.ingest_document.assert_awaited_once_with(
        document_id="doc-123",
        project_id="project-123",
        file_name="requirements.docx",
        file_content=b"document bytes",
    )

    client.complete_ingestion_job.assert_awaited_once_with("job-123")
    client.fail_ingestion_job.assert_not_awaited()

    assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_process_next_job_reports_failure(worker):
    service, client, ingestion = worker

    client.claim_ingestion_job.return_value = {
        "id": "job-123",
        "document": {
            "id": "doc-123",
            "projectId": "project-123",
            "fileName": "requirements.docx",
        },
    }

    client.get_document_content.return_value = b"document bytes"

    ingestion.ingest_document.side_effect = ValueError(
        "Invalid document content"
    )

    result = await service.process_next_job()

    client.fail_ingestion_job.assert_awaited_once_with(
        "job-123",
        "Invalid document content",
    )

    client.complete_ingestion_job.assert_not_awaited()

    assert result["status"] == "failed"


@pytest.mark.asyncio
async def test_process_next_job_returns_none_when_queue_empty(worker):
    service, client, ingestion = worker

    client.claim_ingestion_job.return_value = None

    result = await service.process_next_job()

    assert result is None
    client.get_document_content.assert_not_awaited()
    ingestion.ingest_document.assert_not_awaited()
