
import asyncio
from pathlib import Path

from app.services.document_extractor import extract_document
from app.services.document_processor import DocumentProcessor


async def main():

    file_name = "requirements.pdf"

    pdf_path = Path(
        r"D:\Learning\Prototype\Azure-Devops-AI-Work-Item\local-data\documents\806275ba-64d9-4945-8320-069e519909bc\Requirement.pdf"
    )

    file_content = pdf_path.read_bytes()

    print("PDF size:", len(file_content), "bytes")

    # Step 1: Extract document content
    extracted_data = extract_document(
        file_name=file_name,
        file_content=file_content,
    )

    # Step 2: Process document
    processor = DocumentProcessor()

    document_id = "806275ba-64d9-4945-8320-069e519909bc"
    project_id = "AzureDevOpsAI"

    chunks = await processor.process_document(
        document_id=document_id,
        project_id=project_id,
        file_name=file_name,
        extracted_data=extracted_data,
    )

    print("Total chunks:", len(chunks))

    # Step 3: Verify embeddings and metadata
    for chunk in chunks:
        print(
            "Chunk:", chunk["chunk_index"],
            "Dimensions:", len(chunk["embedding"]),
            "Project:", chunk["project_id"],
            "Page:", chunk["page_number"],
        )


if __name__ == "__main__":
    asyncio.run(main())
