
from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/")
async def root():
    return {
        "message": "Welcome to DevFlow AI",
        "service": settings.ai_service_name,
        "version": settings.ai_service_version,
    }
