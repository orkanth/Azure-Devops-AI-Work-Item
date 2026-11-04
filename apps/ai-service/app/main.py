from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, work_items
from app.core.config import settings

app = FastAPI(
    title=settings.ai_service_name,
    version=settings.ai_service_version,
    description="AI-powered Azure DevOps work item generation",
)

# Allow requests from your local Angular development server.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:4200",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Welcome to DevFlow AI",
        "service": settings.ai_service_name,
        "version": settings.ai_service_version,
    }

app.include_router(health.router)
app.include_router(work_items.router, prefix="/api/v1")