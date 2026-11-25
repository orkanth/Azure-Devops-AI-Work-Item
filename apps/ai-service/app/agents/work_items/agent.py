import logging
from typing import Any, Literal

from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.core.config import settings
from app.tools.registry import get_all_tools

logger = logging.getLogger(__name__)


class WorkItemRequest(BaseModel):
    """Structured interpretation of a work-item request."""

    intent: Literal[
        "list",
        "count",
        "search",
        "get_by_id",
        "assign",
        "update",
        "other",
    ]

    assignee_name: str | None = None
    assignee_email: str | None = None
    work_item_type: str | None = None
    state: str | None = None
    priority: int | None = None
    is_assigned: bool | None = None
    work_item_id: int | None = None


WORK_ITEM_SYSTEM_PROMPT = """
You are an intent extraction assistant for Azure DevOps.

Understand the user's current natural-language request and
extract the effective work-item filters.

CONVERSATION CONTEXT RULES:

1. Use previous conversation messages to understand follow-up
   questions, pronouns and incomplete references.

2. Explicit values in the current user message always take
   precedence over previous values.

3. If the user specifies a different assignee, replace the
   previous assignee.

4. If the user specifies a different priority, state or
   work-item type, replace the previous value.

5. For a clear follow-up, resolve missing information from
   the previous conversation.

6. Preserve previous filters only when the current request
   clearly continues or refines the previous request.

7. Do not carry filters from a previous request into a
   complete, independent new request.

8. Never invent an assignee, state, priority or other filter.

9. If a pronoun cannot be resolved confidently, leave the
   assignee_name empty rather than inventing a person.

10. Return the effective filters for the current request,
    not a collection of unrelated historical filters.

EXAMPLES:

Example 1:
Previous request: Show Ravi's tasks.
Current request: Show Revathi's high-priority tasks.

Result:
- assignee_name: Revathi
- priority: 1 (assuming the configured Azure DevOps
  priority convention uses 1 for High)
- Other unspecified filters: None

Example 2:
Previous request: Show Revathi's high-priority tasks.
Current request: Show her completed tasks.

Result:
- assignee_name: Revathi
- state: Completed
- Preserve priority only if this is clearly a refinement
  of the previous filtered request.

Example 3:
Previous request: Show Ravi's tasks.
Current request: Show all active tasks.

Result:
- assignee_name: None
- state: Active
- Do not retain Ravi as the assignee.

WORK ITEM ID EXTRACTION:

1. If the user asks to show, view, retrieve or get
   a specific work item by ID, use intent "get_by_id".

2. Extract the numeric ID into work_item_id.

3. Examples:
   - "Show item #153"
     intent: get_by_id
     work_item_id: 153

   - "Get details of work item 120"
     intent: get_by_id
     work_item_id: 120

4. Do not use list or search when the user requests
   one specific work item by ID.

5. If the user requests a specific item but its ID
   is missing or unclear, do not invent an ID.
   
   
WORK ITEM ASSIGNMENT:

1. If the user asks to assign or reassign a work item,
   use intent "assign".

2. Extract the numeric work item ID into work_item_id.

3. If the target user is specified by display name,
   extract it into assignee_name.

4. If the target user is specified by email address,
   extract it into assignee_email.

5. Examples:

   "Assign item #153 to Ravi"
   - intent: assign
   - work_item_id: 153
   - assignee_name: Ravi

   "Assign #153 to koundeep@gmail.com"
   - intent: assign
   - work_item_id: 153
   - assignee_email: koundeep@gmail.com

6. Never invent an ID or assignee.

7. If the work item ID or assignee is missing,
   request clarification.
   
   
WORK-ITEM EXTRACTION RULES:

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

WORK ITEM UPDATE RULES:

1. If the user asks to move, change, update, set or mark
   a work item, use intent "update".

2. Extract the numeric work item ID into work_item_id.

3. Extract the requested new state into state.

4. Examples:

   "Move #161 to Done"
   - intent: update
   - work_item_id: 161
   - state: Done

   "Move #160 to Resolved"
   - intent: update
   - work_item_id: 160
   - state: Resolved

5. Never treat a state-changing request as a list or search request.

6. Never invent a work item ID or requested state.
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
        self.get_work_item_by_id_tool = self.tool_map.get("get_work_item_by_id")
        self.assign_work_item_tool = self.tool_map.get("assign_work_item")
        self.update_work_item_tool = self.tool_map.get("update_work_item")
        self.request_llm = self.llm.with_structured_output(WorkItemRequest)

        if self.get_users_tool is None:
            raise ValueError("get_users tool is not registered.")

        if self.get_work_item_by_id_tool is None:
            raise ValueError("get_work_item_by_id tool is not registered.")

        if self.get_work_items_tool is None:
            raise ValueError("get_work_items tool is not registered.")

        if self.assign_work_item_tool is None:
            raise ValueError("assign_work_item tool is not registered.")

    async def execute(
        self,
        question: str,
        messages: list[AnyMessage] | None = None,
    ) -> dict[str, Any]:
        """Interpret and execute a work-item request using conversation history."""

        if not isinstance(question, str) or not question.strip():
            raise ValueError("Question cannot be empty.")

        conversation = messages or []

        # Only include valid LangChain messages.
        conversation = [
            message
            for message in conversation
            if isinstance(message, HumanMessage)
            or message.__class__.__name__ == "AIMessage"
        ]

        # Step 1: Understand the current request and its context.
        request = await self.request_llm.ainvoke(
            [
                SystemMessage(content=WORK_ITEM_SYSTEM_PROMPT),
                *conversation,
                HumanMessage(content=question.strip()),
            ]
        )

        logger.info(
            "Work-item request interpreted: intent=%s, assignee=%s, "
            "state=%s, priority=%s",
            request.intent,
            request.assignee_name,
            request.state,
            request.priority,
        )

        # Handle retrieval of one specific work item.
        if request.intent == "get_by_id":

            if request.work_item_id is None or request.work_item_id <= 0:
                return {
                    "status": "needs_clarification",
                    "message": "Please provide a valid work item ID.",
                }

            item = await self._execute_tool(
                self.get_work_item_by_id_tool,
                {"work_item_id": request.work_item_id},
            )

            if not isinstance(item, dict) or item.get("status") == "error":
                return self._error_response(
                    "Unable to retrieve the requested work item."
                )

            return {
                "status": "success",
                "intent": "get_by_id",
                "work_item_id": request.work_item_id,
                "total": 1,
                "work_items": [item],
            }

            # Handle work-item assignment.
        if request.intent == "assign":

            if not request.work_item_id or request.work_item_id <= 0:
                return {
                    "status": "needs_clarification",
                    "message": "Which work item should I assign?",
                }

            if not request.assignee_name and not request.assignee_email:
                return {
                    "status": "needs_clarification",
                    "message": "Who should I assign this work item to?",
                }

            # Step 1: Resolve and verify the Azure DevOps user.
            assignee = await self._resolve_assignee(
                assignee_name=request.assignee_name,
                assignee_email=request.assignee_email,
            )

            if assignee["status"] != "success":
                return assignee

            verified_email = assignee["assignee_email"]

            # Step 2: Execute the assignment.
            assignment_result = await self._execute_tool(
                self.assign_work_item_tool,
                {
                    "work_item_id": request.work_item_id,
                    "assigned_to": verified_email,
                },
            )

            if (
                not isinstance(assignment_result, dict)
                or assignment_result.get("status") == "error"
            ):
                return self._error_response(
                    f"Failed to assign work item #{request.work_item_id}."
                )

            # Step 3: Retrieve the item again to verify the assignment.
            updated_item = await self._execute_tool(
                self.get_work_item_by_id_tool,
                {"work_item_id": request.work_item_id},
            )

            if not isinstance(updated_item, dict):
                return self._error_response(
                    "Assignment was submitted, but verification failed."
                )

            actual_email = (
                updated_item.get("assignedToEmail")
                or updated_item.get("assignedTo")
                or ""
            )

            if actual_email.strip().casefold() != verified_email.casefold():
                return self._error_response(
                    "Assignment could not be verified. "
                    "Please check the work item in Azure DevOps."
                )

            return {
                "status": "success",
                "intent": "assign",
                "work_item_id": request.work_item_id,
                "assignee_name": assignee["assignee_name"],
                "assignee_email": verified_email,
                "total": 1,
                "work_items": [updated_item],
                "message": (
                    f"Successfully assigned work item "
                    f"#{request.work_item_id} to "
                    f"{assignee['assignee_name']}."
                ),
            }
        # Handle work-item updates.
        if request.intent == "update":

            if request.work_item_id is None or request.work_item_id <= 0:
                return {
                    "status": "needs_clarification",
                    "message": "Which work item should I update?",
                }

            if not request.state or not request.state.strip():
                return {
                    "status": "needs_clarification",
                    "message": "What state should I set for this work item?",
                }

            if self.update_work_item_tool is None:
                return self._error_response(
                    "The work-item update tool is not registered."
                )

            updated_item = await self._execute_tool(
                self.update_work_item_tool,
                {
                    "work_item_id": request.work_item_id,
                    "updates": {
                        "state": request.state.strip(),
                    },
                },
            )

            if (
                not isinstance(updated_item, dict)
                or updated_item.get("status") == "error"
            ):
                error_message = (
                    updated_item.get("message", "Unknown update error.")
                    if isinstance(updated_item, dict)
                    else "Unexpected response from update tool."
                )

                if (
                    isinstance(updated_item, dict)
                    and updated_item.get("status_code") == 400
                    and "Allowed states:" in error_message
                ):
                    return {
                        "status": "needs_clarification",
                        "intent": "update",
                        "work_item_id": request.work_item_id,
                        "message": (
                            f"{error_message} " "Which state would you like to use?"
                        ),
                    }

                return self._error_response(error_message)
            return {
                "status": "success",
                "intent": "update",
                "work_item_id": request.work_item_id,
                "state": request.state.strip(),
                "total": 1,
                "work_items": [updated_item],
                "message": (
                    f"Successfully updated work item "
                    f"#{request.work_item_id} to {request.state}."
                ),
            }

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

    async def _resolve_assignee(
        self,
        assignee_name: str | None = None,
        assignee_email: str | None = None,
    ) -> dict[str, Any]:

        identifier = assignee_email or assignee_name

        if not identifier:
            return {
                "status": "needs_clarification",
                "message": "Please specify the assignee name or email.",
            }

        users = await self._execute_tool(
            self.get_users_tool,
            {"name": identifier},
        )

        if not isinstance(users, list):
            return self._error_response("Azure DevOps user lookup failed.")

        if not users:
            return {
                "status": "not_found",
                "message": f"No Azure DevOps user matched '{identifier}'.",
            }

        if assignee_email:
            users = [
                user
                for user in users
                if (user.get("email") or "").strip().casefold()
                == assignee_email.strip().casefold()
            ]

            if not users:
                return {
                    "status": "not_found",
                    "message": f"No Azure DevOps account verified for '{assignee_email}'.",
                }

        if len(users) > 1:
            return {
                "status": "needs_clarification",
                "message": "Multiple Azure DevOps users matched. Please select an account.",
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

        email = users[0].get("email")

        if not isinstance(email, str) or not email.strip():
            return self._error_response(
                "The selected Azure DevOps account has no valid email."
            )

        return {
            "status": "success",
            "assignee_name": (
                users[0].get("displayName")
                or users[0].get("display_name")
                or users[0].get("name")
            ),
            "assignee_email": email.strip(),
        }

    async def __call__(self, state: dict[str, Any]) -> dict[str, Any]:
        """Allow this agent to be used directly as a LangGraph node."""

        result = await self.execute(
            question=state["question"],
            messages=state.get("messages", []),
        )

        status = result["status"]

        if status == "success":
            total = result["total"]
            intent = result["intent"]

            if intent == "count":
                response = f"Found {total} matching work items."

            elif intent == "assign":
                response = result.get(
                    "message",
                    "Work item assignment completed.",
                )
            elif intent == "update":
                response = result.get(
                    "message",
                    "Work item updated successfully.",
                )

            else:
                response = f"Successfully retrieved {total} work items."

        else:
            response = result.get(
                "message",
                "Work-item request failed.",
            )

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
    async def _execute_tool(
        tool,
        arguments: dict[str, Any],
    ) -> Any:
        """Execute a LangChain tool and preserve API error details."""

        try:
            return await tool.ainvoke(arguments)

        except Exception as exc:
            logger.exception(
                "Tool execution failed: %s",
                tool.name,
            )

            response = getattr(exc, "response", None)
            status_code = getattr(response, "status_code", None)

            error_message = None

            if response is not None:
                try:
                    error_data = response.json()

                    if isinstance(error_data, dict):
                        error_message = error_data.get("message")

                        if isinstance(error_message, list):
                            error_message = " ".join(error_message)

                except Exception:
                    logger.warning(
                        "Could not parse error response from tool: %s",
                        tool.name,
                    )

            return {
                "status": "error",
                "status_code": status_code,
                "message": (error_message or f"Tool '{tool.name}' execution failed."),
            }

    @staticmethod
    def _error_response(message: str) -> dict[str, Any]:
        return {
            "status": "error",
            "message": message,
        }
