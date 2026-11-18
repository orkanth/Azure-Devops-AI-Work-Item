from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.supervisor.agent import (
    SupervisorAgent,
    SupervisorDecision,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "question, expected_agent",
    [
        (
            "Create a Feature for employee registration.",
            "generation",
        ),
        (
            "Generate an Epic with three Features.",
            "generation",
        ),
        (
            "Create tasks from this business requirement.",
            "generation",
        ),
        (
            "Show all Features in the project.",
            "work_items",
        ),
        (
            "Find my active tasks.",
            "work_items",
        ),
        (
            "Update Feature 127.",
            "work_items",
        ),
        (
            "Reassign Task 129 to Ravi.",
            "work_items",
        ),
        (
            "Find users named Ravi.",
            "users",
        ),
        (
            "Explain the uploaded API document.",
            "rag",
        ),
    ],
)
async def test_supervisor_routes_requests_correctly(
    question: str,
    expected_agent: str,
):
    llm = MagicMock()
    router = MagicMock()

    router.ainvoke = AsyncMock(
        return_value=SupervisorDecision(
            next_agent=expected_agent,
            reason="Mocked routing decision.",
        )
    )

    llm.with_structured_output.return_value = router

    supervisor = SupervisorAgent(llm=llm)

    decision = await supervisor.route(question=question)

    assert decision.next_agent == expected_agent
    router.ainvoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_live_supervisor_routes_feature_creation():
    supervisor = SupervisorAgent()

    decision = await supervisor.route(
        question=(
            "Create a Feature called 'DevFlow AI Live Integration Test' "
            "with description 'Verify automatic publishing to Azure DevOps'."
        )
    )

    print("Selected agent:", decision.next_agent)
    print("Reason:", decision.reason)

    assert decision.next_agent == "generation"
