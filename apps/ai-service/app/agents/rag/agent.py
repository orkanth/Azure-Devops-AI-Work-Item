from app.agents.rag.prompts import RAG_SYSTEM_PROMPT, RAG_USER_PROMPT
from app.rag.retrieval import RAGRetrievalService
from app.services.llm_service import LLMService


class RAGAgent:
    """Agent responsible for answering questions using project documents."""

    def __init__(
        self,
        retrieval_service: RAGRetrievalService | None = None,
        llm_service: LLMService | None = None,
    ):
        self.retrieval_service = retrieval_service or RAGRetrievalService()

        self.llm_service = llm_service or LLMService()
        self.llm = self.llm_service.llm

    async def answer_question(
        self,
        question: str,
        project_id: str,
        limit: int = 5,
    ) -> dict:
        """Retrieve relevant knowledge and generate a grounded answer."""

        if not isinstance(question, str) or not question.strip():
            raise ValueError("Question cannot be empty.")

        if not isinstance(project_id, str) or not project_id.strip():
            raise ValueError("Project ID cannot be empty.")

        # 1. Retrieve relevant project knowledge.
        retrieval_result = await self.retrieval_service.retrieve(
            query=question.strip(),
            project_id=project_id.strip(),
            limit=limit,
        )

        context = retrieval_result["context"]

        # 2. Handle cases where no relevant information was retrieved.
        if not context.strip():
            return {
                "answer": (
                    "I couldn't find relevant information in the "
                    "available project documents to answer this question."
                ),
                "project_id": project_id,
                "sources": [],
                "total_results": 0,
            }

        # 3. Build the LLM prompt.
        user_prompt = RAG_USER_PROMPT.format(
            question=question.strip(),
            context=context,
        )

        messages = [
            ("system", RAG_SYSTEM_PROMPT),
            ("human", user_prompt),
        ]

        # 4. Generate an answer using retrieved context.
        response = await self.llm.ainvoke(messages)

        answer = self._extract_text(response.content)

        if not answer:
            raise ValueError("The RAG LLM returned an empty answer.")

        # 5. Build source references.
        sources = self._build_sources(retrieval_result["chunks"])

        return {
            "answer": answer,
            "project_id": project_id.strip(),
            "sources": sources,
            "total_results": retrieval_result["total_results"],
        }

    @staticmethod
    def _extract_text(content) -> str:
        """Normalize LangChain response content into plain text."""

        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            text_parts = []

            for block in content:
                if isinstance(block, str):
                    text_parts.append(block)

                elif isinstance(block, dict):
                    if block.get("type") in ("text", "output_text"):
                        text = block.get("text")

                        if isinstance(text, str):
                            text_parts.append(text)

            return "\n".join(text_parts).strip()

        return ""

    @staticmethod
    def _build_sources(chunks: list[dict]) -> list[dict]:
        """Build source metadata for retrieved chunks."""

        sources = []

        for index, chunk in enumerate(chunks, start=1):
            metadata = chunk.get("metadata") or {}

            sources.append(
                {
                    "source": f"Source {index}",
                    "document_id": chunk.get("document_id"),
                    "file_name": (
                        chunk.get("file_name")
                        or metadata.get("source")
                        or "Unknown document"
                    ),
                    "page_number": chunk.get("page_number"),
                    "chunk_index": chunk.get("chunk_index"),
                }
            )

        return sources
