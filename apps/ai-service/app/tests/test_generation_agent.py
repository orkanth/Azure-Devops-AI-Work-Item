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


@pytest.mark.asyncio
async def test_normal_generation_does_not_call_rag():
    llm = MagicMock()
    intent_llm = MagicMock()

    intent_llm.ainvoke = AsyncMock(
        return_value=GenerationIntent(
            requested_type="Feature",
            requirement="Create employee registration.",
            use_project_documents=False,
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
            "success": True,
            "status": "completed",
            "summary": {
                "created": 1,
                "reused": 0,
                "failed": 0,
            },
        }
    )

    rag_service = MagicMock()
    rag_service.retrieve = AsyncMock()

    agent = GenerationAgent(
        llm=llm,
        publishing_service=publishing_service,
        rag_retrieval_service=rag_service,
    )

    with patch(
        "app.agents.generation.agent.generate_work_item_hierarchy",
        new_callable=AsyncMock,
        return_value=proposal,
    ) as mock_generator:

        result = await agent.execute(
            question="Create a Feature for employee registration."
        )

    assert result["status"] == "completed"
    rag_service.retrieve.assert_not_awaited()

    mock_generator.assert_awaited_once()
    assert mock_generator.await_args.kwargs["retrieved_context"] is None


@pytest.mark.asyncio
async def test_document_generation_passes_context_and_returns_sources():
    llm = MagicMock()
    intent_llm = MagicMock()

    intent_llm.ainvoke = AsyncMock(
        return_value=GenerationIntent(
            requested_type="Feature",
            requirement="Generate employee registration work items.",
            use_project_documents=True,
            document_reference="requirements.docx",
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
            "success": True,
            "status": "completed",
            "summary": {
                "created": 1,
                "reused": 0,
                "failed": 0,
            },
        }
    )

    rag_service = MagicMock()
    rag_service.retrieve = AsyncMock(
        return_value={
            "chunks": [
                {
                    "document_id": "doc-123",
                    "file_name": "requirements.docx",
                    "page_number": 2,
                    "chunk_index": 3,
                    "content": "Users must provide an email address.",
                }
            ],
            "context": "Users must provide an email address.",
            "total_results": 1,
        }
    )

    agent = GenerationAgent(
        llm=llm,
        publishing_service=publishing_service,
        rag_retrieval_service=rag_service,
    )

    with patch(
        "app.agents.generation.agent.generate_work_item_hierarchy",
        new_callable=AsyncMock,
        return_value=proposal,
    ) as mock_generator:

        result = await agent.execute(
            question="Generate employee registration work items from requirements.docx.",
            project_id="project-123",
        )

    rag_service.retrieve.assert_awaited_once_with(
        query="Generate employee registration work items.",
        project_id="project-123",
        document_reference="requirements.docx",
    )

    mock_generator.assert_awaited_once()

    assert (
        mock_generator.await_args.kwargs["retrieved_context"]
        == "Users must provide an email address."
    )

    assert result["status"] == "completed"
    assert result["sources"] == [
        {
            "document_id": "doc-123",
            "file_name": "requirements.docx",
            "page_number": 2,
            "chunk_index": 3,
        }
    ]

    publishing_service.publish_generated_work_items.assert_awaited_once()


@pytest.mark.asyncio
async def test_document_generation_does_not_publish_when_no_chunks_found():
    llm = MagicMock()
    intent_llm = MagicMock()

    intent_llm.ainvoke = AsyncMock(
        return_value=GenerationIntent(
            requested_type="Feature",
            requirement="Generate registration work items.",
            use_project_documents=True,
        )
    )
    llm.with_structured_output.return_value = intent_llm

    publishing_service = MagicMock()
    publishing_service.publish_generated_work_items = AsyncMock()

    rag_service = MagicMock()
    rag_service.retrieve = AsyncMock(
        return_value={
            "chunks": [],
            "context": "",
            "total_results": 0,
        }
    )

    agent = GenerationAgent(
        llm=llm,
        publishing_service=publishing_service,
        rag_retrieval_service=rag_service,
    )

    with patch(
        "app.agents.generation.agent.generate_work_item_hierarchy",
        new_callable=AsyncMock,
    ) as mock_generator:

        result = await agent.execute(
            question="Generate work items using project documentation.",
            project_id="project-123",
        )

    assert result["status"] == "failed"
    assert result["sources"] == []

    mock_generator.assert_not_awaited()
    publishing_service.publish_generated_work_items.assert_not_awaited()
