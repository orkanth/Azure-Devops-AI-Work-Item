
from fastapi import APIRouter

from app.services.nestjs_client import NestJSClient

router = APIRouter()


@router.get("/test-nestjs")
async def test_nestjs():
    client = NestJSClient()
    work_items = await client.get_work_items()

    return {
        "status": "success",
        "count": len(work_items),
        "work_items": work_items,
    }


@router.get("/test-filtered-work-items")
async def test_filtered_work_items():
    client = NestJSClient()

    work_items = await client.get_work_items(
        type="Feature",
        state="New",
        assigned_to="orkanth@gmail.com",
        priority=2,
    )

    return {
        "status": "success",
        "count": len(work_items),
        "work_items": work_items,
    }
