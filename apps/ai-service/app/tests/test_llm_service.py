
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.llm_service import LLMService
from app.schemas.work_items import EpicProposal


@patch("app.services.llm_service.ChatOpenAI")
def test_llm_service_initialization(mock_chat_openai):
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value = MagicMock()
    mock_llm.with_structured_output.return_value = MagicMock()

    mock_chat_openai.return_value = mock_llm

    service = LLMService()

    assert service.llm is mock_llm
    assert len(service.tools) == 4
    assert service.llm_with_tools is not None
    assert service.structured_llm is not None


@patch("app.services.llm_service.ChatOpenAI")
async def test_ask(mock_chat_openai):
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(
        return_value=MagicMock(
            content="An Epic is a large body of work."
        )
    )
    mock_llm.bind_tools.return_value = MagicMock()
    mock_llm.with_structured_output.return_value = MagicMock()

    mock_chat_openai.return_value = mock_llm

    service = LLMService()

    result = await service.ask("What is an Epic?")

    assert result == "An Epic is a large body of work."
    mock_llm.ainvoke.assert_awaited_once_with("What is an Epic?")


@patch("app.services.llm_service.ChatOpenAI")
async def test_generate_epic(mock_chat_openai):
    expected_epic = EpicProposal(
        title="User Management",
        description="Manage application users.",
        features=[
            {
                "title": "User Registration",
                "description": "Allow users to register.",
                "user_stories": [
                    {
                        "title": "Register an account",
                        "description": "As a user, I want to register.",
                        "acceptance_criteria": ["Email must be unique."],
                        "tasks": [
                            {
                                "title": "Create registration API",
                                "description": "Implement registration endpoint.",
                                "acceptance_criteria": ["API returns HTTP 201."],
                            }
                        ],
                    }
                ],
            }
        ],
    )

    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value = MagicMock()

    mock_structured_llm = MagicMock()
    mock_structured_llm.ainvoke = AsyncMock(
        return_value=expected_epic
    )

    mock_llm.with_structured_output.return_value = mock_structured_llm
    mock_chat_openai.return_value = mock_llm

    service = LLMService()

    result = await service.generate_epic(
        "Build a user registration system."
    )

    assert isinstance(result, EpicProposal)
    assert result.title == "User Management"
    assert len(result.features) == 1
    assert len(result.features[0].user_stories) == 1
    assert len(result.features[0].user_stories[0].tasks) == 1

    mock_structured_llm.ainvoke.assert_awaited_once()
