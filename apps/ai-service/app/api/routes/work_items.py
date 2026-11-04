
from fastapi import APIRouter, HTTPException

from app.schemas.work_items import (
    GenerateWorkItemsRequest,
    GenerateWorkItemsResponse,
)
from app.services.work_item_generator import (
    generate_work_item_proposal,
)

router = APIRouter()


@router.post(
    "/work-items/generate",
    response_model=GenerateWorkItemsResponse,
)
async def generate_work_items(
    request: GenerateWorkItemsRequest,
):
    try:
        epic = await generate_work_item_proposal(
            request.requirement
        )

        return GenerateWorkItemsResponse(
            status="success",
            message="AI work-item proposal generated successfully.",
            requirement=request.requirement,
            epic=epic,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="AI generation failed. Check the service logs.",
        ) from exc
