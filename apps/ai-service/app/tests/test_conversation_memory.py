import pytest

from langchain_core.messages import AIMessage, HumanMessage

from app.graph.nodes import _with_conversation_turn


def test_conversation_turn_appends_user_and_assistant_messages():
    state = {
        "question": "Find Ravi Kumar",
    }

    result = {
        "status": "success",
        "agent_response": "Ravi Kumar was found.",
    }

    updated = _with_conversation_turn(state, result)

    assert len(updated["messages"]) == 2

    assert isinstance(updated["messages"][0], HumanMessage)
    assert updated["messages"][0].content == "Find Ravi Kumar"

    assert isinstance(updated["messages"][1], AIMessage)
    assert updated["messages"][1].content == "Ravi Kumar was found."


def test_conversation_turn_does_not_add_empty_messages():
    state = {
        "question": "",
    }

    result = {
        "status": "success",
        "agent_response": "",
    }

    updated = _with_conversation_turn(state, result)

    assert updated["messages"] == []


def test_conversation_turn_preserves_agent_result():
    state = {
        "question": "Show Ravi's tasks",
    }

    result = {
        "status": "success",
        "agent_response": "Found 5 matching work items.",
        "total": 5,
    }

    updated = _with_conversation_turn(state, result)

    assert updated["status"] == "success"
    assert updated["total"] == 5
    assert len(updated["messages"]) == 2
