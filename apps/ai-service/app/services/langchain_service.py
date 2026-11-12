from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.schemas.work_items import EpicProposal
from app.core.config import settings
from datetime import datetime 

from langchain.tools import tool

@tool
def get_current_date() -> str:
    """Get the current date and time."""
    return datetime.now().astimezone().isoformat()
class LangChainService:

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0,
        )
        self.tools = [
            get_current_date,
        ]

        self.llm_with_tools = self.llm.bind_tools(
            self.tools
        )
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are DevFlow AI, an enterprise project management assistant.",
                ),
                ("human", "{question}"),
            ]
        )

        self.chain = self.prompt | self.llm
        # Structured output for Azure DevOps work-item generation
        self.structured_llm = self.llm.with_structured_output(EpicProposal)

        self.epic_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                You are DevFlow AI, an enterprise Azure DevOps
                work-item generation assistant.

                Generate a complete Epic with Features,
                User Stories and Tasks.

                Follow the supplied Pydantic schema.
                Generate meaningful titles, descriptions
                and acceptance criteria.

                Do not invent requirements beyond the
                information provided.
                """,
                ),
                ("human", "Business requirement:\n{requirement}"),
            ]
        )

        self.epic_chain = self.epic_prompt | self.structured_llm

    async def ask(self, question: str) -> str:

        response = await self.chain.ainvoke({"question": question})

        return response.content

    async def generate_epic(
        self,
        requirement: str,
    ) -> EpicProposal:

        response = await self.epic_chain.ainvoke({"requirement": requirement})
        return response
