import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.graph.workflow import build_workflow


class MockSupervisor:
    def __init__(self):
        self.previous_messages = []

    async def __call__(self, state):
        messages = state.get("messages", [])

        # Capture the history available when routing each request.
        self.previous_messages.append(list(messages))

        return {
            "next_agent": "work_items",
            "intent": "work_items",
            "status": "routing",
            "error": None,
        }


class MockWorkItemsAgent:
    async def __call__(self, state):
        question = state["question"]

        if question == "Find Ravi Kumar":
            response = "Ravi Kumar was found."
        else:
            response = "Found 5 tasks assigned to Ravi Kumar."

        return {
            "status": "success",
            "agent_response": response,
            "total": 5,
        }


class MockUsersAgent:
    async def __call__(self, state):
        return {
            "status": "success",
            "agent_response": "Mock users response.",
        }


class MockRagAgent:
    async def answer_question(self, question, project_id):
        return {
            "answer": "Mock document answer.",
            "sources": [],
        }


@pytest.mark.asyncio
async def test_conversation_history_is_restored_across_requests():
    supervisor = MockSupervisor()

    workflow = build_workflow(
        supervisor_agent=supervisor,
        work_items_agent=MockWorkItemsAgent(),
        users_agent=MockUsersAgent(),
        rag_agent=MockRagAgent(),
    )

    config = {
        "configurable": {
            "thread_id": "conversation-memory-test",
        }
    }

    # First request
    first_result = await workflow.ainvoke(
        {
            "question": "Find Ravi Kumar",
            "project_id": "AzureDevOpsAI",
        },
        config=config,
    )

    assert first_result["status"] == "success"
    assert first_result["agent_response"] == "Ravi Kumar was found."

    # Second request using the same thread_id
    second_result = await workflow.ainvoke(
        {
            "question": "Show me his tasks",
            "project_id": "AzureDevOpsAI",
        },
        config=config,
    )

    assert second_result["status"] == "success"
    assert second_result["agent_response"] == ("Found 5 tasks assigned to Ravi Kumar.")

    # Supervisor should have received the previous conversation
    # before routing the second request.
    second_request_history = supervisor.previous_messages[1]

    assert len(second_request_history) == 2

    assert isinstance(second_request_history[0], HumanMessage)
    assert second_request_history[0].content == "Find Ravi Kumar"

    assert isinstance(second_request_history[1], AIMessage)
    assert second_request_history[1].content == "Ravi Kumar was found."

    # Check that the second conversation turn was also saved.
    final_messages = second_result["messages"]

    assert len(final_messages) == 4
    assert final_messages[2].content == "Show me his tasks"
    assert final_messages[3].content == ("Found 5 tasks assigned to Ravi Kumar.")
