from io import BytesIO

from docx import Document

from app.services.document_extractor import extract_document


def create_test_docx() -> bytes:
    """Create a DOCX document containing paragraphs and a table."""

    buffer = BytesIO()

    document = Document()

    document.add_heading("DevFlow AI Extraction Test", level=1)

    document.add_paragraph("Testing document paragraph extraction.")

    table = document.add_table(rows=1, cols=2)

    table.rows[0].cells[0].text = "Name"
    table.rows[0].cells[1].text = "Role"

    row = table.add_row()
    row.cells[0].text = "Ravi"
    row.cells[1].text = "Developer"

    document.save(buffer)

    return buffer.getvalue()


def test_docx_extraction():

    file_content = create_test_docx()

    result = extract_document(
        file_name="sample.docx",
        file_content=file_content,
    )

    assert result["file_type"] == "docx"

    assert result["paragraph_count"] >= 2

    assert result["table_count"] == 1

    assert "DevFlow AI Extraction Test" in result["full_text"]

    assert "Ravi" in result["full_text"]

    assert "Developer" in result["full_text"]
