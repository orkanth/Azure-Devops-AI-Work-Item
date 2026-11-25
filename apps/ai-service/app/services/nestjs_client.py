import httpx

from app.core.config import settings


class NestJSClient:

    async def assign_work_item(
        self,
        work_item_id: int,
        assigned_to: str,
    ) -> dict:
        url = f"{settings.nestjs_api_url}/work-items/" f"{work_item_id}/assignment"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.patch(
                url,
                json={"assignedTo": assigned_to},
            )
            response.raise_for_status()
            return response.json()

    async def get_work_items(
        self,
        type: str | None = None,
        state: str | None = None,
        assigned_to: str | None = None,
        priority: int | None = None,
        is_assigned: bool | None = None,
    ) -> list[dict]:

        url = f"{settings.nestjs_api_url}/work-items"

        base_params = {
            "type": type,
            "state": state,
            "assignedTo": assigned_to,
            "priority": priority,
            "is_assigned": is_assigned,
        }

        base_params = {
            key: value for key, value in base_params.items() if value is not None
        }

        page = 1
        page_size = 200
        all_items: list[dict] = []

        async with httpx.AsyncClient(timeout=30.0) as client:

            while True:
                params = {
                    **base_params,
                    "page": page,
                    "pageSize": page_size,
                }

                response = await client.get(url, params=params)
                response.raise_for_status()

                data = response.json()

                # Backward compatibility with the old list response.
                if isinstance(data, list):
                    return data

                if not isinstance(data, dict) or not isinstance(
                    data.get("items"), list
                ):
                    raise ValueError("Unexpected work-items API response format.")

                page_items = data["items"]
                total_records = data.get(
                    "total",
                    data.get("totalRecords"),
                )

                if not isinstance(total_records, int):
                    raise ValueError(
                        "Work-items API response is missing total records."
                    )

                all_items.extend(page_items)

                # All matching records have been retrieved.
                if len(all_items) >= total_records:
                    break

                if not page_items:
                    raise ValueError(
                        "Work-items API returned an incomplete paginated result."
                    )

                page += 1

        return all_items

    async def get_work_item_by_id(self, work_item_id: int) -> dict:
        url = f"{settings.nestjs_api_url}/work-items/{work_item_id}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

        async def assign_work_item(
            self,
            work_item_id: int,
            assigned_to: str,
        ) -> dict:
            url = f"{settings.nestjs_api_url}/work-items/" f"{work_item_id}/assignment"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.patch(
                url,
                json={"assignedTo": assigned_to},
            )
            response.raise_for_status()
            return response.json()

    async def update_work_item(
        self,
        work_item_id: int,
        updates: dict,
    ) -> dict:
        url = f"{settings.nestjs_api_url}/work-items/" f"{work_item_id}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.patch(
                url,
                json=updates,
            )
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
        url = f"{settings.nestjs_api_url}/documents/" f"{document_id}/content"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content

    async def complete_ingestion_job(self, job_id: str) -> dict:
        url = (
            f"{settings.nestjs_api_url}/documents/" f"ingestion-jobs/{job_id}/complete"
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
        url = f"{settings.nestjs_api_url}/documents/" f"ingestion-jobs/{job_id}/fail"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                json={"errorMessage": error_message[:4000]},
            )
            response.raise_for_status()
            return response.json()


nestjs_client = NestJSClient()
