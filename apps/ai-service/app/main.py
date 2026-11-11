from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, work_items, documents
from app.core.config import settings

app = FastAPI(
    title=settings.ai_service_name,
    version=settings.ai_service_version,
    description="AI-powered enterprise work item generation and orchestration",
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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, work_items, documents
from app.core.config import settings

app = FastAPI(
    title=settings.ai_service_name,
    version=settings.ai_service_version,
    description="AI-powered enterprise work item generation and orchestration",
)

API_V1_PREFIX = "/api/v1"

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

# Health check
app.include_router(health.router)

# API version 1

api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(work_items.router)
api_v1.include_router(documents.router)

app.include_router(api_v1)