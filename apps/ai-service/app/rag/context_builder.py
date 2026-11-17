
import re


class RAGContextBuilder:
    """Build readable context from retrieved knowledge chunks."""

    def build_context(self, chunks: list[dict]) -> str:
        if not chunks:
            return ""

        context_parts = []

        for chunk in chunks:
            content = chunk.get("content", "")

            if not isinstance(content, str) or not content.strip():
                continue

            content = re.sub(r"\s+", " ", content).strip()

            metadata = chunk.get("metadata") or {}

            # Support both the current chunk structure and repository results.
            file_name = (
                chunk.get("file_name")
                or metadata.get("source")
                or "Unknown document"
            )

            document_id = chunk.get("document_id", "Unknown")
            page_number = chunk.get("page_number")
            chunk_index = chunk.get("chunk_index", "Unknown")
            source_number = len(context_parts) + 1
            source = (
                f"[Source {source_number}]\n"
                f"Document: {file_name}\n"
                f"Document ID: {document_id}\n"
                f"Page: {page_number if page_number is not None else 'N/A'}\n"
                f"Chunk: {chunk_index}\n\n"
                f"Content:\n{content}"
            )

            context_parts.append(source)

        return "\n\n".join(context_parts)
