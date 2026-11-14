import re
import json
import logging
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools import tool
from langchain.messages import ToolMessage

from app.schemas.work_items import EpicProposal
from app.core.config import settings
from app.services.nestjs_client import NestJSClient


logger = logging.getLogger(__name__)

nestjs_client = NestJSClient()


# --------------------------------------------------
# Tool 1: Get current date
# --------------------------------------------------

@tool
def get_current_date() -> str:
    """Get the current date and time."""
    return datetime.now().astimezone().isoformat()


# --------------------------------------------------
# Tool 2: Calculator
# --------------------------------------------------

@tool
def add_numbers(a: float, b: float) -> float:
    """Add two numbers and return their sum."""
    return a + b


# --------------------------------------------------
# Tool 3: Get Azure DevOps work items
# --------------------------------------------------

@tool
async def get_work_items(
    type: str | None = None,
    state: str | None = None,
    assigned_to: str | None = None,
    priority: int | None = None,
    is_assigned: bool | None = None,
) -> list[dict]:
    """Retrieve Azure DevOps work items.

    Optional filters:
    - type: Work item type (Epic, Feature, User Story, Task, Bug).
    - state: Work item state.
    - assigned_to: Assignee email address.
    - priority: Priority (1, 2, 3, or 4).
    - is_assigned: True for items assigned to anyone,
      False for unassigned items.

    Use this tool when users ask about Azure DevOps work items.
    """
    return await nestjs_client.get_work_items(
        type=type,
        state=state,
        assigned_to=assigned_to,
        priority=priority,
        is_assigned=is_assigned,
    )

# --------------------------------------------------
# Tool 4: Search Azure DevOps users
# --------------------------------------------------

@tool
async def get_users(name: str) -> list[dict]:
    """Search Azure DevOps users by display name or email address.

    Returns all matching users with their display names and email addresses.
    Use this tool to resolve an assignee before filtering work items.
    """
    return await nestjs_client.search_users(name)


# ==================================================
# LANGCHAIN SERVICE
# ==================================================

class LangChainService:

    def __init__(self):

        # OpenAI LLM
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            use_responses_api=True,
        )

        # Register tools
        self.tools = [
            get_current_date,
            add_numbers,
            get_work_items,
            get_users,
        ]

        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        # Basic LangChain prompt
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

        # Structured output for work-item generation
        self.structured_llm = self.llm.with_structured_output(
            EpicProposal
        )

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

    # --------------------------------------------------
    # Basic LLM question
    # --------------------------------------------------

    async def ask(self, question: str) -> str:

        response = await self.chain.ainvoke(
            {"question": question}
        )

        return response.content

    # --------------------------------------------------
    # Generate Epic
    # --------------------------------------------------

    async def generate_epic(
        self,
        requirement: str,
    ) -> EpicProposal:

        response = await self.epic_chain.ainvoke(
            {"requirement": requirement}
        )

        return response

    # --------------------------------------------------
    # AI Tool Execution
    # --------------------------------------------------

    async def ask_with_tools(self, question: str) -> str:

        messages = [
            (
                "system",
                "You are DevFlow AI, an enterprise project management assistant. "

                "Use available tools to retrieve real Azure DevOps information. "

                "USER RESOLUTION RULES: "

                "When a user mentions an assignee by name, call get_users first. "

                "If exactly one user is returned, use their email address "
                "when calling get_work_items. "

                "If multiple users are returned, do not retrieve work items. "
                "Ask the user to select the correct person by showing their "
                "display names and email addresses. "

                "If no users are returned, tell the user that no matching "
                "Azure DevOps user was found. Do not guess an email address. "

                "Never invent work item counts, details, descriptions, or assignments. "

                "If a tool returns an error, clearly report the failure. "
                "Never interpret a tool error as an empty result. "

                "Only report information supported by successful tool results."
            ),
            ("human", question),
        ]

        # ------------------------------------------
        # User resolution state
        # ------------------------------------------

        # Temporary request detection.
        # We will replace this with structured AI intent
        # classification during the LangGraph implementation.

        user_resolution_required = any(
            term in question.lower()
            for term in ["assigned to", "assigned", "assignee"]
        )
        question_lower = question.lower()

        # Detect whether the user specified a particular assignee.
        assignee_match = re.search(
            r"\bassigned\s+to\s+(.+?)(?=\s+(?:with|and|having|versus|vs)\b|[?.!,]|$)",
            question_lower,
        )

        assignee_name = (
            assignee_match.group(1).strip()
            if assignee_match
            else None
        )

        general_assignee_terms = {
            "all",
            "all users",
            "everyone",
            "anyone",
            "users",
            "me",
            "myself",
        }

        user_resolution_required = (
            assignee_name is not None
            and assignee_name not in general_assignee_terms
        )

        resolved_user_email = None
        user_resolution_error = None

        max_iterations = 5

        # ------------------------------------------
        # LLM tool-calling loop
        # ------------------------------------------

        for iteration in range(max_iterations):

            response = await self.llm_with_tools.ainvoke(messages)

            logger.info("LLM iteration: %s", iteration + 1)

            logger.info(
                "Requested tools: %s",
                [call.get("name") for call in response.tool_calls],
            )

            if not response.tool_calls:
                return response.content

            # Append assistant response
            messages.append(response)

            # --------------------------------------
            # Process user lookup before work items
            # --------------------------------------

            tool_calls = sorted(
                response.tool_calls,
                key=lambda call: (
                    0 if call.get("name") == "get_users" else 1
                ),
            )

            for tool_call in tool_calls:

                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})

                tool_call_id = tool_call["id"]

                selected_tool = next(
                    (
                        tool
                        for tool in self.tools
                        if tool.name == tool_name
                    ),
                    None,
                )

                # ----------------------------------
                # Step 1: Validate tool existence
                # ----------------------------------

                if selected_tool is None:

                    logger.error(
                        "Unknown tool requested: %s",
                        tool_name,
                    )

                    tool_result = {
                        "status": "error",
                        "message": f"Tool '{tool_name}' is not available.",
                    }

                # ----------------------------------
                # Step 2: Validate tool arguments
                # ----------------------------------

                elif not isinstance(tool_args, dict):

                    tool_result = {
                        "status": "error",
                        "message": "Invalid tool arguments. Expected an object.",
                    }

                # ----------------------------------
                # Step 3: Enforce user resolution
                # ----------------------------------

                elif (
                    selected_tool.name == "get_work_items"
                    and user_resolution_required
                ):

                    if user_resolution_error:

                        tool_result = {
                            "status": "error",
                            "message": user_resolution_error,
                        }

                    elif not resolved_user_email:

                        tool_result = {
                            "status": "error",
                            "message": (
                                "Assignee has not been successfully resolved. "
                                "Call get_users before retrieving work items."
                            ),
                        }

                    else:

                        # Never trust an LLM-generated email.
                        # Always use the verified email returned by get_users.

                        tool_args = {
                            **tool_args,
                            "assigned_to": resolved_user_email,
                        }

                        try:

                            tool_result = await selected_tool.ainvoke(
                                tool_args
                            )

                            logger.info(
                                "Retrieved work items for %s",
                                resolved_user_email,
                            )

                        except Exception:

                            logger.exception(
                                "Work-item retrieval failed."
                            )

                            tool_result = {
                                "status": "error",
                                "message": (
                                    "Work-item retrieval failed. "
                                    "Do not invent or assume missing data."
                                ),
                            }

                # ----------------------------------
                # Step 4: Execute other tools
                # ----------------------------------

                else:

                    try:

                        tool_result = await selected_tool.ainvoke(
                            tool_args
                        )

                        logger.info(
                            "Tool executed successfully: %s",
                            selected_tool.name,
                        )

                    except Exception:

                        logger.exception(
                            "Tool execution failed: %s",
                            selected_tool.name,
                        )

                        tool_result = {
                            "status": "error",
                            "message": (
                                f"The tool '{tool_name}' could not complete "
                                "the request. Do not invent or assume missing data."
                            ),
                        }

                        if selected_tool.name == "get_users":
                            user_resolution_error = (
                                "User lookup failed. "
                                "Work-item retrieval is blocked."
                            )

                # ----------------------------------
                # Step 5: Process user lookup result
                # ----------------------------------

                if (
                    selected_tool is not None
                    and selected_tool.name == "get_users"
                    and isinstance(tool_result, list)
                ):

                    if len(tool_result) == 1:

                        email = tool_result[0].get("email")

                        if isinstance(email, str) and email.strip():

                            resolved_user_email = email.strip()

                            user_resolution_error = None

                            logger.info(
                                "User successfully resolved: %s",
                                resolved_user_email,
                            )

                        else:

                            user_resolution_error = (
                                "The matching user does not have "
                                "a valid email address."
                            )

                    elif len(tool_result) > 1:

                        user_resolution_error = (
                            "Multiple users matched. Ask the user to "
                            "select the correct account before retrieving "
                            "work items. Show their display names and emails."
                        )

                    else:

                        user_resolution_error = (
                            "No matching Azure DevOps user was found."
                        )

                # ----------------------------------
                # Step 6: Log work-item retrieval
                # ----------------------------------

                if (
                    selected_tool is not None
                    and selected_tool.name == "get_work_items"
                    and isinstance(tool_result, list)
                ):

                    logger.info(
                        "Retrieved %s work items",
                        len(tool_result),
                    )

                    for item in tool_result:

                        logger.debug(
                            "Work item ID: %s, Title: %s, State: %s",
                            item.get("id"),
                            item.get("title"),
                            item.get("state"),
                        )

                # ----------------------------------
                # Step 7: Return tool result to LLM
                # ----------------------------------

                messages.append(
                    ToolMessage(
                        content=json.dumps(
                            tool_result,
                            default=str,
                        ),
                        tool_call_id=tool_call_id,
                    )
                )

        raise RuntimeError(
            "Maximum tool-calling iterations exceeded."
        )
