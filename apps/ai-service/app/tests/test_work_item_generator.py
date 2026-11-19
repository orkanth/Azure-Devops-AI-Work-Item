from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services import work_item_generator


@pytest.mark.asyncio
async def test_generate_work_item_hierarchy_includes_retrieved_context(
    monkeypatch,
):
    document_context = "The system must support role-based access control."
    requirement = "Generate a Feature for user management."

    # Configure test settings
    monkeypatch.setattr(
        work_item_generator.settings,
        "openai_api_key",
        "test-api-key",
    )
    monkeypatch.setattr(
        work_item_generator.settings,
        "openai_model",
        "test-model",
    )

    # Mock the parsed LLM response
    parsed_proposal = SimpleNamespace(
        requested_type="Feature",
        items=[
            SimpleNamespace(type="Feature"),
        ],
    )

    mock_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(parsed=parsed_proposal))]
    )

    mock_client = MagicMock()
    mock_client.chat.completions.parse = AsyncMock(return_value=mock_response)
    mock_client.close = AsyncMock()

    mock_openai = MagicMock(return_value=mock_client)

    monkeypatch.setattr(
        work_item_generator,
        "AsyncOpenAI",
        mock_openai,
    )

    # Execute
    result = await work_item_generator.generate_work_item_hierarchy(
        requirement=requirement,
        work_item_type="Feature",
        retrieved_context=document_context,
    )

    # Verify result
    assert result == parsed_proposal

    # Verify the actual LLM request
    mock_client.chat.completions.parse.assert_awaited_once()

    call_kwargs = mock_client.chat.completions.parse.await_args.kwargs

    messages = call_kwargs["messages"]

    system_prompt = messages[0]["content"]
    user_message = messages[1]["content"]

    assert document_context in system_prompt
    assert document_context in user_message
    assert requirement in user_message

    assert call_kwargs["model"] == "test-model"

    # Verify client cleanup
    mock_client.close.assert_awaited_once()
