import pytest
from unittest.mock import AsyncMock

from app.graph.workflow import build_workflow


def make_test_config(thread_id: str):
    return {
        "configurable": {
            "thread_id": thread_id,
        }
    }


class FakeSupervisor:
    def __init__(self, next_agent, status="routing"):
        self.next_agent = next_agent
        self.status = status

    async def __call__(self, state):
        return {
            "next_agent": self.next_agent,
            "status": self.status,
            "intent": self.next_agent,
        }


class FakeAgent:
    def __init__(self, response):
        self.response = response
        self.call_count = 0

    async def __call__(self, state):
        self.call_count += 1
        return self.response


class FakeRAGAgent:
    def __init__(self):
        self.answer_question = AsyncMock(
            return_value={
                "answer": "Authentication uses JWT.",
                "sources": [{"source": "Source 1"}],
            }
        )


def create_test_workflow(next_agent, status="routing"):
    supervisor = FakeSupervisor(next_agent, status)

    work_items = FakeAgent(
        {
            "status": "success",
            "agent_response": "Work items retrieved.",
        }
    )

    users = FakeAgent(
        {
            "status": "success",
            "agent_response": "Users retrieved.",
        }
    )

    rag = FakeRAGAgent()

    generation = FakeAgent(
        {
            "status": "success",
            "agent_response": "Work-item hierarchy generated.",
        }
    )

    workflow = build_workflow(
        supervisor_agent=supervisor,
        work_items_agent=work_items,
        users_agent=users,
        rag_agent=rag,
        generation_agent=generation,
    )

    return workflow, work_items, users, rag, generation


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("next_agent", "expected_response"),
    [
        ("work_items", "Work items retrieved."),
        ("users", "Users retrieved."),
        ("generation", "Work-item hierarchy generated."),
    ],
)
async def test_specialist_agent_routing(
    next_agent,
    expected_response,
):
    workflow, work_items, users, rag, generation = create_test_workflow(next_agent)

    result = await workflow.ainvoke(
        {
            "question": "Test request",
            "project_id": "AzureDevOpsAI",
        },
        config=make_test_config("routing-test"),
    )

    assert result["agent_response"] == expected_response

    expected_agents = {
        "work_items": work_items,
        "users": users,
        "generation": generation,
    }

    for agent_name, agent in expected_agents.items():
        expected_count = 1 if agent_name == next_agent else 0
        assert agent.call_count == expected_count

    rag.answer_question.assert_not_awaited()


@pytest.mark.asyncio
async def test_rag_routing():
    workflow, work_items, users, rag, generation = create_test_workflow("rag")

    result = await workflow.ainvoke(
        {
            "question": "Explain authentication",
            "project_id": "AzureDevOpsAI",
        },
        config=make_test_config("rag-routing"),
    )

    assert result["agent_response"] == "Authentication uses JWT."
    assert result["sources"] == [{"source": "Source 1"}]

    rag.answer_question.assert_awaited_once_with(
        question="Explain authentication",
        project_id="AzureDevOpsAI",
    )

    assert work_items.call_count == 0
    assert users.call_count == 0
    assert generation.call_count == 0


@pytest.mark.asyncio
async def test_clarification_stops_routing():
    workflow, work_items, users, rag, generation = create_test_workflow(
        "clarification",
        status="needs_clarification",
    )

    result = await workflow.ainvoke(
        {
            "question": "Show me that",
            "project_id": "AzureDevOpsAI",
        },
        config=make_test_config("clarification-routing"),
    )

    assert result["status"] == "needs_clarification"

    assert work_items.call_count == 0
    assert users.call_count == 0
    assert generation.call_count == 0
    rag.answer_question.assert_not_awaited()


@pytest.mark.asyncio
async def test_supervisor_error_stops_routing():
    workflow, work_items, users, rag, generation = create_test_workflow(
        "clarification",
        status="error",
    )

    result = await workflow.ainvoke(
        {
            "question": "Test request",
            "project_id": "AzureDevOpsAI",
        },
        config=make_test_config("supervisor-error"),
    )

    assert result["status"] == "error"

    assert work_items.call_count == 0
    assert users.call_count == 0
    assert generation.call_count == 0
    rag.answer_question.assert_not_awaited()
