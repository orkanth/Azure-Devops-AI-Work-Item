
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.core.config import settings


class LangChainService:

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0,
        )

        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are DevFlow AI, an enterprise project management assistant."
            ),
            (
                "human",
                "{question}"
            ),
        ])

        self.chain = self.prompt | self.llm

    async def ask(self, question: str) -> str:

        response = await self.chain.ainvoke({
            "question": question
        })

        return response.content
