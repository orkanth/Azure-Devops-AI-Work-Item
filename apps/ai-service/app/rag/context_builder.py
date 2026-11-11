
import re


class RAGContextBuilder:
    """
    Builds structured context from retrieved document chunks
    for use in LLM prompts.
    """

    def build_context(self, chunks: list[dict]) -> str:
        if not chunks:
            return ""

        context_parts = []

        for index, chunk in enumerate(chunks, start=1):
            content = chunk.get("content", "")

            # Normalize excessive whitespace from PDF extraction.
            content = re.sub(r"\s+", " ", content).strip()

            source = (
                f"SOURCE {index}\n"
                f"Document ID: {chunk['document_id']}\n"
                f"Page: {chunk.get('page_number')}\n"
                f"Chunk: {chunk['chunk_index']}\n\n"
                f"Content:\n{content}"
            )

            context_parts.append(source)

        return "\n\n".join(context_parts)
