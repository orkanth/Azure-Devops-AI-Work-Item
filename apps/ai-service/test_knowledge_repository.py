
import asyncio
from pathlib import Path

from app.services.document_extractor import extract_document
from app.services.document_processor import DocumentProcessor
from app.repositories.knowledge_repository import KnowledgeRepository


async def main():

    file_name = "Requirement.pdf"

    pdf_path = Path(
        r"D:\Learning\Prototype\Azure-Devops-AI-Work-Item\local-data\documents\806275ba-64d9-4945-8320-069e519909bc\Requirement.pdf"
    )

    document_id = "806275ba-64d9-4945-8320-069e519909bc"
    project_id = "AzureDevOpsAI"

    file_content = pdf_path.read_bytes()

    extracted_data = extract_document(
        file_name=file_name,
        file_content=file_content,
    )

    processor = DocumentProcessor()

    chunks = await processor.process_document(
        document_id=document_id,
        project_id=project_id,
        file_name=file_name,
        extracted_data=extracted_data,
    )

    repository = KnowledgeRepository()

    saved_count = repository.save_chunks(chunks)

    print("Successfully saved chunks:", saved_count)


if __name__ == "__main__":
    asyncio.run(main())
