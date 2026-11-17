
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.rag.embeddings import EmbeddingService


@pytest.fixture
def embedding_service():
    with patch("app.rag.embeddings.OpenAIEmbeddings") as mock_embeddings:
        service = EmbeddingService()
        yield service, mock_embeddings


def test_embedding_service_initialization(embedding_service):
    _, mock_embeddings = embedding_service

    mock_embeddings.assert_called_once()


@pytest.mark.asyncio
async def test_embed_text(embedding_service):
    service, _ = embedding_service

    expected_vector = [0.1] * 1536
    service.embeddings.aembed_query = AsyncMock(
        return_value=expected_vector
    )

    result = await service.embed_text("Create a new user")

    assert result == expected_vector
    assert len(result) == 1536


@pytest.mark.asyncio
async def test_embed_text_rejects_empty_input(embedding_service):
    service, _ = embedding_service

    with pytest.raises(ValueError, match="Text cannot be empty"):
        await service.embed_text("   ")


@pytest.mark.asyncio
async def test_embed_documents(embedding_service):
    service, _ = embedding_service

    expected_vectors = [
        [0.1] * 1536,
        [0.2] * 1536,
    ]

    service.embeddings.aembed_documents = AsyncMock(
        return_value=expected_vectors
    )

    result = await service.embed_documents(
        ["Create a user", "Update a user"]
    )

    assert result == expected_vectors
    assert len(result) == 2
    assert all(len(vector) == 1536 for vector in result)


@pytest.mark.asyncio
async def test_embed_documents_returns_empty_list(embedding_service):
    service, _ = embedding_service

    result = await service.embed_documents([])

    assert result == []


@pytest.mark.asyncio
async def test_embed_documents_rejects_empty_text(embedding_service):
    service, _ = embedding_service

    with pytest.raises(ValueError, match="All document texts"):
        await service.embed_documents(
            ["Create a user", "   "]
        )
