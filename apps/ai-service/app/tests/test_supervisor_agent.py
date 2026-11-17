import pytest
from unittest.mock import AsyncMock, MagicMock

from app.agents.supervisor.agent import (
    SupervisorAgent,
    SupervisorDecision,
)


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    structured_llm = MagicMock()

    llm.with_structured_output.return_value = structured_llm

    return llm, structured_llm


@pytest.mark.asyncio
async def test_routes_work_item_request(mock_llm):
    llm, structured_llm = mock_llm

    structured_llm.ainvoke = AsyncMock(
        return_value=SupervisorDecision(
            next_agent="work_items",
            reason="The user requested work items.",
        )
    )

    agent = SupervisorAgent(llm=llm)

    result = await agent({"question": "Show all active tasks"})

    assert result["next_agent"] == "work_items"
    assert result["status"] == "routing"


@pytest.mark.asyncio
async def test_routes_user_request(mock_llm):
    llm, structured_llm = mock_llm

    structured_llm.ainvoke = AsyncMock(
        return_value=SupervisorDecision(
            next_agent="users",
            reason="The user requested user information.",
        )
    )

    agent = SupervisorAgent(llm=llm)

    result = await agent({"question": "Find Ravi Kumar"})

    assert result["next_agent"] == "users"


@pytest.mark.asyncio
async def test_routes_rag_request(mock_llm):
    llm, structured_llm = mock_llm

    structured_llm.ainvoke = AsyncMock(
        return_value=SupervisorDecision(
            next_agent="rag",
            reason="The user asked about project documentation.",
        )
    )

    agent = SupervisorAgent(llm=llm)

    result = await agent({"question": "Explain the authentication requirements"})

    assert result["next_agent"] == "rag"


@pytest.mark.asyncio
async def test_routes_generation_request(mock_llm):
    llm, structured_llm = mock_llm

    structured_llm.ainvoke = AsyncMock(
        return_value=SupervisorDecision(
            next_agent="generation",
            reason="The user requested work-item generation.",
        )
    )

    agent = SupervisorAgent(llm=llm)

    result = await agent({"question": "Generate an Epic for user management"})

    assert result["next_agent"] == "generation"


@pytest.mark.asyncio
async def test_handles_clarification(mock_llm):
    llm, structured_llm = mock_llm

    structured_llm.ainvoke = AsyncMock(
        return_value=SupervisorDecision(
            next_agent="clarification",
            reason="The request is ambiguous.",
            clarification_question="Which project are you referring to?",
        )
    )

    agent = SupervisorAgent(llm=llm)

    result = await agent({"question": "Show me that"})

    assert result["status"] == "needs_clarification"
    assert result["next_agent"] == "clarification"


@pytest.mark.asyncio
async def test_rejects_empty_question(mock_llm):
    llm, _ = mock_llm

    agent = SupervisorAgent(llm=llm)

    with pytest.raises(ValueError):
        await agent({"question": ""})
