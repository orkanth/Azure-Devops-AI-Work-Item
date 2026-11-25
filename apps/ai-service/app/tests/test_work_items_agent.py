from unittest.mock import AsyncMock, MagicMock

import pytest

from langchain_core.messages import AIMessage, HumanMessage
from app.agents.work_items.agent import WorkItemsAgent, WorkItemRequest

from app.agents.work_items.agent import (
    WorkItemsAgent,
    WorkItemRequest,
)


@pytest.mark.asyncio
async def test_work_items_agent_receives_conversation_history():
    # Arrange: create mocked LLM
    llm = MagicMock()
    structured_llm = MagicMock()

    llm.with_structured_output.return_value = structured_llm

    structured_llm.ainvoke = AsyncMock(
        return_value=WorkItemRequest(
            intent="list",
            assignee_name="Revathi",
            priority=2,
        )
    )

    # Arrange: create mocked tools
    get_users_tool = MagicMock()
    get_users_tool.name = "get_users"
    get_users_tool.ainvoke = AsyncMock(
        return_value=[
            {
                "displayName": "Revathi",
                "email": "revathi@example.com",
            }
        ]
    )

    get_work_items_tool = MagicMock()
    get_work_items_tool.name = "get_work_items"
    get_work_items_tool.ainvoke = AsyncMock(return_value=[])

    get_work_item_by_id_tool = MagicMock()
    get_work_item_by_id_tool.name = "get_work_item_by_id"
    get_work_item_by_id_tool.ainvoke = AsyncMock(return_value={})

    assign_work_item_tool = MagicMock()
    assign_work_item_tool.name = "assign_work_item"
    assign_work_item_tool.ainvoke = AsyncMock(return_value={"status": "success"})

    agent = WorkItemsAgent(
        llm=llm,
        tools=[
            get_users_tool,
            get_work_items_tool,
            get_work_item_by_id_tool,
            assign_work_item_tool,
        ],
    )

    history = [
        HumanMessage(content="Show Ravi's tasks"),
        AIMessage(content="Here are Ravi's tasks."),
    ]

    # Act
    result = await agent.execute(
        question="Show Revathi's high-priority tasks",
        messages=history,
    )

    # Assert: conversation reaches the structured LLM
    sent_messages = structured_llm.ainvoke.call_args.args[0]

    assert sent_messages[1].content == "Show Ravi's tasks"
    assert sent_messages[2].content == "Here are Ravi's tasks."
    assert sent_messages[3].content == ("Show Revathi's high-priority tasks")

    # Assert: current request overrides previous assignee
    assert result["assignee_name"] == "Revathi"
    assert result["filters"]["priority"] == 2
    assert result["filters"]["assigned_to"] == "revathi@example.com"
