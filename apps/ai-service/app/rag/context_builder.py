
import re


class RAGContextBuilder:

    def build_context(self, chunks: list[dict]) -> str:

        if not chunks:
            return ""

        context_parts = []

        for index, chunk in enumerate(chunks, start=1):

            content = chunk.get("content", "")
            content = re.sub(r"\s+", " ", content).strip()

            file_name = chunk.get("file_name", "Unknown document")
            page_number = chunk.get("page_number")
            chunk_index = chunk.get("chunk_index")

            source = (
                f"[Source {index}]\n"
                f"Document: {file_name}\n"
                f"Document ID: {chunk['document_id']}\n"
                f"Page: {page_number if page_number is not None else 'N/A'}\n"
                f"Chunk: {chunk_index}\n\n"
                f"Content:\n{content}"
            )

            context_parts.append(source)

        return "\n\n".join(context_parts)
