
from app.services.rag_answer_service import RAGAnswerService


def test_extract_cited_sources():
    service = RAGAnswerService.__new__(RAGAnswerService)

    chunks = [
        {
            "document_id": "doc-1",
            "file_name": "Requirement.pdf",
            "page_number": 4,
            "chunk_index": 8,
        },
        {
            "document_id": "doc-1",
            "file_name": "Requirement.pdf",
            "page_number": 5,
            "chunk_index": 9,
        },
    ]

    answer = """
    GST Certificate is required. [Source 1]
    PAN is required. [Source 1]
    Business documents are required. [Source 2]
    [Source 10]
    """

    sources = service.extract_cited_sources(answer, chunks)

    assert len(sources) == 2
    assert sources[0]["source"] == 1
    assert sources[1]["source"] == 2
    assert sources[0]["file_name"] == "Requirement.pdf"


def test_extract_cited_sources_without_citations():
    service = RAGAnswerService.__new__(RAGAnswerService)

    chunks = [
        {
            "document_id": "doc-1",
            "file_name": "Requirement.pdf",
            "page_number": 4,
            "chunk_index": 8,
        }
    ]

    sources = service.extract_cited_sources(
        "No citations in this answer.",
        chunks,
    )

    assert sources == []
