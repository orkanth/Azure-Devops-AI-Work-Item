from io import BytesIO

from docx import Document
from pypdf import PdfWriter

from app.services.document_extractor import extract_document
from app.rag.chunker import chunk_extracted_document


def create_test_pdf() -> bytes:
    """Create a minimal PDF for testing."""

    buffer = BytesIO()

    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.write(buffer)

    return buffer.getvalue()


def create_test_docx() -> bytes:
    """Create a DOCX document for testing."""

    buffer = BytesIO()

    document = Document()
    document.add_heading("DevFlow AI Test Document", level=1)
    document.add_paragraph(
        "This document contains sample content for testing "
        "document extraction and chunk generation."
    )

    document.save(buffer)

    return buffer.getvalue()


def validate_chunks(chunks: list[dict]) -> None:
    """Validate metadata-aware document chunks."""

    assert len(chunks) > 0

    assert all(chunk["document_id"] == "integration-test-document" for chunk in chunks)

    assert all(chunk["chunk_index"] == index for index, chunk in enumerate(chunks))

    assert all(len(chunk["content"]) <= 1000 for chunk in chunks)


def test_pdf_document_pipeline():

    file_name = "sample.pdf"
    file_content = create_test_pdf()

    extracted_data = extract_document(
        file_name=file_name,
        file_content=file_content,
    )

    assert extracted_data["file_type"] == "pdf"

    # A blank PDF contains no extractable text.
    # Verify extraction separately without requiring chunks.
    assert extracted_data["page_count"] == 1


def test_docx_document_pipeline():

    file_name = "sample.docx"
    file_content = create_test_docx()

    extracted_data = extract_document(
        file_name=file_name,
        file_content=file_content,
    )

    assert extracted_data["file_type"] == "docx"
    assert "DevFlow AI Test Document" in extracted_data["full_text"]

    chunks = chunk_extracted_document(
        document_id="integration-test-document",
        file_name=file_name,
        extracted_data=extracted_data,
    )

    validate_chunks(chunks)
