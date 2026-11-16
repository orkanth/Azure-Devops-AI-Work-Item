
from pathlib import Path

from app.services.document_extractor import extract_document


PROJECT_ROOT = Path(__file__).resolve().parents[2]

file_path = (
    PROJECT_ROOT
    / "local-data"
    / "documents"
    / "4c7a7f76-250f-449f-9257-b27bb62b6940"
    / "INFINITY_SPORTZ-_Concept_Note_.docx"
)

print("Looking for:", file_path)
print("File exists:", file_path.exists())

if not file_path.exists():
    raise FileNotFoundError(f"DOCX not found: {file_path}")

file_content = file_path.read_bytes()

result = extract_document(
    file_name=file_path.name,
    file_content=file_content,
)
print("\nFile type:", result["file_type"])
print("Paragraph count:", result["paragraph_count"])
print("Table count:", result["table_count"])

print("\nExtracted text:")
print(result["full_text"][:3000])