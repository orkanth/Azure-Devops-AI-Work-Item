
import pytest

from app.rag.context_builder import RAGContextBuilder


@pytest.fixture
def context_builder():
    return RAGContextBuilder()


def test_build_context_returns_empty_string_for_empty_chunks(context_builder):
    result = context_builder.build_context([])

    assert result == ""


def test_build_context_formats_single_chunk(context_builder):
    chunks = [
        {
            "document_id": "doc-123",
            "file_name": "User_Management_API.docx",
            "page_number": 2,
            "chunk_index": 0,
            "content": "The API supports creating users.",
        }
    ]

    result = context_builder.build_context(chunks)

    assert "[Source 1]" in result
    assert "Document: User_Management_API.docx" in result
    assert "Document ID: doc-123" in result
    assert "Page: 2" in result
    assert "Chunk: 0" in result
    assert "The API supports creating users." in result


def test_build_context_reads_filename_from_metadata(context_builder):
    chunks = [
        {
            "document_id": "doc-123",
            "page_number": None,
            "chunk_index": 0,
            "metadata": {"source": "User_Management_API.docx"},
            "content": "User creation endpoint details.",
        }
    ]

    result = context_builder.build_context(chunks)

    assert "Document: User_Management_API.docx" in result
    assert "Page: N/A" in result


def test_build_context_formats_multiple_chunks(context_builder):
    chunks = [
        {
            "document_id": "doc-123",
            "file_name": "API.docx",
            "page_number": 1,
            "chunk_index": 0,
            "content": "First chunk.",
        },
        {
            "document_id": "doc-123",
            "file_name": "API.docx",
            "page_number": 2,
            "chunk_index": 1,
            "content": "Second chunk.",
        },
    ]

    result = context_builder.build_context(chunks)

    assert "[Source 1]" in result
    assert "[Source 2]" in result
    assert "First chunk." in result
    assert "Second chunk." in result


def test_build_context_handles_missing_document_id(context_builder):
    chunks = [
        {
            "file_name": "API.docx",
            "chunk_index": 0,
            "content": "Some content.",
        }
    ]

    result = context_builder.build_context(chunks)

    assert "Document ID: Unknown" in result


def test_build_context_skips_empty_content(context_builder):
    chunks = [
        {
            "document_id": "doc-123",
            "content": "   ",
        },
        {
            "document_id": "doc-123",
            "content": "Valid content.",
        },
    ]

    result = context_builder.build_context(chunks)

    assert "Valid content." in result
    assert "[Source 1]" in result
    assert "[Source 2]" not in result


def test_build_context_normalizes_whitespace(context_builder):
    chunks = [
        {
            "document_id": "doc-123",
            "content": "The API   supports\n\ncreating    users.",
        }
    ]

    result = context_builder.build_context(chunks)

    assert "The API supports creating users." in result
