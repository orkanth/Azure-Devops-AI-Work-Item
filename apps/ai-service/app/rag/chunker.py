
import re


def split_long_sentence(
    sentence: str,
    chunk_size: int,
) -> list[str]:
    """Split an oversized sentence at word boundaries."""

    words = sentence.split()
    pieces = []
    current = ""

    for word in words:
        # Handle a single word larger than the limit.
        if len(word) > chunk_size:
            if current:
                pieces.append(current)
                current = ""

            for start in range(0, len(word), chunk_size):
                pieces.append(word[start:start + chunk_size])

            continue

        candidate = f"{current} {word}" if current else word

        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                pieces.append(current)

            current = word

    if current:
        pieces.append(current)

    return pieces


def split_paragraph(
    paragraph: str,
    chunk_size: int,
) -> list[str]:
    """Split a paragraph into sentence-based segments."""

    sentences = re.split(
        r"(?<=[.!?])\s+",
        paragraph.strip(),
    )

    segments = []

    for sentence in sentences:
        sentence = sentence.strip()

        if not sentence:
            continue

        if len(sentence) <= chunk_size:
            segments.append(sentence)
        else:
            segments.extend(
                split_long_sentence(sentence, chunk_size)
            )

    return segments


def get_overlap(
    text: str,
    overlap_size: int,
) -> str:
    """Get a previous chunk's trailing overlap at a word boundary."""

    if overlap_size <= 0:
        return ""

    overlap = text[-overlap_size:]

    # Prefer a complete-word starting boundary.
    if len(overlap) < len(text):
        first_space = overlap.find(" ")

        if first_space != -1:
            overlap = overlap[first_space + 1:]

    return overlap


def split_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> list[str]:

    if chunk_size <= 0:
        raise ValueError("Chunk size must be greater than zero.")

    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError(
            "Chunk overlap must be non-negative and smaller "
            "than chunk size."
        )

    if not text.strip():
        return []

    paragraphs = [
        paragraph.strip()
        for paragraph in text.split("\n\n")
        if paragraph.strip()
    ]

    segments = []

    for paragraph in paragraphs:
        segments.extend(
            split_paragraph(paragraph, chunk_size)
        )

    chunks = []
    current = ""

    for segment in segments:
        separator = "\n\n" if current else ""
        candidate = current + separator + segment

        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            chunks.append(current)

        overlap = get_overlap(current, chunk_overlap)
        separator = "\n\n" if overlap else ""

        available = chunk_size - len(overlap) - len(separator)

        if len(segment) <= available:
            current = overlap + separator + segment
        else:
            # The segment must fit alongside the overlap.
            # If it does not, start a fresh chunk rather than
            # exceeding the configured size.
            current = segment

    if current:
        chunks.append(current)

    return chunks


def chunk_extracted_document(
    document_id: str,
    file_name: str,
    extracted_data: dict,
) -> list[dict]:
    """
    Convert extracted PDF or DOCX content into
    metadata-aware chunks.
    """

    file_type = extracted_data["file_type"]
    chunks = []

    if file_type == "pdf":
        pages = extracted_data["pages"]

        for page in pages:
            page_chunks = split_text(
                text=page["text"],
                chunk_size=1000,
                chunk_overlap=200,
            )

            for chunk in page_chunks:
                chunks.append({
                    "document_id": document_id,
                    "chunk_index": len(chunks),
                    "page_number": page["page_number"],
                    "file_type": file_type,
                    "content": chunk,
                    "metadata": {
                        "source": file_name,
                    },
                })

    elif file_type == "docx":
        docx_chunks = split_text(
            text=extracted_data["full_text"],
            chunk_size=1000,
            chunk_overlap=200,
        )

        for chunk in docx_chunks:
            chunks.append({
                "document_id": document_id,
                "chunk_index": len(chunks),
                "page_number": None,
                "file_type": file_type,
                "content": chunk,
                "metadata": {
                    "source": file_name,
                },
            })

    else:
        raise ValueError(
            f"Unsupported document type: {file_type}"
        )

    return chunks
