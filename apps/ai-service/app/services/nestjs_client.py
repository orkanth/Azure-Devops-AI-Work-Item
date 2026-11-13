import httpx

from app.core.config import settings


class NestJSClient:

    async def get_work_items(self) -> list[dict]:
        url = f"{settings.nestjs_api_url}/work-items"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)

            response.raise_for_status()

            return response.json()