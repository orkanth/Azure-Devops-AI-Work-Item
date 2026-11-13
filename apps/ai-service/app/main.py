
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import health, root, work_items, documents, langchain, nestjs

API_V1_PREFIX = "/api/v1"

app = FastAPI(
    title=settings.ai_service_name,
    version=settings.ai_service_version,
    description="AI-powered enterprise work item generation and orchestration",
)

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

app.include_router(root.router)
app.include_router(health.router)

app.include_router(work_items.router, prefix=API_V1_PREFIX)
app.include_router(documents.router, prefix=API_V1_PREFIX)
app.include_router(langchain.router, prefix=API_V1_PREFIX)
app.include_router(nestjs.router, prefix=API_V1_PREFIX)
