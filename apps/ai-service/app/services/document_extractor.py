
from io import BytesIO
from pathlib import Path

from docx import Document
from pypdf import PdfReader
from zipfile import ZipFile, BadZipFile

def extract_pdf(file_content: bytes) -> dict:
    """
    Extract text from a PDF document, page by page.
    """

    reader = PdfReader(BytesIO(file_content))

    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""

        pages.append({
            "page_number": page_number,
            "text": text.strip(),
        })

    return {
        "file_type": "pdf",
        "page_count": len(pages),
        "pages": pages,
        "full_text": "\n\n".join(
            page["text"] for page in pages
        ),
    }



def extract_docx(file_content: bytes) -> dict:
    try:
        with ZipFile(BytesIO(file_content)) as archive:
            if "word/document.xml" not in archive.namelist():
                raise ValueError("Invalid DOCX file content.")

    except BadZipFile as exc:
        raise ValueError("Invalid DOCX file content.") from exc
 

    document = Document(BytesIO(file_content))

    # 1. Extract normal paragraphs.
    paragraphs = [
        paragraph.text.strip()
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    ]

    # 2. Extract tables.
    tables = []

    for table_index, table in enumerate(document.tables, start=1):
        table_rows = []

        for row in table.rows:
            cells = [
                cell.text.strip().replace("\n", " ")
                for cell in row.cells
            ]

            table_rows.append(" | ".join(cells))

        tables.append({
            "table_number": table_index,
            "rows": table_rows,
        })

    # 3. Combine paragraphs and tables into searchable text.
    text_sections = []

    if paragraphs:
        text_sections.append("\n".join(paragraphs))

    for table in tables:
        table_text = "\n".join(table["rows"])

        text_sections.append(
            f"\n[TABLE {table['table_number']}]\n{table_text}"
        )

    full_text = "\n\n".join(text_sections)

    return {
        "file_type": "docx",
        "paragraph_count": len(paragraphs),
        "table_count": len(tables),
        "tables": tables,
        "full_text": full_text,
    }

def extract_document(
    file_name: str,
    file_content: bytes,
) -> dict:
    """
    Identify the document type and extract its text.
    """

    extension = Path(file_name).suffix.lower()

    if extension == ".pdf":
        return extract_pdf(file_content)

    if extension == ".docx":
        return extract_docx(file_content)

    raise ValueError(
        f"Unsupported document format: {extension}"
    )
