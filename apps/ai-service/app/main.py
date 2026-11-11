
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.api.routes import health, work_items, documents
from app.core.config import settings
from app.services.langchain_service import LangChainService


# --------------------------------------------------
# Application configuration
# --------------------------------------------------

API_V1_PREFIX = "/api/v1"

app = FastAPI(
    title=settings.ai_service_name,
    version=settings.ai_service_version,
    description="AI-powered enterprise work item generation and orchestration",
)


# --------------------------------------------------
# CORS configuration
# --------------------------------------------------

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


# --------------------------------------------------
# Services
# --------------------------------------------------

langchain_service = LangChainService()


# --------------------------------------------------
# Request schemas
# --------------------------------------------------

class LangChainQuestionRequest(BaseModel):
    question: str


# --------------------------------------------------
# Root endpoint
# --------------------------------------------------

@app.get("/")
async def root():
    return {
        "message": "Welcome to DevFlow AI",
        "service": settings.ai_service_name,
        "version": settings.ai_service_version,
    }


# --------------------------------------------------
# API v1 routes
# --------------------------------------------------

api_v1 = APIRouter(prefix=API_V1_PREFIX)

api_v1.include_router(work_items.router)
api_v1.include_router(documents.router)


@api_v1.post("/langchain/ask")
async def ask_langchain(request: LangChainQuestionRequest):
    answer = await langchain_service.ask(request.question)

    return {
        "status": "success",
        "answer": answer,
    }


# --------------------------------------------------
# Register routers
# --------------------------------------------------

app.include_router(health.router)
app.include_router(api_v1)
