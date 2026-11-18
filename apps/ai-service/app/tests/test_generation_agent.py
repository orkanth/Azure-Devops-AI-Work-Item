from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.generation.agent import GenerationAgent
from app.schemas.work_items import (
    GenerationIntent,
    WorkItemGenerationProposal,
)
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_generation_agent_publishes_generated_proposal():
    # Arrange: mock the structured LLM response.
    llm = MagicMock()
    intent_llm = MagicMock()

    intent_llm.ainvoke = AsyncMock(
        return_value=GenerationIntent(
            requested_type="Feature",
            requirement="Create employee registration functionality.",
        )
    )

    llm.with_structured_output.return_value = intent_llm

    # Mock the generated hierarchy.
    proposal = WorkItemGenerationProposal(
        requested_type="Feature",
        items=[
            {
                "type": "Feature",
                "title": "Employee Registration",
                "description": "Create employee registration.",
                "children": [],
            }
        ],
    )

    # Mock NestJS publishing.
    publishing_service = MagicMock()

    publishing_service.publish_generated_work_items = AsyncMock(
        return_value={
            "success": True,
            "status": "completed",
            "created": [
                {
                    "id": 150,
                    "type": "Feature",
                    "title": "Employee Registration",
                }
            ],
            "reused": [],
            "errors": [],
            "summary": {
                "created": 1,
                "reused": 0,
                "failed": 0,
            },
        }
    )

    agent = GenerationAgent(
        llm=llm,
        publishing_service=publishing_service,
    )

    # Mock the hierarchy generator.
    from unittest.mock import patch

    with patch(
        "app.agents.generation.agent.generate_work_item_hierarchy",
        new_callable=AsyncMock,
        return_value=proposal,
    ) as mock_generator:

        # Act.
        result = await agent.execute(
            question="Create a Feature for employee registration."
        )

    # Assert.
    assert result["intent"] == "generation"
    assert result["status"] == "completed"
    assert result["publishing_result"]["success"] is True
    assert result["publishing_result"]["summary"]["created"] == 1
    assert result["publish_id"]

    mock_generator.assert_awaited_once()
    publishing_service.publish_generated_work_items.assert_awaited_once()


@pytest.mark.asyncio
async def test_generation_agent_handles_partial_publishing():
    llm = MagicMock()
    intent_llm = MagicMock()

    intent_llm.ainvoke = AsyncMock(
        return_value=GenerationIntent(
            requested_type="Feature",
            requirement="Create employee registration functionality.",
        )
    )
    llm.with_structured_output.return_value = intent_llm

    proposal = WorkItemGenerationProposal(
        requested_type="Feature",
        items=[
            {
                "type": "Feature",
                "title": "Employee Registration",
                "description": "Create employee registration.",
                "children": [],
            }
        ],
    )

    publishing_service = MagicMock()
    publishing_service.publish_generated_work_items = AsyncMock(
        return_value={
            "success": False,
            "status": "partial",
            "message": "Some work items failed.",
            "created": [{"id": 150, "type": "Feature"}],
            "reused": [],
            "errors": [{"message": "Task creation failed."}],
            "summary": {
                "created": 1,
                "reused": 0,
                "failed": 1,
            },
        }
    )

    agent = GenerationAgent(
        llm=llm,
        publishing_service=publishing_service,
    )

    with patch(
        "app.agents.generation.agent.generate_work_item_hierarchy",
        new_callable=AsyncMock,
        return_value=proposal,
    ):
        result = await agent.execute(
            question="Create a Feature for employee registration."
        )

    assert result["status"] == "partial"
    assert result["publishing_result"]["summary"]["created"] == 1
    assert result["publishing_result"]["summary"]["failed"] == 1
    assert "partially completed" in result["agent_response"]


@pytest.mark.asyncio
async def test_generation_agent_handles_failed_publishing():
    llm = MagicMock()
    intent_llm = MagicMock()

    intent_llm.ainvoke = AsyncMock(
        return_value=GenerationIntent(
            requested_type="Feature",
            requirement="Create employee registration functionality.",
        )
    )
    llm.with_structured_output.return_value = intent_llm

    proposal = WorkItemGenerationProposal(
        requested_type="Feature",
        items=[
            {
                "type": "Feature",
                "title": "Employee Registration",
                "description": "Create employee registration.",
                "children": [],
            }
        ],
    )

    publishing_service = MagicMock()
    publishing_service.publish_generated_work_items = AsyncMock(
        return_value={
            "success": False,
            "status": "failed",
            "message": "Azure DevOps is unavailable.",
            "created": [],
            "reused": [],
            "errors": [{"message": "Connection failed."}],
            "summary": {
                "created": 0,
                "reused": 0,
                "failed": 1,
            },
        }
    )

    agent = GenerationAgent(
        llm=llm,
        publishing_service=publishing_service,
    )

    with patch(
        "app.agents.generation.agent.generate_work_item_hierarchy",
        new_callable=AsyncMock,
        return_value=proposal,
    ):
        result = await agent.execute(
            question="Create a Feature for employee registration."
        )

    assert result["status"] == "failed"
    assert result["publishing_result"]["success"] is False
    assert "unsuccessful" in result["agent_response"]
