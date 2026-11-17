
from unittest.mock import AsyncMock, patch

import pytest

from app.tools.azure_devops.user_tools import get_users
from app.tools.azure_devops.work_item_tools import get_work_items


@pytest.mark.anyio
async def test_get_users():
    expected_users = [
        {
            "name": "Ravi",
            "email": "ravi@example.com",
        }
    ]

    with patch(
        "app.tools.azure_devops.user_tools.nestjs_client.search_users",
        new_callable=AsyncMock,
    ) as mock_search:

        mock_search.return_value = expected_users

        result = await get_users.ainvoke({"name": "Ravi"})

        assert result == expected_users
        mock_search.assert_awaited_once_with("Ravi")


@pytest.mark.anyio
async def test_get_work_items():
    expected_items = [
        {
            "id": 101,
            "title": "Implement authentication",
            "state": "Active",
        }
    ]

    filters = {
        "type": "Task",
        "state": "Active",
        "assigned_to": "ravi@example.com",
        "priority": 1,
        "is_assigned": True,
    }

    with patch(
        "app.tools.azure_devops.work_item_tools.nestjs_client.get_work_items",
        new_callable=AsyncMock,
    ) as mock_get_items:

        mock_get_items.return_value = expected_items

        result = await get_work_items.ainvoke(filters)

        assert result == expected_items
        mock_get_items.assert_awaited_once_with(**filters)
