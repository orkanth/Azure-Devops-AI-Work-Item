import pytest
from unittest.mock import AsyncMock, MagicMock
from langchain_core.messages import AIMessage, HumanMessage
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


@pytest.mark.asyncio
async def test_supervisor_receives_previous_conversation(mock_llm):
    llm, structured_llm = mock_llm

    structured_llm.ainvoke = AsyncMock(
        return_value=SupervisorDecision(
            next_agent="work_items",
            reason="The user requested Revathi's high-priority tasks.",
        )
    )

    agent = SupervisorAgent(llm=llm)

    previous_messages = [
        HumanMessage(content="Show Ravi's tasks"),
        AIMessage(content="Here are Ravi's tasks."),
    ]

    result = await agent(
        {
            "question": "Show Revathi's high-priority tasks",
            "messages": previous_messages,
        }
    )

    assert result["next_agent"] == "work_items"

    # Inspect the messages sent to the structured LLM.
    sent_messages = structured_llm.ainvoke.call_args.args[0]

    assert len(sent_messages) == 4

    assert sent_messages[1].content == "Show Ravi's tasks"
    assert sent_messages[2].content == "Here are Ravi's tasks."
    assert sent_messages[3].content == ("Show Revathi's high-priority tasks")


@pytest.mark.asyncio
async def test_supervisor_handles_new_conversation_without_history(mock_llm):
    llm, structured_llm = mock_llm

    structured_llm.ainvoke = AsyncMock(
        return_value=SupervisorDecision(
            next_agent="work_items",
            reason="The user requested Revathi's tasks.",
        )
    )

    agent = SupervisorAgent(llm=llm)

    result = await agent(
        {
            "question": "Show Revathi's tasks",
            "messages": [],
        }
    )

    assert result["next_agent"] == "work_items"

    sent_messages = structured_llm.ainvoke.call_args.args[0]

    # System message + current user question.
    assert len(sent_messages) == 2

    assert sent_messages[1].content == "Show Revathi's tasks"


@pytest.mark.asyncio
async def test_supervisor_uses_current_question_with_previous_context(mock_llm):
    llm, structured_llm = mock_llm

    structured_llm.ainvoke = AsyncMock(
        return_value=SupervisorDecision(
            next_agent="work_items",
            reason="The user is asking for Ravi's completed tasks.",
        )
    )

    agent = SupervisorAgent(llm=llm)

    previous_messages = [
        HumanMessage(content="Show Ravi's tasks"),
        AIMessage(content="Here are Ravi's tasks."),
    ]

    result = await agent(
        {
            "question": "Show his completed tasks",
            "messages": previous_messages,
        }
    )

    assert result["next_agent"] == "work_items"

    sent_messages = structured_llm.ainvoke.call_args.args[0]

    assert sent_messages[-1].content == "Show his completed tasks"
