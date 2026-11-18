import httpx
import pytest

from unittest.mock import AsyncMock, patch

from app.services.nestjs_publishing_service import (
    NestJSPublishingService,
)


@pytest.mark.asyncio
async def test_publish_generated_work_items():
    proposal = {
        "requested_type": "Feature",
        "items": [
            {
                "type": "Feature",
                "title": "Employee Registration",
                "description": "Create employee registration.",
                "acceptance_criteria": [],
                "children": [],
            }
        ],
        "parent_reference": None,
    }

    expected_response = {
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

    service = NestJSPublishingService()

    mock_response = httpx.Response(
        201,
        json=expected_response,
        request=httpx.Request(
            "POST",
            "http://localhost:3000/api/work-items/publish-generated",
        ),
    )

    with patch(
        "app.services.nestjs_publishing_service.httpx.AsyncClient"
    ) as mock_client:

        client_instance = mock_client.return_value.__aenter__.return_value

        client_instance.post = AsyncMock(return_value=mock_response)

        result = await service.publish_generated_work_items(
            proposal=proposal,
            publish_id="a2b3c4d5-e6f7-4890-8123-456789abcdef",
        )

    assert result["success"] is True
    assert result["status"] == "completed"
    assert result["summary"]["created"] == 1

    client_instance.post.assert_awaited_once()
