import logging
from typing import Any, Literal

from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.core.config import settings
from app.agents.supervisor.prompts import DEVFLOW_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class SupervisorDecision(BaseModel):
    """Structured routing decision produced by the Supervisor."""

    next_agent: Literal[
        "work_items",
        "users",
        "rag",
        "generation",
        "clarification",
    ] = Field(description="The specialist agent that should handle the request.")

    reason: str = Field(description="Brief explanation for selecting this destination.")

    clarification_question: str | None = Field(
        default=None,
        description="Question to ask when the user's request is unclear.",
    )


class SupervisorAgent:
    """Routes natural-language requests to specialist agents."""

    def __init__(self, llm=None):

        self.llm = llm or ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            use_responses_api=True,
        )

        self.router = self.llm.with_structured_output(SupervisorDecision)

    async def route(
        self,
        question: str,
        messages: list[AnyMessage] | None = None,
    ) -> SupervisorDecision:
        """Understand the request using the conversation history."""

        if not isinstance(question, str) or not question.strip():
            raise ValueError("Question cannot be empty.")

        conversation = messages or []

        response = await self.router.ainvoke(
            [
                SystemMessage(content=DEVFLOW_SYSTEM_PROMPT),
                *conversation,
                HumanMessage(content=question.strip()),
            ]
        )

        logger.info(
            "Supervisor selected agent: %s | Reason: %s",
            response.next_agent,
            response.reason,
        )

        return response

    async def __call__(
        self,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute the Supervisor as a LangGraph node."""

        question = state.get("question")

        # Validate input before entering the exception handler.
        if not isinstance(question, str) or not question.strip():
            raise ValueError("Question cannot be empty.")

        try:
            decision = await self.route(
                question=question,
                messages=state.get("messages", []),
            )

            if decision.next_agent == "clarification":
                return {
                    "next_agent": "clarification",
                    "intent": "clarification",
                    "agent_response": (
                        decision.clarification_question
                        or "Could you please clarify your request?"
                    ),
                    "status": "needs_clarification",
                    "error": None,
                }

            return {
                "next_agent": decision.next_agent,
                "intent": decision.next_agent,
                "agent_response": "",
                "status": "routing",
                "error": None,
            }

        except Exception:
            logger.exception("Supervisor routing failed.")

            return {
                "next_agent": "clarification",
                "agent_response": (
                    "I couldn't understand your request. "
                    "Could you please rephrase it?"
                ),
                "status": "error",
                "error": "Supervisor routing failed.",
            }
