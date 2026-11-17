
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.rag.retrieval import RAGRetrievalService


@pytest.fixture
def service():
    embedding_service = MagicMock()
    embedding_service.embed_text = AsyncMock(
        return_value=[0.1] * 1536
    )

    repository = MagicMock()
    repository.search_hybrid_chunks.return_value = [
        {
            "content": "The developer builds AI applications.",
            "document_id": "doc-123",
            "chunk_index": 0,
            "page_number": 1,
            "metadata": {"source": "Requirement.pdf"},
        }
    ]

    context_builder = MagicMock()
    context_builder.build_context.return_value = (
        "Document: Requirement.pdf\n"
        "Content: The developer builds AI applications."
    )

    return RAGRetrievalService(
        embedding_service=embedding_service,
        knowledge_repository=repository,
        context_builder=context_builder,
    )


@pytest.mark.asyncio
async def test_retrieve_success(service):
    result = await service.retrieve(
        query="What does the developer do?",
        project_id="AzureDevOpsAI",
    )

    assert result["total_results"] == 1
    assert result["project_id"] == "AzureDevOpsAI"
    assert "developer builds AI applications" in result["context"]


@pytest.mark.asyncio
async def test_retrieve_generates_embedding(service):
    await service.retrieve(
        query="Explain the developer role",
        project_id="AzureDevOpsAI",
    )

    service.embedding_service.embed_text.assert_awaited_once_with(
        "Explain the developer role"
    )


@pytest.mark.asyncio
async def test_retrieve_uses_project_scoped_hybrid_search(service):
    await service.retrieve(
        query="Explain the developer role",
        project_id="AzureDevOpsAI",
        limit=5,
    )

    service.knowledge_repository.search_hybrid_chunks.assert_called_once_with(
        "Explain the developer role",
        [0.1] * 1536,
        "AzureDevOpsAI",
        5,
    )


@pytest.mark.asyncio
async def test_retrieve_rejects_empty_query(service):
    with pytest.raises(ValueError, match="Query cannot be empty"):
        await service.retrieve("", "AzureDevOpsAI")


@pytest.mark.asyncio
async def test_retrieve_rejects_empty_project(service):
    with pytest.raises(ValueError, match="Project ID cannot be empty"):
        await service.retrieve("Test question", "")


@pytest.mark.asyncio
async def test_retrieve_rejects_invalid_limit(service):
    with pytest.raises(ValueError, match="positive integer"):
        await service.retrieve(
            "Test question",
            "AzureDevOpsAI",
            limit=0,
        )
