
from fastapi import APIRouter
from pydantic import BaseModel

from app.services.langchain_service import LangChainService
from app.schemas.work_items import GenerateWorkItemsRequest

router = APIRouter()

langchain_service = LangChainService()


class LangChainQuestionRequest(BaseModel):
    question: str


@router.post("/langchain/ask")
async def ask_langchain(request: LangChainQuestionRequest):
    answer = await langchain_service.ask(request.question)

    return {
        "status": "success",
        "answer": answer,
    }


@router.post("/langchain/generate-epic")
async def generate_epic(request: GenerateWorkItemsRequest):
    epic = await langchain_service.generate_epic(
        request.requirement
    )

    return {
        "status": "success",
        "epic": epic.model_dump(),
    }


@router.post("/langchain/ask-with-tools")
async def ask_with_tools(request: LangChainQuestionRequest):
    answer = await langchain_service.ask_with_tools(
        request.question
    )

    return {
        "status": "success",
        "answer": answer,
    }
