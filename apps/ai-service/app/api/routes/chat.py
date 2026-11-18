from functools import lru_cache

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.chat_service import ChatService

router = APIRouter()


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    conversation_id: str | None = None
    project_id: str | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    status: str
    agent_response: str
    intent: str | None = None
    filters: dict = Field(default_factory=dict)
    tool_results: list = Field(default_factory=list)
    sources: list = Field(default_factory=list)
    clarification_options: list = Field(default_factory=list)
    error: str | None = None
    work_item_intent: str | None = None
    proposal: dict | None = None


@lru_cache(maxsize=1)
def get_chat_service() -> ChatService:
    """Create and reuse one ChatService instance."""
    return ChatService()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a natural-language DevFlow AI request."""

    try:
        service = get_chat_service()

        result = await service.chat(
            question=request.question,
            conversation_id=request.conversation_id,
            project_id=request.project_id,
        )

        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="DevFlow AI could not process the request.",
        ) from exc
