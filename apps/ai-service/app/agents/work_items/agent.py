import logging
from typing import Any, Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.core.config import settings
from app.tools.registry import get_all_tools

logger = logging.getLogger(__name__)


class WorkItemRequest(BaseModel):
    """Structured interpretation of a work-item request."""

    intent: Literal["list", "count", "search", "other"]

    assignee_name: str | None = None
    work_item_type: str | None = None
    state: str | None = None
    priority: int | None = None
    is_assigned: bool | None = None


WORK_ITEM_SYSTEM_PROMPT = """
You are an intent extraction assistant for Azure DevOps.

Understand the user's natural-language request and extract
the requested work-item information.

Rules:

1. Identify a specific assignee whenever a person is mentioned.
2. Understand natural-language variations, including:
   - Tasks assigned to Ravi.
   - Show Ravi's tasks.
   - What work is John responsible for?
   - Find tasks owned by Sarah.
3. Never invent an assignee name.
4. Extract work-item type when specified.
5. Extract state when specified.
6. Extract priority when specified.
7. Extract whether the user wants assigned or unassigned items.
8. Do not invent filters that the user did not specify.
9. Return only the requested structured information.
"""


class WorkItemsAgent:

    def __init__(self, llm=None, tools=None):

        self.llm = llm or ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            use_responses_api=True,
        )

        self.tools = tools if tools is not None else get_all_tools()

        self.tool_map = {tool.name: tool for tool in self.tools}

        self.get_users_tool = self.tool_map.get("get_users")
        self.get_work_items_tool = self.tool_map.get("get_work_items")

        if self.get_users_tool is None:
            raise ValueError("get_users tool is not registered.")

        if self.get_work_items_tool is None:
            raise ValueError("get_work_items tool is not registered.")

        self.request_llm = self.llm.with_structured_output(WorkItemRequest)

    async def execute(self, question: str) -> dict[str, Any]:
        """Interpret and execute an Azure DevOps work-item request."""

        if not isinstance(question, str) or not question.strip():
            raise ValueError("Question cannot be empty.")

        # Step 1: Understand the natural-language request.
        request = await self.request_llm.ainvoke(
            [
                SystemMessage(content=WORK_ITEM_SYSTEM_PROMPT),
                HumanMessage(content=question.strip()),
            ]
        )

        logger.info(
            "Work-item request interpreted: intent=%s, assignee=%s",
            request.intent,
            request.assignee_name,
        )

        # Step 2: Build filters from structured LLM output.
        filters = {
            "type": request.work_item_type,
            "state": request.state,
            "priority": request.priority,
            "is_assigned": request.is_assigned,
        }

        filters = {key: value for key, value in filters.items() if value is not None}

        resolved_email = None

        # Step 3: Resolve a specifically requested assignee.
        if request.assignee_name:

            users = await self._execute_tool(
                self.get_users_tool,
                {"name": request.assignee_name},
            )

            # A tool error must never be treated as an empty result.
            if not isinstance(users, list):
                return self._error_response(
                    "Azure DevOps user lookup failed. "
                    "Work-item retrieval was blocked."
                )

            if len(users) == 0:
                return {
                    "status": "not_found",
                    "message": (
                        f"No Azure DevOps user matched " f"'{request.assignee_name}'."
                    ),
                }

            if len(users) > 1:
                return {
                    "status": "needs_clarification",
                    "message": (
                        "Multiple Azure DevOps users matched. "
                        "Please select the correct account."
                    ),
                    "users": [
                        {
                            "display_name": (
                                user.get("displayName")
                                or user.get("display_name")
                                or user.get("name")
                            ),
                            "email": user.get("email"),
                        }
                        for user in users
                    ],
                }

            # Exactly one match: use its verified email.
            email = users[0].get("email")

            if not isinstance(email, str) or not email.strip():
                return self._error_response(
                    "The matching Azure DevOps user does not have "
                    "a valid email address. Work-item retrieval "
                    "was blocked."
                )

            resolved_email = email.strip()

        # Step 4: Add only the verified email to the filters.
        if resolved_email:
            filters["assigned_to"] = resolved_email

        # Step 5: Retrieve work items.
        work_items = await self._execute_tool(
            self.get_work_items_tool,
            filters,
        )

        if not isinstance(work_items, list):
            return self._error_response("Azure DevOps work-item retrieval failed.")

        logger.info(
            "Retrieved %s Azure DevOps work items.",
            len(work_items),
        )

        return {
            "status": "success",
            "intent": request.intent,
            "assignee_email": resolved_email,
            "filters": filters,
            "total": len(work_items),
            "work_items": work_items,
            "assignee_name": request.assignee_name,
        }

    async def __call__(self, state: dict[str, Any]) -> dict[str, Any]:
        """Allow this agent to be used directly as a LangGraph node."""

        result = await self.execute(state["question"])

        status = result["status"]

        if status == "success":
            total = result["total"]
            intent = result["intent"]

            if intent == "count":
                response = f"Found {total} matching work items."
            else:
                response = f"Successfully retrieved {total} work items."

        else:
            response = result.get("message", "Work-item request failed.")

        return {
            "work_item_intent": result.get("intent"),
            "assignee_name": result.get("assignee_name"),
            "assignee_email": result.get("assignee_email"),
            "filters": result.get("filters", {}),
            "tool_results": result.get("work_items", []),
            "agent_response": response,
            "status": status,
            "error": result.get("message") if status == "error" else None,
            "clarification_options": result.get("users", []),
        }

    @staticmethod
    async def _execute_tool(tool, arguments: dict[str, Any]) -> Any:
        """Execute a LangChain tool and preserve execution failures."""

        try:
            return await tool.ainvoke(arguments)

        except Exception:
            logger.exception(
                "Tool execution failed: %s",
                tool.name,
            )

            return {
                "status": "error",
                "message": f"Tool '{tool.name}' execution failed.",
            }

    @staticmethod
    def _error_response(message: str) -> dict[str, Any]:
        return {
            "status": "error",
            "message": message,
        }
