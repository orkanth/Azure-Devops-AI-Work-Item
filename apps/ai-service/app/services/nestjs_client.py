
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
        
        
    
    async def claim_ingestion_job(self) -> dict | None:
        url = f"{settings.nestjs_api_url}/documents/ingestion-jobs/claim"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url)
            response.raise_for_status()
            data = response.json()
            return data.get("job")

        print("Claim URL:", response.request.url)
        print("HTTP Status:", response.status_code)
        print("Content-Type:", response.headers.get("content-type"))
        print("Response Body:", repr(response.text))

        response.raise_for_status()

        if not response.content:
            return None

        return response.json()


    async def get_document_content(self, document_id: str) -> bytes:
        url = (
            f"{settings.nestjs_api_url}/documents/"
            f"{document_id}/content"
        )

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content

    async def complete_ingestion_job(self, job_id: str) -> dict:
        url = (
            f"{settings.nestjs_api_url}/documents/"
            f"ingestion-jobs/{job_id}/complete"
        )

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url)
            response.raise_for_status()
            return response.json()

    async def fail_ingestion_job(
        self,
        job_id: str,
        error_message: str,
    ) -> dict:
        url = (
            f"{settings.nestjs_api_url}/documents/"
            f"ingestion-jobs/{job_id}/fail"
        )

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                json={"errorMessage": error_message[:4000]},
            )
            response.raise_for_status()
            return response.json()

nestjs_client = NestJSClient()