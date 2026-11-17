import json
import logging
import re

from langchain_core.messages import ToolMessage

from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.schemas.work_items import EpicProposal
from app.tools.registry import get_all_tools
from app.agents.generation.prompts import EPIC_GENERATION_PROMPT

from app.agents.supervisor.prompts import DEVFLOW_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class LLMService:

    def __init__(self):

        # Initialize OpenAI model
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            use_responses_api=True,
        )

        # Load registered LangChain tools
        self.tools = get_all_tools()

        # Bind tools to the LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        # Configure structured output
        self.structured_llm = self.llm.with_structured_output(EpicProposal)

    async def ask(self, question: str) -> str:
        """
        Answer a general user question using the LLM.
        """
        response = await self.llm.ainvoke(question)

        return response.content

    async def generate_epic(self, requirement: str) -> EpicProposal:
        prompt = EPIC_GENERATION_PROMPT.format(requirement=requirement)

        response = await self.structured_llm.ainvoke(prompt)

        return response

    async def ask_with_tools(self, question: str) -> str:
        messages = [
            ("system", DEVFLOW_SYSTEM_PROMPT),
            ("human", question),
        ]

        # ------------------------------------------
        # Step 1: Detect assignee requirements
        # ------------------------------------------

        question_lower = question.lower()

        assignee_match = re.search(
            r"\bassigned\s+to\s+(.+?)(?=\s+(?:with|and|having|versus|vs)\b|[?.!,]|$)",
            question_lower,
        )

        assignee_name = assignee_match.group(1).strip() if assignee_match else None

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
            assignee_name is not None and assignee_name not in general_assignee_terms
        )

        resolved_user_email = None
        user_resolution_error = None

        max_iterations = 5

        # ------------------------------------------
        # Step 2: LLM tool-calling loop
        # ------------------------------------------

        for iteration in range(max_iterations):

            response = await self.llm_with_tools.ainvoke(messages)

            logger.info("LLM iteration: %s", iteration + 1)

            tool_calls = response.tool_calls or []

            logger.info(
                "Requested tools: %s",
                [call.get("name") for call in tool_calls],
            )

            if not tool_calls:
                return response.content

            messages.append(response)

            # Always process user lookup before work items.
            tool_calls = sorted(
                tool_calls,
                key=lambda call: (0 if call.get("name") == "get_users" else 1),
            )

            # --------------------------------------
            # Step 3: Execute requested tools
            # --------------------------------------

            for tool_call in tool_calls:

                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})
                tool_call_id = tool_call["id"]

                selected_tool = next(
                    (tool for tool in self.tools if tool.name == tool_name),
                    None,
                )

                # Validate tool existence.
                if selected_tool is None:

                    tool_result = {
                        "status": "error",
                        "message": f"Tool '{tool_name}' is not available.",
                    }

                # Validate arguments.
                elif not isinstance(tool_args, dict):

                    tool_result = {
                        "status": "error",
                        "message": "Invalid tool arguments. Expected an object.",
                    }

                # Enforce assignee resolution.
                elif (
                    selected_tool.name == "get_work_items" and user_resolution_required
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
                        tool_args = {
                            **tool_args,
                            "assigned_to": resolved_user_email,
                        }

                        tool_result = await self._execute_tool(
                            selected_tool,
                            tool_args,
                        )

                else:

                    tool_result = await self._execute_tool(
                        selected_tool,
                        tool_args,
                    )

                # ----------------------------------
                # Step 4: Process user lookup result
                # ----------------------------------

                if selected_tool is not None and selected_tool.name == "get_users":

                    if isinstance(tool_result, list):

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

                    else:

                        user_resolution_error = (
                            "User lookup failed. " "Work-item retrieval is blocked."
                        )

                # ----------------------------------
                # Step 5: Log work-item retrieval
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

                # ----------------------------------
                # Step 6: Return result to the LLM
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

        raise RuntimeError("Maximum tool-calling iterations exceeded.")

    async def _execute_tool(self, selected_tool, tool_args: dict):
        """
        Execute a registered tool and handle failures.
        """

        try:

            result = await selected_tool.ainvoke(tool_args)

            logger.info(
                "Tool executed successfully: %s",
                selected_tool.name,
            )

            return result

        except Exception:

            logger.exception(
                "Tool execution failed: %s",
                selected_tool.name,
            )

            return {
                "status": "error",
                "message": (
                    f"The tool '{selected_tool.name}' could not complete "
                    "the request. Do not invent or assume missing data."
                ),
            }
