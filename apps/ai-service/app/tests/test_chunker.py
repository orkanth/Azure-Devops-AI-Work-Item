
from app.rag.chunker import chunk_extracted_document

sample_pdf = {
    "file_type": "pdf",
    "page_count": 2,
    "pages": [
        {
            "page_number": 1,
            "text": (
                "Authentication uses JWT tokens. "
                * 15
            ),
        },
        {
            "page_number": 2,
            "text": (
                "User permissions are managed through RBAC. "
                * 15
            ),
        },
    ],
    "full_text": "Sample PDF content",
}

chunks = chunk_extracted_document(
    document_id="doc-123",
    file_name="requirements.pdf",
    extracted_data=sample_pdf,
)

print("\nMetadata-aware chunk test")

for chunk in chunks:
    print(chunk)

assert len(chunks) > 0
assert all(
    chunk["document_id"] == "doc-123"
    for chunk in chunks
)
assert all(
    chunk["page_number"] in (1, 2)
    for chunk in chunks
)
assert all(
    chunk["chunk_index"] == index
    for index, chunk in enumerate(chunks)
)

print("Metadata-aware chunk test passed!")
