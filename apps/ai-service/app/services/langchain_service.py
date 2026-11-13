from urllib import response

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.schemas.work_items import EpicProposal
from app.core.config import settings
from datetime import datetime 

from langchain.tools import tool
from langchain.messages import ToolMessage
from app.services.nestjs_client import NestJSClient

@tool
def get_current_date() -> str:
    """Get the current date and time."""
    return datetime.now().astimezone().isoformat()

@tool
def add_numbers(a: float, b: float) -> float:
    """Add two numbers and return their sum."""
    return a + b

nestjs_client = NestJSClient()


@tool
async def get_work_items() -> list[dict]:
    """Retrieve all work items from Azure DevOps, including their
    IDs, titles, types, states, assignees, priorities and URLs.
    Use this tool when the user asks about Azure DevOps work items.
    """
    return await nestjs_client.get_work_items()

class LangChainService:

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            use_responses_api=True,
        )
        self.tools = [
            get_current_date,
            add_numbers,
            get_work_items,
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
    
    async def ask_with_tools(self, question: str) -> str:
        messages = [
            (
                "system",
                "You are DevFlow AI, an enterprise project management assistant. "
                "Use available tools to retrieve real Azure DevOps information. "
                "Never invent work item counts or details.",
            ),
            ("human", question),
        ]

        max_iterations = 5

        for iteration in range(max_iterations):

            response = await self.llm_with_tools.ainvoke(messages)

            print(f"\nIteration: {iteration + 1}")
            print("Tool calls:", response.tool_calls)
            print("Response content:", response.content)

            if not response.tool_calls:
                return response.content

            messages.append(response)

            for tool_call in response.tool_calls:

                selected_tool = next(
                    (
                        tool
                        for tool in self.tools
                        if tool.name == tool_call["name"]
                    ),
                    None,
                )

                if selected_tool is None:
                    raise ValueError(
                        f"Unknown tool: {tool_call['name']}"
                    )

                tool_result = await selected_tool.ainvoke(
                    tool_call["args"]
                )

                print("Executed tool:", selected_tool.name)
                print("Tool result type:", type(tool_result))

                if isinstance(tool_result, list):
                    print("Retrieved records:", len(tool_result))

                messages.append(
                    ToolMessage(
                        content=str(tool_result),
                        tool_call_id=tool_call["id"],
                    )
                )

        raise RuntimeError(
            "Maximum tool-calling iterations exceeded."
        )