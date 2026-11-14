
import httpx

from app.core.config import settings


class NestJSClient:

    async def get_work_items(
        self,
        type: str | None = None,
        state: str | None = None,
        assigned_to: str | None = None,
        priority: int | None = None,
        is_assigned: bool | None = None,
    ) -> list[dict]:

        url = f"{settings.nestjs_api_url}/work-items"

        params = {
            "type": type,
            "state": state,
            "assignedTo": assigned_to,
            "priority": priority,
            "is_assigned": is_assigned,
        }

        params = {
            key: value
            for key, value in params.items()
            if value is not None
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()

            return response.json()

    
    async def search_users(self, name: str) -> list[dict]:
        url = f"{settings.nestjs_api_url}/users/search"

        params = {"name": name}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
