
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.rag.agent import RAGAgent


@pytest.fixture
def agent():
    retrieval_service = MagicMock()
    retrieval_service.retrieve = AsyncMock(
        return_value={
            "context": "[Source 1]\nDocument: Requirement.pdf\nContent: AI development.",
            "chunks": [
                {
                    "document_id": "doc-123",
                    "chunk_index": 0,
                    "page_number": 2,
                    "metadata": {"source": "Requirement.pdf"},
                }
            ],
            "total_results": 1,
        }
    )

    llm_service = MagicMock()
    llm_service.llm.ainvoke = AsyncMock(
        return_value=MagicMock(
            content="The developer builds AI solutions [Source 1]."
        )
    )

    return RAGAgent(
        retrieval_service=retrieval_service,
        llm_service=llm_service,
    )


@pytest.mark.asyncio
async def test_answer_question_success(agent):
    result = await agent.answer_question(
        "What does the developer do?",
        "AzureDevOpsAI",
    )

    assert "[Source 1]" in result["answer"]
    assert result["total_results"] == 1
    assert result["sources"][0]["page_number"] == 2


@pytest.mark.asyncio
async def test_answer_question_calls_retrieval(agent):
    await agent.answer_question(
        "Explain the developer role",
        "AzureDevOpsAI",
    )

    agent.retrieval_service.retrieve.assert_awaited_once()


@pytest.mark.asyncio
async def test_answer_question_calls_llm(agent):
    await agent.answer_question(
        "Explain the developer role",
        "AzureDevOpsAI",
    )

    agent.llm_service.llm.ainvoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_answer_question_rejects_empty_question(agent):
    with pytest.raises(ValueError, match="Question cannot be empty"):
        await agent.answer_question("", "AzureDevOpsAI")


@pytest.mark.asyncio
async def test_answer_question_rejects_empty_project(agent):
    with pytest.raises(ValueError, match="Project ID cannot be empty"):
        await agent.answer_question("Test question", "")


@pytest.mark.asyncio
async def test_answer_question_handles_no_context(agent):
    agent.retrieval_service.retrieve.return_value = {
        "context": "",
        "chunks": [],
        "total_results": 0,
    }

    result = await agent.answer_question(
        "What is the project architecture?",
        "AzureDevOpsAI",
    )

    assert result["total_results"] == 0
    assert result["sources"] == []
    agent.llm_service.llm.ainvoke.assert_not_called()
