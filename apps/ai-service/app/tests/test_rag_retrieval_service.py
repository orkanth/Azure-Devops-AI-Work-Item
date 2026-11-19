from unittest.mock import AsyncMock, MagicMock

import pytest

from app.rag.retrieval import RAGRetrievalService


@pytest.fixture
def retrieval_dependencies():
    embedding_service = MagicMock()
    embedding_service.embed_text = AsyncMock(return_value=[0.1] * 1536)

    knowledge_repository = MagicMock()
    context_builder = MagicMock()

    context_builder.build_context.return_value = "Retrieved project document context."

    return embedding_service, knowledge_repository, context_builder


@pytest.fixture
def retrieval_service(retrieval_dependencies):
    embedding, repository, context_builder = retrieval_dependencies

    return RAGRetrievalService(
        embedding_service=embedding,
        knowledge_repository=repository,
        context_builder=context_builder,
    )


@pytest.mark.asyncio
async def test_retrieve_project_documents_without_specific_reference(
    retrieval_service,
    retrieval_dependencies,
):
    embedding, repository, context_builder = retrieval_dependencies

    repository.search_hybrid_chunks.return_value = [
        {
            "document_id": "doc-123",
            "file_name": "requirements.docx",
            "page_number": 1,
            "chunk_index": 0,
            "content": "User registration requirements.",
        }
    ]

    result = await retrieval_service.retrieve(
        query="What are the registration requirements?",
        project_id="project-123",
    )

    assert result["project_id"] == "project-123"
    assert result["document_id"] is None
    assert result["total_results"] == 1
    assert result["context"] == "Retrieved project document context."

    repository.resolve_document_id.assert_not_called()

    repository.search_hybrid_chunks.assert_called_once_with(
        "What are the registration requirements?",
        [0.1] * 1536,
        "project-123",
        5,
        document_id=None,
    )

    context_builder.build_context.assert_called_once()


@pytest.mark.asyncio
async def test_retrieve_specific_document(
    retrieval_service,
    retrieval_dependencies,
):
    embedding, repository, context_builder = retrieval_dependencies

    document_id = "5e779f8f-cdf7-4395-914e-000000000001"

    repository.resolve_document_id.return_value = document_id

    repository.search_hybrid_chunks.return_value = [
        {
            "document_id": document_id,
            "file_name": "requirements.docx",
            "page_number": 1,
            "chunk_index": 0,
            "content": "User registration requirements.",
        }
    ]

    result = await retrieval_service.retrieve(
        query="Generate registration work items.",
        project_id="project-123",
        document_reference="requirements.docx",
    )

    assert result["document_id"] == document_id
    assert result["total_results"] == 1

    repository.resolve_document_id.assert_called_once_with(
        "project-123",
        "requirements.docx",
    )

    repository.search_hybrid_chunks.assert_called_once_with(
        "Generate registration work items.",
        [0.1] * 1536,
        "project-123",
        5,
        document_id=document_id,
    )


@pytest.mark.asyncio
async def test_retrieve_rejects_empty_query(retrieval_service):
    with pytest.raises(ValueError, match="Query cannot be empty"):
        await retrieval_service.retrieve(
            query=" ",
            project_id="project-123",
        )


@pytest.mark.asyncio
async def test_retrieve_rejects_empty_project_id(retrieval_service):
    with pytest.raises(ValueError, match="Project ID cannot be empty"):
        await retrieval_service.retrieve(
            query="User registration",
            project_id=" ",
        )


@pytest.mark.asyncio
async def test_retrieve_rejects_empty_document_reference(
    retrieval_service,
    retrieval_dependencies,
):
    embedding, repository, context_builder = retrieval_dependencies

    with pytest.raises(ValueError, match="Document reference cannot be empty"):
        await retrieval_service.retrieve(
            query="User registration",
            project_id="project-123",
            document_reference=" ",
        )

    repository.resolve_document_id.assert_not_called()
    embedding.embed_text.assert_not_awaited()
