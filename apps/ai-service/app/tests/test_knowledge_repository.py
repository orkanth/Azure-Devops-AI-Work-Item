
import pytest

from unittest.mock import MagicMock, patch

from app.repositories.knowledge_repository import KnowledgeRepository


@pytest.fixture
def repository():
    return KnowledgeRepository()


@pytest.fixture
def valid_chunks():
    return [
        {
            "document_id": "5e779f8f-cdf7-4395-914e-000000000001",
            "project_id": "project-123",
            "content": "User registration requirements.",
            "chunk_index": 0,
            "page_number": 1,
            "metadata": {"source": "requirements.docx"},
            "embedding": [0.1] * 1536,
        }
    ]


def test_save_chunks_rejects_empty_list(repository):
    with pytest.raises(ValueError, match="empty chunk list"):
        repository.save_chunks([])


def test_save_chunks_rejects_invalid_embedding_dimensions(
    repository,
    valid_chunks,
):
    valid_chunks[0]["embedding"] = [0.1] * 100

    with pytest.raises(ValueError, match="embedding dimensions"):
        repository.save_chunks(valid_chunks)


def test_save_chunks_rejects_missing_project_id(
    repository,
    valid_chunks,
):
    valid_chunks[0]["project_id"] = ""

    with pytest.raises(ValueError, match="Project ID"):
        repository.save_chunks(valid_chunks)


def test_save_chunks_rejects_duplicate_chunk_indexes(
    repository,
    valid_chunks,
):
    second_chunk = {
        **valid_chunks[0],
        "content": "Another chunk.",
    }

    valid_chunks.append(second_chunk)

    with pytest.raises(ValueError, match="Duplicate chunk indexes"):
        repository.save_chunks(valid_chunks)



def test_save_chunks_replaces_existing_chunks(
    repository,
    valid_chunks,
):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = ("project-123",)

    mock_connection = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

    connection_context = MagicMock()
    connection_context.__enter__.return_value = mock_connection

    with patch.object(
        repository,
        "_get_connection",
        return_value=connection_context,
    ):
        result = repository.save_chunks(valid_chunks)

    assert result == 1

    executed_queries = [
        call.args[0]
        for call in mock_cursor.execute.call_args_list
    ]

    assert any("SELECT project_id" in query for query in executed_queries)
    assert any("DELETE FROM knowledge_chunks" in query for query in executed_queries)

    mock_cursor.executemany.assert_called_once()
    mock_connection.commit.assert_not_called()

def test_save_chunks_rolls_back_when_insert_fails(
    repository,
    valid_chunks,
):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = ("project-123",)

    mock_cursor.executemany.side_effect = Exception(
        "Database insertion failed"
    )

    mock_connection = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

    connection_context = MagicMock()
    connection_context.__enter__.return_value = mock_connection

    with patch.object(
        repository,
        "_get_connection",
        return_value=connection_context,
    ):
        with pytest.raises(Exception, match="Database insertion failed"):
            repository.save_chunks(valid_chunks)

    connection_context.__exit__.assert_called_once()
    assert connection_context.__exit__.call_args.args[0] is not None
    
    
def test_search_hybrid_chunks_combines_semantic_and_keyword_results(repository):
    semantic_results = [
        {
            "document_id": "doc-1",
            "chunk_index": 0,
            "content": "User registration",
            "similarity": 0.95,
        },
        {
            "document_id": "doc-1",
            "chunk_index": 1,
            "content": "User authentication",
            "similarity": 0.85,
        },
    ]

    keyword_results = [
        {
            "document_id": "doc-1",
            "chunk_index": 1,
            "content": "User authentication",
            "keyword_score": 0.8,
        },
        {
            "document_id": "doc-1",
            "chunk_index": 2,
            "content": "User permissions",
            "keyword_score": 0.7,
        },
    ]

    with (
        patch.object(
            repository,
            "search_similar_chunks",
            return_value=semantic_results,
        ),
        patch.object(
            repository,
            "search_keyword_chunks",
            return_value=keyword_results,
        ),
    ):
        results = repository.search_hybrid_chunks(
            query="user management",
            query_embedding=[0.1] * 1536,
            project_id="project-123",
        )

    assert len(results) == 3

    # Chunk 1 appears in both searches and should rank first.
    assert results[0]["chunk_index"] == 1

    assert results[0]["semantic_rank"] == 2
    assert results[0]["keyword_rank"] == 1

    assert results[0]["rrf_score"] == (
        1 / (60 + 2) + 1 / (60 + 1)
    )

def test_search_similar_chunks_rejects_invalid_embedding(repository):
    with pytest.raises(ValueError, match="embedding dimensions"):
        repository.search_similar_chunks(
            query_embedding=[0.1] * 100,
            project_id="project-123",
        )


def test_search_similar_chunks_rejects_invalid_limit(repository):
    with pytest.raises(ValueError, match="Limit"):
        repository.search_similar_chunks(
            query_embedding=[0.1] * 1536,
            project_id="project-123",
            limit=0,
        )
        

def test_search_keyword_chunks_maps_database_results(repository):
    from uuid import UUID

    document_id = UUID("5e779f8f-cdf7-4395-914e-000000000001")

    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        (
            document_id,
            "project-123",
            "requirements.docx",
            "User registration requirements",
            0,
            1,
            {"source": "requirements.docx"},
            0.85,
        )
    ]

    mock_connection = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

    connection_context = MagicMock()
    connection_context.__enter__.return_value = mock_connection

    with patch.object(
        repository,
        "_get_connection",
        return_value=connection_context,
    ):
        results = repository.search_keyword_chunks(
            query="user registration",
            project_id="project-123",
        )

    assert len(results) == 1
    assert results[0]["document_id"] == str(document_id)
    assert results[0]["project_id"] == "project-123"
    assert results[0]["file_name"] == "requirements.docx"
    assert results[0]["content"] == "User registration requirements"
    assert results[0]["chunk_index"] == 0
    assert results[0]["page_number"] == 1
    assert results[0]["metadata"] == {"source": "requirements.docx"}
    assert results[0]["keyword_score"] == 0.85

    mock_cursor.execute.assert_called_once()


def test_search_similar_chunks_maps_database_results(repository):
    from uuid import UUID

    document_id = UUID("5e779f8f-cdf7-4395-914e-000000000001")

    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        (
            document_id,
            "project-123",
            "requirements.docx",
            "User registration requirements",
            0,
            1,
            {"source": "requirements.docx"},
            0.92,
        )
    ]

    mock_connection = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

    connection_context = MagicMock()
    connection_context.__enter__.return_value = mock_connection

    with patch.object(
        repository,
        "_get_connection",
        return_value=connection_context,
    ):
        results = repository.search_similar_chunks(
            query_embedding=[0.1] * 1536,
            project_id="project-123",
        )

    assert len(results) == 1
    assert results[0]["document_id"] == str(document_id)
    assert results[0]["project_id"] == "project-123"
    assert results[0]["file_name"] == "requirements.docx"
    assert results[0]["content"] == "User registration requirements"
    assert results[0]["chunk_index"] == 0
    assert results[0]["page_number"] == 1
    assert results[0]["metadata"] == {"source": "requirements.docx"}
    assert results[0]["similarity"] == 0.92

    mock_cursor.execute.assert_called_once()
