
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.document_extractor import extract_document
from io import BytesIO
from pathlib import Path

from docx import Document
from pypdf import PdfReader

router = APIRouter()
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

@router.post("/documents/extract")
async def extract_uploaded_document(
    file: UploadFile = File(...),
):
    try:
        if not file.filename:
            raise HTTPException(
                status_code=400,
                    detail="Filename is required.",
                )

        # Step 1: Read at most 10 MB + 1 byte
        file_content = await file.read(MAX_FILE_SIZE + 1)

        # Step 2: Check file size
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File size exceeds the maximum allowed size of 10 MB.",
            )

        # Step 3: Check whether the file is empty
        if not file_content:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty.",
            )

        # Step 4: Extract document content
        result = extract_document(
            file_name=file.filename,
            file_content=file_content,
        )

        return {
            "status": "success",
            "file_name": file.filename,
            "message": "Document text extracted successfully.",
            "data": result,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=415,
            detail=str(exc),
        ) from exc

    finally:
        await file.close()
        
def extract_pdf(file_content: bytes) -> dict:
    if not file_content.startswith(b"%PDF-"):
        raise ValueError("Invalid PDF file content.")

    reader = PdfReader(BytesIO(file_content))