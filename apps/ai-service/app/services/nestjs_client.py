import httpx

from app.core.config import settings


class NestJSClient:

    async def get_work_items(
            self,
            type: str | None = None,
            state: str | None = None,
            assigned_to: str | None = None,
            priority: int | None = None,
        ) -> list[dict]:

        url = f"{settings.nestjs_api_url}/work-items"

        params = {
            "type": type,
            "state": state,
            "assignedTo": assigned_to,
            "priority": priority,
        }

        # Remove parameters that were not provided.
        params = {
            key: value
            for key, value in params.items()
            if value is not None
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)

            response.raise_for_status()

            return response.json()
            response = await client.get(url)

            response.raise_for_status()

            return response.json()