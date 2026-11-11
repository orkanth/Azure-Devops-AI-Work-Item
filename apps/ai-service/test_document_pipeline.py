
from pathlib import Path

from app.services.document_extractor import extract_document
from app.rag.chunker import chunk_extracted_document


PROJECT_ROOT = Path(__file__).resolve().parents[2]

TEST_DOCUMENTS = [
    PROJECT_ROOT
    / "local-data"
    / "documents"
    / "5e779f8f-cdf7-4395-914e-324fe4f16fc8"
    / "0917_FrontEnd_Dev_Exp_Tjaart.pdf",

    PROJECT_ROOT
    / "local-data"
    / "documents"
    / "4c7a7f76-250f-449f-9257-b27bb62b6940"
    / "INFINITY_SPORTZ-_Concept_Note_.docx",
]


for file_path in TEST_DOCUMENTS:

    print(f"\nProcessing: {file_path.name}")

    if not file_path.exists():
        raise FileNotFoundError(file_path)

    # Step 1: Extract document text
    extracted_data = extract_document(
        file_name=file_path.name,
        file_content=file_path.read_bytes(),
    )

    # Step 2: Generate metadata-aware chunks
    chunks = chunk_extracted_document(
        document_id="integration-test-document",
        file_name=file_path.name,
        extracted_data=extracted_data,
    )

    # Step 3: Validate results
    assert len(chunks) > 0

    assert all(
        chunk["document_id"] == "integration-test-document"
        for chunk in chunks
    )

    assert all(
        chunk["chunk_index"] == index
        for index, chunk in enumerate(chunks)
    )

    assert all(
        len(chunk["content"]) <= 1000
        for chunk in chunks
    )

    print("File type:", extracted_data["file_type"])
    print("Total chunks:", len(chunks))
    print("First chunk length:", len(chunks[0]["content"]))
    print("First chunk page:", chunks[0]["page_number"])
    print("First chunk content:")
    print(chunks[0]["content"][:200])

    print("Integration test passed!")

print("\nAll document pipeline tests passed!")
