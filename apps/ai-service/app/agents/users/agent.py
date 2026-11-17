import logging
from typing import Any, Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.core.config import settings
from app.tools.registry import get_all_tools

logger = logging.getLogger(__name__)


class UserRequest(BaseModel):
    """Structured interpretation of a user-related request."""

    intent: Literal["search", "other"] = Field(
        description="The type of user operation requested."
    )

    search_query: str | None = Field(
        default=None,
        description="The user's name or email to search for.",
    )


# IMPORTANT: This prompt must be outside the Pydantic model.
USER_SYSTEM_PROMPT = """
You are an intent extraction assistant for DevFlow AI user operations.

Understand the user's natural-language request and extract
the user search information.

Supported operation:
- Search for a user by name or email address.

Rules:
1. Extract the specific person's name or email when provided.
2. Understand natural-language variations.
3. Never invent a name or email address.
4. Do not interpret unrelated work-item requests as user searches.
5. If the user asks to list every user, do not invent a search query.
6. If no specific search target is available, return null.
7. Return only the requested structured information.
"""


class UsersAgent:
    """Handles independent Azure DevOps user searches."""

    def __init__(self, llm=None, tools=None):

        self.llm = llm or ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            use_responses_api=True,
        )

        self.tools = tools if tools is not None else get_all_tools()

        self.tool_map = {tool.name: tool for tool in self.tools}

        self.get_users_tool = self.tool_map.get("get_users")

        if self.get_users_tool is None:
            raise ValueError("get_users tool is not registered.")

        self.request_llm = self.llm.with_structured_output(UserRequest)

    async def execute(self, question: str) -> dict[str, Any]:
        """Interpret and execute a user search request."""

        if not isinstance(question, str) or not question.strip():
            raise ValueError("Question cannot be empty.")

        request = await self.request_llm.ainvoke(
            [
                SystemMessage(content=USER_SYSTEM_PROMPT),
                HumanMessage(content=question.strip()),
            ]
        )

        logger.info(
            "User request interpreted: intent=%s, query=%s",
            request.intent,
            request.search_query,
        )

        if request.intent != "search":
            return {
                "status": "unsupported",
                "message": "This user operation is not currently supported.",
            }

        search_query = request.search_query

        if not isinstance(search_query, str) or not search_query.strip():
            return {
                "status": "needs_clarification",
                "message": (
                    "Please provide a user's name or email address "
                    "so I can search for the account."
                ),
            }

        users = await self._execute_tool(
            self.get_users_tool,
            {"name": search_query.strip()},
        )

        # A tool error must never be treated as an empty result.
        if not isinstance(users, list):
            return {
                "status": "error",
                "message": "Azure DevOps user search failed.",
            }

        if not users:
            return {
                "status": "not_found",
                "search_query": search_query.strip(),
                "total": 0,
                "users": [],
                "message": (
                    f"No Azure DevOps users matched " f"'{search_query.strip()}'."
                ),
            }

        logger.info("Found %s Azure DevOps users.", len(users))

        return {
            "status": "success",
            "search_query": search_query.strip(),
            "total": len(users),
            "users": users,
            "message": (f"Found {len(users)} matching Azure DevOps user(s)."),
        }

    async def __call__(
        self,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        """Allow UsersAgent to be used as a LangGraph node."""

        question = state.get("question")

        if not isinstance(question, str) or not question.strip():
            raise ValueError("Question cannot be empty.")

        result = await self.execute(question)

        return {
            "tool_results": result.get("users", []),
            "agent_response": result.get("message", ""),
            "status": result["status"],
            "error": (result.get("message") if result["status"] == "error" else None),
            "clarification_options": [],
        }

    @staticmethod
    async def _execute_tool(
        tool,
        arguments: dict[str, Any],
    ) -> Any:
        """Execute the registered LangChain tool."""

        try:
            return await tool.ainvoke(arguments)

        except Exception:
            logger.exception(
                "User tool execution failed: %s",
                tool.name,
            )

            return {
                "status": "error",
                "message": f"Tool '{tool.name}' execution failed.",
            }
