import pytest
from unittest.mock import AsyncMock, MagicMock

from app.agents.users.agent import UsersAgent, UserRequest


@pytest.fixture
def mock_dependencies():
    llm = MagicMock()
    structured_llm = MagicMock()

    llm.with_structured_output.return_value = structured_llm

    get_users_tool = MagicMock()
    get_users_tool.name = "get_users"
    get_users_tool.ainvoke = AsyncMock()

    return llm, structured_llm, get_users_tool


@pytest.mark.asyncio
async def test_search_user_success(mock_dependencies):
    llm, structured_llm, get_users_tool = mock_dependencies

    structured_llm.ainvoke = AsyncMock(
        return_value=UserRequest(
            intent="search",
            search_query="Ravi Kumar",
        )
    )

    get_users_tool.ainvoke.return_value = [
        {
            "displayName": "Ravi Kumar",
            "email": "ravi@example.com",
        }
    ]

    agent = UsersAgent(
        llm=llm,
        tools=[get_users_tool],
    )

    result = await agent.execute("Find Ravi Kumar")

    assert result["status"] == "success"
    assert result["total"] == 1
    assert result["users"][0]["displayName"] == "Ravi Kumar"

    get_users_tool.ainvoke.assert_awaited_once_with({"name": "Ravi Kumar"})


@pytest.mark.asyncio
async def test_search_user_not_found(mock_dependencies):
    llm, structured_llm, get_users_tool = mock_dependencies

    structured_llm.ainvoke = AsyncMock(
        return_value=UserRequest(
            intent="search",
            search_query="Unknown User",
        )
    )

    get_users_tool.ainvoke.return_value = []

    agent = UsersAgent(llm=llm, tools=[get_users_tool])

    result = await agent.execute("Find Unknown User")

    assert result["status"] == "not_found"
    assert result["total"] == 0


@pytest.mark.asyncio
async def test_search_multiple_users(mock_dependencies):
    llm, structured_llm, get_users_tool = mock_dependencies

    structured_llm.ainvoke = AsyncMock(
        return_value=UserRequest(
            intent="search",
            search_query="John",
        )
    )

    get_users_tool.ainvoke.return_value = [
        {"displayName": "John Smith", "email": "john1@example.com"},
        {"displayName": "John Brown", "email": "john2@example.com"},
    ]

    agent = UsersAgent(llm=llm, tools=[get_users_tool])

    result = await agent.execute("Find John")

    assert result["status"] == "success"
    assert result["total"] == 2


@pytest.mark.asyncio
async def test_search_requires_clarification(mock_dependencies):
    llm, structured_llm, get_users_tool = mock_dependencies

    structured_llm.ainvoke = AsyncMock(
        return_value=UserRequest(
            intent="search",
            search_query=None,
        )
    )

    agent = UsersAgent(llm=llm, tools=[get_users_tool])

    result = await agent.execute("Find a user")

    assert result["status"] == "needs_clarification"
    get_users_tool.ainvoke.assert_not_awaited()


@pytest.mark.asyncio
async def test_user_tool_failure(mock_dependencies):
    llm, structured_llm, get_users_tool = mock_dependencies

    structured_llm.ainvoke = AsyncMock(
        return_value=UserRequest(
            intent="search",
            search_query="Ravi",
        )
    )

    get_users_tool.ainvoke.side_effect = RuntimeError("Azure DevOps unavailable")

    agent = UsersAgent(llm=llm, tools=[get_users_tool])

    result = await agent.execute("Find Ravi")

    assert result["status"] == "error"
    assert "failed" in result["message"].lower()


@pytest.mark.asyncio
async def test_unsupported_operation(mock_dependencies):
    llm, structured_llm, get_users_tool = mock_dependencies

    structured_llm.ainvoke = AsyncMock(
        return_value=UserRequest(
            intent="other",
            search_query=None,
        )
    )

    agent = UsersAgent(llm=llm, tools=[get_users_tool])

    result = await agent.execute("Change a user's permissions")

    assert result["status"] == "unsupported"
    get_users_tool.ainvoke.assert_not_awaited()


@pytest.mark.asyncio
async def test_rejects_empty_question(mock_dependencies):
    llm, _, get_users_tool = mock_dependencies

    agent = UsersAgent(llm=llm, tools=[get_users_tool])

    with pytest.raises(ValueError):
        await agent.execute("   ")


def test_requires_get_users_tool():
    llm = MagicMock()
    llm.with_structured_output.return_value = MagicMock()

    with pytest.raises(ValueError, match="get_users"):
        UsersAgent(llm=llm, tools=[])
